from dataclasses import dataclass, field


@dataclass
class RequestMetrics:
    stt_ms: int = 0
    intent_ms: int = 0
    tool_ms: int = 0
    llm_ms: int = 0
    tts_ms: int = 0
    cache_hit: bool = False

    @property
    def total_ms(self) -> int:
        return self.stt_ms + self.intent_ms + self.tool_ms + self.llm_ms + self.tts_ms


def record_latency(metrics: RequestMetrics, session_id: str) -> None:
    from app.utils.logger import get_logger
    logger = get_logger("metrics")
    logger.info(
        f"session={session_id} stt={metrics.stt_ms}ms intent={metrics.intent_ms}ms "
        f"tool={metrics.tool_ms}ms llm={metrics.llm_ms}ms tts={metrics.tts_ms}ms "
        f"total={metrics.total_ms}ms cache_hit={metrics.cache_hit}"
    )
