import os
import re
import numpy as np
from app.utils.logger import get_logger

logger = get_logger(__name__)


class KokoroEngine:
    """
    Kokoro TTS engine wrapper.
    Loaded once at startup; reused for all requests.
    Converts SSML text → WAV audio file.
    Runs on GPU (CUDA) when available, falls back to CPU.
    """

    def __init__(self, lang_code: str = "a"):
        # Resolve device — import here to avoid circular imports at module level
        try:
            from app.core.device import DEVICE_TTS
            self._device = DEVICE_TTS
        except Exception:
            self._device = "cpu"

        try:
            from kokoro import KPipeline
            # Pass device so Kokoro moves its tensors to GPU when available
            self.pipeline = KPipeline(lang_code=lang_code, device=self._device)
            self.available = True
            logger.info(f"Kokoro TTS loaded: lang_code={lang_code} device={self._device}")
            print(f"\033[92m[AI] Kokoro TTS running on {self._device.upper()}\033[0m", flush=True)
        except Exception as e:
            logger.warning(f"Kokoro TTS unavailable: {e}. Falling back to silent mode.")
            self.pipeline = None
            self.available = False

    def _strip_ssml_tags(self, ssml: str) -> str:
        """Remove SSML tags, preserving plain text for synthesis."""
        text = re.sub(r"<[^>]+>", " ", ssml)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def synthesize(self, ssml_text: str, output_path: str) -> str:
        """
        Convert SSML text to WAV audio file.
        Returns the output_path on success.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if not self.available or self.pipeline is None:
            # Create a minimal silent WAV as fallback
            self._write_silent_wav(output_path)
            logger.warning(f"TTS unavailable — wrote silent WAV: {output_path}")
            return output_path

        plain_text = self._strip_ssml_tags(ssml_text)

        try:
            import soundfile as sf
            wrote_audio = False
            with sf.SoundFile(
                output_path, mode="w", samplerate=24000, channels=1, subtype="PCM_16"
            ) as f:
                for _, _, audio in self.pipeline(plain_text, voice="af_heart"):
                    if audio is not None:
                        # Move GPU tensor → CPU numpy before soundfile can write it
                        import torch
                        if isinstance(audio, torch.Tensor):
                            chunk = audio.detach().cpu().numpy()
                        else:
                            chunk = np.asarray(audio)
                        chunk = np.squeeze(chunk).astype(np.float32)
                        f.write(chunk)
                        wrote_audio = True

            if wrote_audio:
                logger.info(f"TTS synthesis complete (streamed): {output_path}")
            else:
                self._write_silent_wav(output_path)
                logger.warning("Kokoro produced no audio — wrote silent WAV")

            # Release unused VRAM after synthesis (important for 4GB GPU)
            try:
                from app.core.device import free_gpu_cache
                free_gpu_cache()
            except Exception:
                pass

        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            self._write_silent_wav(output_path)

        return output_path

    def _write_silent_wav(self, path: str, duration_sec: float = 1.0) -> None:
        """Write a short silent WAV file as a fallback."""
        try:
            import soundfile as sf
            samples = int(24000 * duration_sec)
            sf.write(path, np.zeros(samples, dtype=np.float32), samplerate=24000)
        except Exception:
            # Absolute last resort: write minimal valid WAV header
            with open(path, "wb") as f:
                f.write(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00"
                        b"\x01\x00\x01\x00\x80\x3e\x00\x00\x00\x7d\x00\x00"
                        b"\x02\x00\x10\x00data\x00\x00\x00\x00")
