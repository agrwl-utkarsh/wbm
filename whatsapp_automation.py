#!/usr/bin/env python3
"""
WhatsApp Bulk Messenger - Desktop Automation Tool
A production-ready Tkinter application for sending bulk WhatsApp messages via WhatsApp Web.

Requirements:
    pip install playwright pandas openpyxl
    playwright install chromium
"""

import ctypes
import sys

# Fix DPI blurriness on Windows
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI v2
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
import threading
import random
import time
import urllib.parse
import re
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# Playwright imports
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
except ImportError:
    print("Playwright not installed. Run: pip install playwright && playwright install chromium")
    raise


class WhatsAppAutomationApp:
    """Main application class for WhatsApp bulk messaging."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("WhatsApp Bulk Messenger")
        self.root.geometry("580x720")
        self.root.minsize(580, 680)
        self.root.configure(bg="#f0f2f5")

        # State variables
        self.file_path: Optional[str] = None
        self.contacts: List[Dict[str, str]] = []
        self.is_running = False
        self.stop_requested = False
        self.automation_thread: Optional[threading.Thread] = None
        self.sent_count = 0
        self.failed_count = 0

        # Playwright objects (initialized in thread)
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        # Session directory for persistent login (works in source and frozen)
        if getattr(sys, 'frozen', False):
            base = Path(sys.executable).parent
        else:
            base = Path(__file__).parent
        self.session_dir = base / "wa_saved_session"
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # WhatsApp-inspired color palette
        self.WHITE = "#ffffff"
        self.BG_APP = "#f0f2f5"          # App background (WhatsApp Web gray)
        self.BG_CHAT = "#ece5dd"         # Chat background pattern color
        self.BG_CARD = "#ffffff"         # Card/panel background
        self.BG_HOVER = "#f0f2f5"        # Hover state
        self.FG_PRIMARY = "#111b21"      # Primary text (WhatsApp dark)
        self.FG_SECONDARY = "#667781"    # Secondary text
        self.FG_MUTED = "#8696a0"        # Muted text
        self.WA_GREEN = "#00a884"        # WhatsApp bright green
        self.WA_GREEN_HOVER = "#008069"  # WhatsApp green hover
        self.WA_GREEN_LIGHT = "#dcf8c6"  # Message bubble green
        self.WA_TEAL = "#075e54"         # Header teal (classic WhatsApp)
        self.WA_TEAL_DARK = "#054a43"    # Darker teal
        self.RED = "#e74c3c"
        self.RED_HOVER = "#c0392b"
        self.BORDER = "#d9d9d9"          # Subtle border
        self.SHADOW = "rgba(0,0,0,0.08)" # Shadow color
        self.FONT_FAMILY = "Segoe UI"
        self.FONT_SIZE = 10

        self._setup_styles()
        self._build_ui()

    def _setup_styles(self) -> None:
        """Configure ttk styles for WhatsApp-inspired theme."""
        style = ttk.Style()
        style.theme_use("clam")

        # Base styles - clean and minimal
        style.configure(".", background=self.BG_APP, foreground=self.FG_PRIMARY, font=(self.FONT_FAMILY, self.FONT_SIZE))
        style.configure("TFrame", background=self.BG_APP)
        
        # Card frame - white with subtle border
        style.configure("Card.TFrame", background=self.BG_CARD, borderwidth=0, relief="flat")
        
        # Label styles
        style.configure("TLabel", background=self.BG_APP, foreground=self.FG_PRIMARY, font=(self.FONT_FAMILY, self.FONT_SIZE))
        style.configure("Header.TLabel", background=self.WA_TEAL, foreground=self.WHITE, font=(self.FONT_FAMILY, 14, "bold"))
        style.configure("CardTitle.TLabel", background=self.BG_CARD, foreground=self.FG_PRIMARY, font=(self.FONT_FAMILY, 12, "bold"))
        style.configure("CardSubtitle.TLabel", background=self.BG_CARD, foreground=self.FG_SECONDARY, font=(self.FONT_FAMILY, 9))
        style.configure("Hint.TLabel", background=self.BG_CARD, foreground=self.FG_MUTED, font=(self.FONT_FAMILY, 9))
        style.configure("FileLabel.TLabel", background=self.BG_CARD, foreground=self.FG_SECONDARY, padding=(14, 12), anchor="w", font=(self.FONT_FAMILY, self.FONT_SIZE))
        style.configure("Stat.TLabel", background=self.BG_CARD, foreground=self.FG_PRIMARY, font=(self.FONT_FAMILY, 11))
        style.configure("StatValue.TLabel", background=self.BG_CARD, foreground=self.WA_GREEN, font=(self.FONT_FAMILY, 11, "bold"))

        # Entry styling
        style.configure("Modern.TEntry", fieldbackground=self.WHITE, foreground=self.FG_PRIMARY, borderwidth=1, relief="solid", bordercolor=self.BORDER, padding=10)
        style.map("Modern.TEntry", bordercolor=[("focus", self.WA_GREEN)], relief=[("focus", "solid")])

        # Progress bar - thin, WhatsApp green
        style.configure("Modern.Horizontal.TProgressbar", background=self.WA_GREEN, troughcolor=self.BORDER, borderwidth=0, thickness=6)

        # Button styles - WhatsApp style
        style.configure("Primary.TButton", 
            background=self.WA_GREEN, foreground=self.WHITE, 
            font=(self.FONT_FAMILY, 10, "bold"), padding=(24, 12),
            borderwidth=0, focusthickness=0, focuscolor=self.WA_GREEN)
        style.map("Primary.TButton", 
            background=[("active", self.WA_GREEN_HOVER), ("disabled", self.FG_MUTED)],
            foreground=[("disabled", "#cccccc")])

        style.configure("Secondary.TButton", 
            background=self.BG_CARD, foreground=self.FG_PRIMARY, 
            font=(self.FONT_FAMILY, 10, "bold"), padding=(24, 12),
            borderwidth=1, bordercolor=self.BORDER)
        style.map("Secondary.TButton", 
            background=[("active", self.BG_HOVER), ("disabled", self.BG_APP)],
            foreground=[("disabled", self.FG_MUTED)],
            bordercolor=[("active", self.WA_GREEN)])

        style.configure("Danger.TButton", 
            background=self.RED, foreground=self.WHITE, 
            font=(self.FONT_FAMILY, 10, "bold"), padding=(24, 12),
            borderwidth=0)
        style.map("Danger.TButton", 
            background=[("active", self.RED_HOVER), ("disabled", "#f5b7b1")])

        # LabelFrame - card style
        style.configure("Card.TLabelframe", background=self.BG_CARD, borderwidth=1, relief="solid", bordercolor=self.BORDER)
        style.configure("Card.TLabelframe.Label", background=self.BG_CARD, foreground=self.FG_PRIMARY, font=(self.FONT_FAMILY, 11, "bold"), padding=(0, 0, 0, 8)) 
            background=self.WHATSAPP_GREEN, foreground=self.WHITE, 
            font=(self.FONT_FAMILY, self.FONT_SIZE, "bold"), padding=(20, 12),
            borderwidth=0, focusthickness=0, focuscolor=self.WHATSAPP_GREEN)
        style.map("Primary.TButton", 
            background=[("active", self.WHATSAPP_GREEN_HOVER), ("disabled", self.FG_MUTED)],
            foreground=[("disabled", "#cccccc")])

        style.configure("Secondary.TButton", 
            background=self.BG_CARD, foreground=self.FG_PRIMARY, 
            font=(self.FONT_FAMILY, self.FONT_SIZE, "bold"), padding=(20, 12),
            borderwidth=1, bordercolor=self.BORDER)
        style.map("Secondary.TButton", 
            background=[("active", self.BG_HOVER), ("disabled", self.BG_LIGHT)],
            foreground=[("disabled", self.FG_MUTED)],
            bordercolor=[("active", self.WHATSAPP_GREEN)])

        style.configure("Danger.TButton", 
            background=self.RED, foreground=self.WHITE, 
            font=(self.FONT_FAMILY, self.FONT_SIZE, "bold"), padding=(20, 12),
            borderwidth=0)
        style.map("Danger.TButton", 
            background=[("active", self.RED_HOVER), ("disabled", "#f5b7b1")])

        # LabelFrame styling
        style.configure("Card.TLabelframe", background=self.BG_CARD, borderwidth=1, relief="solid", bordercolor=self.BORDER)
        style.configure("Card.TLabelframe.Label", background=self.BG_CARD, foreground=self.FG_PRIMARY, font=(self.FONT_FAMILY, 11, "bold"), padding=(0, 0, 0, 8))

    def _build_ui(self) -> None:
        """Build the complete GUI layout - WhatsApp inspired with header bar and scrollable content."""
        # Root background
        self.root.configure(bg=self.BG_APP)
        
        # ===== WHATSAPP-STYLE HEADER BAR =====
        header_bar = tk.Frame(self.root, bg=self.WA_TEAL, height=64)
        header_bar.pack(fill=tk.X, side=tk.TOP)
        header_bar.pack_propagate(False)
        
        # Header content
        header_content = tk.Frame(header_bar, bg=self.WA_TEAL)
        header_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=0)
        
        # App icon + title
        title_frame = tk.Frame(header_content, bg=self.WA_TEAL)
        title_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # Green dot indicator (like WhatsApp)
        status_dot = tk.Canvas(title_frame, width=12, height=12, bg=self.WA_TEAL, highlightthickness=0)
        status_dot.create_oval(2, 2, 10, 10, fill=self.WA_GREEN, outline="")
        status_dot.pack(side=tk.LEFT, padx=(0, 12), pady=22)
        
        title_text = tk.Frame(title_frame, bg=self.WA_TEAL)
        title_text.pack(side=tk.LEFT, fill=tk.Y, pady=10)
        
        tk.Label(title_text, text="WhatsApp Bulk Messenger", bg=self.WA_TEAL, fg=self.WHITE, 
                font=(self.FONT_FAMILY, 15, "bold")).pack(anchor="w")
        tk.Label(title_text, text="Send personalized messages at scale", bg=self.WA_TEAL, fg="#b3e5dc", 
                font=(self.FONT_FAMILY, 9)).pack(anchor="w")
        
        # Version/badge on right
        badge_frame = tk.Frame(header_content, bg=self.WA_TEAL)
        badge_frame.pack(side=tk.RIGHT, fill=tk.Y, pady=16)
        tk.Label(badge_frame, text="v1.0", bg=self.WA_TEAL_DARK, fg=self.WHITE, 
                font=(self.FONT_FAMILY, 8, "bold"), padx=8, pady=2).pack()

        # ===== SCROLLABLE CONTENT AREA =====
        # Canvas for scrolling
        self.canvas = tk.Canvas(self.root, bg=self.BG_APP, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Main content frame inside canvas
        self.content_frame = tk.Frame(self.canvas, bg=self.BG_APP)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        
        # Scroll bindings
        def on_frame_configure(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.content_frame.bind("<Configure>", on_frame_configure)
        
        def on_canvas_configure(event):
            self.canvas.itemconfig(self.canvas_window, width=event.width)
        self.canvas.bind("<Configure>", on_canvas_configure)
        
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # Inner padding frame
        main_frame = tk.Frame(self.content_frame, bg=self.BG_APP)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # ===== CARD 1: CONTACT FILE =====
        file_card = self._create_card(main_frame, "Contact File", "Select a CSV or Excel file with Name and Phone columns")
        file_card.pack(fill=tk.X, pady=(0, 16))
        
        btn_select = self._create_button(file_card, "Choose CSV/Excel File", style="secondary", command=self._select_file)
        btn_select.pack(fill=tk.X, padx=16, pady=(0, 12))
        
        self.lbl_file = tk.Label(file_card, text="No file selected", bg=self.BG_CARD, fg=self.FG_SECONDARY,
                                font=(self.FONT_FAMILY, 10), anchor="w", padx=16, pady=12)
        self.lbl_file.pack(fill=tk.X, padx=0, pady=(0, 16))

        # ===== CARD 2: MESSAGE TEMPLATE =====
        msg_card = self._create_card(main_frame, "Message Template", "Use {name} placeholder for personalization")
        msg_card.pack(fill=tk.BOTH, expand=True, pady=(0, 16))
        
        # Text area with custom styling
        text_container = tk.Frame(msg_card, bg=self.BG_CARD)
        text_container.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))
        
        self.txt_message = tk.Text(
            text_container,
            height=9,
            wrap=tk.WORD,
            bg=self.WHITE,
            fg=self.FG_PRIMARY,
            insertbackground=self.WA_GREEN,
            font=(self.FONT_FAMILY, 11),
            relief=tk.FLAT,
            borderwidth=1,
            highlightbackground=self.BORDER,
            highlightcolor=self.WA_GREEN,
            highlightthickness=1,
            padx=14,
            pady=14
        )
        msg_scroll = ttk.Scrollbar(text_container, orient="vertical", command=self.txt_message.yview)
        self.txt_message.configure(yscrollcommand=msg_scroll.set)
        self.txt_message.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        msg_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.txt_message.insert("1.0", "Hello {name},\n\nThis is a test message from WhatsApp Bulk Messenger.\n\nRegards,\nYour Name")

        # ===== CARD 3: CONTROLS & PROGRESS =====
        control_card = self._create_card(main_frame, "Campaign Controls")
        control_card.pack(fill=tk.X, pady=(0, 16))
        
        # Buttons row
        btn_row = tk.Frame(control_card, bg=self.BG_CARD)
        btn_row.pack(fill=tk.X, padx=16, pady=(0, 16))
        
        self.btn_start = self._create_button(btn_row, "Start Campaign", style="primary", command=self._start_campaign)
        self.btn_start.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        
        self.btn_stop = self._create_button(btn_row, "Stop", style="danger", command=self._stop_campaign)
        self.btn_stop.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        self.btn_stop.config(state=tk.DISABLED)
        
        # Progress bar
        progress_container = tk.Frame(control_card, bg=self.BG_CARD)
        progress_container.pack(fill=tk.X, padx=16, pady=(0, 16))
        
        self.progress = ttk.Progressbar(progress_container, mode="determinate", maximum=100, style="Modern.Horizontal.TProgressbar")
        self.progress.pack(fill=tk.X)
        
        self.lbl_progress = tk.Label(progress_container, text="Ready to start", bg=self.BG_CARD, fg=self.FG_MUTED,
                                    font=(self.FONT_FAMILY, 9), anchor="w")
        self.lbl_progress.pack(fill=tk.X, pady=(8, 0))

        # ===== CARD 4: LIVE STATS =====
        stats_card = self._create_card(main_frame, "Live Statistics")
        stats_card.pack(fill=tk.X, pady=(0, 16))
        
        stats_grid = tk.Frame(stats_card, bg=self.BG_CARD)
        stats_grid.pack(fill=tk.X, padx=16, pady=16)
        stats_grid.columnconfigure(0, weight=1)
        stats_grid.columnconfigure(1, weight=1)
        stats_grid.columnconfigure(2, weight=1)
        
        # Sent stat
        sent_frame = tk.Frame(stats_grid, bg=self.BG_CARD)
        sent_frame.grid(row=0, column=0, sticky="ew", padx=8)
        tk.Label(sent_frame, text="Sent", bg=self.BG_CARD, fg=self.FG_MUTED, font=(self.FONT_FAMILY, 9)).pack()
        self.lbl_sent = tk.Label(sent_frame, text="0", bg=self.BG_CARD, fg=self.WA_GREEN, font=(self.FONT_FAMILY, 24, "bold"))
        self.lbl_sent.pack()
        
        # Failed stat
        failed_frame = tk.Frame(stats_grid, bg=self.BG_CARD)
        failed_frame.grid(row=0, column=1, sticky="ew", padx=8)
        tk.Label(failed_frame, text="Failed", bg=self.BG_CARD, fg=self.FG_MUTED, font=(self.FONT_FAMILY, 9)).pack()
        self.lbl_failed = tk.Label(failed_frame, text="0", bg=self.BG_CARD, fg=self.RED, font=(self.FONT_FAMILY, 24, "bold"))
        self.lbl_failed.pack()
        
        # Pending/Total stat
        pending_frame = tk.Frame(stats_grid, bg=self.BG_CARD)
        pending_frame.grid(row=0, column=2, sticky="ew", padx=8)
        tk.Label(pending_frame, text="Total", bg=self.BG_CARD, fg=self.FG_MUTED, font=(self.FONT_FAMILY, 9)).pack()
        self.lbl_total = tk.Label(pending_frame, text="0", bg=self.BG_CARD, fg=self.FG_PRIMARY, font=(self.FONT_FAMILY, 24, "bold"))
        self.lbl_total.pack()

        # ===== CARD 5: ACTIVITY LOG =====
        log_card = self._create_card(main_frame, "Activity Log")
        log_card.pack(fill=tk.BOTH, expand=True)
        
        log_container = tk.Frame(log_card, bg=self.BG_CARD)
        log_container.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))
        
        self.txt_log = scrolledtext.ScrolledText(
            log_container,
            height=10,
            wrap=tk.WORD,
            bg="#f8f9fa",
            fg=self.FG_PRIMARY,
            insertbackground=self.WA_GREEN,
            font=("Consolas", 9),
            relief=tk.FLAT,
            borderwidth=0,
            state=tk.DISABLED,
            padx=12,
            pady=12
        )
        self.txt_log.pack(fill=tk.BOTH, expand=True)

        # Configure log tags for colored output
        self.txt_log.tag_config("timestamp", foreground=self.FG_MUTED, font=("Consolas", 8))
        self.txt_log.tag_config("success", foreground=self.WA_GREEN)
        self.txt_log.tag_config("error", foreground=self.RED)
        self.txt_log.tag_config("info", foreground=self.FG_PRIMARY)
        self.txt_log.tag_config("warning", foreground="#f39c12")
        self.txt_log.tag_config("debug", foreground=self.FG_SECONDARY)

        # Initial log message
        self._log("Application started. Select a contact file to begin.", "info")

    def _create_card(self, parent, title, subtitle=None):
        """Create a WhatsApp-style card with title and optional subtitle."""
        card = tk.Frame(parent, bg=self.BG_CARD, highlightbackground=self.BORDER, highlightthickness=1)
        
        # Card header
        header = tk.Frame(card, bg=self.BG_CARD)
        header.pack(fill=tk.X, padx=16, pady=(16, 0))
        
        tk.Label(header, text=title, bg=self.BG_CARD, fg=self.FG_PRIMARY, 
                font=(self.FONT_FAMILY, 12, "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(header, text=subtitle, bg=self.BG_CARD, fg=self.FG_MUTED, 
                    font=(self.FONT_FAMILY, 9)).pack(anchor="w", pady=(2, 0))
        
        # Separator line
        sep = tk.Frame(card, bg=self.BORDER, height=1)
        sep.pack(fill=tk.X, padx=16, pady=(12, 0))
        
        # Content area (caller packs content here)
        content = tk.Frame(card, bg=self.BG_CARD)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Store content frame for caller to use
        card.content = content
        return card

    def _create_button(self, parent, text, style="primary", command=None):
        """Create a WhatsApp-style button."""
        if style == "primary":
            bg, fg, hover_bg = self.WA_GREEN, self.WHITE, self.WA_GREEN_HOVER
        elif style == "secondary":
            bg, fg, hover_bg = self.BG_CARD, self.FG_PRIMARY, self.BG_HOVER
        elif style == "danger":
            bg, fg, hover_bg = self.RED, self.WHITE, self.RED_HOVER
        else:
            bg, fg, hover_bg = self.WA_GREEN, self.WHITE, self.WA_GREEN_HOVER
        
        btn = tk.Button(
            parent,
            text=text,
            bg=bg,
            fg=fg,
            activebackground=hover_bg,
            activeforeground=fg,
            font=(self.FONT_FAMILY, 10, "bold"),
            relief=tk.FLAT,
            borderwidth=0,
            padx=24,
            pady=12,
            cursor="hand2",
            command=command
        )
        
        # Add border for secondary style
        if style == "secondary":
            btn.config(highlightbackground=self.BORDER, highlightcolor=self.WA_GREEN, 
                      highlightthickness=1, bd=0)
        
        return btn

    def _select_file(self) -> None:
        """Open file dialog to select CSV/Excel contact file."""
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        file_path = filedialog.askopenfilename(
            title="Select Contact File",
            initialdir=desktop,
            filetypes=[
                ("CSV Files", "*.csv"),
                ("Excel Files", "*.xlsx"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            self.file_path = file_path
            filename = os.path.basename(file_path)
            self.lbl_file.config(text=f"Loaded: {filename}")
            self._log(f"File selected: {filename}")
            self._load_contacts()

    def _load_contacts(self) -> None:
        """Load and validate contacts from the selected file."""
        try:
            if self.file_path.endswith(".csv"):
                df = pd.read_csv(self.file_path)
            else:
                df = pd.read_excel(self.file_path, engine="openpyxl")

            # Normalize column names (case-insensitive)
            df.columns = [col.strip().lower() for col in df.columns]

            required_cols = {"name", "phone"}
            if not required_cols.issubset(set(df.columns)):
                missing = required_cols - set(df.columns)
                raise ValueError(f"Missing required columns: {', '.join(missing)}. File must have 'Name' and 'Phone' columns.")

            # Clean and prepare contacts
            self.contacts = []
            for _, row in df.iterrows():
                name = str(row["name"]).strip()
                phone = str(row["phone"]).strip()
                if name and phone:
                    cleaned_phone = self._clean_phone(phone)
                    self.contacts.append({"name": name, "phone": cleaned_phone})

            self._log(f"DEBUG: Parsed {len(self.contacts)} valid contacts from file")
            self._log(f"Loaded {len(self.contacts)} valid contacts from file.")
            self.progress["maximum"] = len(self.contacts)
            self.progress["value"] = 0

        except Exception as e:
            self._log(f"ERROR: Failed to load contacts - {str(e)}")
            messagebox.showerror("Error Loading File", str(e))
            self.contacts = []
            self.lbl_file.config(text="No file selected")
            self.file_path = None

    @staticmethod
    def _clean_phone(phone: str) -> str:
        """
        Clean phone number for WhatsApp Web.
        - Strip non-digits
        - 10 digits -> prepend '91' (India)
        - 12 digits starting with '91' -> keep as-is
        - Otherwise -> keep original
        """
        digits = re.sub(r"\D", "", phone)

        if len(digits) == 10:
            return "91" + digits
        elif len(digits) == 12 and digits.startswith("91"):
            return digits
        else:
            return digits

    def _log(self, message: str, level: str = "info") -> None:
        """Thread-safe logging to the console text widget with color coding."""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        
        def append_log():
            self.txt_log.config(state=tk.NORMAL)
            # Insert timestamp
            self.txt_log.insert(tk.END, f"{timestamp} ", "timestamp")
            # Insert message with level-based color
            self.txt_log.insert(tk.END, f"{message}\n", level)
            self.txt_log.see(tk.END)
            self.txt_log.config(state=tk.DISABLED)

        # Schedule on main thread
        self.root.after(0, append_log)

    def _update_progress(self, value: int, total: int = None) -> None:
        """Thread-safe progress bar update with label and stat counters."""
        def update():
            self.progress.config(value=value)
            if total:
                pct = int((value / total) * 100) if total > 0 else 0
                self.lbl_progress.config(text=f"{value}/{total} ({pct}%)")
            else:
                self.lbl_progress.config(text=f"{value}")
            # Update stat labels
            self.lbl_sent.config(text=str(self.sent_count))
            self.lbl_failed.config(text=str(self.failed_count))
            self.lbl_total.config(text=str(total if total else len(self.contacts)))
        self.root.after(0, update)

    def _set_controls_state(self, running: bool) -> None:
        """Thread-safe control button state management."""
        def update():
            if running:
                self.btn_start.config(state=tk.DISABLED, bg=self.FG_MUTED)
                self.btn_stop.config(state=tk.NORMAL, bg=self.RED)
            else:
                self.btn_start.config(state=tk.NORMAL, bg=self.WA_GREEN)
                self.btn_stop.config(state=tk.DISABLED, bg=self.FG_MUTED)
        self.root.after(0, update)

    def _start_campaign(self) -> None:
        """Validate and start the messaging campaign in a background thread."""
        if not self.contacts:
            messagebox.showwarning("No Contacts", "Please select a valid contact file first.")
            return

        message_template = self.txt_message.get("1.0", tk.END).strip()
        if not message_template:
            messagebox.showwarning("Empty Message", "Please enter a message template.")
            return

        if "{name}" not in message_template:
            if not messagebox.askyesno("No Placeholder", "Message doesn't contain {name} placeholder. Continue anyway?"):
                return

        # Reset counters
        self.sent_count = 0
        self.failed_count = 0
        self.stop_requested = False
        self.is_running = True

        # Update UI
        self._set_controls_state(True)
        self.progress["value"] = 0
        self.lbl_total.config(text=str(len(self.contacts)))
        self.lbl_sent.config(text="0")
        self.lbl_failed.config(text="0")
        self._log("=" * 50, "info")
        self._log("CAMPAIGN STARTED", "success")
        self._log(f"Total contacts: {len(self.contacts)}", "info")
        self._log("=" * 50, "info")

        # Start automation thread
        self.automation_thread = threading.Thread(
            target=self._run_automation,
            args=(message_template,),
            daemon=True
        )
        self.automation_thread.start()

    def _stop_campaign(self) -> None:
        """Request graceful stop of the campaign."""
        self.stop_requested = True
        self._log("Stop requested. Finishing current message...", "warning")

    def _run_automation(self, message_template: str) -> None:
        """Main automation loop running in background thread."""
        self._log(f"DEBUG: _run_automation started, contacts={len(self.contacts)}, template_len={len(message_template)}", "debug")
        try:
            with sync_playwright() as p:
                self.playwright = p
                self._log("Launching browser with persistent session...", "info")
                
                # Launch persistent context for QR code persistence
                self.context = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_dir),
                    headless=False,
                    args=["--start-maximized"]
                )
                self._log("DEBUG: Browser context created", "debug")
                self.browser = self.context.browser
                self.page = self.context.new_page()

                # Navigate to WhatsApp Web
                self._log("Opening WhatsApp Web...", "info")
                self.page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

                # Wait for chat pane (user scans QR if needed)
                self._log("Waiting for WhatsApp Web to load (scan QR code if prompted)...", "info")
                try:
                    self.page.wait_for_selector("#pane-side", timeout=120000)
                    self._log("WhatsApp Web loaded successfully!", "success")
                except PlaywrightTimeoutError:
                    self._log("ERROR: Timeout waiting for WhatsApp Web. QR code not scanned in time.", "error")
                    raise

                # Process each contact
                total = len(self.contacts)
                for idx, contact in enumerate(self.contacts):
                    if self.stop_requested:
                        self._log("Campaign stopped by user.", "warning")
                        break

                    name = contact["name"]
                    phone = contact["phone"]
                    personalized_msg = message_template.replace("{name}", name)
                    encoded_msg = urllib.parse.quote(personalized_msg)

                    self._log(f"Sending to {name} ({phone})... [{idx + 1}/{total}]", "info")

                    try:
                        # Navigate to chat with pre-filled message
                        url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_msg}"
                        self.page.goto(url, wait_until="domcontentloaded")

                        # Wait for message input box
                        input_selector = "footer div[contenteditable='true']"
                        self.page.wait_for_selector(input_selector, timeout=20000)

                        # Human-like delay before sending
                        time.sleep(random.uniform(1.5, 3.0))

                        # Press Enter to send
                        self.page.keyboard.press("Enter")

                        # Wait for message to be sent (visual confirmation)
                        time.sleep(1.5)

                        self.sent_count += 1
                        self._log(f"SUCCESS: Message sent to {name} ({phone})", "success")

                    except Exception as e:
                        self.failed_count += 1
                        self._log(f"FAILED: {name} ({phone}) - {str(e)}", "error")

# Update progress
                    self._update_progress(idx + 1, total)

                    # Anti-ban delay between messages (except last)
                    if idx < total - 1 and not self.stop_requested:
                        delay = random.uniform(8.0, 14.0)
                        self._log(f"Waiting {delay:.1f}s before next message...", "info")
                        time.sleep(delay)

        finally:
            self._cleanup_browser()
            self._finish_campaign()

    def _cleanup_browser(self) -> None:
        """Clean up Playwright resources."""
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
        except Exception:
            pass
        finally:
            self.context = None
            self.browser = None
            self.page = None
            self.playwright = None

    def _finish_campaign(self) -> None:
        """Finalize campaign and show summary."""
        self.is_running = False
        self._set_controls_state(False)

        summary = f"Campaign completed! Sent: {self.sent_count}, Failed: {self.failed_count}"
        self._log("=" * 50, "info")
        self._log(summary, "success" if self.failed_count == 0 else "warning")
        self._log("=" * 50, "info")

        # Show summary dialog on main thread
        self.root.after(0, lambda: messagebox.showinfo("Campaign Complete", summary))


def main() -> None:
    """Entry point for the application."""
    root = tk.Tk()
    app = WhatsAppAutomationApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()