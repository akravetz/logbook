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
import { logger } from '@/lib/logger'
import { toast } from 'sonner'

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
  const { activeWorkout, updateExerciseInWorkout } = useWorkoutStore()
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const audioFormatRef = useRef<{ mimeType: string; extension: string } | null>(null)

  const updateExerciseMutation = useUpdateExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdPatch()
  const transcribeMutation = useTranscribeAudioApiV1VoiceTranscribePost()

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
      setIsProcessing(false) // Reset processing state since we're not blocking UI
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

      // Call transcription API using the generated hook
      const transcriptionResult = await transcribeMutation.mutateAsync({
        data: {
          audio_file: new File([audioBlob], `voice_note.${format.extension}`, {
            type: format.mimeType
          })
        }
      })

      const transcriptionText = transcriptionResult.transcribed_text

      // Update the exercise note with the transcribed text
      await updateExerciseMutation.mutateAsync({
        workoutId: activeWorkout.id,
        exerciseId: modals.voiceNote.exerciseId,
        data: { note_text: transcriptionText }
      })

      // Find and update the exercise in local state
      const currentExecution = activeWorkout.exercise_executions?.find(
        (ex) => ex.exercise_id === modals.voiceNote.exerciseId
      )

      if (currentExecution) {
        const updatedExecution = {
          ...currentExecution,
          note_text: transcriptionText
        }
        updateExerciseInWorkout(updatedExecution)
      }

      toast.success('Voice note transcribed successfully')
    } catch (error) {
      logger.error('Error transcribing audio:', error)

      // Replace placeholder with empty text on error
      if (activeWorkout?.id && modals.voiceNote.exerciseId) {
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
      }

      toast.error('Failed to transcribe voice note')
    }
  }

  const handleMouseDown = () => {
    if (!isRecording && !isProcessing) {
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
              disabled={isProcessing}
              className={`w-32 h-32 rounded-full flex items-center justify-center ${
                isRecording
                  ? 'bg-red-500 recording-pulse'
                  : 'bg-gray-800 hover:bg-gray-700 transition-all duration-200'
              } ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              <Mic className={`${isRecording ? 'w-14 h-14' : 'w-12 h-12'} text-white transition-all duration-200`} />
            </button>
          </div>

          <div className="text-center">
            <h3 className="text-xl font-semibold mb-2">
              {isRecording ? 'Recording...' : isProcessing ? 'Processing...' : 'Tap and hold to record'}
            </h3>
            <p className="text-gray-600">
              {isRecording
                ? 'Release to stop and transcribe'
                : isProcessing
                  ? 'Converting speech to text...'
                  : 'Hold to record your voice note'
              }
            </p>
          </div>

          {!isRecording && !isProcessing && (
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
