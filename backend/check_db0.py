#!/usr/bin/env python3
"""
Simple DB0 checker - shows what's in Redis DB0
"""

import redis
import json
import sys
import os

# Add path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.config import settings
    
    # Connect to DB0
    r = redis.StrictRedis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db0,
        decode_responses=True,
    )
    
    print("🔍 Checking Redis DB0 (conversation history & health logs)")
    print(f"Connection: {settings.redis_host}:{settings.redis_port}")
    
    # Test connection
    r.ping()
    print("✅ Connected successfully")
    
    # Get all keys
    keys = r.keys("*")
    print(f"📊 Found {len(keys)} keys in DB0")
    
    if keys:
        print("\n🔑 Keys found:")
        for i, key in enumerate(sorted(keys), 1):
            print(f"{i}. {key}")
            
            # Show key type and TTL
            key_type = r.type(key)
            ttl = r.ttl(key)
            ttl_info = f"{ttl}s" if ttl > 0 else "no expiry" if ttl == -1 else "expired"
            print(f"   Type: {key_type}, TTL: {ttl_info}")
            
            # Show value preview
            try:
                if key_type == "string":
                    value = r.get(key)
                    if len(str(value)) > 100:
                        preview = str(value)[:100] + "..."
                    else:
                        preview = str(value)
                    print(f"   Value: {preview}")
                elif key_type == "list":
                    count = r.llen(key)
                    print(f"   List with {count} items")
                elif key_type == "hash":
                    count = r.hlen(key)
                    print(f"   Hash with {count} fields")
                else:
                    print(f"   {key_type} data structure")
            except Exception as e:
                print(f"   Error reading: {e}")
            
            print()
    else:
        print("📭 DB0 is empty")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("Make sure Redis server is running")