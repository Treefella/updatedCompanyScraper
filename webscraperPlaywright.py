import csv
import os
import random
import time
import threading
import queue
import tkinter as tk
from tkinter import ttk

from playwright.sync_api import sync_playwright

# ================= CONFIG =================
QUERY = "businesses in Consett"
MAX_RESULTS = 50

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "consett_businesses.csv")

# ================= THREAD QUEUE =================
ui_queue = queue.Queue()

# ================= GUI =================
root = tk.Tk()
root.title("Consett Google Maps Scraper")
root.geometry("1100x600")

tree = ttk.Treeview(root, columns=("Name", "Phone", "Website"), show="headings")
for col, w in [("Name", 360), ("Phone", 180), ("Website", 520)]:
    tree.heading(col, text=col)
    tree.column(col, width=w)
tree.pack(fill=tk.BOTH, expand=True)

log_box = tk.Text(root, height=8)
log_box.pack(fill=tk.BOTH)

def process_queue():
    while not ui_queue.empty():
        item = ui_queue.get()
        if item["type"] == "log":
            log_box.insert(tk.END, item["msg"] + "\n")
            log_box.see(tk.END)

        elif item["type"] == "row":
            tree.insert("", tk.END, values=item["data"])
            with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(item["data"])

    root.after(100, process_queue)

# ================= SCRAPER =================
def scrape():
    ui_queue.put({"type": "log", "msg": "Starting browser..."})

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://www.google.com/maps", timeout=60000)
        page.fill("#searchboxinput", QUERY)
        page.keyboard.press("Enter")
        page.wait_for_timeout(6000)

        ui_queue.put({"type": "log", "msg": "Results loaded"})

        seen = set()
        count = 0

        while count < MAX_RESULTS:
            cards = page.query_selector_all("div[role='article']")

            for card in cards:
                try:
                    name_el = card.query_selector(".qBF1Pd")
                    if not name_el:
                        continue

                    name = name_el.inner_text().strip()
                    if name in seen:
                        continue
                    seen.add(name)

                    card.click()
                    page.wait_for_timeout(random.randint(1200, 2000))

                    phone = "N/A"
                    website = "N/A"

                    phone_el = page.query_selector("button[data-item-id^='phone']")
                    if phone_el:
                        phone = phone_el.inner_text().strip()

                    site_el = page.query_selector("a[data-item-id='authority']")
                    if site_el:
                        website = site_el.get_attribute("href")

                    ui_queue.put({
                        "type": "row",
                        "data": (name, phone, website)
                    })

                    ui_queue.put({
                        "type": "log",
                        "msg": f"Scraped: {name}"
                    })

                    count += 1
                    time.sleep(random.uniform(0.8, 1.4))

                    if count >= MAX_RESULTS:
                        break

                except Exception as e:
                    ui_queue.put({"type": "log", "msg": f"Error: {e}"})

            page.mouse.wheel(0, random.randint(1200, 1800))
            page.wait_for_timeout(random.randint(1200, 2200))

        browser.close()

    ui_queue.put({"type": "log", "msg": f"Finished. {count} businesses scraped."})

# ================= START =================
with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerow(["Name", "Phone", "Website"])

threading.Thread(target=scrape, daemon=True).start()
process_queue()
root.mainloop()
