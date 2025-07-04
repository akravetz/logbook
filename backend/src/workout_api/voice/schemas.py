"""Voice transcription schemas."""

from pydantic import BaseModel, Field


class TranscriptionResponse(BaseModel):
    """Schema for voice transcription response."""

    transcribed_text: str = Field(
        ..., description="The transcribed text from the audio"
    )
    confidence: float | None = Field(
        None,
        description="Confidence score of the transcription (0.0 to 1.0)",
        ge=0.0,
        le=1.0,
    )
    duration_seconds: float | None = Field(
        None, description="Duration of the audio in seconds", ge=0.0
    )


class TranscriptionError(BaseModel):
    """Schema for transcription error response."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: dict | None = Field(None, description="Additional error details")
