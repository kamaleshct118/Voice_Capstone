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
    """

    def __init__(self, lang_code: str = "a"):
        try:
            from kokoro import KPipeline
            self.pipeline = KPipeline(lang_code=lang_code)
            self.available = True
            logger.info(f"Kokoro TTS loaded: lang_code={lang_code}")
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
            audio_chunks = []
            for _, _, audio in self.pipeline(plain_text, voice="af_heart"):
                if audio is not None:
                    audio_chunks.append(audio)

            if audio_chunks:
                full_audio = np.concatenate(audio_chunks, axis=0)
                sf.write(output_path, full_audio, samplerate=24000)
                logger.info(f"TTS synthesis complete: {output_path}")
            else:
                self._write_silent_wav(output_path)
                logger.warning("Kokoro produced no audio — wrote silent WAV")

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
