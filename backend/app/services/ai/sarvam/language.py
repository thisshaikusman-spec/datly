import logging
import re

from app.services.ai.sarvam.client import sarvam_client

logger = logging.getLogger("datly.ai.language")

UNICODE_LANG_PATTERNS = [
    (re.compile(r"[\u0B80-\u0BFF]"), "ta-IN"),  # Tamil
    (re.compile(r"[\u0900-\u097F]"), "hi-IN"),  # Hindi / Devanagari
    (re.compile(r"[\u0C00-\u0C7F]"), "te-IN"),  # Telugu
    (re.compile(r"[\u0C80-\u0CFF]"), "kn-IN"),  # Kannada
    (re.compile(r"[\u0D00-\u0D7F]"), "ml-IN"),  # Malayalam
    (re.compile(r"[\u0980-\u09FF]"), "bn-IN"),  # Bengali
    (re.compile(r"[\u0A80-\u0AFF]"), "gu-IN"),  # Gujarati
    (re.compile(r"[\u0A00-\u0A7F]"), "pa-IN"),  # Punjabi
    (re.compile(r"[\u0B00-\u0B7F]"), "od-IN"),  # Odia
]


def detect_language(text: str) -> str:
    """
    Detect language code (e.g. 'ta-IN', 'hi-IN', 'en-IN') from input text.
    First checks Unicode script ranges for instant 0ms detection.
    If Romanized text, uses Sarvam language identification.
    """
    if not text or not text.strip():
        return "en-IN"

    clean = text.strip()

    # 1. Instant Unicode script check
    for pattern, lang_code in UNICODE_LANG_PATTERNS:
        if pattern.search(clean):
            return lang_code

    # 2. Check Romanized / Latin text with Sarvam identify_language
    try:
        client = sarvam_client.client or (sarvam_client.get_client() if hasattr(sarvam_client, "get_client") else None)
        if client and hasattr(client, "text") and hasattr(client.text, "identify_language"):
            res = client.text.identify_language(input=clean[:200])
            lang = getattr(res, "language_code", None)
            if lang and isinstance(lang, str):
                return lang
    except Exception as e:  # noqa: BLE001
        logger.debug(f"[LANGUAGE] identify_language fallback: {e}")

    return "en-IN"


def translate_answer(answer: str, target_lang: str) -> str:
    """
    Translate English answer to target language (e.g. 'ta-IN', 'hi-IN').
    If target language is English or translation fails, returns original answer safely.
    """
    if not answer or not answer.strip():
        return answer

    if not target_lang or target_lang.lower().startswith("en"):
        return answer

    try:
        client = sarvam_client.client or (sarvam_client.get_client() if hasattr(sarvam_client, "get_client") else None)
        if client and hasattr(client, "text") and hasattr(client.text, "translate"):
            res = client.text.translate(
                input=answer,
                source_language_code="en-IN",
                target_language_code=target_lang,
                mode="modern-colloquial"
            )
            translated = getattr(res, "translated_text", None)
            if translated and isinstance(translated, str) and translated.strip():
                logger.info(f"[LANGUAGE] Translated answer to {target_lang} (length={len(translated)})")
                return translated.strip()
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[LANGUAGE] Translation to {target_lang} failed, using English fallback: {e!s}")

    return answer
