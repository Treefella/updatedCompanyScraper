import tkinter as tk
from tkinter import ttk, messagebox
import threading, logging, requests, re, os, subprocess
import pandas as pd
from pathlib import Path
from datetime import datetime

# --- CONFIGURATION ---
BASE_DIR = Path.home() / "Documents" / "updatedCompanyScraper"
DATA_DIR = BASE_DIR / "data"
INSTANCE_URL = "http://localhost:8088"
TARGET_POSTCODE = "DH8" # Consett, Blackhill, Leadgate, Shotley Bridge

DATA_DIR.mkdir(parents=True, exist_ok=True)

class DH8SearchExpert:
    def __init__(self, root):
        self.root = root
        self.root.title(f"SearXNG Expert - Postcode {TARGET_POSTCODE} Scanner")
        self.root.geometry("1000x750")
        self.setup_ui()

    def setup_ui(self):
        # Navbar
        nav = tk.Frame(self.root, bg="#1a1a1a", height=50)
        nav.pack(fill="x")
        tk.Label(nav, text=f"SEARXNG PIPELINE: {TARGET_POSTCODE}", fg="#00d1b2", bg="#1a1a1a", font=("Consolas", 12, "bold")).pack(side="left", padx=20)

        # Table
        style = ttk.Style()
        style.theme_use("clam")
        self.tree = ttk.Treeview(self.root, columns=("Company", "Phone", "Postcode", "Email"), show="headings")
        self.tree.heading("Company", text="Business Name")
        self.tree.heading("Phone", text="Phone")
        self.tree.heading("Postcode", text="Postcode")
        self.tree.heading("Email", text="Extracted Email")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Console
        self.console = tk.Text(self.root, height=10, bg="#000", fg="#0f0", font=("Courier", 9))
        self.console.pack(fill="x", padx=10, pady=5)

        # Controls
        btns = tk.Frame(self.root)
        btns.pack(pady=15)
        ttk.Button(btns, text="🔍 RUN DH8 SCAN", command=self.start_thread).pack(side="left", padx=10)
        ttk.Button(btns, text="💾 SAVE & PUSH", command=self.sync_git).pack(side="left", padx=10)

    def log(self, text):
        self.console.insert("end", f"> {text}\n")
        self.console.see("end")

    def start_thread(self):
        threading.Thread(target=self.execute_search, daemon=True).start()

    def execute_search(self):
        self.log(f"Connecting to SearXNG Instance at {INSTANCE_URL}...")
        leads = []
        
        # Expert Search Criteria: Combining Postcode with local identifiers
        search_queries = [
            f'business "{TARGET_POSTCODE}" Consett',
            f'site:yell.com "{TARGET_POSTCODE}"',
            f'"{TARGET_POSTCODE}" local directory consett'
        ]

        try:
            for query in search_queries:
                params = {
                    'q': query,
                    'format': 'json',
                    'categories': 'general,it',
                    'language': 'en-GB'
                }
                
                response = requests.get(f"{INSTANCE_URL}/search", params=params, timeout=15)
                results = response.json().get('results', [])
                
                for item in results:
                    content = item.get('content', '')
                    
                    # Regex for UK Postcode validation within DH8
                    if f"{TARGET_POSTCODE}" in content.upper() or f"{TARGET_POSTCODE}" in item.get('title', '').upper():
                        
                        # Extract Phone
                        phone_match = re.search(r'((?:\+44|0)[\d\s]{10,13})', content)
                        phone = phone_match.group(0) if phone_match else "N/A"
                        
                        # Extract Email (Expert Addition)
                        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
                        email = email_match.group(0) if email_match else "No Email in Snippet"
                        
                        name = item.get('title', 'Unknown')[:50]
                        
                        self.tree.insert("", "end", values=(name, phone, TARGET_POSTCODE, email))
                        leads.append([name, phone, TARGET_POSTCODE, email, item.get('url')])

            # File Generation
            if leads:
                df = pd.DataFrame(leads, columns=["Name", "Phone", "Postcode", "Email", "URL"])
                df.to_csv(DATA_DIR / "dh8_leads.csv", index=False)
                self.log(f"✅ Successfully captured {len(leads)} DH8 leads.")

        except Exception as e:
            self.log(f"❌ Connection Error: {e}")

    def sync_git(self):
        self.log("Syncing to GitHub via VS Code parameters...")
        try:
            subprocess.run(["git", "add", "."], cwd=BASE_DIR)
            subprocess.run(["git", "commit", "-m", f"DH8 Lead Sync {datetime.now().date()}"], cwd=BASE_DIR)
            subprocess.run(["git", "push", "origin", "main"], cwd=BASE_DIR)
            self.log("🚀 GitHub Updated.")
        except:
            self.log("⚠️ Git push failed. Ensure remote is connected in VS Code.")

if __name__ == "__main__":
    root = tk.Tk()
    app = DH8SearchExpert(root)
    root.mainloop()