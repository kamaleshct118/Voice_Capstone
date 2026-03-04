import httpx
import redis
from app.cache.db1_cag import build_cache_key, get_cached_chunk, store_chunk
from app.mcp.router import ToolOutput
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_medical_news(entities: dict, redis_db1: redis.Redis) -> ToolOutput:
    """Fetch latest medical news via NewsAPI with short-TTL caching."""
    topic = entities.get("disease") or entities.get("drug") or "medical health"
    key = build_cache_key("medical_news", topic)

    cached = get_cached_chunk(redis_db1, key)
    if cached:
        logger.info(f"News cache HIT for: {topic}")
        return ToolOutput(tool_name="medical_news", result=cached)

    try:
        from datetime import datetime, timedelta
        from_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": topic,
            "language": "en",
            "pageSize": 3,
            "from": from_date,
            "sortBy": "publishedAt",
            "apiKey": settings.news_api_key,
        }
        with httpx.Client(timeout=10) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        articles = []
        for article in data.get("articles", [])[:3]:
            articles.append({
                "title": article.get("title", ""),
                "description": article.get("description", "")[:300],
                "url": article.get("url", ""),
                "published_at": article.get("publishedAt", ""),
            })

        result = {"topic": topic, "articles": articles, "source": "NewsAPI"}
        store_chunk(redis_db1, key, result, ttl=settings.ttl_news)
        return ToolOutput(tool_name="medical_news", result=result)

    except Exception as e:
        logger.error(f"News API error for '{topic}': {e}")
        return ToolOutput(
            tool_name="medical_news",
            result={"message": f"Unable to fetch news for '{topic}' at this time."},
            error=str(e),
        )
