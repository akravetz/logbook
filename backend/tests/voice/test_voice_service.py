"""Test voice transcription service."""

import io
from unittest.mock import AsyncMock, Mock

import pytest

from workout_api.voice.deepgram_client import (
    MockDeepGramClient,
)
from workout_api.voice.schemas import TranscriptionResponse
from workout_api.voice.service import VoiceTranscriptionService

# Mark all tests in this file as anyio tests
pytestmark = pytest.mark.anyio


class TestVoiceTranscriptionService:
    """Test voice transcription service with dependency injection."""

    @pytest.fixture
    def mock_client(self):
        """Create mock DeepGram client."""
        return MockDeepGramClient()

    @pytest.fixture
    def mock_deepgram_client(self):
        """Create a mock DeepGram client for testing."""
        mock_client = Mock()
        mock_client.transcribe_audio = AsyncMock()
        return mock_client

    @pytest.fixture
    def service_with_mock_client(self, mock_client):
        """Create service with mock client."""
        return VoiceTranscriptionService(mock_client)

    @pytest.fixture
    def service_with_custom_mock(self, mock_deepgram_client):
        """Create service with custom mock client."""
        return VoiceTranscriptionService(mock_deepgram_client)

    @pytest.fixture
    def audio_file(self):
        """Create a fake audio file."""
        return io.BytesIO(b"fake audio data for testing")

    async def test_service_initialization(self, mock_client):
        """Test service initialization with client dependency."""
        service = VoiceTranscriptionService(mock_client)
        assert service.deepgram_client == mock_client

    async def test_transcribe_audio_delegates_to_client(
        self, service_with_custom_mock, mock_deepgram_client, audio_file
    ):
        """Test that service delegates transcription to injected client."""
        # Setup mock response
        expected_response = TranscriptionResponse(
            transcribed_text="Test transcription", confidence=0.95, duration_seconds=3.5
        )
        mock_deepgram_client.transcribe_audio.return_value = expected_response

        # Call service
        result = await service_with_custom_mock.transcribe_audio(audio_file)

        # Verify delegation
        mock_deepgram_client.transcribe_audio.assert_called_once_with(audio_file)
        assert result == expected_response

    async def test_transcribe_audio_with_mock_client(
        self, service_with_mock_client, audio_file
    ):
        """Test transcription with actual mock client."""
        result = await service_with_mock_client.transcribe_audio(audio_file)

        assert isinstance(result, TranscriptionResponse)
        assert result.transcribed_text in [
            "Could probably go heavier next session",
            "Felt strong today, good form",
            "Lower back was tight, need to stretch more",
            "Rest pause set, pushed through the burn",
            "Form was sloppy on the last few reps",
            "Great pump today, muscles felt activated",
            "Need to focus on mind-muscle connection",
            "Shoulders felt tight during the movement",
        ]
        assert result.confidence == 0.85
        assert result.duration_seconds == 2.5

    async def test_transcribe_audio_propagates_client_errors(
        self, service_with_custom_mock, mock_deepgram_client, audio_file
    ):
        """Test that service propagates client errors properly."""
        # Setup mock to raise exception
        mock_deepgram_client.transcribe_audio.side_effect = Exception("Client error")

        # Test that exception is propagated
        with pytest.raises(Exception) as exc_info:
            await service_with_custom_mock.transcribe_audio(audio_file)

        assert "Client error" in str(exc_info.value)
        mock_deepgram_client.transcribe_audio.assert_called_once_with(audio_file)

    async def test_transcribe_audio_consistency(
        self, service_with_mock_client, audio_file
    ):
        """Test that service produces consistent results with mock client."""
        result1 = await service_with_mock_client.transcribe_audio(audio_file)
        result2 = await service_with_mock_client.transcribe_audio(audio_file)

        # Should be consistent due to mock client behavior
        assert result1.transcribed_text == result2.transcribed_text
        assert result1.confidence == result2.confidence
        assert result1.duration_seconds == result2.duration_seconds

    async def test_service_with_production_client_interface(self, audio_file):
        """Test that service works with production client interface."""
        # Create a mock that behaves like production client
        mock_production_client = Mock()
        mock_production_client.transcribe_audio = AsyncMock()
        mock_production_client.transcribe_audio.return_value = TranscriptionResponse(
            transcribed_text="Production transcription",
            confidence=0.98,
            duration_seconds=4.2,
        )

        service = VoiceTranscriptionService(mock_production_client)
        result = await service.transcribe_audio(audio_file)

        assert result.transcribed_text == "Production transcription"
        assert result.confidence == 0.98
        assert result.duration_seconds == 4.2
        mock_production_client.transcribe_audio.assert_called_once_with(audio_file)
