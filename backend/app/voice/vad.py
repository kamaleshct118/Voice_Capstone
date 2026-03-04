# app/voice/vad.py
# ── Voice Activity Detection & Audio Preprocessing ────────────────
# Decodes browser audio (WebM/Opus, WAV, OGG, etc.) using PyAV,
# trims silence, validates duration, and returns a clean numpy array
# at the target sample rate for Whisper STT.
# ──────────────────────────────────────────────────────────────────

import io
import numpy as np
import librosa
import av
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AudioTooLongError(Exception):
    pass


class AudioTooShortError(Exception):
    pass


def _decode_with_av(audio_bytes: bytes) -> tuple[np.ndarray, int]:
    """
    Decode any browser audio format (WebM, Opus, OGG, MP4, WAV)
    using PyAV (ffmpeg bindings). Returns (float32 numpy array, sample_rate).
    """
    container = av.open(io.BytesIO(audio_bytes))
    stream = next(s for s in container.streams if s.type == "audio")
    sample_rate = stream.codec_context.sample_rate or 16000

    frames = []
    resampler = av.AudioResampler(
        format="fltp",   # float32 planar
        layout="mono",
        rate=sample_rate,
    )

    for packet in container.demux(stream):
        for frame in packet.decode():
            # resample() returns a LIST of AudioFrame in newer PyAV versions
            resampled = resampler.resample(frame)
            for rf in resampled:
                arr = rf.to_ndarray()   # shape: (channels, n_samples)
                frames.append(arr[0])  # take channel 0 (mono)

    # Flush remaining buffered frames
    for rf in resampler.resample(None):
        arr = rf.to_ndarray()
        frames.append(arr[0])

    container.close()

    if not frames:
        raise ValueError("No audio frames decoded from the stream")

    audio_data = np.concatenate(frames, axis=0).astype(np.float32)
    return audio_data, sample_rate


def process_audio(audio_bytes: bytes, sample_rate: int = settings.audio_sample_rate) -> np.ndarray:
    """
    VAD pipeline:
    1. Decode audio bytes (WebM/Opus/WAV/OGG) → numpy float32 array via PyAV
    2. Resample to target sample rate (16 kHz for Whisper)
    3. Trim leading/trailing silence
    4. Validate duration (0.5s – max_audio_duration_sec)

    Returns cleaned numpy array ready for Faster-Whisper.
    """
    # ── Decode audio ──────────────────────────────────────────────
    try:
        audio_data, sr = _decode_with_av(audio_bytes)
        logger.info(f"[VAD] Decoded via PyAV: sr={sr} samples={len(audio_data)}")
    except Exception as av_err:
        logger.warning(f"[VAD] PyAV failed ({av_err}), falling back to librosa")
        try:
            audio_data, sr = librosa.load(io.BytesIO(audio_bytes), sr=None, mono=True)
        except Exception as lb_err:
            raise RuntimeError(
                f"Could not decode audio. PyAV: {av_err} | librosa: {lb_err}"
            )

    # ── Resample to Whisper target rate ───────────────────────────
    if sr != sample_rate:
        audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=sample_rate)
        logger.info(f"[VAD] Resampled {sr}Hz → {sample_rate}Hz")

    # ── Trim silence ─────────────────────────────────────────────
    trimmed, _ = librosa.effects.trim(audio_data, top_db=20)

    duration = len(trimmed) / sample_rate
    logger.info(f"[VAD] Duration after trim: {duration:.2f}s")

    # ── Validate ──────────────────────────────────────────────────
    if duration < 0.5:
        raise AudioTooShortError("Audio too short after silence trimming (< 0.5s). Please speak clearly.")

    if duration > settings.max_audio_duration_sec:
        raise AudioTooLongError(
            f"Audio duration {duration:.1f}s exceeds maximum {settings.max_audio_duration_sec}s"
        )

    return trimmed
