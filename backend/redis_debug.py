#!/usr/bin/env python3
"""
Redis Database Debug Script
Prints all keys and values from Redis DB0 and DB1 for debugging purposes.
"""

import redis
import json
from datetime import datetime
from typing import Dict, Any
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

def format_value(value: str) -> str:
    """Format Redis value for better readability."""
    try:
        # Try to parse as JSON for pretty printing
        parsed = json.loads(value)
        return json.dumps(parsed, indent=2, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        # Return as-is if not JSON
        return str(value)

def print_database_contents(db_num: int, redis_client: redis.Redis) -> None:
    """Print all contents of a Redis database."""
    print(f"\n{'='*60}")
    print(f"REDIS DATABASE {db_num}")
    print(f"{'='*60}")
    
    try:
        # Check connection
        if not redis_client.ping():
            print(f"❌ Cannot connect to Redis DB{db_num}")
            return
            
        # Get all keys
        keys = redis_client.keys("*")
        
        if not keys:
            print(f"📭 Database {db_num} is empty")
            return
            
        print(f"📊 Found {len(keys)} keys in DB{db_num}")
        print(f"Host: {settings.redis_host}:{settings.redis_port}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)
        
        for i, key in enumerate(sorted(keys), 1):
            print(f"\n[{i}] KEY: {key}")
            
            # Get key type
            key_type = redis_client.type(key)
            print(f"    TYPE: {key_type}")
            
            # Get TTL
            ttl = redis_client.ttl(key)
            if ttl == -1:
                print("    TTL: No expiration")
            elif ttl == -2:
                print("    TTL: Key does not exist")
            else:
                print(f"    TTL: {ttl} seconds")
            
            # Get value based on type
            try:
                if key_type == "string":
                    value = redis_client.get(key)
                    print(f"    VALUE:")
                    print(f"    {format_value(value)}")
                    
                elif key_type == "list":
                    values = redis_client.lrange(key, 0, -1)
                    print(f"    VALUES ({len(values)} items):")
                    for j, val in enumerate(values):
                        print(f"    [{j}] {format_value(val)}")
                        
                elif key_type == "set":
                    values = redis_client.smembers(key)
                    print(f"    VALUES ({len(values)} items):")
                    for val in sorted(values):
                        print(f"    - {format_value(val)}")
                        
                elif key_type == "hash":
                    values = redis_client.hgetall(key)
                    print(f"    HASH ({len(values)} fields):")
                    for field, val in values.items():
                        print(f"    {field}: {format_value(val)}")
                        
                elif key_type == "zset":
                    values = redis_client.zrange(key, 0, -1, withscores=True)
                    print(f"    SORTED SET ({len(values)} items):")
                    for val, score in values:
                        print(f"    {score}: {format_value(val)}")
                        
                else:
                    print(f"    VALUE: <unsupported type: {key_type}>")
                    
            except Exception as e:
                print(f"    ERROR reading value: {e}")
                
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ Error accessing Redis DB{db_num}: {e}")

def main():
    """Main function to print both databases."""
    print("🔍 Redis Database Debug Tool")
    print(f"Connecting to Redis at {settings.redis_host}:{settings.redis_port}")
    
    # Create Redis connections
    try:
        redis_db0 = redis.StrictRedis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db0,
            decode_responses=True,
        )
        
        redis_db1 = redis.StrictRedis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db1,
            decode_responses=True,
        )
        
        # Print DB0 contents (conversation history & health logs)
        print_database_contents(0, redis_db0)
        
        # Print DB1 contents (tool retrieval cache)
        print_database_contents(1, redis_db1)
        
        print(f"\n{'='*60}")
        print("✅ Debug complete!")
        
    except Exception as e:
        print(f"❌ Failed to connect to Redis: {e}")
        print("Make sure Redis server is running and accessible.")
        sys.exit(1)

if __name__ == "__main__":
    main()