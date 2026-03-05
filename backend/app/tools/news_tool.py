import httpx
import redis
from app.cache.db1_cag import build_cache_key, get_cached_chunk, store_chunk
from app.mcp.router import ToolOutput
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _expand_query(topic: str) -> str:
    """Expand search query for better news retrieval."""
    expansions = {
        "pharmaceutical": "pharmaceutical OR drug discovery OR clinical trial OR pharma industry",
        "pharma": "pharmaceutical OR drug discovery OR clinical trial OR pharma industry",
        "cancer": "cancer treatment OR oncology research OR cancer drug trial",
        "diabetes": "diabetes treatment OR insulin research OR diabetes drug",
        "heart": "heart disease OR cardiovascular research OR cardiology",
        "alzheimer": "alzheimer disease OR dementia research OR alzheimer treatment",
        "covid": "covid-19 OR coronavirus OR pandemic research",
        "vaccine": "vaccine development OR vaccination OR immunization research",
    }
    
    topic_lower = topic.lower()
    for key, expansion in expansions.items():
        if key in topic_lower:
            return expansion
    
    # Default: add medical context
    return f"{topic} AND (medical OR health OR drug OR treatment)"


def get_medical_news(entities: dict, redis_db1: redis.Redis) -> ToolOutput:
    """Fetch latest medical news via NewsAPI with query expansion and fallback."""
    topic = entities.get("disease") or entities.get("drug") or entities.get("topic") or "medical health"
    key = build_cache_key("medical_news", topic)

    cached = get_cached_chunk(redis_db1, key)
    if cached:
        logger.info(f"News cache HIT for: {topic}")
        return ToolOutput(tool_name="medical_news", result=cached, error=None)

    try:
        from datetime import datetime, timedelta
        from_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        url = "https://newsapi.org/v2/everything"
        
        # Try with expanded query first
        expanded_query = _expand_query(topic)
        params = {
            "q": expanded_query,
            "language": "en",
            "pageSize": 5,
            "from": from_date,
            "sortBy": "publishedAt",
            "apiKey": settings.news_api_key,
        }
        
        with httpx.Client(timeout=10) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        articles = []
        for article in data.get("articles", [])[:5]:
            articles.append({
                "title": article.get("title", ""),
                "description": article.get("description", "")[:300],
                "url": article.get("url", ""),
                "published_at": article.get("publishedAt", ""),
            })

        # Fallback: if no results, try broader query
        if not articles:
            logger.warning(f"No articles found for '{expanded_query}', trying broader search")
            params["q"] = "medical research OR pharmaceutical news OR health breakthrough"
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            for article in data.get("articles", [])[:3]:
                articles.append({
                    "title": article.get("title", ""),
                    "description": article.get("description", "")[:300],
                    "url": article.get("url", ""),
                    "published_at": article.get("publishedAt", ""),
                })

        result = {
            "topic": topic,
            "articles": articles,
            "count": len(articles),
            "source": "NewsAPI",
            "success": True
        }
        
        store_chunk(redis_db1, key, result, ttl=settings.ttl_news)
        logger.info(f"News fetched: {len(articles)} articles for '{topic}'")
        return ToolOutput(tool_name="medical_news", result=result, error=None)

    except Exception as e:
        logger.error(f"News API error for '{topic}': {e}")
        # Return fallback with general guidance
        fallback_result = {
            "topic": topic,
            "articles": [],
            "count": 0,
            "message": f"I was unable to fetch recent news about {topic} right now. The news service may be temporarily unavailable.",
            "success": False
        }
        return ToolOutput(
            tool_name="medical_news",
            result=fallback_result,
            error=str(e),
        )
