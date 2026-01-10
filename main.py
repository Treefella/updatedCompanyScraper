import tkinter as tk
from tkinter import ttk, messagebox
import threading, subprocess, requests, re
from pathlib import Path

BASE_DIR = Path.home() / "Documents" / "updatedCompanyScraper"

class LeadGenPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Consett Lead Agent - GitHub Integrated")
        self.root.geometry("1000x650")
        self.root.configure(bg="#2b2b2b")
        self.setup_ui()

    def setup_ui(self):
        # Navbar with GitHub Status
        nav = tk.Frame(self.root, bg="#3c3f41", height=40)
        nav.pack(fill="x")
        
        self.git_label = tk.Label(nav, text="Git: Checking...", bg="#3c3f41", fg="white", font=("Arial", 9))
        self.git_label.pack(side="right", padx=10)
        
        # Table
        self.tree = ttk.Treeview(self.root, columns=("Name", "Phone", "Link"), show="headings")
        self.tree.heading("Name", text="Business Name")
        self.tree.heading("Phone", text="Phone")
        self.tree.heading("Link", text="Website")
        self.tree.pack(fill="both", expand=True, padx=20, pady=20)

        # Actions
        btn_frame = tk.Frame(self.root, bg="#2b2b2b")
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="🔍 Fetch Leads", command=self.fetch).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🚀 Push to GitHub", command=self.push_to_git).pack(side="left", padx=5)

    def push_to_git(self):
        """Automatically commits and pushes leads to GitHub."""
        try:
            subprocess.run(["git", "add", "."], cwd=BASE_DIR, check=True)
            subprocess.run(["git", "commit", "-m", "Automated lead update"], cwd=BASE_DIR)
            subprocess.run(["git", "push", "origin", "main"], cwd=BASE_DIR, check=True)
            messagebox.showinfo("GitHub Sync", "Leads pushed successfully!")
        except Exception as e:
            messagebox.showerror("Git Error", f"Push failed: {e}")

    def fetch(self):
        # The scraping logic we built previously...
        self.tree.insert("", "end", values=("Example Biz", "01207 123456", "http://example.com"))
        messagebox.showinfo("Scan", "Scan complete. Don't forget to Push to GitHub!")

if __name__ == "__main__":
    root = tk.Tk(); app = LeadGenPro(root); root.mainloop()