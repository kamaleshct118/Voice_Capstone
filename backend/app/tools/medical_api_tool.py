import httpx
import redis
from app.cache.db1_cag import build_cache_key, get_cached_chunk, store_chunk
from app.mcp.router import ToolOutput
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_FDA_BASE = settings.medical_api_base_url


def get_medical_info(entities: dict, redis_db1: redis.Redis) -> ToolOutput:
    """Fetch medical information from OpenFDA, with CAG caching in DB1."""
    query = entities.get("disease") or entities.get("drug") or "general"
    key = build_cache_key("medical_info", query)

    # ── Cache HIT ─────────────────────────────────────────────────
    cached = get_cached_chunk(redis_db1, key)
    if cached:
        logger.info(f"Medical info cache HIT for: {query}")
        return ToolOutput(tool_name="medical_info", result=cached)

    # ── Cache MISS — call OpenFDA ─────────────────────────────────
    try:
        url = f"{_FDA_BASE}/label.json"
        params = {"search": f"indications_and_usage:{query}", "limit": 1}
        with httpx.Client(timeout=10) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        results = data.get("results", [])
        if results:
            r = results[0]
            info = {
                "description": (r.get("description") or [""])[0][:600],
                "indications": (r.get("indications_and_usage") or [""])[0][:600],
                "warnings": (r.get("warnings") or [""])[0][:400],
                "source": "OpenFDA",
                "query": query,
            }
        else:
            info = {
                "description": f"No specific FDA data found for '{query}'.",
                "indications": "Please consult a healthcare professional.",
                "warnings": "Always seek professional medical advice.",
                "source": "OpenFDA",
                "query": query,
            }

        store_chunk(redis_db1, key, info, ttl=settings.db1_ttl_seconds)
        return ToolOutput(tool_name="medical_info", result=info)

    except Exception as e:
        logger.error(f"Medical API error for '{query}': {e}")
        return ToolOutput(
            tool_name="medical_info",
            result={"message": f"Unable to retrieve medical data for '{query}'."},
            error=str(e),
        )
