import requests
import re
import json
import pandas as pd
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
INSTANCE_URL = "http://127.0.0.1:8088"
TARGET_DOMAIN = "glstech.co.uk"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0'

# Regex for UK Phones (Landlines like 01207 and Mobiles 07xxx)
PHONE_REGEX = r'(?:(?:\+44\s?\(0\)\s?\d{2,5})|(?:\+44\s?\d{2,5})|(?:0\d{2,5}))(?:\s?\d{3,4}){1,2}'
EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

def deep_scan_url(url):
    """Visits the actual website to extract hidden contact info."""
    print(f"   ∟ 🕵️ Deep Scanning: {url}")
    try:
        response = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=8)
        if response.status_code != 200:
            return "N/A", "N/A"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text()

        # 1. Look for emails (Regex + mailto links)
        emails = re.findall(EMAIL_REGEX, page_text)
        mailto_links = [a['href'].replace('mailto:', '') for a in soup.select('a[href^="mailto:"]')]
        all_emails = list(set(emails + mailto_links))
        
        # 2. Look for phones
        phones = re.findall(PHONE_REGEX, page_text)
        
        # Clean up and return first found
        email_res = all_emails[0] if all_emails else "N/A"
        phone_res = phones[0] if phones else "N/A"
        
        return email_res, phone_res
    except Exception:
        return "N/A", "N/A"

def run_expert_scraper():
    print(f"🚀 Starting Search for {TARGET_DOMAIN}...")
    
    params = {'q': f'site:{TARGET_DOMAIN}', 'format': 'json'}
    headers = {'User-Agent': USER_AGENT, 'Referer': f"{INSTANCE_URL}/"}

    try:
        # Step 1: Get results from your Local SearXNG
        response = requests.get(f"{INSTANCE_URL}/search", params=params, headers=headers)
        if response.status_code != 200:
            print(f"❌ Server Error: {response.status_code}")
            return

        data = response.json()
        results = data.get('results', [])
        final_leads = []

        # Step 2: Loop results and perform Deep Scan
        for item in results:
            name = item.get('title', 'Unknown')
            link = item.get('url')
            
            # Use Deep Scan to get the "Invisible" data
            email, phone = deep_scan_url(link)
            
            final_leads.append({
                'Company Name': name,
                'Website': link,
                'Email': email,
                'Phone': phone
            })

        # Step 3: Save to JSON/CSV properly
        df = pd.DataFrame(final_leads)
        df.to_json('glstech_leads.json', orient='records', indent=4)
        df.to_csv('glstech_leads.csv', index=False)
        
        print(f"\n✅ DONE! Found {len(final_leads)} records.")
        print("📁 Saved to glstech_leads.json and glstech_leads.csv")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_expert_scraper()