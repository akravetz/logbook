"""Voice transcription router."""

from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from .dependencies import get_voice_transcription_service
from .schemas import TranscriptionResponse
from .service import VoiceTranscriptionService

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    summary="Transcribe audio to text",
    description="Upload an audio file and get the transcribed text",
)
async def transcribe_audio(
    audio_file: UploadFile = File(..., description="Audio file to transcribe"),
    service: VoiceTranscriptionService = Depends(get_voice_transcription_service),
) -> TranscriptionResponse:
    """
    Transcribe uploaded audio file to text.

    Accepts various audio formats including:
    - WebM audio (.webm)
    - MP3 (.mp3)
    - WAV (.wav)
    - M4A (.m4a)
    - OGG (.ogg)

    Returns the transcribed text with optional confidence score and duration.
    """
    # Validate file type
    if not audio_file.content_type or not audio_file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_file_type",
                "message": "File must be an audio file",
                "details": {"content_type": audio_file.content_type},
            },
        )

    # Validate file size (limit to 10MB)
    max_file_size = 10 * 1024 * 1024  # 10MB
    if audio_file.size and audio_file.size > max_file_size:
        raise HTTPException(
            status_code=413,
            detail={
                "error": "file_too_large",
                "message": "Audio file must be smaller than 10MB",
                "details": {
                    "size_bytes": audio_file.size,
                    "max_size_bytes": max_file_size,
                },
            },
        )

    try:
        # Read audio file
        audio_content = await audio_file.read()

        # Create a file-like object from the content
        audio_buffer = BytesIO(audio_content)

        # Transcribe audio
        result = await service.transcribe_audio(audio_buffer)

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "transcription_failed",
                "message": "Failed to transcribe audio",
                "details": {"error": str(e)},
            },
        ) from e
