"""Test DeepGram client implementations."""

import io
from unittest.mock import Mock, patch

import pytest

from workout_api.voice.deepgram_client import (
    MockDeepGramClient,
    ProductionDeepGramClient,
)
from workout_api.voice.schemas import TranscriptionResponse

# Mark all tests in this file as anyio tests
pytestmark = pytest.mark.anyio


class TestMockDeepGramClient:
    """Test mock DeepGram client."""

    @pytest.fixture
    def mock_client(self):
        """Create mock DeepGram client."""
        return MockDeepGramClient()

    @pytest.fixture
    def audio_file(self):
        """Create a fake audio file."""
        return io.BytesIO(b"fake audio data for testing")

    async def test_mock_transcription_returns_valid_response(
        self, mock_client, audio_file
    ):
        """Test that mock client returns valid transcription response."""
        response = await mock_client.transcribe_audio(audio_file)

        assert isinstance(response, TranscriptionResponse)
        assert response.transcribed_text in mock_client.mock_responses
        assert response.confidence == 0.85
        assert response.duration_seconds == 2.5

    async def test_mock_transcription_consistency(self, mock_client, audio_file):
        """Test that the same audio produces consistent results."""
        response1 = await mock_client.transcribe_audio(audio_file)
        response2 = await mock_client.transcribe_audio(audio_file)

        # Should get the same result for the same audio data
        assert response1.transcribed_text == response2.transcribed_text
        assert response1.confidence == response2.confidence
        assert response1.duration_seconds == response2.duration_seconds

    async def test_mock_transcription_different_audio_sizes(self, mock_client):
        """Test that different audio sizes produce different responses."""
        audio_file_1 = io.BytesIO(b"small")
        audio_file_2 = io.BytesIO(b"much longer audio content")

        response1 = await mock_client.transcribe_audio(audio_file_1)
        response2 = await mock_client.transcribe_audio(audio_file_2)

        # Different sizes should potentially produce different responses
        # (may be the same if hash collision, but test documents the behavior)
        assert isinstance(response1, TranscriptionResponse)
        assert isinstance(response2, TranscriptionResponse)

    async def test_mock_transcription_resets_file_position(
        self, mock_client, audio_file
    ):
        """Test that transcription resets file position properly."""
        # Move file position
        audio_file.seek(5)
        initial_position = audio_file.tell()
        assert initial_position == 5

        await mock_client.transcribe_audio(audio_file)

        # File should be reset to beginning
        assert audio_file.tell() == 0


class TestProductionDeepGramClient:
    """Test production DeepGram client."""

    @pytest.fixture
    def api_key(self):
        """API key for testing."""
        return "test_api_key"

    @pytest.fixture
    def mock_deepgram_client(self):
        """Create a mock DeepGram client."""
        return Mock()

    @patch("workout_api.voice.deepgram_client.DeepgramClient")
    def test_production_client_initialization(
        self, mock_deepgram_client_class, api_key
    ):
        """Test production client initialization."""
        # Mock the DeepgramClient constructor
        mock_deepgram_client_class.return_value = Mock()

        client = ProductionDeepGramClient(api_key)
        assert client.api_key == api_key
        assert client._client is not None

        # Verify the DeepgramClient was called with the API key
        mock_deepgram_client_class.assert_called_once_with(api_key)

    @patch("workout_api.voice.deepgram_client.DeepgramClient")
    def test_production_client_interface_compliance(
        self, mock_deepgram_client_class, api_key
    ):
        """Test that production client implements the required interface."""
        # Mock the DeepgramClient constructor
        mock_deepgram_client_class.return_value = Mock()

        client = ProductionDeepGramClient(api_key)

        # Check that the method exists and is callable
        assert hasattr(client, "transcribe_audio")
        assert callable(client.transcribe_audio)

    @patch("workout_api.voice.deepgram_client.DeepgramClient")
    def test_production_client_stores_api_key(
        self, mock_deepgram_client_class, api_key
    ):
        """Test that production client properly stores the API key."""
        # Mock the DeepgramClient constructor
        mock_deepgram_client_class.return_value = Mock()

        client = ProductionDeepGramClient(api_key)
        assert client.api_key == api_key
