"""DeepGram client interface and implementations."""

from typing import BinaryIO, Protocol

from deepgram import DeepgramClient, PrerecordedOptions

from .schemas import TranscriptionResponse


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
        try:
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
            response = await self._client.listen.asyncrest.v("1").transcribe_file(
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
