import requests
import json

# Configuration
TARGET_DOMAIN = "glstech.co.uk"
INSTANCE_URL = "http://127.0.0.1:8088/search" # Using IP to avoid DNS resolution issues

def test_searxng_connection():
    print(f"--- 🔍 Testing SearXNG for {TARGET_DOMAIN} ---")
    
    params = {
        'q': f'site:{TARGET_DOMAIN}',
        'format': 'json',
        'categories': 'general'
    }
    
    # Using a browser-like User-Agent is the #1 fix for local instances
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(INSTANCE_URL, params=params, headers=headers, timeout=5)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content Type: {response.headers.get('Content-Type')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                results = data.get('results', [])
                print(f"✅ Success! Found {len(results)} results for {TARGET_DOMAIN}.")
                
                for idx, item in enumerate(results, 1):
                    print(f"{idx}. {item.get('title')} - {item.get('url')}")
                    
            except json.JSONDecodeError:
                print("❌ ERROR: Received non-JSON response.")
                print("--- RAW RESPONSE START ---")
                print(response.text[:500]) # Print first 500 chars to see the HTML error
                print("--- RAW RESPONSE END ---")
        else:
            print(f"❌ Server returned error: {response.status_code}")

    except Exception as e:
        print(f"❌ Failed to connect: {e}")

if __name__ == "__main__":
    test_searxng_connection()