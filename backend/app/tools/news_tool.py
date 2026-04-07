"""
news_tool.py
Implements the Medical News RAG Pipeline from the Colab notebook:
  1. Parse user query into structured JSON using Groq (llama-3.1-8b-instant)
  2. Expand the search keywords and fetch articles from NewsAPI
  3. Rank articles by relevance using TF-IDF cosine similarity (scikit-learn)
  4. Summarize top-ranked articles using Groq (llama-3.3-70b-versatile)
  5. Cache the final result in Redis DB1
"""

import json
import requests
import numpy as np
import redis
from datetime import datetime, timedelta
from typing import List, Dict
from groq import Groq
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.cache.db1_cag import build_cache_key, get_cached_chunk, store_chunk
from app.mcp.router import ToolOutput
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
NEWS_API_URL = "https://newsapi.org/v2/everything"
NEWS_API_TOP_HEADLINES_URL = "https://newsapi.org/v2/top-headlines"

MEDICAL_KEYWORDS = [
    'medical', 'health', 'medicine', 'doctor', 'hospital', 'patient',
    'disease', 'treatment', 'drug', 'vaccine', 'clinical', 'study',
    'research', 'cancer', 'diabetes', 'heart', 'brain', 'surgery',
    'therapy', 'diagnosis', 'symptom', 'outbreak', 'pandemic',
    'FDA', 'WHO', 'CDC', 'pharma', 'biotech', 'genome', 'mental health'
]

QUERY_EXPANSION_TERMS = [
    "clinical trial", "drug discovery", "FDA", "biotech", "therapy", "treatment"
]


# ── Step 1: Parse user query to structured JSON via Groq ──────────────────────

def _parse_query_to_json(user_query: str, groq_client: Groq) -> dict:
    """Use Groq llama-3.1-8b-instant to extract structured topic + keywords from query."""
    system_prompt = "Convert the user medical query into JSON. Return only JSON."
    user_prompt = f"""Query: {user_query}

Return JSON:
{{
  "main_topic": "",
  "sub_topics": [],
  "search_keywords": ""
}}"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        parsed = json.loads(response.choices[0].message.content)
        logger.info(f"[NewsRAG] Query parsed: {parsed}")
        return parsed
    except Exception as e:
        logger.warning(f"[NewsRAG] Query parse failed, using raw query: {e}")
        return {
            "main_topic": user_query,
            "sub_topics": [],
            "search_keywords": user_query
        }


# ── Step 2: Expand query and fetch articles from NewsAPI ─────────────────────

def _expand_query(query: str) -> str:
    """Append biomedical expansion terms to the query for broader news coverage."""
    expansion = " OR ".join(QUERY_EXPANSION_TERMS)
    # Safely group the query and expansion terms so NewsAPI doesn't over-broaden
    safe_query = query.replace('"', '').strip()
    return f'("{safe_query}") AND ({expansion})'


def _fetch_articles(parsed_query: dict, page_size: int = 20) -> List[dict]:
    """Fetch articles from NewsAPI using expanded search keywords."""
    keywords = parsed_query.get("search_keywords") or parsed_query.get("main_topic") or "medical research"
    keywords = _expand_query(keywords)
    from_date = (datetime.now() - timedelta(days=25)).strftime("%Y-%m-%d")

    params = {
        "q": keywords,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "from": from_date,
        "apiKey": settings.news_api_key,
    }

    try:
        response = requests.get(NEWS_API_URL, params=params, timeout=10)
        data = response.json()
        if data.get("status") != "ok":
            logger.error(f"[NewsRAG] NewsAPI error: {data}")
            return []
        articles = data.get("articles", [])
        logger.info(f"[NewsRAG] Fetched {len(articles)} articles for '{keywords}'")
        return articles
    except Exception as e:
        logger.error(f"[NewsRAG] Fetch error: {e}")
        return []


# ── Step 3: Rank articles by TF-IDF cosine similarity ────────────────────────

def _rank_articles(articles: List[dict], parsed_query: dict, top_n: int = 5) -> List[dict]:
    """Rank articles by cosine similarity to the query using TF-IDF."""
    if not articles:
        return []

    query_text = parsed_query.get("search_keywords", "") or parsed_query.get("main_topic", "")

    article_texts = [
        f"{a.get('title', '')} {a.get('description', '')}".lower()
        for a in articles
    ]

    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf = vectorizer.fit_transform([query_text] + article_texts)
        query_vec = tfidf[0:1]
        article_vecs = tfidf[1:]
        sims = cosine_similarity(query_vec, article_vecs).flatten()
        top_indices = np.argsort(sims)[::-1][:top_n]
        ranked = []
        for i in top_indices:
            art = articles[i]
            art["score"] = float(sims[i])
            ranked.append(art)
        logger.info(f"[NewsRAG] Ranked top {len(ranked)} articles")
        return ranked
    except Exception as e:
        logger.warning(f"[NewsRAG] Ranking failed, returning un-ranked: {e}")
        return articles[:top_n]


# ── Step 4: Summarize article using Groq ─────────────────────────────────────

def _summarize_article(article: dict, query: str, groq_client: Groq) -> dict:
    """Use Groq llama-3.3-70b-versatile to summarize a single article."""
    content = (
        f"Title: {article.get('title', '')}\n"
        f"Description: {article.get('description', '')}\n"
        f"Content: {article.get('content', '')}"
    )

    prompt = (
        f"Summarize this medical article related to:\n{query}\n\n"
        f"Write two paragraphs. Each paragraph should contain four sentences.\n\n"
        f"Article:\n{content}"
    )

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300
        )
        summary_text = response.choices[0].message.content or ""
        return {
            "valid": True,
            "title": article.get("title", ""),
            "source": article.get("source", {}).get("name", "Unknown"),
            "date": article.get("publishedAt", ""),
            "url": article.get("url", ""),
            "summary": summary_text,
        }
    except Exception as e:
        logger.warning(f"[NewsRAG] Summarize failed: {e}")
        return {"valid": False, "reason": str(e)}


# ── Main Entry Point ──────────────────────────────────────────────────────────

def get_medical_news(entities: dict, redis_db1: redis.Redis, llm_client=None) -> ToolOutput:
    """
    Full RAG pipeline:
      parse query → expand → fetch → rank → summarize → cache → return ToolOutput
    """
    import random
    topic = entities.get("disease") or entities.get("drug") or entities.get("topic") or "medical health"
    
    # Bypass cache to always provide fresh and different news
    logger.info(f"[NewsRAG] Processing news request for: {topic} (Cache Bypassed)")

    # ── Build Groq client for RAG ─────────────────────────────────────────────
    groq_client = Groq(api_key=settings.groq_api_key)

    try:
        # Step 1: Parse
        parsed = _parse_query_to_json(topic, groq_client)

        # Step 2: Fetch articles
        raw_articles = _fetch_articles(parsed, page_size=20)

        if not raw_articles:
            # Fallback to top-headlines if no results
            logger.warning("[NewsRAG] No articles from search, trying top-headlines fallback")
            try:
                fallback_resp = requests.get(
                    NEWS_API_TOP_HEADLINES_URL,
                    params={"category": "health", "language": "en", "apiKey": settings.news_api_key},
                    timeout=10
                )
                raw_articles = fallback_resp.json().get("articles", [])[:15]
                logger.info(f"[NewsRAG] Fallback returned {len(raw_articles)} articles")
            except Exception:
                pass

        if not raw_articles:
            result = {
                "topic": topic,
                "articles": [],
                "count": 0,
                "message": f"Unable to fetch recent news about {topic} right now.",
                "success": False
            }
            return ToolOutput(tool_name="medical_news", result=result, error="No articles found")

        # Step 3: Rank
        ranked_articles = _rank_articles(raw_articles, parsed, top_n=15)
        
        # Randomize selection from the top ranked articles to provide different answers
        if len(ranked_articles) > 5:
            ranked_articles = random.sample(ranked_articles, 5)

        # Step 4: Summarize top ranked articles
        summarized = []
        for art in ranked_articles:
            summary = _summarize_article(art, topic, groq_client)
            if summary.get("valid"):
                summarized.append(summary)

        result = {
            "topic": topic,
            "articles": summarized,
            "count": len(summarized),
            "source": "NewsAPI + Groq RAG",
            "success": True
        }

        # Removed caching step to ensure fresh news every time

        return ToolOutput(tool_name="medical_news", result=result, error=None)

    except Exception as e:
        logger.error(f"[NewsRAG] Pipeline error for '{topic}': {e}")
        fallback_result = {
            "topic": topic,
            "articles": [],
            "count": 0,
            "message": f"I was unable to fetch recent news about {topic} right now.",
            "success": False
        }
        return ToolOutput(tool_name="medical_news", result=fallback_result, error=str(e))
