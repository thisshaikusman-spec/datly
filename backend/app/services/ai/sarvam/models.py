from pydantic import BaseModel, Field


class SpeechToTextResult(BaseModel):
    text: str = Field(..., description="Transcribed text from speech")
    language_code: str = Field(default="en-IN", description="Detected language code")


class SynthesizeRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize to speech")
