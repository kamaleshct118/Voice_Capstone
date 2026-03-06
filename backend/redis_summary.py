#!/usr/bin/env python3
"""
Redis Database Summary Script
Shows a quick overview of Redis DB0 and DB1 contents without full data dump.
"""

import redis
import sys
import os
from datetime import datetime

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

def print_database_summary(db_num: int, redis_client: redis.Redis) -> None:
    """Print summary of a Redis database."""
    print(f"\n📊 REDIS DB{db_num} SUMMARY")
    print("-" * 40)
    
    try:
        if not redis_client.ping():
            print(f"❌ Cannot connect to Redis DB{db_num}")
            return
            
        keys = redis_client.keys("*")
        
        if not keys:
            print(f"📭 Database {db_num} is empty")
            return
            
        print(f"🔑 Total Keys: {len(keys)}")
        
        # Group keys by pattern/prefix
        key_patterns = {}
        for key in keys:
            # Extract pattern (prefix before first colon or underscore)
            if ':' in key:
                pattern = key.split(':')[0] + ':*'
            elif '_' in key:
                pattern = key.split('_')[0] + '_*'
            else:
                pattern = 'other'
                
            key_patterns[pattern] = key_patterns.get(pattern, 0) + 1
        
        print("📋 Key Patterns:")
        for pattern, count in sorted(key_patterns.items()):
            print(f"   {pattern}: {count} keys")
            
        # Show memory usage if available
        try:
            info = redis_client.info('memory')
            used_memory = info.get('used_memory_human', 'N/A')
            print(f"💾 Memory Usage: {used_memory}")
        except:
            pass
            
    except Exception as e:
        print(f"❌ Error accessing Redis DB{db_num}: {e}")

def main():
    """Main function to show database summaries."""
    print("📈 Redis Database Summary Tool")
    print(f"🔗 Redis: {settings.redis_host}:{settings.redis_port}")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
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
        
        # DB0: conversation history & health logs
        print_database_summary(0, redis_db0)
        
        # DB1: tool retrieval cache
        print_database_summary(1, redis_db1)
        
        print(f"\n✅ Summary complete!")
        
    except Exception as e:
        print(f"❌ Failed to connect to Redis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()