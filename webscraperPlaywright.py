import csv
import time
import random
import warnings
import asyncio
import webbrowser
from threading import Thread
from tkinter import Tk, Button, Label, ttk, Scrollbar, VERTICAL, HORIZONTAL, RIGHT, LEFT, Y, X, BOTH, END, BOTTOM, Frame, Text, Checkbutton, IntVar
from playwright.sync_api import sync_playwright, TimeoutError

# Suppress Windows event loop warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, message="Event loop is closed")
asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

SEARCH_URL = "https://www.google.com/maps/search/businesses+in+Consett"

def log_verbose(gui_log, message):
    gui_log.insert(END, message + "\n")
    gui_log.see(END)

def human_scroll(page, gui_log, max_scrolls=50, min_delay=1.5, max_delay=4):
    last_height = 0
    for _ in range(max_scrolls):
        scroll_distance = random.randint(500, 1500)
        try:
            page.mouse.wheel(0, scroll_distance)
        except Exception as e:
            log_verbose(gui_log, f"[Scroll] Failed, retrying... {e}")
            time.sleep(1)
        time.sleep(random.uniform(min_delay, max_delay))
        x, y = random.randint(100, 800), random.randint(100, 600)
        try:
            page.mouse.move(x, y, steps=random.randint(5, 15))
        except Exception:
            pass
        try:
            new_height = page.evaluate("document.querySelector('div[role=main]').scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        except Exception:
            break

def scrape_google_maps(gui_tree, gui_log, filters):
    """Runs in background thread"""
    log_verbose(gui_log, "[Info] Starting Playwright scraper...")
    with sync_playwright() as p:
        with p.chromium.launch(headless=False) as browser:
            page = browser.new_page()

            # Retry page load
            for attempt in range(3):
                try:
                    page.goto(SEARCH_URL, timeout=30000)
                    log_verbose(gui_log, "[Info] Page loaded successfully.")
                    break
                except TimeoutError:
                    log_verbose(gui_log, f"[Warning] Timeout loading page, retry {attempt+1}")
                    time.sleep(5)
            else:
                log_verbose(gui_log, "[Error] Failed to load page after 3 retries.")
                return

            time.sleep(random.uniform(3, 6))
            log_verbose(gui_log, "[Info] Scrolling page to load businesses...")
            human_scroll(page, gui_log)

            results = page.query_selector_all("div[role='article']")
            businesses = []
            log_verbose(gui_log, f"[Info] Found {len(results)} result elements.")

            for idx, r in enumerate(results, start=1):
                name, address, phone, website = "", "", "", ""

                for _ in range(2):
                    try:
                        name = r.query_selector("h3 span").inner_text()
                        break
                    except:
                        time.sleep(0.5)
                for _ in range(2):
                    try:
                        address = r.query_selector("span[aria-label*='Address']").inner_text()
                        break
                    except:
                        time.sleep(0.5)
                for _ in range(2):
                    try:
                        phone = r.query_selector("button[data-tooltip*='Call']").inner_text()
                        break
                    except:
                        time.sleep(0.5)
                for _ in range(2):
                    try:
                        website_elem = r.query_selector("a[data-tooltip*='Website']")
                        if website_elem:
                            website = website_elem.get_attribute("href")
                        break
                    except:
                        time.sleep(0.5)

                if name:
                    business = {
                        "name": name,
                        "address": address,
                        "phone": phone,
                        "website": website
                    }
                    businesses.append(business)

                    # Apply filters before populating GUI
                    if filters["website"].get() and not website:
                        continue
                    if filters["phone"].get() and not phone:
                        continue

                    gui_tree.insert("", END, values=(name, address, phone, website))
                    log_verbose(gui_log, f"[Scraped {idx}] {name} | {address} | {phone} | {website}")
                    time.sleep(random.uniform(0.3, 1))

            # Save CSV
            with open("consett_businesses.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["name", "address", "phone", "website"])
                writer.writeheader()
                writer.writerows(businesses)
            log_verbose(gui_log, f"[Info] Scraping finished. Total businesses: {len(businesses)}")
            log_verbose(gui_log, "[Info] Results saved to consett_businesses.csv")

def start_scraper_thread(tree, log, filters):
    thread = Thread(target=scrape_google_maps, args=(tree, log, filters), daemon=True)
    thread.start()

def on_tree_click(event, tree):
    item = tree.selection()
    if item:
        url = tree.item(item, "values")[3]
        if url:
            webbrowser.open(url)

def create_gui():
    root = Tk()
    root.title("Consett Businesses Scraper")
    root.geometry("1300x750")

    frame = Frame(root)
    frame.pack(fill=BOTH, expand=True)

    # Treeview
    tree = ttk.Treeview(frame, columns=("Name", "Address", "Phone", "Website"), show='headings')
    for col, width in zip(["Name", "Address", "Phone", "Website"], [250, 350, 120, 400]):
        tree.heading(col, text=col)
        tree.column(col, width=width)

    vsb = Scrollbar(frame, orient=VERTICAL, command=tree.yview)
    hsb = Scrollbar(frame, orient=HORIZONTAL, command=tree.xview)
    tree.configure(yscroll=vsb.set, xscroll=hsb.set)

    vsb.pack(side=RIGHT, fill=Y)
    hsb.pack(side=BOTTOM, fill=X)
    tree.pack(side=LEFT, fill=BOTH, expand=True)

    tree.bind("<Double-1>", lambda e: on_tree_click(e, tree))

    # Verbose log box
    log_frame = Frame(root)
    log_frame.pack(fill=BOTH, expand=False)
    gui_log = Text(log_frame, height=10)
    log_scroll = Scrollbar(log_frame, command=gui_log.yview)
    gui_log.configure(yscrollcommand=log_scroll.set)
    log_scroll.pack(side=RIGHT, fill=Y)
    gui_log.pack(side=LEFT, fill=BOTH, expand=True)

    # Filters
    filter_frame = Frame(root)
    filter_frame.pack(pady=5)
    website_var = IntVar()
    phone_var = IntVar()
    filters = {"website": website_var, "phone": phone_var}

    Checkbutton(filter_frame, text="Only show businesses with Website", variable=website_var).pack(side=LEFT, padx=5)
    Checkbutton(filter_frame, text="Only show businesses with Phone", variable=phone_var).pack(side=LEFT, padx=5)

    label = Label(root, text="Click 'Start Scraper' to begin scraping Consett businesses")
    label.pack(pady=5)

    start_button = Button(root, text="Start Scraper", command=lambda: start_scraper_thread(tree, gui_log, filters))
    start_button.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
