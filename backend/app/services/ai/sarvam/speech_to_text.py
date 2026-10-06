import logging
from typing import IO

from app.core.config import settings
from app.core.exceptions import DatlyException
from app.services.ai.sarvam.client import sarvam_client

logger = logging.getLogger("datly.ai.sarvam.stt")


def _extract_sarvam_error(exc: Exception) -> tuple[int, str]:
    """Extract HTTP status code and clean human-readable error from Sarvam exception,
    ensuring no API keys or sensitive authorization headers are ever leaked.
    """
    status_code = getattr(exc, "status_code", None) or 502
    body = getattr(exc, "body", None)

    extracted = ""
    if isinstance(body, dict):
        err_obj = body.get("error")
        if isinstance(err_obj, dict):
            extracted = err_obj.get("message") or err_obj.get("code") or ""
        elif isinstance(err_obj, str):
            extracted = err_obj
        if not extracted:
            extracted = body.get("message") or body.get("detail") or ""
    elif isinstance(body, str):
        extracted = body

    if not extracted:
        extracted = str(exc)

    # Sanitize in case any secret or header could appear in error message string
    if settings.SARVAM_API_KEY and settings.SARVAM_API_KEY in extracted:
        extracted = extracted.replace(settings.SARVAM_API_KEY, "[REDACTED]")

    return status_code, extracted.strip()


def transcribe_audio(
    audio_data: IO[bytes] | bytes | str,
    filename: str = "recording.wav",
    content_type: str = "audio/wav"
) -> dict:
    client = sarvam_client.client or (sarvam_client.get_client() if hasattr(sarvam_client, "get_client") else None)
    if not client:
        raise DatlyException(
            code="SARVAM_NOT_CONFIGURED",
            message="Sarvam API key is missing or speech service is not configured.",
            status_code=503
        )

    clean_content_type = content_type.split(";")[0].strip() if content_type else "audio/wav"
    file_arg = (filename, audio_data, clean_content_type) if isinstance(audio_data, (bytes, bytearray)) else audio_data
    audio_size = len(audio_data) if isinstance(audio_data, (bytes, bytearray)) else "stream"

    # Detect codec if known (e.g. webm, ogg, wav, mp3)
    codec = None
    fname_lower = (filename or "").lower()
    if "webm" in clean_content_type or fname_lower.endswith(".webm"):
        codec = "webm"
    elif "ogg" in clean_content_type or fname_lower.endswith(".ogg") or "opus" in clean_content_type:
        codec = "ogg"
    elif "wav" in clean_content_type or fname_lower.endswith(".wav"):
        codec = "wav"
    elif "mp3" in clean_content_type or fname_lower.endswith(".mp3"):
        codec = "mp3"

    logger.info(
        f"[SARVAM_STT] Sending transcription request: file='{filename}', "
        f"content_type='{clean_content_type}', size={audio_size} bytes, "
        f"model='{settings.SARVAM_STT_MODEL}', codec={codec}"
    )

    try:
        kwargs: dict = {
            "file": file_arg,
            "model": settings.SARVAM_STT_MODEL,
            "mode": getattr(settings, "SARVAM_STT_MODE", "transcribe") or "transcribe",
            "language_code": "unknown",
        }
        if codec:
            kwargs["input_audio_codec"] = codec

        response = client.speech_to_text.transcribe(**kwargs)

        transcript_text = getattr(response, "transcript", "") or getattr(response, "text", "")
        if hasattr(response, 'data') and hasattr(response.data, 'transcript'):
            dt = getattr(response.data, 'transcript', None)
            if isinstance(dt, str) and dt:
                transcript_text = dt
        if not isinstance(transcript_text, str):
            transcript_text = str(transcript_text) if transcript_text else ""

        lang = getattr(response, "language_code", None)
        if hasattr(response, 'data') and hasattr(response.data, 'language_code'):
            data_lang = getattr(response.data, 'language_code', None)
            if isinstance(data_lang, str) and data_lang:
                lang = data_lang
        if not isinstance(lang, str) or not lang:
            lang = "en-IN"

        logger.info(
            f"[SARVAM_STT] Transcription succeeded: '{transcript_text}' (language={lang})"
        )

        return {
            "text": transcript_text.strip(),
            "language_code": lang
        }
    except DatlyException:
        raise
    except Exception as exc:  # noqa: BLE001
        status_code, err_msg = _extract_sarvam_error(exc)
        logger.error(
            f"[SARVAM_STT] Transcription failed: status={status_code}, error={err_msg}"
        )
        if "timeout" in str(exc).lower() or "timeout" in err_msg.lower():
            raise DatlyException(
                code="SARVAM_STT_TIMEOUT",
                message=f"Sarvam STT timed out: {err_msg}",
                status_code=504
            )
        raise DatlyException(
            code="SARVAM_STT_FAILED",
            message=f"Sarvam STT failed ({status_code}): {err_msg}",
            status_code=status_code if status_code in (400, 422, 502, 503, 504) else 502
        )
