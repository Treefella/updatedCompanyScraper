import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue
import time
import random
import csv
import os
import re
from datetime import datetime


# =========================
# CONFIG
# =========================

SEARCH_QUERY = "Businesses in Consett"
MAX_RESULTS = 300
MIN_DELAY = 1.2
MAX_DELAY = 3.2

CSV_FILE = f"consett_businesses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}")
URL_RE = re.compile(r"https?://[^\s]+")


# =========================
# GUI
# =========================

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Consett Business Scraper")

        self.q = queue.Queue()
        self.scraped = 0

        self.build_ui()
        self.root.after(100, self.process_queue)

    def build_ui(self):
        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, padx=10, pady=5)

        self.start_btn = ttk.Button(top, text="START SCRAPING", command=self.start)
        self.start_btn.pack(side=tk.LEFT)

        self.counter = ttk.Label(top, text="Scraped: 0")
        self.counter.pack(side=tk.LEFT, padx=20)

        self.tree = ttk.Treeview(
            self.root,
            columns=("Name", "Phone", "Website"),
            show="headings",
            height=12
        )

        for c in ("Name", "Phone", "Website"):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=260)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10)

        self.log = scrolledtext.ScrolledText(self.root, height=10, state="disabled")
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def log_msg(self, msg):
        self.log.config(state="normal")
        self.log.insert(tk.END, msg + "\n")
        self.log.yview(tk.END)
        self.log.config(state="disabled")

    def start(self):
        self.start_btn.config(state="disabled")
        self.log_msg(f"CSV will be saved to: {os.path.abspath(CSV_FILE)}")

        t = threading.Thread(target=scraper_worker, args=(self.q,), daemon=False)
        t.start()

    def process_queue(self):
        try:
            while True:
                msg = self.q.get_nowait()

                if msg["type"] == "log":
                    self.log_msg(msg["data"])

                elif msg["type"] == "data":
                    self.scraped += 1
                    self.counter.config(text=f"Scraped: {self.scraped}")
                    self.tree.insert("", tk.END, values=msg["data"])

        except queue.Empty:
            pass

        self.root.after(100, self.process_queue)


# =========================
# SCRAPER WORKER
# =========================

def jitter():
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


def scraper_worker(q):
    try:
        q.put({"type": "log", "data": "Starting Playwright..."})

        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                viewport={"width": random.randint(1100, 1400),
                          "height": random.randint(700, 900)},
                user_agent=random.choice([
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Mozilla/5.0 (X11; Linux x86_64)",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
                ])
            )

            page = context.new_page()

            page.goto(
                f"https://www.google.com/maps/search/{SEARCH_QUERY.replace(' ', '+')}",
                timeout=60000
            )

            jitter()

            seen = set()

            with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Name", "Phone", "Website"])

                while len(seen) < MAX_RESULTS:
                    cards = page.query_selector_all("a[href*='/place/']")

                    if not cards:
                        q.put({"type": "log", "data": "No result cards found."})
                        break

                    for card in cards:
                        try:
                            card.click()
                            page.wait_for_timeout(1200)

                            panel = page.locator("div[role='main']").inner_text()

                            name = panel.split("\n")[0].strip()
                            if name in seen:
                                continue

                            seen.add(name)

                            phone = ", ".join(PHONE_RE.findall(panel)) or "N/A"
                            website = ", ".join(URL_RE.findall(panel)) or "N/A"

                            writer.writerow([name, phone, website])
                            f.flush()

                            q.put({
                                "type": "data",
                                "data": (name, phone, website)
                            })

                            q.put({"type": "log", "data": f"Scraped: {name}"})

                            jitter()

                            if len(seen) >= MAX_RESULTS:
                                break

                        except Exception as e:
                            q.put({"type": "log", "data": f"Card error: {e}"})

                    # SCROLL RESULTS PANE
                    page.mouse.wheel(0, 4000)
                    jitter()

            browser.close()
            q.put({"type": "log", "data": "Scraping completed."})

    except Exception as e:
        q.put({"type": "log", "data": f"FATAL ERROR: {e}"})


# =========================
# MAIN
# =========================

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("900x700")
    App(root)
    root.mainloop()
