# app/core/device.py
# ── Global AI Device Detection ──────────────────────────────────────────────
# Single source of truth for which device (cuda / cpu) all local AI models use.
# Import DEVICE and COMPUTE_TYPE from here — never hard-code "cpu" or "cuda".
# ────────────────────────────────────────────────────────────────────────────

import sys
import torch

# ── Primary detection ────────────────────────────────────────────────────────
HAS_CUDA = torch.cuda.is_available()

# 1. BYPASS for Windows PyTorch cuDNN crash (Error code 127) on older GPUs
if HAS_CUDA:
    torch.backends.cudnn.enabled = False

# 2. DEVICE ASSIGNMENTS
# Map both TTS and STT to GPU if available.
DEVICE_TTS: str = "cuda" if HAS_CUDA else "cpu"
DEVICE: str     = "cuda" if HAS_CUDA else "cpu"

if DEVICE == "cuda":
    _cc_major = torch.cuda.get_device_properties(0).major
    COMPUTE_TYPE: str = "float16" if _cc_major >= 7 else "int8"
else:
    COMPUTE_TYPE = "int8"

# ── Startup banner ───────────────────────────────────────────────────────────
_SEP = "─" * 58

def _banner() -> None:
    """Print a clear device banner to the terminal on import."""
    print(f"\n\033[1m\033[97m{_SEP}\033[0m", flush=True)
    if HAS_CUDA:
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb  = torch.cuda.get_device_properties(0).total_memory / 1024**3
        cc       = torch.cuda.get_device_properties(0)
        cc_str   = f"{cc.major}.{cc.minor}"
        print(f"\033[1m\033[92m[AI] System     : CUDA (GPU) Available\033[0m", flush=True)
        print(f"\033[92m[AI] GPU        : {gpu_name}\033[0m", flush=True)
        print(f"\033[92m[AI] VRAM       : {vram_gb:.1f} GB\033[0m", flush=True)
        print(f"\033[1m\033[96m[AI] TTS Engine : CUDA (cuDNN disabled to prevent crash)\033[0m", flush=True)
        print(f"\033[96m[AI] STT Engine : CUDA (compute={cc_str}, precision={COMPUTE_TYPE})\033[0m", flush=True)
    else:
        print(f"\033[1m\033[93m[AI] System     : CPU Only\033[0m", flush=True)
        print(f"\033[93m[AI] CUDA not detected – falling back to CPU\033[0m", flush=True)
        print(f"\033[93m[AI] Precision  : int8 (quantised)\033[0m", flush=True)
    print(f"\033[1m\033[97m{_SEP}\033[0m\n", flush=True)

_banner()


def free_gpu_cache() -> None:
    """Release unused GPU memory — call after heavy inference if needed."""
    if HAS_CUDA:
        torch.cuda.empty_cache()
