import threading
import time
import random
import csv
import re
import os
from datetime import datetime
from queue import Queue

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox


# =========================
# CONFIG
# =========================

START_URL = "https://www.lifeindurham.co.uk/business-directory/"
MAX_RESULTS = 200
CSV_FILENAME = f"businesses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

PHONE_REGEX = re.compile(r"\+?\d[\d\s().-]{7,}")
WEBSITE_REGEX = re.compile(r"https?://[^\s\"'>]+")

MIN_DELAY = 1.5
MAX_DELAY = 4.0
RETRY_LIMIT = 3


# =========================
# GUI CLASS
# =========================

class ScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Business Directory Scraper")

        self.queue = Queue()
        self.scraped_count = 0
        self.running = False

        self.build_gui()
        self.root.after(100, self.process_queue)

    def build_gui(self):
        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, padx=10, pady=5)

        self.start_btn = ttk.Button(top, text="Start Scraping", command=self.start_scraper)
        self.start_btn.pack(side=tk.LEFT)

        self.count_label = ttk.Label(top, text="Scraped: 0")
        self.count_label.pack(side=tk.LEFT, padx=20)

        # Results table
        self.tree = ttk.Treeview(
            self.root,
            columns=("Name", "Phone", "Website"),
            show="headings",
            height=12
        )
        for col in ("Name", "Phone", "Website"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=220)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Log output
        self.log = scrolledtext.ScrolledText(self.root, height=10, state="disabled")
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def log_msg(self, msg):
        self.log.configure(state="normal")
        self.log.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {msg}\n")
        self.log.yview(tk.END)
        self.log.configure(state="disabled")

    def start_scraper(self):
        if self.running:
            return

        self.running = True
        self.start_btn.config(state="disabled")
        self.log_msg(f"CSV will be saved to: {os.path.abspath(CSV_FILENAME)}")

        thread = threading.Thread(
            target=run_scraper,
            args=(self.queue,),
            daemon=True
        )
        thread.start()

    def process_queue(self):
        try:
            while True:
                msg = self.queue.get_nowait()

                if msg["type"] == "log":
                    self.log_msg(msg["data"])

                elif msg["type"] == "data":
                    self.scraped_count += 1
                    self.count_label.config(text=f"Scraped: {self.scraped_count}")
                    self.tree.insert("", tk.END, values=msg["data"])

                elif msg["type"] == "done":
                    self.log_msg("Scraping completed.")
                    self.start_btn.config(state="normal")
                    self.running = False

        except Exception:
            pass

        self.root.after(100, self.process_queue)


# =========================
# SCRAPER LOGIC
# =========================

def human_delay():
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


def extract_details(text):
    phone = ", ".join(set(PHONE_REGEX.findall(text))) or "N/A"
    website = ", ".join(set(WEBSITE_REGEX.findall(text))) or "N/A"
    return phone, website


def run_scraper(queue):
    queue.put({"type": "log", "data": "Launching browser..."})

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.ne
