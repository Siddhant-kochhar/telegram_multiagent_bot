#!/usr/bin/env python3
"""
Test Upstash Redis Connection
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_upstash_redis():
    """Test Upstash Redis connection"""
    
    try:
        upstash_url = os.getenv('UPSTASH_REDIS_REST_URL')
        upstash_token = os.getenv('UPSTASH_REDIS_REST_TOKEN')
        
        if not upstash_url or not upstash_token:
            print("❌ Upstash Redis credentials not found in environment")
            return False
        
        print("🔗 Connecting to Upstash Redis...")
        print(f"📍 URL: {upstash_url}")
        
        from upstash_redis import Redis
        redis_client = Redis(url=upstash_url, token=upstash_token)
        
        # Test basic operations
        print("🔄 Testing basic operations...")
        
        # Ping test
        result = redis_client.ping()
        print(f"📡 Ping result: {result}")
        
        # Set/Get test
        test_key = "test_key"
        test_value = "test_value_from_syro"
        
        redis_client.set(test_key, test_value)
        print(f"✅ Set: {test_key} = {test_value}")
        
        retrieved_value = redis_client.get(test_key)
        print(f"📖 Get: {test_key} = {retrieved_value}")
        
        # Clean up
        redis_client.delete(test_key)
        print(f"🧹 Deleted test key: {test_key}")
        
        print("✅ Upstash Redis connection successful!")
        return True
        
    except Exception as e:
        print(f"❌ Upstash Redis connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Upstash Redis Connection...")
    print("=" * 50)
    
    success = test_upstash_redis()
    
    print("=" * 50)
    if success:
        print("✅ Upstash Redis setup completed successfully!")
        print("🎉 Your Syro bot is ready to use Upstash Redis!")
    else:
        print("❌ Upstash Redis setup failed!")
        print("🔧 Please check your credentials and network connection")
