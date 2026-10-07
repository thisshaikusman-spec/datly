import logging
import uuid

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from app.core.exceptions import DatlyException
from app.services.ai.sarvam.speech_to_text import transcribe_audio
from app.services.ai.sarvam.text_to_speech import synthesize_speech
from app.services.analysis_service import AnalysisService

logger = logging.getLogger("datly.voice")

router = APIRouter()

class SynthesizeRequest(BaseModel):
    text: str
    language_code: str | None = None

@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):  # noqa: B008
    logger.info("[VOICE] request received")
    if not file or not file.filename:
        logger.warning("[VOICE] STT error=No audio file uploaded.")
        raise DatlyException(code="INVALID_FILE", message="No audio file uploaded.", status_code=400)

    logger.info(f"[VOICE] filename={file.filename}")
    logger.info(f"[VOICE] content_type={file.content_type}")

    # Read file content directly
    audio_bytes = await file.read()
    audio_size = len(audio_bytes) if audio_bytes else 0
    logger.info(f"[VOICE] audio_size={audio_size}")

    if not audio_bytes:
        logger.warning("[VOICE] STT error=Recorded audio is empty.")
        raise DatlyException(
            code="EMPTY_AUDIO",
            message="Recorded audio is empty. Please speak clearly and try again.",
            status_code=400
        )

    resolved_content_type = file.content_type
    if not resolved_content_type or resolved_content_type == "application/octet-stream":
        if (file.filename or "").lower().endswith(".webm"):
            resolved_content_type = "audio/webm"
        elif (file.filename or "").lower().endswith(".ogg"):
            resolved_content_type = "audio/ogg"
        else:
            resolved_content_type = "audio/wav"

    logger.info("[VOICE] STT request started")
    try:
        result = transcribe_audio(
            audio_bytes,
            filename=file.filename or "recording.webm",
            content_type=resolved_content_type
        )
        logger.info("[VOICE] STT response status=200")
        logger.info(f"[VOICE] transcript={result.get('text', '')}")
        return {
            "success": True,
            "text": result["text"],
            "language_code": result.get("language_code", "en-IN"),
            "transcript": result["text"]
        }
    except DatlyException as de:
        logger.warning(f"[VOICE] STT response status={de.status_code}")
        logger.error(f"[VOICE] STT error={de.message}")
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("[VOICE] STT response status=502")
        logger.error(f"[VOICE] STT error={exc!s}")
        raise DatlyException(
            code="SARVAM_STT_FAILED",
            message=f"Speech transcription failed: {exc!s}",
            status_code=502
        )

@router.post("/synthesize")
async def synthesize(request: SynthesizeRequest):
    audio_bytes = synthesize_speech(request.text, language_code=request.language_code)
    return Response(content=audio_bytes, media_type="audio/wav")


# Simple in-memory store for generated audio
audio_store: dict[str, bytes] = {}

@router.post("/analyze")
async def analyze_voice(
    dataset_id: str = Form(None),
    workspace_id: str = Form(None),
    dataset_ids: str = Form(None),
    file: UploadFile = File(...)  # noqa: B008
):
    if not file or not file.filename:
        raise DatlyException(code="INVALID_FILE", message="No audio file uploaded.", status_code=400)
        
    audio_bytes = await file.read()
    if not audio_bytes:
        raise DatlyException(code="INVALID_FILE", message="Audio file is empty.", status_code=400)
        
    # 1. STT
    logger.info(f"[VOICE] STT started: filename={file.filename}")
    stt_result = transcribe_audio(audio_bytes)
    transcript = stt_result["text"]
    logger.info(f"[VOICE] transcript={transcript}")
    logger.info(f"[VOICE] workspace_id={workspace_id}, dataset_id={dataset_id}")
    
    if not transcript or not transcript.strip():
        raise DatlyException(code="INVALID_QUESTION", message="Could not understand audio. Transcript is empty.", status_code=400)
        
    # 2. Analyze
    if workspace_id:
        from app.services.multi_analysis_service import MultiDatasetAnalysisService
        parsed_ids = None
        if dataset_ids:
            try:
                import json
                parsed_ids = json.loads(dataset_ids) if dataset_ids.startswith("[") else [d.strip() for d in dataset_ids.split(",") if d.strip()]
            except Exception:  # noqa: BLE001
                parsed_ids = [d.strip() for d in dataset_ids.split(",") if d.strip()]
        analysis_response = await MultiDatasetAnalysisService.analyze(
            workspace_id=workspace_id,
            question=transcript,
            target_dataset_ids=parsed_ids,
        )
    elif dataset_id:
        analysis_response = await AnalysisService.analyze(dataset_id, transcript)
    else:
        raise DatlyException(code="MISSING_DATASET_OR_WORKSPACE", message="Either workspace_id or dataset_id must be provided.", status_code=400)
    
    # 3. TTS (non-fatal — analysis must succeed even if TTS fails)
    audio_id = None
    tts_available = False
    try:
        tts_lang = getattr(analysis_response, "language_code", None) or stt_result.get("language_code")
        tts_audio_bytes = synthesize_speech(analysis_response.answer, language_code=tts_lang)
        audio_id = f"audio_{uuid.uuid4().hex[:8]}"
        audio_store[audio_id] = tts_audio_bytes
        tts_available = True
    except Exception as tts_err:  # noqa: BLE001
        import logging as _log
        _log.getLogger("datly.voice").warning(f"TTS failed (non-fatal): {tts_err!s}")

    # 4. Return JSON with analysis and optional audio path
    vis_data = None
    if analysis_response.visualization:
        vis_data = analysis_response.visualization.model_dump()

    vis_list = None
    if getattr(analysis_response, "visualizations", None):
        vis_list = [v.model_dump() for v in analysis_response.visualizations]

    verification_data = None
    if getattr(analysis_response, "verification", None):
        verification_data = analysis_response.verification.model_dump()
    elif getattr(analysis_response, "analysis_plan", None):
        verification_data = analysis_response.analysis_plan.model_dump()

    return {
        "success": True,
        "dataset_id": getattr(analysis_response, "dataset_id", dataset_id),
        "workspace_id": workspace_id,
        "transcript": transcript,
        "language_code": getattr(analysis_response, "language_code", "en-IN"),
        "answer": analysis_response.answer,
        "result": analysis_response.result,
        "visualization": vis_data,
        "visualizations": vis_list,
        "verification": verification_data,
        "clarification_needed": getattr(analysis_response, "clarification_needed", False),
        "clarification_question": getattr(analysis_response, "clarification_question", None),
        "audio": {
            "content_type": "audio/wav",
            "available": tts_available,
            "audio_url": f"/api/v1/voice/audio/{audio_id}" if audio_id else None
        }
    }

@router.get("/audio/{audio_id}")
async def get_audio(audio_id: str):
    if audio_id not in audio_store:
        raise DatlyException(code="AUDIO_NOT_FOUND", message="Audio not found or expired.", status_code=404)
        
    audio_bytes = audio_store[audio_id]
    return Response(content=audio_bytes, media_type="audio/wav")
