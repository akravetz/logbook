"use client"

import { useState, useRef } from 'react'
import { Mic } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/modal'
import { useUIStore } from '@/lib/stores/ui-store'
import { useWorkoutStore } from '@/lib/stores/workout-store'
import {
  useUpdateExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdPatch,
  useTranscribeAudioApiV1VoiceTranscribePost
} from '@/lib/api/generated'
import { useOptimisticMutation } from '@/lib/hooks/use-optimistic-mutation'
import { logger } from '@/lib/logger'
import type { ExerciseExecutionUpdate, ExerciseExecutionResponse } from '@/lib/api/model'

// Utility function to detect supported audio MIME types
function getSupportedAudioMimeType(): { mimeType: string; extension: string } {
  const formats = [
    { mimeType: 'audio/webm;codecs=opus', extension: 'webm' },
    { mimeType: 'audio/webm', extension: 'webm' },
    { mimeType: 'audio/ogg;codecs=opus', extension: 'ogg' },
    { mimeType: 'audio/ogg', extension: 'ogg' },
    { mimeType: 'audio/mp4', extension: 'mp4' },
    { mimeType: 'audio/mpeg', extension: 'mp3' },
    { mimeType: 'audio/wav', extension: 'wav' },
  ]

  for (const format of formats) {
    if (MediaRecorder.isTypeSupported(format.mimeType)) {
      return format
    }
  }

  // Fallback to webm if no specific format is supported
  return { mimeType: 'audio/webm', extension: 'webm' }
}

export function VoiceNoteModal() {
  const { modals, closeAllModals } = useUIStore()
  const { activeWorkout, updateExerciseInWorkout, addPendingOperation } = useWorkoutStore()
  const [isRecording, setIsRecording] = useState(false)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const audioFormatRef = useRef<{ mimeType: string; extension: string } | null>(null)

  const updateExerciseMutation = useUpdateExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdPatch()
  const transcribeMutation = useTranscribeAudioApiV1VoiceTranscribePost()

  // Optimistic voice note mutation
  const voiceNoteMutation = useOptimisticMutation({
    getDependency: (data: { workoutId: number; exerciseId: number; data: ExerciseExecutionUpdate }) => {
      // Check if workout ID is optimistic (negative)
      if (data.workoutId < 0) {
        return `workout-creation-${Math.abs(data.workoutId)}`
      }
      return null
    },
    addOptimistic: (data: { workoutId: number; exerciseId: number; data: ExerciseExecutionUpdate }) => {
      if (!activeWorkout?.id || !modals.voiceNote.exerciseId) {
        throw new Error('No active workout or exercise selected')
      }

      // Find and update the exercise in local state with transcribed text
      const currentExecution = activeWorkout.exercise_executions?.find(
        (ex) => ex.exercise_id === modals.voiceNote.exerciseId
      )

      if (currentExecution && data.data.note_text) {
        const updatedExecution = {
          ...currentExecution,
          note_text: data.data.note_text
        }
        updateExerciseInWorkout(updatedExecution)
      }

      return `voice-note-${modals.voiceNote.exerciseId}-${Date.now()}`
    },
    reconcile: (optimisticId: string, serverData: ExerciseExecutionResponse) => {
      // Update local state with authoritative server data
      // serverData is the complete ExerciseExecutionResponse from the server
      if (serverData && activeWorkout?.id && modals.voiceNote.exerciseId) {
        updateExerciseInWorkout(serverData)
      }
    },
    cleanup: (optimisticId: string) => {
      if (!activeWorkout?.id || !modals.voiceNote.exerciseId) return

      // Remove placeholder text on error
      const currentExecution = activeWorkout.exercise_executions?.find(
        (ex) => ex.exercise_id === modals.voiceNote.exerciseId
      )

      if (currentExecution) {
        const updatedExecution = {
          ...currentExecution,
          note_text: ''
        }
        updateExerciseInWorkout(updatedExecution)
      }
    },
    addPendingOperation,
    mutation: updateExerciseMutation,
    onSuccess: () => 'Voice note transcribed successfully',
    onError: () => 'Failed to transcribe voice note'
  })

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

      // Detect the best supported audio format
      const supportedFormat = getSupportedAudioMimeType()
      audioFormatRef.current = supportedFormat

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: supportedFormat.mimeType
      })
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data)
      }

      mediaRecorder.onstop = async () => {
        const format = audioFormatRef.current || getSupportedAudioMimeType()
        const audioBlob = new Blob(audioChunksRef.current, { type: format.mimeType })

        // Close modal immediately after recording stops
        closeAllModals()

        // Add placeholder text immediately
        addPlaceholderText()

        // Handle transcription in background
        await handleAudioTranscription(audioBlob)

        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
    } catch (error) {
      logger.error('Error starting recording:', error)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  const addPlaceholderText = () => {
    if (!activeWorkout?.id || !modals.voiceNote.exerciseId) {
      return
    }

    // Find and update the exercise in local state with placeholder
    const currentExecution = activeWorkout.exercise_executions?.find(
      (ex) => ex.exercise_id === modals.voiceNote.exerciseId
    )

    if (currentExecution) {
      const updatedExecution = {
        ...currentExecution,
        note_text: 'Transcribing...'
      }
      updateExerciseInWorkout(updatedExecution)
    }
  }

  const handleAudioTranscription = async (audioBlob: Blob) => {
    try {
      if (!activeWorkout?.id || !modals.voiceNote.exerciseId) {
        throw new Error('No active workout or exercise selected')
      }

      const format = audioFormatRef.current || getSupportedAudioMimeType()

      // Call transcription API
      const transcriptionResult = await transcribeMutation.mutateAsync({
        data: {
          audio_file: new File([audioBlob], `voice_note.${format.extension}`, {
            type: format.mimeType
          })
        }
      })

      const transcriptionText = transcriptionResult.transcribed_text

      // Use optimistic mutation to update exercise note
      await voiceNoteMutation.execute({
        workoutId: activeWorkout.id,
        exerciseId: modals.voiceNote.exerciseId,
        data: { note_text: transcriptionText } as ExerciseExecutionUpdate
      })
    } catch (error) {
      logger.error('Error transcribing audio:', error)
      // Cleanup is handled by the optimistic mutation hook
    }
  }

  const handleMouseDown = () => {
    if (!isRecording && !voiceNoteMutation.isExecuting) {
      startRecording()
    }
  }

  const handleMouseUp = () => {
    if (isRecording) {
      stopRecording()
    }
  }

  const handleClose = () => {
    if (isRecording) {
      stopRecording()
    }
    closeAllModals()
  }

  return (
    <Dialog open={modals.voiceNote.open} onOpenChange={handleClose}>
        <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            Voice Note
            {modals.voiceNote.exerciseName && (
              <span className="text-sm font-normal text-gray-500 ml-2">
                for {modals.voiceNote.exerciseName}
              </span>
            )}
          </DialogTitle>
          <DialogDescription>
            Hold down the microphone button to record a voice note that will be transcribed automatically
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col items-center py-8">
          <div className="mb-8">
            <button
              onMouseDown={handleMouseDown}
              onMouseUp={handleMouseUp}
              onTouchStart={handleMouseDown}
              onTouchEnd={handleMouseUp}
              disabled={voiceNoteMutation.isExecuting}
              className={`w-32 h-32 rounded-full flex items-center justify-center ${
                isRecording
                  ? 'bg-red-500 recording-pulse'
                  : 'bg-gray-800 hover:bg-gray-700 transition-all duration-200'
              } ${voiceNoteMutation.isExecuting ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              <Mic className={`${isRecording ? 'w-14 h-14' : 'w-12 h-12'} text-white transition-all duration-200`} />
            </button>
          </div>

          <div className="text-center">
            <h3 className="text-xl font-semibold mb-2">
              {isRecording ? 'Recording...' : voiceNoteMutation.isExecuting ? 'Processing...' : 'Tap and hold to record'}
            </h3>
            <p className="text-gray-600">
              {isRecording
                ? 'Release to stop and transcribe'
                : voiceNoteMutation.isExecuting
                  ? 'Converting speech to text...'
                  : 'Hold to record your voice note'
              }
            </p>
          </div>

          {!isRecording && !voiceNoteMutation.isExecuting && (
            <button
              onClick={handleClose}
              className="mt-8 px-6 py-2 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
