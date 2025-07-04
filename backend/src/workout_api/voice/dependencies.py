"""Voice transcription dependencies."""

from functools import lru_cache

from fastapi import Depends

from ..core.config import Settings, get_settings
from .service import VoiceTranscriptionService


@lru_cache
def get_voice_transcription_service_dependency():
    """Create voice transcription service dependency factory."""

    def dependency(settings: Settings = Depends(get_settings)):
        return VoiceTranscriptionService(settings)

    return dependency


# Convenience export
get_voice_transcription_service = get_voice_transcription_service_dependency()
