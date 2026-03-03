import io
import numpy as np
import librosa
import soundfile as sf
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AudioTooLongError(Exception):
    pass


class AudioTooShortError(Exception):
    pass


def process_audio(audio_bytes: bytes, sample_rate: int = settings.audio_sample_rate) -> np.ndarray:
    """
    VAD pipeline:
    1. Decode audio bytes → numpy float32 array
    2. Trim leading/trailing silence
    3. Validate duration
    Returns cleaned numpy array at target sample_rate.
    """
    try:
        audio_data, sr = sf.read(io.BytesIO(audio_bytes), dtype="float32")
    except Exception:
        # Fallback: use librosa for webm/ogg formats
        audio_data, sr = librosa.load(io.BytesIO(audio_bytes), sr=None, mono=True)

    # Convert to mono if stereo
    if audio_data.ndim > 1:
        audio_data = np.mean(audio_data, axis=1)

    # Resample if needed
    if sr != sample_rate:
        audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=sample_rate)

    # Trim silence
    trimmed, _ = librosa.effects.trim(audio_data, top_db=20)

    duration = len(trimmed) / sample_rate
    logger.info(f"VAD: duration={duration:.2f}s after trimming")

    if duration < 0.5:
        raise AudioTooShortError("Audio too short after silence trimming (< 0.5s)")

    if duration > settings.max_audio_duration_sec:
        raise AudioTooLongError(
            f"Audio duration {duration:.1f}s exceeds max {settings.max_audio_duration_sec}s"
        )

    return trimmed
