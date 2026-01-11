import customtkinter as ctk
from tkinter import ttk, messagebox
import threading
import queue
import logging
import time
import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

class DH8IntelligenceApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # --- THREAD-SAFE INFRASTRUCTURE ---
        self.log_queue = queue.Queue()
        self.is_running = False
        
        # --- UI SETUP ---
        self.title("GLSTech | DH8 AI Intelligence Dashboard")
        self.geometry("1200x850")
        self._setup_styles()
        self._build_layout()
        
        # --- START QUEUE MONITOR ---
        self.after(100, self._process_queue)

    def _setup_styles(self):
        """Configure professional dark-mode aesthetics."""
        ctk.set_appearance_mode("dark")
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", rowheight=30)
        self.style.map("Treeview", background=[('selected', '#1f538d')])

    def _build_layout(self):
        """Created a split-pane view for Live Data and Verbose Logs."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=3) # Table
        self.grid_rowconfigure(2, weight=2) # Logs

        # 1. Control Header
        self.header = ctk.CTkFrame(self)
        self.header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        self.start_btn = ctk.CTkButton(self.header, text="🚀 START ENGINE", command=self.toggle_engine, fg_color="#28a745")
        self.start_btn.pack(side="left", padx=10)
        
        self.status_label = ctk.CTkLabel(self.header, text="SYSTEM READY", text_color="#555")
        self.status_label.pack(side="right", padx=10)

        # 2. Live Data Table
        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        self.tree = ttk.Treeview(self.table_frame, columns=("Name", "Phone", "Website"), show='headings')
        for col in ("Name", "Phone", "Website"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=300)
        self.tree.pack(expand=True, fill="both")

        # 3. Live Verbose Logging View
        self.log_view = ctk.CTkTextbox(self, fg_color="black", text_color="#00FF41", font=("Consolas", 12))
        self.log_view.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.log_view.insert("0.0", ">>> INITIALIZING VERBOSE LOG STREAM...\n")

    # --- THE "HEARTBEAT" LOGIC ---
    def queue_log(self, message, level="INFO"):
        """Background threads call this to 'drop a message in the bucket'."""
        self.log_queue.put(f"[{time.strftime('%H:%M:%S')}] [{level}] {message}")

    def _process_queue(self):
        """The GUI thread periodically checks the bucket for new logs/data."""
        try:
            while True: # Process all pending messages
                msg = self.log_queue.get_nowait()
                self.log_view.configure(state="normal")
                self.log_view.insert("end", msg + "\n")
                self.log_view.see("end")
                self.log_view.configure(state="disabled")
        except queue.Empty:
            pass
        finally:
            self.after(100, self._process_queue) # Repeat every 100ms

    # --- ENGINE LOGIC ---
    def toggle_engine(self):
        if not self.is_running:
            self.is_running = True
            self.start_btn.configure(text="🛑 STOP ENGINE", fg_color="#dc3545")
            threading.Thread(target=self.background_worker, daemon=True).start()
        else:
            self.is_running = False
            self.start_btn.configure(text="🚀 START ENGINE", fg_color="#28a745")

    def background_worker(self):
        """The Heavy Lifter: Selenium + Phi-3."""
        self.queue_log("Booting Chromium Driver...", "DEBUG")
        options = Options()
        # Visual mode is better for debugging 'dying' apps
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        try:
            self.queue_log("Connecting to Yell.com (DH8)...", "NETWORK")
            driver.get("https://www.yell.com/ucs/UcsSearchAction.do?keywords=business&location=DH8")
            
            # Wait for content
            time.sleep(3) 
            cards = driver.find_elements(By.CLASS_NAME, "businessCapsule")
            self.queue_log(f"Detected {len(cards)} entries.", "SCRAPE")

            for card in cards:
                if not self.is_running: break
                
                name = card.find_element(By.TAG_NAME, "h2").text
                self.queue_log(f"Processing: {name}", "AI_WAIT")
                
                # AI Logic Placeholder (Ollama Phi-3)
                # payload = {"model": "phi3", "prompt": card.text, "stream": False}
                # response = requests.post("http://localhost:11434/api/generate", json=payload)
                
                # Mock update for table safety
                self.after(0, lambda n=name: self.tree.insert("", "end", values=(n, "Extracting...", "Extracting...")))
                
            self.queue_log("Full Scan Completed Successfully.", "SUCCESS")
        except Exception as e:
            self.queue_log(f"FATAL ERROR: {str(e)}", "CRITICAL")
        finally:
            driver.quit()
            self.queue_log("Browser Session Closed.", "CLEANUP")

if __name__ == "__main__":
    app = DH8IntelligenceApp()
    app.mainloop()