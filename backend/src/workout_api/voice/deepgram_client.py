"""DeepGram client interface and implementations."""

from typing import BinaryIO, Protocol

from deepgram import DeepgramClient, FileSource, PrerecordedOptions

from .schemas import DeepgramResponse, TranscriptionResponse


class DeepGramClientProtocol(Protocol):
    """Protocol for DeepGram transcription clients."""

    async def transcribe_audio(self, audio_file: BinaryIO) -> TranscriptionResponse:
        """Transcribe audio file to text."""
        ...


class ProductionDeepGramClient:
    """Production DeepGram client using real API."""

    def __init__(self, api_key: str):
        """Initialize with API key."""
        self.api_key = api_key
        self._client = DeepgramClient(api_key)

    async def transcribe_audio(self, audio_file: BinaryIO) -> TranscriptionResponse:
        """Transcribe using DeepGram API."""
        # Configure transcription options
        options = PrerecordedOptions(
            model="nova-2",
            language="en-US",
            punctuate=True,
            smart_format=True,
        )

        # Reset file pointer to beginning and read the file data
        audio_file.seek(0)
        audio_data = audio_file.read()

        # Create FileSource for the audio data
        payload: FileSource = {
            "buffer": audio_data,
        }

        # Use the correct v3+ SDK method for async transcription
        raw_response = await self._client.listen.asyncrest.v("1").transcribe_file(
            payload, options
        )

        # Parse response using Pydantic schema for type safety
        response = DeepgramResponse.model_validate_json(raw_response.to_json())

        # Extract transcription data from structured response
        primary_alternative = response.results.channels[0].alternatives[0]

        return TranscriptionResponse(
            transcribed_text=primary_alternative.transcript,
            confidence=primary_alternative.confidence,
            duration_seconds=response.metadata.duration,
        )


class MockDeepGramClient:
    """Mock DeepGram client for testing and development."""

    def __init__(self):
        """Initialize mock client."""
        self.mock_responses = [
            "Could probably go heavier next session",
            "Felt strong today, good form",
            "Lower back was tight, need to stretch more",
            "Rest pause set, pushed through the burn",
            "Form was sloppy on the last few reps",
            "Great pump today, muscles felt activated",
            "Need to focus on mind-muscle connection",
            "Shoulders felt tight during the movement",
        ]

    async def transcribe_audio(self, audio_file: BinaryIO) -> TranscriptionResponse:
        """Mock transcription for development/testing."""
        # Use a simple hash of the audio size to get consistent mock response
        audio_file.seek(0, 2)  # Seek to end
        audio_size = audio_file.tell()
        audio_file.seek(0)  # Seek back to beginning

        mock_text = self.mock_responses[audio_size % len(self.mock_responses)]

        return TranscriptionResponse(
            transcribed_text=mock_text,
            confidence=0.85,
            duration_seconds=2.5,
        )
