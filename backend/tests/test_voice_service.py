"""Test voice transcription service."""

import io
from unittest.mock import AsyncMock, Mock, patch

import pytest

from workout_api.core.config import Settings
from workout_api.voice.schemas import TranscriptionResponse
from workout_api.voice.service import VoiceTranscriptionService

# Mark all tests in this file as anyio tests
pytestmark = pytest.mark.anyio


class TestVoiceTranscriptionService:
    """Test voice transcription service."""

    @pytest.fixture
    def mock_settings(self, test_settings: Settings):
        """Mock settings for development mode."""
        # Create new settings with empty deepgram key to force mock mode
        settings_dict = test_settings.model_dump()
        settings_dict["deepgram_api_key"] = ""  # Override to force mock mode
        return Settings(**settings_dict)

    @pytest.fixture
    def production_settings(self, test_settings: Settings):
        """Production settings with deepgram key."""
        # Create production settings to test actual DeepGram usage
        settings_dict = test_settings.model_dump()
        settings_dict["environment"] = "production"  # Not development mode
        return Settings(**settings_dict)

    @pytest.fixture
    def production_service(self, production_settings: Settings):
        """Create voice transcription service for production mode."""
        return VoiceTranscriptionService(production_settings)

    @pytest.fixture
    def service(self, test_settings: Settings):
        """Create voice transcription service."""
        return VoiceTranscriptionService(test_settings)

    @pytest.fixture
    def mock_service(self, mock_settings: Settings):
        """Create voice transcription service in mock mode."""
        return VoiceTranscriptionService(mock_settings)

    @pytest.fixture
    def audio_file(self):
        """Create a fake audio file."""
        return io.BytesIO(b"fake audio data for testing")

    async def test_service_initialization(self, service, test_settings):
        """Test service initialization."""
        assert service.settings == test_settings
        assert service.deepgram_api_key == "test_deepgram_key"
        # In development mode, service always uses mock regardless of API key
        assert service.use_mock is True

    async def test_service_mock_mode(self, mock_service, mock_settings):  # noqa: ARG002
        """Test service in mock mode."""
        assert mock_service.use_mock is True

    async def test_production_service_uses_deepgram(
        self,
        production_service,
        production_settings,  # noqa: ARG002
    ):
        """Test service in production mode with API key uses DeepGram."""
        assert production_service.use_mock is False
        assert production_service.deepgram_api_key == "test_deepgram_key"

    async def test_mock_transcription(self, mock_service, audio_file):
        """Test mock transcription."""
        response = await mock_service.transcribe_audio(audio_file)

        assert isinstance(response, TranscriptionResponse)
        assert response.transcribed_text in [
            "Could probably go heavier next session",
            "Felt strong today, good form",
            "Lower back was tight, need to stretch more",
            "Rest pause set, pushed through the burn",
            "Form was sloppy on the last few reps",
            "Great pump today, muscles felt activated",
            "Need to focus on mind-muscle connection",
            "Shoulders felt tight during the movement",
        ]
        assert response.confidence == 0.85
        assert response.duration_seconds == 2.5

    async def test_deepgram_transcription_error_handling(
        self, production_service, audio_file
    ):
        """Test error handling in DeepGram transcription."""
        with patch("workout_api.voice.service.DeepgramClient") as mock_client:
            mock_client.side_effect = Exception("DeepGram API Error")

            with pytest.raises(Exception) as exc_info:
                await production_service.transcribe_audio(audio_file)

            assert "DeepGram transcription failed" in str(exc_info.value)

    def test_mime_type_detection(self, service):
        """Test MIME type detection."""
        assert service._get_mimetype("test.webm") == "audio/webm"
        assert service._get_mimetype("test.mp3") == "audio/mpeg"
        assert service._get_mimetype("test.wav") == "audio/wav"
        assert service._get_mimetype("test.m4a") == "audio/mp4"
        assert service._get_mimetype("test.ogg") == "audio/ogg"
        assert service._get_mimetype("test.unknown") == "audio/webm"  # Default

    async def test_transcribe_audio_uses_mock_in_development(
        self, mock_service, audio_file
    ):
        """Test that transcribe_audio uses mock in development mode."""
        response = await mock_service.transcribe_audio(audio_file)

        # Should use mock transcription
        assert isinstance(response, TranscriptionResponse)
        assert response.transcribed_text is not None
        assert response.confidence == 0.85

    async def test_transcribe_audio_uses_deepgram_with_key(
        self, production_service, audio_file
    ):
        """Test that transcribe_audio attempts to use DeepGram when key is provided in production."""
        with patch("workout_api.voice.service.DeepgramClient") as mock_client:
            # Mock the response structure
            mock_response = {
                "results": {
                    "channels": [
                        {
                            "alternatives": [
                                {
                                    "transcript": "Test transcription",
                                    "confidence": 0.95,
                                }
                            ]
                        }
                    ],
                    "duration": 3.5,
                }
            }

            # Create the full mock chain properly
            mock_transcribe_obj = Mock()
            mock_transcribe_obj.transcribe_file = AsyncMock(return_value=mock_response)

            mock_version_obj = Mock()
            mock_version_obj.return_value = mock_transcribe_obj

            mock_prerecorded = Mock()
            mock_prerecorded.v = mock_version_obj

            mock_listen = Mock()
            mock_listen.asyncprerecorded = mock_prerecorded

            mock_deepgram = Mock()
            mock_deepgram.listen = mock_listen

            mock_client.return_value = mock_deepgram

            response = await production_service.transcribe_audio(audio_file)

            assert isinstance(response, TranscriptionResponse)
            assert response.transcribed_text == "Test transcription"
            assert response.confidence == 0.95
            assert response.duration_seconds == 3.5

    async def test_filename_parameter_handling(self, mock_service, audio_file):
        """Test that filename parameter is handled correctly."""
        response = await mock_service.transcribe_audio(audio_file)

        assert isinstance(response, TranscriptionResponse)
        assert response.transcribed_text is not None
