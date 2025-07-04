"""Voice transcription service."""

import asyncio
from pathlib import Path
from typing import BinaryIO

from ..core.config import Settings
from .schemas import TranscriptionResponse


class VoiceTranscriptionService:
    """Service for transcribing audio to text."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.deepgram_api_key = settings.deepgram_api_key
        self.use_mock = settings.is_development or not self.deepgram_api_key

    async def transcribe_audio(
        self, audio_file: BinaryIO, filename: str = "audio.webm"
    ) -> TranscriptionResponse:
        """
        Transcribe audio file to text.

        Args:
            audio_file: Binary audio file data
            filename: Original filename (used for format detection)

        Returns:
            TranscriptionResponse with transcribed text

        Raises:
            Exception: If transcription fails
        """
        if self.use_mock:
            return await self._mock_transcription(audio_file, filename)
        else:
            return await self._deepgram_transcription(audio_file, filename)

    async def _mock_transcription(
        self,
        audio_file: BinaryIO,
        filename: str,  # noqa: ARG002
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
        audio_file: BinaryIO,  # noqa: ARG002
        filename: str,  # noqa: ARG002
    ) -> TranscriptionResponse:
        """Transcribe using DeepGram API."""
        try:
            # Import DeepGram SDK (will be installed later)
            # from deepgram import Deepgram

            # For now, return a placeholder since DeepGram SDK isn't installed yet
            raise NotImplementedError(
                "DeepGram transcription not yet implemented. "
                "Please set IS_DEVELOPMENT=true to use mock transcription."
            )

            # TODO: Implement actual DeepGram transcription
            # dg_client = Deepgram(self.deepgram_api_key)
            #
            # # Save audio to temporary file
            # with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix) as temp_file:
            #     temp_file.write(audio_file.read())
            #     temp_file.flush()
            #
            #     # Configure transcription options
            #     options = {
            #         "punctuate": True,
            #         "model": "nova-2",
            #         "language": "en-US",
            #     }
            #
            #     # Transcribe audio
            #     with open(temp_file.name, "rb") as audio:
            #         source = {"buffer": audio, "mimetype": self._get_mimetype(filename)}
            #         response = await dg_client.transcription.prerecorded(source, options)
            #
            #     # Extract transcription result
            #     transcript = response["results"]["channels"][0]["alternatives"][0]
            #
            #     return TranscriptionResponse(
            #         transcribed_text=transcript["transcript"],
            #         confidence=transcript.get("confidence"),
            #         duration_seconds=response["results"]["channels"][0].get("duration"),
            #     )

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
