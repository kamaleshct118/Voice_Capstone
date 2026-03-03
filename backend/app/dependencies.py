"""
Dependency injection helpers for FastAPI routes.
Singletons (Whisper, Kokoro, LLM clients) are stored on app.state at startup.
Redis connections are module-level singletons from redis_client.py.
"""
from fastapi import Request
from app.cache.redis_client import redis_db1, redis_db2


def get_redis_db1():
    return redis_db1


def get_redis_db2():
    return redis_db2


def get_whisper_model(request: Request):
    return request.app.state.whisper_model


def get_kokoro_engine(request: Request):
    return request.app.state.kokoro_engine


def get_llm_client(request: Request):
    return request.app.state.llm_client


def get_gemini_client(request: Request):
    return request.app.state.gemini_client
