"""Voice transcription service."""

from typing import BinaryIO

from .deepgram_client import DeepGramClientProtocol
from .schemas import TranscriptionResponse


class VoiceTranscriptionService:
    """Service for transcribing audio to text using dependency injection."""

    def __init__(self, deepgram_client: DeepGramClientProtocol):
        """Initialize with DeepGram client dependency."""
        self.deepgram_client = deepgram_client

    async def transcribe_audio(self, audio_file: BinaryIO) -> TranscriptionResponse:
        """
        Transcribe audio file to text using injected client.

        Args:
            audio_file: Binary audio file data

        Returns:
            TranscriptionResponse with transcribed text

        Raises:
            Exception: If transcription fails
        """
        return await self.deepgram_client.transcribe_audio(audio_file)
