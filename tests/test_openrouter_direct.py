#!/usr/bin/env python3
"""
Test script to verify OpenRouter API connection directly
"""

import asyncio
import os
import sys
import httpx

# Set the API key
OPENROUTER_API_KEY = "REDACTED_API_KEY"

async def test_openrouter_api():
    """Test OpenRouter API directly"""
    print("="*60)
    print("Testing OpenRouter API Connection")
    print("="*60)
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://ricco.ai",
        "X-Title": "RICCO AI Test"
    }
    
    # Test with a free model
    payload = {
        "model": "meta-llama/llama-3.1-8b-instruct",
        "messages": [
            {"role": "user", "content": "Say 'Hello from OpenRouter!' in exactly those words."}
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    print(f"\n📡 Sending request to OpenRouter...")
    print(f"   Model: {payload['model']}")
    print(f"   Message: {payload['messages'][0]['content']}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            print(f"\n📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                model_used = data.get("model", "unknown")
                usage = data.get("usage", {})
                
                print(f"\n✅ SUCCESS!")
                print(f"   Model Used: {model_used}")
                print(f"   Response: {content}")
                print(f"   Tokens Used: {usage.get('total_tokens', 'N/A')}")
                
                return True
            else:
                print(f"\n❌ FAILED!")
                print(f"   Error: {response.text}")
                return False
                
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        return False


async def test_openrouter_models():
    """List available models from OpenRouter"""
    print("\n" + "="*60)
    print("Testing OpenRouter Models Endpoint")
    print("="*60)
    
    url = "https://openrouter.ai/api/v1/models"
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                
                # Count free models
                free_models = [m for m in models if m.get("pricing", {}).get("prompt", "1") == "0"]
                
                print(f"\n✅ Found {len(models)} total models")
                print(f"   Free models: {len(free_models)}")
                
                # Show some free models
                print("\n📋 Sample Free Models:")
                for model in free_models[:5]:
                    print(f"   - {model.get('id', 'unknown')}")
                
                return True
            else:
                print(f"\n❌ Failed to get models: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# OpenRouter Integration Test")
    print("#"*60)
    
    results = []
    
    # Test 1: Models endpoint
    result1 = await test_openrouter_models()
    results.append(("Models Endpoint", result1))
    
    # Test 2: Chat completion
    result2 = await test_openrouter_api()
    results.append(("Chat Completion", result2))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(r[1] for r in results)
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
