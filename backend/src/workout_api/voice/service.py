"""Voice transcription service."""

import asyncio
from pathlib import Path
from typing import BinaryIO

from deepgram import DeepgramClient, PrerecordedOptions

from ..core.config import Settings
from .schemas import TranscriptionResponse


class VoiceTranscriptionService:
    """Service for transcribing audio to text."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.deepgram_api_key = settings.deepgram_api_key
        self.use_mock = settings.is_development or not self.deepgram_api_key

    async def transcribe_audio(self, audio_file: BinaryIO) -> TranscriptionResponse:
        """
        Transcribe audio file to text.

        Args:
            audio_file: Binary audio file data

        Returns:
            TranscriptionResponse with transcribed text

        Raises:
            Exception: If transcription fails
        """
        if self.use_mock:
            return await self._mock_transcription(audio_file)
        else:
            return await self._deepgram_transcription(audio_file)

    async def _mock_transcription(
        self,
        audio_file: BinaryIO,
    ) -> TranscriptionResponse:
        """Mock transcription for development/testing."""
        # Simulate processing time
        await asyncio.sleep(1.0)

        # Mock transcription responses based on common workout phrases
        mock_responses = [
            "Could probably go heavier next session",
            "Felt strong today, good form",
            "Lower back was tight, need to stretch more",
            "Rest pause set, pushed through the burn",
            "Form was sloppy on the last few reps",
            "Great pump today, muscles felt activated",
            "Need to focus on mind-muscle connection",
            "Shoulders felt tight during the movement",
        ]

        # Use a simple hash of the audio size to get consistent mock response
        audio_file.seek(0, 2)  # Seek to end
        audio_size = audio_file.tell()
        audio_file.seek(0)  # Seek back to beginning

        mock_text = mock_responses[audio_size % len(mock_responses)]

        return TranscriptionResponse(
            transcribed_text=mock_text,
            confidence=0.85,
            duration_seconds=2.5,
        )

    async def _deepgram_transcription(
        self,
        audio_file: BinaryIO,
    ) -> TranscriptionResponse:
        """Transcribe using DeepGram API."""
        try:
            # Initialize DeepGram client
            deepgram = DeepgramClient(self.deepgram_api_key)

            # Configure transcription options
            options = PrerecordedOptions(
                model="nova-2",
                language="en-US",
                punctuate=True,
                smart_format=True,
            )

            # Reset file pointer to beginning and transcribe directly
            audio_file.seek(0)
            payload = {"buffer": audio_file}
            response = await deepgram.listen.asyncprerecorded.v("1").transcribe_file(
                payload, options
            )

            # Extract transcription result
            results = response["results"]
            channels = results["channels"]
            alternatives = channels[0]["alternatives"]
            transcript = alternatives[0]

            return TranscriptionResponse(
                transcribed_text=transcript["transcript"],
                confidence=transcript.get("confidence", 0.0),
                duration_seconds=results.get("duration", 0.0),
            )

        except Exception as e:
            raise Exception(f"DeepGram transcription failed: {str(e)}") from e

    def _get_mimetype(self, filename: str) -> str:
        """Get MIME type from filename extension."""
        extension = Path(filename).suffix.lower()
        mime_types = {
            ".webm": "audio/webm",
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".m4a": "audio/mp4",
            ".ogg": "audio/ogg",
        }
        return mime_types.get(extension, "audio/webm")
