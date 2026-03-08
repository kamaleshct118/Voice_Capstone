import sys
from dataclasses import dataclass
from datetime import datetime


# ── ANSI colour helpers ────────────────────────────────────────────────────────
_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_DIM    = "\033[2m"
_CYAN   = "\033[96m"
_GREEN  = "\033[92m"
_YELLOW = "\033[93m"
_RED    = "\033[91m"
_BLUE   = "\033[94m"
_MAGENTA= "\033[95m"
_WHITE  = "\033[97m"

# Colour per stage
_STAGE_COLOR = {
    "STT":    _CYAN,
    "INTENT": _BLUE,
    "TOOLS":  _MAGENTA,
    "LLM":    _YELLOW,
    "TTS":    _GREEN,
}

def _bar(ms: int, total_ms: int, width: int = 30) -> str:
    """ASCII bar proportional to share of total latency."""
    if total_ms == 0:
        return "░" * width
    filled = max(1, round((ms / total_ms) * width))
    return "█" * filled + "░" * (width - filled)

def _badge(ms: int) -> str:
    """Colour-coded speed badge."""
    if ms < 300:
        return f"{_GREEN}FAST{_RESET}"
    if ms < 800:
        return f"{_YELLOW}OK  {_RESET}"
    return f"{_RED}SLOW{_RESET}"


@dataclass
class RequestMetrics:
    stt_ms:    int  = 0
    intent_ms: int  = 0
    tool_ms:   int  = 0
    llm_ms:    int  = 0
    tts_ms:    int  = 0
    cache_hit: bool = False

    @property
    def total_ms(self) -> int:
        return self.stt_ms + self.intent_ms + self.tool_ms + self.llm_ms + self.tts_ms


def record_latency(metrics: RequestMetrics, session_id: str) -> None:
    """Print a rich, colour-coded latency report to the terminal."""
    total = metrics.total_ms or 1          # avoid div-by-zero
    now   = datetime.now().strftime("%H:%M:%S.%f")[:-3]   # e.g. 21:05:43.217

    stages = [
        ("STT",    metrics.stt_ms,    "Speech-to-Text  (Whisper)"),
        ("INTENT", metrics.intent_ms, "Intent Classify (LLM)    "),
        ("TOOLS",  metrics.tool_ms,   "MCP Tool Routing          "),
        ("LLM",    metrics.llm_ms,    "Response Gen    (LLM)    "),
        ("TTS",    metrics.tts_ms,    "Text-to-Speech  (Kokoro) "),
    ]

    sep   = f"{_DIM}{'─' * 68}{_RESET}"
    cache = f"{_GREEN}HIT ✓{_RESET}" if metrics.cache_hit else f"{_DIM}MISS{_RESET}"

    lines = [
        "",
        sep,
        f"  {_BOLD}{_WHITE}⏱  VOICE PIPELINE LATENCY REPORT{_RESET}   "
        f"{_DIM}{now}{_RESET}   "
        f"session: {_DIM}{session_id[:8]}…{_RESET}",
        sep,
        f"  {'STAGE':<8}  {'LABEL':<30}  {'TIME':>7}   {'SHARE':>5}   BREAKDOWN",
        f"{_DIM}  {'─'*8}  {'─'*30}  {'─'*7}   {'─'*5}   {'─'*31}{_RESET}",
    ]

    for name, ms, label in stages:
        color = _STAGE_COLOR.get(name, _WHITE)
        pct   = (ms / total) * 100
        bar   = _bar(ms, total)
        skip  = f"{_DIM}(skipped){_RESET}" if ms == 0 else ""
        lines.append(
            f"  {color}{_BOLD}{name:<8}{_RESET}  {_DIM}{label}{_RESET}  "
            f"{color}{ms:>5} ms{_RESET}   {pct:>4.0f}%   {color}{bar}{_RESET} {skip}"
        )

    lines += [
        f"{_DIM}  {'─'*8}  {'─'*30}  {'─'*7}   {'─'*5}   {'─'*31}{_RESET}",
        f"  {_BOLD}{'TOTAL':<8}{_RESET}  {'End-to-end wall time':<30}  "
        f"{_BOLD}{_WHITE}{metrics.total_ms:>5} ms{_RESET}          "
        f"cache: {cache}   {_badge(metrics.total_ms)}",
        sep,
        "",
    ]

    sys.stdout.write("\n".join(lines) + "\n")
    sys.stdout.flush()

    # Also keep the structured JSON log for file-based monitoring
    from app.utils.logger import get_logger
    import json
    logger = get_logger("metrics")
    logger.info(
        f"session={session_id} stt={metrics.stt_ms}ms intent={metrics.intent_ms}ms "
        f"tool={metrics.tool_ms}ms llm={metrics.llm_ms}ms tts={metrics.tts_ms}ms "
        f"total={metrics.total_ms}ms cache_hit={metrics.cache_hit}"
    )
    
    # Save to Redis for Frontend Dashboard
    try:
        from app.cache.redis_client import redis_db1
        metric_data = {
            "session_id": session_id,
            "stt_ms": metrics.stt_ms,
            "intent_ms": metrics.intent_ms,
            "tool_ms": metrics.tool_ms,
            "llm_ms": metrics.llm_ms,
            "tts_ms": metrics.tts_ms,
            "total_ms": metrics.total_ms,
            "cache_hit": metrics.cache_hit,
            "timestamp": datetime.utcnow().isoformat()
        }
        redis_db1.lpush("system_latency_metrics", json.dumps(metric_data))
        # Keep only the last 1000 requests to avoid ballooning memory
        redis_db1.ltrim("system_latency_metrics", 0, 999)
    except Exception as e:
        logger.error(f"Failed to save metrics to Redis: {e}")
