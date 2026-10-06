import base64
import logging

from app.core.config import settings
from app.core.exceptions import DatlyException
from app.services.ai.sarvam.client import sarvam_client

logger = logging.getLogger("datly.ai.sarvam.tts")

def synthesize_speech(text: str) -> bytes:
    if not sarvam_client.client:
        raise DatlyException(
            code="SARVAM_NOT_CONFIGURED",
            message="Speech service is not configured.",
            status_code=503
        )
        
    if not text or not text.strip():
        raise DatlyException(
            code="INVALID_REQUEST",
            message="Text to synthesize cannot be empty.",
            status_code=400
        )
        
    if len(text) > settings.VOICE_MAX_TTS_CHARACTERS:
        raise DatlyException(
            code="INVALID_REQUEST",
            message=f"Text exceeds the maximum length of {settings.VOICE_MAX_TTS_CHARACTERS} characters.",
            status_code=400
        )
        
    try:
        response = sarvam_client.client.text_to_speech.convert(
            text=text,
            language_code=settings.SARVAM_TTS_LANGUAGE,
            speaker=settings.SARVAM_TTS_SPEAKER,
            speech_sample_rate=settings.SARVAM_TTS_SAMPLE_RATE,
            model=settings.SARVAM_TTS_MODEL,
            pace=1.18,
        )
        # response should be TextToSpeechResponse with audios field containing base64 string
        audio_b64 = None
        if hasattr(response, "audios") and response.audios:
            audio_b64 = response.audios[0]
        elif hasattr(response, "audio"):
             audio_b64 = response.audio
             
        if not audio_b64:
             raise DatlyException(
                code="SARVAM_INVALID_RESPONSE",
                message="Received empty audio data from TTS service.",
                status_code=502
             )
             
        return base64.b64decode(audio_b64)
        
    except DatlyException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error(f"Sarvam TTS Error: {e!s}")
        if "timeout" in str(e).lower():
            raise DatlyException(code="SARVAM_TTS_TIMEOUT", message="Voice synthesis timed out.", status_code=504)
        raise DatlyException(code="SARVAM_TTS_FAILED", message="Voice generation failed.", status_code=502)
