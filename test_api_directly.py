#!/usr/bin/env python3
"""Direct API test - bypassing all Portrait Generator code."""
import os
import sys
import google.genai as genai

# Get the API key
api_key = os.getenv('GOOGLE_API_KEY', '').strip()

# Remove any prefix
if 'google_api_key:' in api_key.lower():
    parts = api_key.split(':', 1)
    if len(parts) > 1:
        api_key = parts[1].strip()

print("=" * 70)
print("DIRECT API KEY TEST")
print("=" * 70)
print(f"Key format: {api_key[:10]}...{api_key[-5:]}")
print(f"Key length: {len(api_key)}")
print()

# Test the key
try:
    print("Creating client...")
    client = genai.Client(api_key=api_key)
    print("✅ Client created")
    
    print("\nTesting with gemini-2.0-flash-exp...")
    response = client.models.generate_content(
        model='gemini-2.0-flash-exp',
        contents='Say "Hello World"'
    )
    print(f"✅ SUCCESS! Response: {response.text}")
    print("\n🎉 API KEY IS VALID AND WORKING!")
    sys.exit(0)
    
except Exception as e:
    error_str = str(e)
    print(f"\n❌ FAILED: {error_str[:300]}")
    
    if 'expired' in error_str.lower():
        print("\n⚠️  KEY IS EXPIRED")
        print("Please get a new key from: https://makersuite.google.com/app/apikey")
    elif 'invalid' in error_str.lower():
        print("\n⚠️  KEY IS INVALID")
    
    sys.exit(1)
