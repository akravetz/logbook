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


# Deepgram Response Schemas


class DeepgramWord(BaseModel):
    """Individual word in Deepgram transcription."""

    word: str = Field(..., description="The word as recognized")
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    confidence: float = Field(..., description="Confidence score for this word")
    punctuated_word: str = Field(..., description="Word with punctuation applied")


class DeepgramSentence(BaseModel):
    """Sentence in Deepgram paragraphs."""

    text: str = Field(..., description="The sentence text")
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")


class DeepgramParagraph(BaseModel):
    """Paragraph containing sentences."""

    sentences: list[DeepgramSentence] = Field(..., description="List of sentences")
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    num_words: int = Field(..., description="Number of words in paragraph")


class DeepgramParagraphs(BaseModel):
    """Container for paragraphs and transcript."""

    transcript: str = Field(..., description="Full transcript with paragraphs")
    paragraphs: list[DeepgramParagraph] = Field(..., description="List of paragraphs")


class DeepgramAlternative(BaseModel):
    """Alternative transcription result."""

    transcript: str = Field(..., description="The transcribed text")
    confidence: float = Field(..., description="Overall confidence score")
    words: list[DeepgramWord] = Field(..., description="List of words with timing")
    paragraphs: DeepgramParagraphs | None = Field(
        None, description="Paragraph structure if requested"
    )


class DeepgramChannel(BaseModel):
    """Audio channel transcription."""

    alternatives: list[DeepgramAlternative] = Field(
        ..., description="List of transcription alternatives"
    )


class DeepgramResults(BaseModel):
    """Results container for all channels."""

    channels: list[DeepgramChannel] = Field(..., description="List of audio channels")


class DeepgramModelInfo(BaseModel):
    """Information about the model used."""

    name: str = Field(..., description="Model name")
    version: str = Field(..., description="Model version")
    arch: str = Field(..., description="Model architecture")


class DeepgramMetadata(BaseModel):
    """Metadata about the transcription request."""

    transaction_key: str = Field(..., description="Transaction key (deprecated)")
    request_id: str = Field(..., description="Unique request identifier")
    sha256: str | None = Field(None, description="SHA256 hash of the audio")
    created: str = Field(..., description="ISO timestamp when request was created")
    duration: float = Field(..., description="Duration of audio in seconds")
    channels: int = Field(..., description="Number of audio channels")
    models: list[str] = Field(..., description="List of model IDs used")
    model_info: dict[str, DeepgramModelInfo] = Field(
        ..., description="Detailed model information"
    )


class DeepgramResponse(BaseModel):
    """Complete Deepgram API response."""

    metadata: DeepgramMetadata = Field(..., description="Request metadata")
    results: DeepgramResults = Field(..., description="Transcription results")
