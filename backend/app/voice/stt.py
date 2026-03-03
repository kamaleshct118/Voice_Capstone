import numpy as np
from faster_whisper import WhisperModel
from pydantic import BaseModel
from app.utils.logger import get_logger

logger = get_logger(__name__)


class STTResult(BaseModel):
    transcript: str
    confidence: float  # 0.0 – 1.0
    language: str


def transcribe(audio_array: np.ndarray, model: WhisperModel) -> STTResult:
    """
    Transcribe a cleaned audio numpy array using Faster-Whisper.
    Returns transcript text, confidence score (avg log_prob), and detected language.
    """
    segments_iter, info = model.transcribe(
        audio_array,
        beam_size=5,
        language=None,  # auto-detect
        vad_filter=False,  # already handled by vad.py
    )

    texts = []
    log_probs = []

    for segment in segments_iter:
        texts.append(segment.text.strip())
        if segment.avg_logprob is not None:
            log_probs.append(segment.avg_logprob)

    transcript = " ".join(t for t in texts if t).strip()
    # Convert avg log_prob (typically -0.5 to 0) to 0–1 confidence
    avg_logprob = float(np.mean(log_probs)) if log_probs else -1.0
    confidence = max(0.0, min(1.0, (avg_logprob + 1.0)))

    logger.info(
        f"STT: '{transcript[:60]}...' lang={info.language} conf={confidence:.2f}"
        if len(transcript) > 60
        else f"STT: '{transcript}' lang={info.language} conf={confidence:.2f}"
    )

    return STTResult(
        transcript=transcript,
        confidence=confidence,
        language=info.language,
    )
