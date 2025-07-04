/**
 * Generated by orval v6.31.0 🍺
 * Do not edit manually.
 * Workout API
 * A workout tracking API built with FastAPI
 * OpenAPI spec version: 1.0.0
 */
import type { TranscriptionResponseConfidence } from "./transcriptionResponseConfidence";
import type { TranscriptionResponseDurationSeconds } from "./transcriptionResponseDurationSeconds";

/**
 * Schema for voice transcription response.
 */
export interface TranscriptionResponse {
  /** Confidence score of the transcription (0.0 to 1.0) */
  confidence?: TranscriptionResponseConfidence;
  /** Duration of the audio in seconds */
  duration_seconds?: TranscriptionResponseDurationSeconds;
  /** The transcribed text from the audio */
  transcribed_text: string;
}
