"""Test voice transcription dependencies."""

from unittest.mock import Mock, patch

import pytest

from workout_api.core.config import Settings
from workout_api.voice.deepgram_client import (
    MockDeepGramClient,
    ProductionDeepGramClient,
)
from workout_api.voice.dependencies import (
    get_deepgram_client_dependency,
    get_voice_transcription_service_dependency,
)
from workout_api.voice.service import VoiceTranscriptionService

# Mark all tests in this file as anyio tests
pytestmark = pytest.mark.anyio


class TestDeepGramClientDependency:
    """Test DeepGram client dependency factory."""

    def test_development_environment_uses_mock_client(self):
        """Test that development environment uses mock client."""
        settings = Settings(
            environment="development",
            deepgram_api_key="test_key",
            database_url="postgresql://test",
            secret_key="test_secret_key_with_32_characters",
        )

        dependency_factory = get_deepgram_client_dependency()
        client = dependency_factory(settings)

        assert isinstance(client, MockDeepGramClient)

    @patch("workout_api.voice.deepgram_client.DeepgramClient")
    def test_production_environment_with_api_key_uses_production_client(
        self, mock_deepgram_client_class
    ):
        """Test that production environment with API key uses production client."""
        # Mock the DeepgramClient constructor
        mock_deepgram_client_class.return_value = Mock()

        settings = Settings(
            environment="production",
            deepgram_api_key="test_api_key",
            database_url="postgresql://test",
            secret_key="test_secret_key_with_32_characters",
        )

        dependency_factory = get_deepgram_client_dependency()
        client = dependency_factory(settings)

        assert isinstance(client, ProductionDeepGramClient)
        assert client.api_key == "test_api_key"
        # Verify the DeepgramClient was called with the API key
        mock_deepgram_client_class.assert_called_once_with("test_api_key")

    def test_production_environment_without_api_key_uses_mock_client(self):
        """Test that production environment without API key uses mock client."""
        settings = Settings(
            environment="production",
            deepgram_api_key="",  # Empty API key
            database_url="postgresql://test",
            secret_key="test_secret_key_with_32_characters",
        )

        dependency_factory = get_deepgram_client_dependency()
        client = dependency_factory(settings)

        assert isinstance(client, MockDeepGramClient)

    def test_test_environment_uses_mock_client(self):
        """Test that test environment uses mock client."""
        settings = Settings(
            environment="test",
            deepgram_api_key="test_key",
            database_url="postgresql://test",
            secret_key="test_secret_key_with_32_characters",
        )

        dependency_factory = get_deepgram_client_dependency()
        client = dependency_factory(settings)

        # Test environment is not development, but no API key should still use mock
        # Based on the logic: is_development OR not deepgram_api_key
        assert isinstance(client, MockDeepGramClient)

    def test_client_caching_behavior(self):
        """Test that dependency factory is properly cached."""
        factory1 = get_deepgram_client_dependency()
        factory2 = get_deepgram_client_dependency()

        # Should be the same function due to @lru_cache
        assert factory1 is factory2


class TestVoiceTranscriptionServiceDependency:
    """Test voice transcription service dependency factory."""

    def test_service_creation_with_mock_client(self):
        """Test service creation with mock client."""
        mock_client = MockDeepGramClient()

        dependency_factory = get_voice_transcription_service_dependency()
        service = dependency_factory(mock_client)

        assert isinstance(service, VoiceTranscriptionService)
        assert service.deepgram_client == mock_client

    @patch("workout_api.voice.deepgram_client.DeepgramClient")
    def test_service_creation_with_production_client(self, mock_deepgram_client_class):
        """Test service creation with production client."""
        # Mock the DeepgramClient constructor
        mock_deepgram_client_class.return_value = Mock()

        production_client = ProductionDeepGramClient("test_key")

        dependency_factory = get_voice_transcription_service_dependency()
        service = dependency_factory(production_client)

        assert isinstance(service, VoiceTranscriptionService)
        assert service.deepgram_client == production_client

    def test_service_dependency_caching(self):
        """Test that service dependency factory is properly cached."""
        factory1 = get_voice_transcription_service_dependency()
        factory2 = get_voice_transcription_service_dependency()

        # Should be the same function due to @lru_cache
        assert factory1 is factory2

    def test_service_with_mock_client_dependency(self):
        """Test service creation using mock client dependency."""
        mock_client = Mock()

        dependency_factory = get_voice_transcription_service_dependency()
        service = dependency_factory(mock_client)

        assert isinstance(service, VoiceTranscriptionService)
        assert service.deepgram_client == mock_client


class TestDependencyIntegration:
    """Test full dependency integration."""

    def test_full_dependency_chain_development(self):
        """Test full dependency chain in development environment."""
        settings = Settings(
            environment="development",
            deepgram_api_key="test_key",
            database_url="postgresql://test",
            secret_key="test_secret_key_with_32_characters",
        )

        # Create client
        client_factory = get_deepgram_client_dependency()
        client = client_factory(settings)

        # Create service
        service_factory = get_voice_transcription_service_dependency()
        service = service_factory(client)

        assert isinstance(client, MockDeepGramClient)
        assert isinstance(service, VoiceTranscriptionService)
        assert service.deepgram_client == client

    @patch("workout_api.voice.deepgram_client.DeepgramClient")
    def test_full_dependency_chain_production(self, mock_deepgram_client_class):
        """Test full dependency chain in production environment."""
        # Mock the DeepgramClient constructor
        mock_deepgram_client_class.return_value = Mock()

        settings = Settings(
            environment="production",
            deepgram_api_key="prod_api_key",
            database_url="postgresql://test",
            secret_key="test_secret_key_with_32_characters",
        )

        # Create client
        client_factory = get_deepgram_client_dependency()
        client = client_factory(settings)

        # Create service
        service_factory = get_voice_transcription_service_dependency()
        service = service_factory(client)

        assert isinstance(client, ProductionDeepGramClient)
        assert client.api_key == "prod_api_key"
        assert isinstance(service, VoiceTranscriptionService)
        assert service.deepgram_client == client
