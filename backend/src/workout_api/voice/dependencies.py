"""Voice transcription dependencies."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from ..core.config import Settings, get_settings
from .deepgram_client import (
    DeepGramClientProtocol,
    MockDeepGramClient,
    ProductionDeepGramClient,
)
from .service import VoiceTranscriptionService


@lru_cache
def get_deepgram_client_dependency():
    """Create DeepGram client dependency factory."""

    def dependency(
        settings: Settings = Depends(get_settings),
    ) -> DeepGramClientProtocol:
        """Create appropriate DeepGram client based on environment."""
        # Use mock in development/test or when no API key is provided
        if settings.is_development or settings.is_test or not settings.deepgram_api_key:
            return MockDeepGramClient()
        else:
            return ProductionDeepGramClient(settings.deepgram_api_key)

    return dependency


@lru_cache
def get_voice_transcription_service_dependency():
    """Create voice transcription service dependency factory."""

    def dependency(
        deepgram_client: DeepGramClientProtocol = Depends(
            get_deepgram_client_dependency()
        ),
    ) -> VoiceTranscriptionService:
        """Create voice transcription service with injected client."""
        return VoiceTranscriptionService(deepgram_client)

    return dependency


# Convenience exports
get_deepgram_client = get_deepgram_client_dependency()
get_voice_transcription_service = get_voice_transcription_service_dependency()

# Type alias for easy use in routers
DeepGramClientDep = Annotated[DeepGramClientProtocol, Depends(get_deepgram_client)]
VoiceTranscriptionServiceDep = Annotated[
    VoiceTranscriptionService, Depends(get_voice_transcription_service)
]
