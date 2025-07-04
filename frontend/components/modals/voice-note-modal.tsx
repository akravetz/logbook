"use client"

import { useState, useRef } from 'react'
import { Mic } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/modal'
import { useUIStore } from '@/lib/stores/ui-store'
import { useWorkoutStore } from '@/lib/stores/workout-store'
import {
  useUpdateExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdPatch,
  useTranscribeAudioApiV1VoiceTranscribePost
} from '@/lib/api/generated'
import { useCacheUtils } from '@/lib/cache-tags'

export function VoiceNoteModal() {
  const { modals, closeAllModals } = useUIStore()
  const { activeWorkout, updateExerciseInWorkout } = useWorkoutStore()
  const { invalidateWorkoutData } = useCacheUtils()
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])

  const updateExerciseMutation = useUpdateExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdPatch()
  const transcribeMutation = useTranscribeAudioApiV1VoiceTranscribePost()

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data)
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        await handleAudioTranscription(audioBlob)

        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
    } catch (error) {
      console.error('Error starting recording:', error)
      alert('Could not access microphone. Please check permissions.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      setIsProcessing(true)
    }
  }

  const handleAudioTranscription = async (audioBlob: Blob) => {
    try {
      if (!activeWorkout?.id || !modals.voiceNote.exerciseId) {
        throw new Error('No active workout or exercise selected')
      }

      // Call transcription API using the generated hook
      const transcriptionResult = await transcribeMutation.mutateAsync({
        data: { audio_file: new File([audioBlob], 'voice_note.webm', { type: 'audio/webm' }) }
      })

      const transcriptionText = transcriptionResult.transcribed_text

      // Update the exercise note with the transcribed text
      await updateExerciseMutation.mutateAsync({
        workoutId: activeWorkout.id,
        exerciseId: modals.voiceNote.exerciseId,
        data: { note_text: transcriptionText }
      })

      // Invalidate workout data to refresh the UI
      await invalidateWorkoutData()

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

      setIsProcessing(false)
      closeAllModals()
    } catch (error) {
      console.error('Error transcribing audio:', error)
      alert('Failed to transcribe audio. Please try again.')
      setIsProcessing(false)
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
        </DialogHeader>

        <div className="flex flex-col items-center py-8">
          <div className="mb-8">
            <button
              onMouseDown={handleMouseDown}
              onMouseUp={handleMouseUp}
              onTouchStart={handleMouseDown}
              onTouchEnd={handleMouseUp}
              disabled={isProcessing}
              className={`w-32 h-32 rounded-full flex items-center justify-center transition-all duration-200 ${
                isRecording
                  ? 'bg-red-500 recording-pulse'
                  : 'bg-gray-800 hover:bg-gray-700'
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
