# app/api/redis_explorer.py
# ── Redis Data Explorer API ────────────────────────────────────────
# Provides detailed view of Redis DB0 and DB1 contents for debugging
# and monitoring purposes.
# ──────────────────────────────────────────────────────────────────

import json
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.cache.redis_client import redis_db0, redis_db1
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# ── Response Models ────────────────────────────────────────────────

class RedisKeyInfo(BaseModel):
    key: str
    type: str
    ttl: int  # -1 = no expiry, -2 = expired/not exists
    size: int  # memory usage in bytes
    value_preview: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DB0ConversationEntry(BaseModel):
    key: str
    session_id: str
    type: str  # "conversation" or "health_log" or "health_chat"
    message_count: int
    ttl_seconds: int
    last_updated: Optional[str] = None
    preview: List[Dict[str, str]]  # First few messages


class DB1CacheEntry(BaseModel):
    key: str
    tool_name: str  # "medicine_info", "medical_news", "medical_info"
    cache_key_hash: str
    query_info: str  # Human-readable query description
    ttl_seconds: int
    cached_at: Optional[str] = None
    data_preview: Optional[Dict[str, Any]] = None


class RedisDBSummary(BaseModel):
    db_number: int
    db_name: str
    total_keys: int
    memory_usage: str
    key_patterns: Dict[str, int]  # pattern -> count
    entries: List[Dict[str, Any]]  # List of dicts instead of Pydantic models


# ── Helper Functions ───────────────────────────────────────────────

def parse_db0_key(key: str, client) -> Optional[Dict[str, Any]]:
    """Parse a DB0 key and extract metadata."""
    try:
        if key.startswith("ctx:"):
            session_id = key.split(":", 1)[1]
            raw = client.get(key)
            if not raw:
                return None
            
            messages = json.loads(raw)
            ttl = client.ttl(key)
            
            return {
                "key": key,
                "session_id": session_id,
                "type": "conversation",
                "message_count": len(messages),
                "ttl_seconds": ttl,
                "last_updated": None,
                "preview": messages  # all messages
            }
        
        elif key.startswith("health:"):
            session_id = key.split(":", 1)[1]
            raw = client.get(key)
            if not raw:
                return None
            
            logs = json.loads(raw)
            ttl = client.ttl(key)
            
            return {
                "key": key,
                "session_id": session_id,
                "type": "health_log",
                "message_count": len(logs),
                "ttl_seconds": ttl,
                "last_updated": logs[-1].get("timestamp") if logs else None,
                "preview": [{"type": "health_entry", "data": str(logs[-1])}] if logs else []
            }
        
        elif key.startswith("healthchat:"):
            session_id = key.split(":", 1)[1]
            raw = client.get(key)
            if not raw:
                return None
            
            messages = json.loads(raw)
            ttl = client.ttl(key)
            
            return {
                "key": key,
                "session_id": session_id,
                "type": "health_chat",
                "message_count": len(messages),
                "ttl_seconds": ttl,
                "last_updated": None,
                "preview": messages  # all messages
            }
        
        return None
    except Exception as e:
        logger.error(f"Error parsing DB0 key {key}: {e}")
        return None
        return None


def parse_db1_key(key: str, client) -> Optional[Dict[str, Any]]:
    """Parse a DB1 key and extract cached tool information."""
    try:
        raw = client.get(key)
        if not raw:
            return None
        
        data = json.loads(raw)
        ttl = client.ttl(key)
        
        # Determine tool type from data structure
        tool_name = "unknown"
        query_info = "Unknown query"
        data_preview = {}
        
        if "medicine_name" in data:
            tool_name = "medicine_classifier"
            query_info = f"Medicine: {data.get('medicine_name', 'N/A')}"
            data_preview = {
                "medicine_name": data.get("medicine_name"),
                "drug_category": data.get("drug_category"),
                "purpose": data.get("purpose", "")[:100]
            }
        
        elif "articles" in data:
            tool_name = "medical_news"
            query_info = f"News topic: {data.get('topic', 'N/A')}"
            articles = data.get("articles", [])
            data_preview = {
                "topic": data.get("topic"),
                "article_count": len(articles),
                "latest_article": articles[0].get("title") if articles else None
            }
        
        elif "drug_name" in data or "brand_name" in data:
            tool_name = "medical_api"
            query_info = f"Drug: {data.get('drug_name') or data.get('brand_name', 'N/A')}"
            data_preview = {
                "drug_name": data.get("drug_name"),
                "brand_name": data.get("brand_name"),
                "manufacturer": data.get("manufacturer")
            }
        
        elif "summary" in data and "flagged_readings" in data:
            tool_name = "health_analysis"
            query_info = "Health trend analysis"
            data_preview = {
                "summary": data.get("summary", "")[:100],
                "flagged_count": len(data.get("flagged_readings", []))
            }
        
        elif "report_title" in data:
            tool_name = "medical_report"
            query_info = "Medical report"
            data_preview = {
                "title": data.get("report_title"),
                "conditions": data.get("health_conditions", "")[:100]
            }
        
        return {
            "key": key,
            "tool_name": tool_name,
            "cache_key_hash": key[:16] + "...",
            "query_info": query_info,
            "ttl_seconds": ttl,
            "cached_at": None,
            "data_preview": data_preview
        }
    
    except Exception as e:
        logger.error(f"Error parsing DB1 key {key}: {e}")
        return None


# ── API Endpoints ──────────────────────────────────────────────────

@router.get("/redis/db0")
async def get_db0_data():
    """
    Get all conversation cache data from Redis DB0.
    All Redis calls are run in a thread to avoid blocking the async event loop.
    """
    def _fetch():
        keys = redis_db0.keys("*")

        try:
            info = redis_db0.info("memory")
            memory_usage = info.get("used_memory_human", "N/A")
        except Exception:
            memory_usage = "N/A"

        key_patterns = {}
        for key in keys:
            if key.startswith("ctx:"):
                key_patterns["ctx:*"] = key_patterns.get("ctx:*", 0) + 1
            elif key.startswith("health:"):
                key_patterns["health:*"] = key_patterns.get("health:*", 0) + 1
            elif key.startswith("healthchat:"):
                key_patterns["healthchat:*"] = key_patterns.get("healthchat:*", 0) + 1
            else:
                key_patterns["other"] = key_patterns.get("other", 0) + 1

        entries = []
        for key in keys:
            try:
                entry = parse_db0_key(key, redis_db0)
                if entry:
                    entries.append(entry)
            except Exception as e:
                logger.error(f"Error parsing key {key}: {e}")

        def _sort_key(e):
            if e.get("last_updated"):
                return e["last_updated"]
            return str(e.get("ttl_seconds", 0)).zfill(10)

        entries.sort(key=_sort_key, reverse=True)
        logger.info(f"DB0: {len(entries)} entries returned")

        return {
            "db_number": 0,
            "db_name": "Conversation Cache",
            "total_keys": len(keys),
            "memory_usage": memory_usage,
            "key_patterns": key_patterns,
            "entries": entries,
        }

    try:
        return await asyncio.to_thread(_fetch)
    except Exception as e:
        logger.error(f"Error fetching DB0 data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch DB0 data: {str(e)}")


@router.get("/redis/db1")
async def get_db1_data():
    """
    Get all tool retrieval cache data from Redis DB1.
    All Redis calls are run in a thread to avoid blocking the async event loop.
    """
    def _fetch():
        keys = redis_db1.keys("*")

        try:
            info = redis_db1.info("memory")
            memory_usage = info.get("used_memory_human", "N/A")
        except Exception:
            memory_usage = "N/A"

        tool_counts = {}
        entries = []
        for key in keys:
            entry = parse_db1_key(key, redis_db1)
            if entry:
                entries.append(entry)
                tool_counts[entry["tool_name"]] = tool_counts.get(entry["tool_name"], 0) + 1

        entries.sort(key=lambda e: e.get("ttl_seconds", 0), reverse=True)

        return {
            "db_number": 1,
            "db_name": "Tool Retrieval Cache",
            "total_keys": len(keys),
            "memory_usage": memory_usage,
            "key_patterns": tool_counts,
            "entries": entries,
        }

    try:
        return await asyncio.to_thread(_fetch)
    except Exception as e:
        logger.error(f"Error fetching DB1 data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch DB1 data: {str(e)}")


@router.get("/redis/key/{db}/{key:path}")
async def get_key_details(db: int, key: str):
    """
    Get detailed information about a specific Redis key.
    
    Parameters:
    - db: Database number (0 or 1)
    - key: Redis key name
    """
    try:
        client = redis_db0 if db == 0 else redis_db1
        
        if not client.exists(key):
            raise HTTPException(status_code=404, detail="Key not found")
        
        key_type = client.type(key)
        ttl = client.ttl(key)
        
        # Get value based on type
        value = None
        if key_type == "string":
            raw = client.get(key)
            try:
                value = json.loads(raw)
            except:
                value = raw
        
        return {
            "key": key,
            "db": db,
            "type": key_type,
            "ttl": ttl,
            "value": value
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching key details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch key details: {str(e)}")


@router.delete("/redis/key/{db}/{key:path}")
async def delete_key(db: int, key: str):
    """Delete a specific Redis key."""
    try:
        client = redis_db0 if db == 0 else redis_db1
        
        if not client.exists(key):
            raise HTTPException(status_code=404, detail="Key not found")
        
        client.delete(key)
        return {"status": "deleted", "key": key, "db": db}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting key: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete key: {str(e)}")
