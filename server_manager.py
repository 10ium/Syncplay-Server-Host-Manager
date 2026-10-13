import os
import sys
import json
import time
import socket
import webbrowser
import urllib.request
import threading
import subprocess
import winsound
import psutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULT_CONFIG = {
    "port": "24680",
    "password": "2210",
    "room": "movie",
    "public_ip": "5.232.118.106",
    "local_ip": "192.168.1.6",
    "syncplay_dir": "",
    "enable_logs": True,
    "enable_sound_alerts": True
}

def find_syncplay_installation(custom_dir=""):
    """Auto-detect Syncplay directory across standard Windows locations or portable folder"""
    candidates = []
    if custom_dir and os.path.isdir(custom_dir):
        candidates.append(custom_dir)
    
    # Common Windows installation directories
    prog_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    prog_64 = os.environ.get("ProgramFiles", r"C:\Program Files")
    candidates.extend([
        os.path.join(prog_x86, "Syncplay"),
        os.path.join(prog_64, "Syncplay"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "Syncplay"),
        r"C:\Program Files (x86)\Syncplay",
        r"C:\Program Files\Syncplay"
    ])
    
    for c in candidates:
        server_exe = os.path.join(c, "syncplayServer.exe")
        if os.path.isfile(server_exe):
            return c
    return ""

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                return {**DEFAULT_CONFIG, **cfg}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving config: {e}")

def detect_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "192.168.1.6"

def get_syncplay_pid():
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == "syncplayserver.exe":
                return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return None

def kill_syncplay_processes():
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == "syncplayserver.exe":
                proc.kill()
        except Exception:
            pass

def check_windows_firewall_rule(port):
    try:
        cmd = f'netsh advfirewall firewall show rule name=all | findstr "{port}"'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, errors='replace')
        return str(port) in res.stdout
    except Exception:
        return False

def format_bytes(b):
    if b < 1024:
        return f"{b} B"
    elif b < 1024 * 1024:
        return f"{b / 1024:.1f} KB"
    elif b < 1024 * 1024 * 1024:
        return f"{b / (1024 * 1024):.1f} MB"
    else:
        return f"{b / (1024 * 1024 * 1024):.2f} GB"

def format_speed(bps):
    if bps < 1024:
        return f"{bps:.1f} B/s"
    elif bps < 1024 * 1024:
        return f"{bps / 1024:.1f} KB/s"
    else:
        return f"{bps / (1024 * 1024):.2f} MB/s"

class SyncplayManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("کنترل پنل سرور سینک‌پلی | Syncplay Server Manager")
        
        # Responsive & Resizable window with full Maximize support
        window_width = 780
        window_height = 920
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        pos_x = max(0, (screen_w - window_width) // 2)
        pos_y = max(0, (screen_h - window_height) // 2 - 25)
        self.root.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")
        self.root.minsize(700, 780)
        self.root.resizable(True, True)

        self.config = load_config()
        self.server_process = None
        self.server_start_time = None
        self.running_port = int(self.config.get("port", "24680"))
        self.is_monitoring = True

        # Syncplay paths
        self.syncplay_dir = find_syncplay_installation(self.config.get("syncplay_dir", ""))
        self.local_ip = self.config.get("local_ip") or detect_local_ip()

        # Stats & Traffic Tracking
        self.initial_proc_io = None
        self.last_proc_io = None
        self.last_io_time = None
        self.last_client_count = 0

        # Modern Dark Theme Palette
        self.bg_color = "#161622"
        self.card_bg = "#1e1e2f"
        self.subcard_bg = "#27273d"
        self.input_bg = "#31314d"
        self.text_color = "#e4e4f2"
        self.subtext_color = "#9fa3c7"
        self.accent_green = "#2ecc71"
        self.accent_red = "#e74c3c"
        self.accent_blue = "#4c8bf5"
        self.accent_yellow = "#f39c12"
        self.accent_purple = "#a27bfa"
        self.accent_cyan = "#00d2d3"

        self.root.configure(bg=self.bg_color)
        self.setup_ui()

        # Initial checks
        self.check_initial_status()
        self.check_firewall_status_real()
        self.start_monitoring_thread()

    def setup_ui(self):
        container = tk.Frame(self.root, bg=self.bg_color, padx=16, pady=10)
        container.pack(fill="both", expand=True)

        # 1. Header (Title & Help Button)
        header = tk.Frame(container, bg=self.card_bg, padx=18, pady=10, highlightthickness=1, highlightbackground="#2d2d48")
        header.pack(fill="x", pady=(0, 6))

        h_top = tk.Frame(header, bg=self.card_bg)
        h_top.pack(fill="x")

        tk.Label(
            h_top,
            text="🎬 کنترل پنل سرور سینک‌پلی",
            font=("Segoe UI", 16, "bold"),
            bg=self.card_bg,
            fg=self.accent_blue,
            justify="right"
        ).pack(side="right")

        btn_guide = tk.Button(
            h_top,
            text="📖 راهنمای مودم و تست CGNAT",
            font=("Segoe UI", 9, "bold"),
            bg="#2c3e50",
            fg=self.accent_cyan,
            activebackground="#34495e",
            activeforeground="#ffffff",
            cursor="hand2",
            padx=12,
            pady=4,
            relief="flat",
            command=self.open_cgnat_guide
        )
        btn_guide.pack(side="left")

        tk.Label(
            header,
            text="مدیریت آسان سرور، استعلام خودکار آی‌پی، آمار اختصاصی ترافیک و فرمت اشتراک تلگرام",
            font=("Segoe UI", 9),
            bg=self.card_bg,
            fg=self.subtext_color,
            justify="right"
        ).pack(anchor="e", pady=(2, 0))

        # 2. Status & Control Banner
        status_card = tk.Frame(container, bg=self.card_bg, padx=18, pady=12, highlightthickness=1, highlightbackground="#2d2d48")
        status_card.pack(fill="x", pady=3)

        st_top = tk.Frame(status_card, bg=self.card_bg)
        st_top.pack(fill="x")

        self.status_lbl = tk.Label(
            st_top,
            text="وضعیت سرور: در حال بررسی...",
            font=("Segoe UI", 12, "bold"),
            bg=self.card_bg,
            fg=self.text_color,
            justify="right"
        )
        self.status_lbl.pack(side="right")

        self.status_indicator = tk.Label(
            st_top,
            text="●",
            font=("Segoe UI", 18),
            bg=self.card_bg,
            fg=self.accent_yellow
        )
        self.status_indicator.pack(side="right", padx=(6, 0))

        # Control Row 1: Start/Stop Server & Online Port Test
        row1 = tk.Frame(status_card, bg=self.card_bg)
        row1.pack(fill="x", pady=(10, 4))

        self.btn_toggle = tk.Button(
            row1,
            text="▶ روشن کردن سرور",
            font=("Segoe UI", 11, "bold"),
            bg=self.accent_green,
            fg="#ffffff",
            activebackground="#27ae60",
            activeforeground="#ffffff",
            cursor="hand2",
            padx=20,
            pady=6,
            relief="flat",
            command=self.toggle_server
        )
        self.btn_toggle.pack(side="right")

        self.btn_test_port = tk.Button(
            row1,
            text="🔍 تست آنلاین پورت مودم از اینترنت",
            font=("Segoe UI", 9),
            bg=self.subcard_bg,
            fg=self.accent_cyan,
            activebackground="#353554",
            activeforeground=self.accent_cyan,
            cursor="hand2",
            padx=12,
            pady=6,
            relief="flat",
            command=self.run_online_port_test
        )
        self.btn_test_port.pack(side="left")

        # Control Row 2: Sharing Buttons (Dedicated 2 Spacious Buttons with Zero Overlap!)
        row2 = tk.Frame(status_card, bg=self.card_bg)
        row2.pack(fill="x", pady=(4, 0))

        self.btn_copy_friend = tk.Button(
            row2,
            text="📤 کپی مشخصات برای دوست (آی‌پی اینترنت)",
            font=("Segoe UI", 10, "bold"),
            bg=self.accent_yellow,
            fg="#11111b",
            activebackground="#e67e22",
            activeforeground="#11111b",
            cursor="hand2",
            padx=16,
            pady=6,
            relief="flat",
            command=self.copy_friend_info
        )
        self.btn_copy_friend.pack(side="right")

        self.btn_copy_self = tk.Button(
            row2,
            text="📋 کپی آدرس برای خودم (لوکال)",
            font=("Segoe UI", 10, "bold"),
            bg="#2c3e50",
            fg=self.accent_cyan,
            activebackground="#34495e",
            activeforeground="#ffffff",
            cursor="hand2",
            padx=16,
            pady=6,
            relief="flat",
            command=self.copy_self_info
        )
        self.btn_copy_self.pack(side="right", padx=(0, 10))

        # 3. Dedicated Syncplay Server Stats
        stats_card = tk.Frame(container, bg=self.card_bg, padx=18, pady=10, highlightthickness=1, highlightbackground="#2d2d48")
        stats_card.pack(fill="x", pady=3)

        tk.Label(
            stats_card,
            text="📊 وضعیت آنلاین کلاینت‌ها و ترافیک اختصاصی سرور",
            font=("Segoe UI", 10, "bold"),
            bg=self.card_bg,
            fg=self.accent_purple,
            justify="right"
        ).pack(anchor="e", pady=(0, 6))

        stats_grid = tk.Frame(stats_card, bg=self.card_bg)
        stats_grid.pack(fill="x")

        # Card 1: Clients
        c1 = tk.Frame(stats_grid, bg=self.subcard_bg, padx=8, pady=6, highlightthickness=1, highlightbackground="#363654")
        c1.pack(side="right", expand=True, fill="both", padx=3)
        tk.Label(c1, text="کاربران آنلاین در اتاق", font=("Segoe UI", 8), bg=self.subcard_bg, fg=self.subtext_color).pack()
        self.lbl_clients = tk.Label(c1, text="۰ نفر", font=("Segoe UI", 11, "bold"), bg=self.subcard_bg, fg=self.text_color)
        self.lbl_clients.pack(pady=1)
        self.lbl_clients_detail = tk.Label(c1, text="منتظر اتصال", font=("Segoe UI", 7), bg=self.subcard_bg, fg="#6c7094")
        self.lbl_clients_detail.pack()

        # Card 2: Speed
        c2 = tk.Frame(stats_grid, bg=self.subcard_bg, padx=8, pady=6, highlightthickness=1, highlightbackground="#363654")
        c2.pack(side="right", expand=True, fill="both", padx=3)
        tk.Label(c2, text="سرعت تبادل سرور", font=("Segoe UI", 8), bg=self.subcard_bg, fg=self.subtext_color).pack()
        self.lbl_speed = tk.Label(c2, text="0.0 KB/s", font=("Segoe UI", 11, "bold"), bg=self.subcard_bg, fg=self.accent_cyan)
        self.lbl_speed.pack(pady=1)
        tk.Label(c2, text="Transfer Speed", font=("Segoe UI", 7), bg=self.subcard_bg, fg="#6c7094").pack()

        # Card 3: Total Traffic
        c3 = tk.Frame(stats_grid, bg=self.subcard_bg, padx=8, pady=6, highlightthickness=1, highlightbackground="#363654")
        c3.pack(side="right", expand=True, fill="both", padx=3)
        tk.Label(c3, text="کل ترافیک مصرفی سرور", font=("Segoe UI", 8), bg=self.subcard_bg, fg=self.subtext_color).pack()
        self.lbl_total_data = tk.Label(c3, text="0 B", font=("Segoe UI", 11, "bold"), bg=self.subcard_bg, fg=self.accent_green)
        self.lbl_total_data.pack(pady=1)
        tk.Label(c3, text="Total Traffic", font=("Segoe UI", 7), bg=self.subcard_bg, fg="#6c7094").pack()

        # Card 4: RAM
        c4 = tk.Frame(stats_grid, bg=self.subcard_bg, padx=8, pady=6, highlightthickness=1, highlightbackground="#363654")
        c4.pack(side="right", expand=True, fill="both", padx=3)
        tk.Label(c4, text="مصرف حافظه رم سرور", font=("Segoe UI", 8), bg=self.subcard_bg, fg=self.subtext_color).pack()
        self.lbl_ram = tk.Label(c4, text="0 MB", font=("Segoe UI", 11, "bold"), bg=self.subcard_bg, fg=self.accent_yellow)
        self.lbl_ram.pack(pady=1)
        tk.Label(c4, text="Process RAM", font=("Segoe UI", 7), bg=self.subcard_bg, fg="#6c7094").pack()

        # Uptime
        uptime_bar = tk.Frame(stats_card, bg=self.card_bg)
        uptime_bar.pack(fill="x", pady=(6, 0))

        self.lbl_uptime = tk.Label(
            uptime_bar,
            text="مدت زمان فعالیت سرور: 00:00:00",
            font=("Segoe UI", 8),
            bg=self.card_bg,
            fg=self.subtext_color
        )
        self.lbl_uptime.pack(side="right")

        # 4. Connection Guide Banner
        guide_banner = tk.Frame(container, bg="#1a2538", padx=16, pady=6, highlightthickness=1, highlightbackground="#2d4263")
        guide_banner.pack(fill="x", pady=3)

        tk.Label(
            guide_banner,
            text="💡 راهنمای اتصال: خودتان در برنامه سینک‌پلی 127.0.0.1 بزنید | دوستتان آی‌پی عمومی مودم را بزند",
            font=("Segoe UI", 8, "bold"),
            bg="#1a2538",
            fg=self.accent_cyan,
            justify="right"
        ).pack(anchor="e")

        # 5. Network, IP & Firewall Card (Both IPs Editable with Auto-Detect Buttons!)
        info_card = tk.Frame(container, bg=self.card_bg, padx=18, pady=8, highlightthickness=1, highlightbackground="#2d2d48")
        info_card.pack(fill="x", pady=3)

        tk.Label(
            info_card,
            text="🌐 اطلاعات شبکه، آی‌پی‌ها و وضعیت فایروال",
            font=("Segoe UI", 10, "bold"),
            bg=self.card_bg,
            fg=self.accent_blue,
            justify="right"
        ).pack(anchor="e", pady=(0, 4))

        # Firewall Row
        fw_bar = tk.Frame(info_card, bg=self.card_bg)
        fw_bar.pack(fill="x", pady=2)

        self.btn_fix_firewall = tk.Button(
            fw_bar,
            text="🛡️ ثبت پورت در فایروال",
            font=("Segoe UI", 8),
            bg=self.subcard_bg,
            fg=self.accent_yellow,
            cursor="hand2",
            relief="flat",
            command=self.fix_firewall_action
        )
        self.btn_fix_firewall.pack(side="left")

        self.lbl_fw_status = tk.Label(
            fw_bar,
            text="فایروال ویندوز: در حال بررسی...",
            font=("Segoe UI", 9, "bold"),
            bg=self.card_bg,
            fg=self.subtext_color
        )
        self.lbl_fw_status.pack(side="right")

        # Public IP Row (Editable + Auto-Detect)
        pub_bar = tk.Frame(info_card, bg=self.card_bg)
        pub_bar.pack(fill="x", pady=2)

        tk.Label(pub_bar, text="آی‌پی عمومی مودم (Public IP):", font=("Segoe UI", 9), bg=self.card_bg, fg=self.text_color).pack(side="right", padx=(4, 0))
        self.entry_public_ip = tk.Entry(pub_bar, font=("Segoe UI", 10), bg=self.input_bg, fg=self.accent_yellow, insertbackground="white", width=16, relief="flat", justify="center")
        self.entry_public_ip.insert(0, self.config.get("public_ip", "5.232.118.106"))
        self.entry_public_ip.pack(side="right", padx=(4, 10))

        btn_detect_pub = tk.Button(
            pub_bar,
            text="🌐 استعلام آی‌پی اینترنت",
            font=("Segoe UI", 8),
            bg=self.subcard_bg,
            fg=self.accent_cyan,
            cursor="hand2",
            relief="flat",
            command=self.manual_fetch_public_ip
        )
        btn_detect_pub.pack(side="left")

        # Local IP Row (Editable + Auto-Detect)
        loc_bar = tk.Frame(info_card, bg=self.card_bg)
        loc_bar.pack(fill="x", pady=2)

        tk.Label(loc_bar, text="آی‌پی داخلی سیستم (Local IP):", font=("Segoe UI", 9), bg=self.card_bg, fg=self.text_color).pack(side="right", padx=(4, 0))
        self.entry_local_ip = tk.Entry(loc_bar, font=("Segoe UI", 10), bg=self.input_bg, fg=self.accent_green, insertbackground="white", width=16, relief="flat", justify="center")
        self.entry_local_ip.insert(0, self.local_ip)
        self.entry_local_ip.pack(side="right", padx=(4, 10))

        btn_detect_loc = tk.Button(
            loc_bar,
            text="🔄 استعلام آی‌پی داخلی",
            font=("Segoe UI", 8),
            bg=self.subcard_bg,
            fg=self.subtext_color,
            cursor="hand2",
            relief="flat",
            command=self.manual_detect_local_ip
        )
        btn_detect_loc.pack(side="left")

        # 6. Settings Card
        cfg_card = tk.Frame(container, bg=self.card_bg, padx=18, pady=8, highlightthickness=1, highlightbackground="#2d2d48")
        cfg_card.pack(fill="x", pady=3)

        cfg_top = tk.Frame(cfg_card, bg=self.card_bg)
        cfg_top.pack(fill="x", pady=(0, 4))

        tk.Label(
            cfg_top,
            text="⚙️ تنظیمات سرور و اعلان‌ها",
            font=("Segoe UI", 10, "bold"),
            bg=self.card_bg,
            fg=self.accent_blue,
            justify="right"
        ).pack(side="right")

        self.var_sound_alert = tk.BooleanVar(value=self.config.get("enable_sound_alerts", True))
        chk_sound = tk.Checkbutton(
            cfg_top,
            text="🔔 صدای اعلان ورود/خروج دوست",
            variable=self.var_sound_alert,
            bg=self.card_bg,
            fg=self.accent_yellow,
            selectcolor=self.input_bg,
            activebackground=self.card_bg,
            activeforeground=self.accent_yellow,
            font=("Segoe UI", 8),
            command=self.save_sound_pref
        )
        chk_sound.pack(side="left")

        cfg_form = tk.Frame(cfg_card, bg=self.card_bg)
        cfg_form.pack(fill="x", pady=2)

        btn_save = tk.Button(
            cfg_form,
            text="💾 ذخیره تنظیمات",
            font=("Segoe UI", 9, "bold"),
            bg=self.accent_blue,
            fg="#ffffff",
            activebackground="#3877db",
            activeforeground="#ffffff",
            cursor="hand2",
            padx=14,
            pady=3,
            relief="flat",
            command=self.save_settings_action
        )
        btn_save.pack(side="left", anchor="center")

        f_port = tk.Frame(cfg_form, bg=self.card_bg)
        f_port.pack(side="right", padx=(10, 0))
        tk.Label(f_port, text="پورت سرور:", font=("Segoe UI", 9), bg=self.card_bg, fg=self.text_color).pack(anchor="e")
        self.entry_port = tk.Entry(f_port, font=("Segoe UI", 10), bg=self.input_bg, fg=self.text_color, insertbackground="white", width=8, relief="flat", justify="center")
        self.entry_port.insert(0, self.config.get("port", "24680"))
        self.entry_port.pack(anchor="e", pady=(2, 0))

        f_pass = tk.Frame(cfg_form, bg=self.card_bg)
        f_pass.pack(side="right", padx=(10, 0))
        tk.Label(f_pass, text="رمز عبور:", font=("Segoe UI", 9), bg=self.card_bg, fg=self.text_color).pack(anchor="e")
        self.entry_pass = tk.Entry(f_pass, font=("Segoe UI", 10), bg=self.input_bg, fg=self.text_color, insertbackground="white", width=12, relief="flat", justify="center")
        self.entry_pass.insert(0, self.config.get("password", "2210"))
        self.entry_pass.pack(anchor="e", pady=(2, 0))

        f_room = tk.Frame(cfg_form, bg=self.card_bg)
        f_room.pack(side="right", padx=(10, 0))
        tk.Label(f_room, text="اتاق مشترک:", font=("Segoe UI", 9), bg=self.card_bg, fg=self.text_color).pack(anchor="e")
        self.entry_room = tk.Entry(f_room, font=("Segoe UI", 10), bg=self.input_bg, fg=self.text_color, insertbackground="white", width=10, relief="flat", justify="center")
        self.entry_room.insert(0, self.config.get("room", "movie"))
        self.entry_room.pack(anchor="e", pady=(2, 0))

        # 7. Quick Shortcuts & Path Config
        sc_card = tk.Frame(container, bg=self.card_bg, padx=18, pady=8, highlightthickness=1, highlightbackground="#2d2d48")
        sc_card.pack(fill="x", pady=3)

        sc_bar = tk.Frame(sc_card, bg=self.card_bg)
        sc_bar.pack(fill="x")

        tk.Label(
            sc_bar,
            text="🚀 میانبرهای سریع:",
            font=("Segoe UI", 9, "bold"),
            bg=self.card_bg,
            fg=self.accent_purple
        ).pack(side="right", padx=(0, 16))

        btn_client = tk.Button(
            sc_bar,
            text="🎬 اجرای برنامه سینک‌پلی (کلاینت)",
            font=("Segoe UI", 9, "bold"),
            bg=self.subcard_bg,
            fg=self.text_color,
            cursor="hand2",
            padx=14,
            pady=4,
            relief="flat",
            command=self.open_syncplay_client
        )
        btn_client.pack(side="right", padx=(0, 12))

        btn_modem = tk.Button(
            sc_bar,
            text="🌐 ورود به پنل مودم",
            font=("Segoe UI", 9),
            bg=self.subcard_bg,
            fg=self.subtext_color,
            cursor="hand2",
            padx=14,
            pady=4,
            relief="flat",
            command=lambda: webbrowser.open("http://192.168.1.1")
        )
        btn_modem.pack(side="right", padx=(0, 12))

        btn_path = tk.Button(
            sc_bar,
            text="📁 تغییر مسیر نصب سینک‌پلی",
            font=("Segoe UI", 8),
            bg=self.subcard_bg,
            fg=self.subtext_color,
            cursor="hand2",
            relief="flat",
            command=self.choose_syncplay_path
        )
        btn_path.pack(side="left")

        # 8. Live Logs
        log_card = tk.Frame(container, bg=self.card_bg, padx=18, pady=8, highlightthickness=1, highlightbackground="#2d2d48")
        log_card.pack(fill="both", expand=True, pady=(3, 0))

        log_top = tk.Frame(log_card, bg=self.card_bg)
        log_top.pack(fill="x", pady=(0, 4))

        tk.Label(
            log_top,
            text="📜 گزارش رویدادها و لاگ سرور",
            font=("Segoe UI", 10, "bold"),
            bg=self.card_bg,
            fg=self.text_color
        ).pack(side="right")

        self.var_enable_logs = tk.BooleanVar(value=self.config.get("enable_logs", True))
        chk_log = tk.Checkbutton(
            log_top,
            text="ثبت فعال لاگ (روشن/خاموش)",
            variable=self.var_enable_logs,
            bg=self.card_bg,
            fg=self.accent_cyan,
            selectcolor=self.input_bg,
            activebackground=self.card_bg,
            activeforeground=self.accent_cyan,
            font=("Segoe UI", 8),
            command=self.toggle_log_recording
        )
        chk_log.pack(side="right", padx=(0, 15))

        btn_clear = tk.Button(
            log_top,
            text="پاک کردن لاگ",
            font=("Segoe UI", 8),
            bg=self.subcard_bg,
            fg=self.subtext_color,
            cursor="hand2",
            relief="flat",
            command=self.clear_logs
        )
        btn_clear.pack(side="left")

        self.log_text = tk.Text(
            log_card,
            bg="#101018",
            fg="#9fa3c7",
            font=("Consolas", 9),
            relief="flat",
            wrap="word",
            state="disabled"
        )
        self.log_text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(log_card, orient="vertical", command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)

    def choose_syncplay_path(self):
        d = filedialog.askdirectory(title="پوشه نصب برنامه Syncplay را انتخاب کنید")
        if d:
            test_server = os.path.join(d, "syncplayServer.exe")
            if os.path.isfile(test_server):
                self.syncplay_dir = d
                self.config["syncplay_dir"] = d
                save_config(self.config)
                self.log(f"مسیر برنامه تنظیم شد: {d}")
                messagebox.showinfo("موفقیت", f"مسیر Syncplay با موفقیت ذخیره شد:\n{d}")
            else:
                messagebox.showerror("خطا", f"فایل syncplayServer.exe در این پوشه یافت نشد:\n{d}")

    def open_cgnat_guide(self):
        """Display an exhaustive, comprehensive CGNAT & Router guide window"""
        win = tk.Toplevel(self.root)
        win.title("راهنمای تشخیص CGNAT و تنظیم پورت انواع مودم‌ها")
        win.geometry("680x640")
        win.configure(bg=self.bg_color)

        c = tk.Frame(win, bg=self.card_bg, padx=16, pady=16)
        c.pack(fill="both", expand=True, padx=12, pady=12)

        tk.Label(
            c,
            text="📖 راهنمای کامل تشخیص CGNAT و فوروارد پورت در مودم‌ها",
            font=("Segoe UI", 13, "bold"),
            bg=self.card_bg,
            fg=self.accent_blue,
            justify="right"
        ).pack(anchor="e", pady=(0, 10))

        txt = tk.Text(c, bg="#101018", fg="#cdd6f4", font=("Segoe UI", 9), wrap="word", relief="flat")
        txt.pack(fill="both", expand=True)

        guide_content = """۱. چطور بفهمیم اینترنت ما پشت CGNAT (نات اپراتور) است یا آی‌پی اختصاصی داریم؟
--------------------------------------------------------------------------------
- وارد صفحه تنظیمات مودم خود شوید (معمولاً http://192.168.1.1).
- به بخش Status یا Device Info بروید و مقدار WAN IP Address را ببینید.
- اکنون یک سایت استعلام آی‌پی مانند https://api.ipify.org را باز کنید.

نتیجه:
الف) اگر آی‌پی صفحه مودم شما با سایتی که باز کردید یکی باشد: شما آی‌پی عمومی (Public IP) دارید و پورت فوروارد ۱۰۰٪ کار می‌کند!
ب) اگر آی‌پی مودم با اعدادی مثل:
   • 100.64.0.0 تا 100.127.255.255 (رنج استاندارد CGNAT)
   • 10.x.x.x یا 172.16.x.x
   شروع شود، خط شما پشت CGNAT است. در این حالت پورت فوروارد کار نمی‌کند و باید با پشتیبانی شرکت اینترنت خود تماس بگیرید و درخواست «آی‌پی استاتیک» (یا خروج از CGNAT) بدهید.

--------------------------------------------------------------------------------
۲. نحوه تنظیم فوروارد پورت (Virtual Server) در انواع مودم‌ها:
--------------------------------------------------------------------------------
در تمام مودم‌ها هدف این است که پورت سرور (24680) را به سمت آی‌پی داخلی سیستم (Local IP) بفرستید.

• مودم‌های یوتل (U.Tel):
  مسیر: Advanced > NAT > Virtual Server
  دکمه: User-defined Service Name: Syncplay
  پورت‌ها: WAN Port: 24680 | LAN Port: 24680 | Protocol: TCP
  آی‌پی: Server IP Address را روی Local IP کامپیوتر بگذارید.

• مودم‌های تی‌پی‌لینک (TP-Link):
  مسیر: Forwarding > Virtual Servers (یا Advanced > NAT Forwarding)
  پورت ورودی و خروجی: 24680
  پروتکل: TCP | آی‌پی: Local IP کامپیوتر.

• مودم‌های دی‌لینک (D-Link):
  مسیر: Advanced > Port Forwarding یا Virtual Server
  نام: Syncplay | پورت: 24680 | آی‌پی: Local IP | پروتکل: TCP.

• مودم‌های هواوی، ایرانسل، مبین‌نت:
  مسیر: Security > Virtual Server یا Port Forwarding
  تنظیمات مشابه: پورت 24680 و آی‌پی داخلی کامپیوتر.

--------------------------------------------------------------------------------
۳. نکته مهم لوپ‌بک (NAT Loopback):
--------------------------------------------------------------------------------
مودم‌های خانگی ترافیک ارسالی از داخل همان خانه به آی‌پی اینترنتی خودشان را برنمی‌گردانند.
به همین دلیل:
- خودتان روی کامپیوتر سرور باید در سینک‌پلی 127.0.0.1 را بزنید.
- دوستتان در خانه خودش باید آی‌پی اینترنت شما را بزند.
"""
        txt.insert("1.0", guide_content)
        txt.config(state="disabled")

    def play_chime(self, is_join=True):
        if not self.var_sound_alert.get():
            return
        def _beep():
            try:
                if is_join:
                    winsound.MessageBeep(winsound.MB_ICONASTERISK)
                else:
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            except Exception:
                pass
        threading.Thread(target=_beep, daemon=True).start()

    def save_sound_pref(self):
        self.config["enable_sound_alerts"] = self.var_sound_alert.get()
        save_config(self.config)

    def log(self, message):
        if not self.var_enable_logs.get():
            return
        def _append():
            self.log_text.config(state="normal")
            ts = time.strftime("[%H:%M:%S] ")
            self.log_text.insert("end", ts + message + "\n")
            lines = int(self.log_text.index('end-1c').split('.')[0])
            if lines > 300:
                self.log_text.delete("1.0", "50.0")
            self.log_text.see("end")
            self.log_text.config(state="disabled")
        self.root.after(0, _append)

    def clear_logs(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

    def toggle_log_recording(self):
        enabled = self.var_enable_logs.get()
        self.config["enable_logs"] = enabled
        save_config(self.config)
        if not enabled:
            self.clear_logs()
            self.log("ثبت لاگ موقتاً غیرفعال شد.")
        else:
            self.log("ثبت لاگ مجدداً فعال شد.")

    def check_firewall_status_real(self):
        port = self.entry_port.get().strip()
        def _check():
            ok = check_windows_firewall_rule(port)
            def _update():
                if ok:
                    self.lbl_fw_status.config(
                        text=f"فایروال ویندوز: پورت {port} باز و مجاز است ✅",
                        fg=self.accent_green
                    )
                    self.btn_fix_firewall.pack_forget()
                else:
                    self.lbl_fw_status.config(
                        text=f"فایروال ویندوز: پورت {port} مسدود است ❌",
                        fg=self.accent_red
                    )
                    self.btn_fix_firewall.pack(side="left")
            self.root.after(0, _update)
        threading.Thread(target=_check, daemon=True).start()

    def fix_firewall_action(self):
        port = self.entry_port.get().strip()
        cmd = f'netsh advfirewall firewall add rule name="Syncplay Server {port}" dir=in action=allow protocol=TCP localport={port}'
        self.log(f"در حال ثبت پورت {port} در فایروال با دسترسی مدیر...")
        try:
            subprocess.Popen(["powershell", "-Command", f'Start-Process cmd -ArgumentList \'/c "{cmd}"\' -Verb RunAs'])
            self.root.after(3000, self.check_firewall_status_real)
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در تنظیم فایروال: {e}")

    def run_online_port_test(self):
        port = self.entry_port.get().strip()
        pub_ip = self.entry_public_ip.get().strip()
        if not pub_ip or not port.isdigit():
            messagebox.showerror("خطا", "لطفاً آی‌پی عمومی و شماره پورت را وارد کنید.")
            return

        self.log(f"در حال تست پورت {port} روی {pub_ip} از طریق اینترنت...")
        self.btn_test_port.config(text="در حال تست...", state="disabled")

        def _test():
            success = False
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                res = s.connect_ex((pub_ip, int(port)))
                s.close()
                success = (res == 0)
            except Exception:
                pass

            def _done():
                self.btn_test_port.config(text="🔍 تست آنلاین پورت مودم از اینترنت", state="normal")
                if success:
                    self.log(f"نتیجه تست: پورت {port} مودم کاملاً باز و آماده اتصال است! ✅")
                    messagebox.showinfo("موفقیت‌آمیز", f"پورت {port} روی آی‌پی {pub_ip} با موفقیت تایید شد!\nمودم و سرور کاملاً آنلاین و در دسترس هستند.")
                else:
                    self.log(f"نتیجه تست: پورت {port} پاسخ نداد (سرور باید روشن باشد). ⚠️")
                    messagebox.showwarning("توجه", f"پورت {port} پاسخ نداد.\nمطمئن شوید سرور روشن است و مودم فوروارد شده است.")
            self.root.after(0, _done)

        threading.Thread(target=_test, daemon=True).start()

    def open_syncplay_client(self):
        if not self.syncplay_dir:
            self.choose_syncplay_path()
            if not self.syncplay_dir:
                return

        client_exe = os.path.join(self.syncplay_dir, "Syncplay.exe")
        if os.path.isfile(client_exe):
            try:
                subprocess.Popen([client_exe])
                self.log("برنامه اصلی سینک‌پلی باز شد.")
            except Exception as e:
                messagebox.showerror("خطا", f"خطا در باز کردن برنامه: {e}")
        else:
            messagebox.showerror("خطا", f"فایل Syncplay.exe در مسیر زیر پیدا نشد:\n{client_exe}")

    def manual_detect_local_ip(self):
        new_ip = detect_local_ip()
        self.local_ip = new_ip
        self.entry_local_ip.delete(0, "end")
        self.entry_local_ip.insert(0, new_ip)
        self.config["local_ip"] = new_ip
        save_config(self.config)
        self.log(f"آی‌پی داخلی سیستم استعلام شد: {new_ip}")

    def manual_fetch_public_ip(self):
        self.log("در حال استعلام آی‌پی عمومی اینترنت...")
        threading.Thread(target=self.fetch_public_ip, daemon=True).start()

    def fetch_public_ip(self):
        for url in ["https://api.ipify.org", "https://icanhazip.com", "https://ifconfig.me/ip"]:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=3) as response:
                    ip = response.read().decode('utf-8').strip()
                    if ip:
                        self.config["public_ip"] = ip
                        save_config(self.config)
                        def _update():
                            self.entry_public_ip.delete(0, "end")
                            self.entry_public_ip.insert(0, ip)
                        self.root.after(0, _update)
                        self.log(f"آی‌پی عمومی دریافت شد: {ip}")
                        return
            except Exception:
                continue
        self.log("استعلام ناموفق بود (آی‌پی را از تب Status مودم مشاهده کرده و دستی وارد کنید).")

    def check_initial_status(self):
        pid = get_syncplay_pid()
        if pid:
            self.server_start_time = time.time()
            self.set_ui_online()
            self.log(f"سرور سینک‌پلی فعال است (PID: {pid}).")
        else:
            self.set_ui_offline()
            self.log("سرور متوقف است. برای شروع، دکمه 'روشن کردن سرور' را بزنید.")

    def set_ui_online(self):
        self.status_indicator.config(fg=self.accent_green)
        port = self.running_port
        self.status_lbl.config(text=f"وضعیت سرور: روشن (آنلاین روی پورت {port})", fg=self.accent_green)
        self.btn_toggle.config(
            text="⏹ خاموش کردن سرور",
            bg=self.accent_red,
            activebackground="#c0392b"
        )

    def set_ui_offline(self):
        self.status_indicator.config(fg=self.accent_red)
        self.status_lbl.config(text="وضعیت سرور: خاموش (آفلاین)", fg=self.accent_red)
        self.btn_toggle.config(
            text="▶ روشن کردن سرور",
            bg=self.accent_green,
            activebackground="#27ae60"
        )
        self.server_start_time = None
        self.initial_proc_io = None
        self.last_client_count = 0
        self.lbl_uptime.config(text="مدت زمان فعالیت سرور: 00:00:00")
        self.lbl_clients.config(text="۰ نفر", fg=self.text_color)
        self.lbl_clients_detail.config(text="منتظر اتصال", fg="#6c7094")
        self.lbl_speed.config(text="0.0 KB/s")
        self.lbl_total_data.config(text="0 B")
        self.lbl_ram.config(text="0 MB")

    def toggle_server(self):
        pid = get_syncplay_pid()
        if pid:
            self.log("در حال توقف سرور...")
            kill_syncplay_processes()
            time.sleep(1)
            self.set_ui_offline()
            self.log("سرور با موفقیت خاموش شد.")
        else:
            if not self.syncplay_dir:
                self.choose_syncplay_path()
                if not self.syncplay_dir:
                    return

            server_exe = os.path.join(self.syncplay_dir, "syncplayServer.exe")
            if not os.path.isfile(server_exe):
                messagebox.showerror("خطا", f"فایل سرور پیدا نشد:\n{server_exe}")
                return

            port_str = self.entry_port.get().strip()
            password = self.entry_pass.get().strip()
            if not port_str.isdigit():
                messagebox.showerror("خطا", "شماره پورت باید یک عدد باشد.")
                return

            self.running_port = int(port_str)
            cmd = [server_exe, "--port", port_str, "--password", password]
            self.log(f"در حال روشن کردن سرور روی پورت {port_str}...")
            self.server_start_time = time.time()
            self.initial_proc_io = None

            def _run():
                try:
                    self.server_process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    self.root.after(0, self.set_ui_online)
                    for line in iter(self.server_process.stdout.readline, ''):
                        if line:
                            self.log(line.strip())
                    self.server_process.stdout.close()
                    self.server_process.wait()
                except Exception as e:
                    self.log(f"خطا در اجرای سرور: {e}")
                finally:
                    self.root.after(0, self.set_ui_offline)

            threading.Thread(target=_run, daemon=True).start()

    def save_settings_action(self):
        port = self.entry_port.get().strip()
        pwd = self.entry_pass.get().strip()
        room = self.entry_room.get().strip()
        pub_ip = self.entry_public_ip.get().strip()
        loc_ip = self.entry_local_ip.get().strip()

        if not port.isdigit():
            messagebox.showerror("خطا", "شماره پورت نامعتبر است.")
            return

        self.config["port"] = port
        self.config["password"] = pwd
        self.config["room"] = room
        self.config["public_ip"] = pub_ip
        self.config["local_ip"] = loc_ip
        self.local_ip = loc_ip
        save_config(self.config)
        self.log(f"تنظیمات ذخیره شد: پورت {port} | رمز {pwd} | اتاق {room}")
        self.check_firewall_status_real()
        messagebox.showinfo("ذخیره شد", "تنظیمات با موفقیت ذخیره شدند.\n(در صورت تغییر پورت، سرور را خاموش و دوباره روشن کنید).")

    def copy_self_info(self):
        port = self.entry_port.get().strip()
        addr = f"`127.0.0.1:{port}`"
        
        # Raw value for immediate paste
        raw_addr = f"127.0.0.1:{port}"
        self.root.clipboard_clear()
        self.root.clipboard_append(raw_addr)
        messagebox.showinfo(
            "کپی شد! ✅",
            f"آدرس سرور برای خودتان کپی شد (بدون https):\n\n{raw_addr}\n\nکافیست در کادر Server address برنامه سینک‌پلی پیست (Ctrl+V) کنید."
        )

    def copy_friend_info(self):
        port = self.entry_port.get().strip()
        pwd = self.entry_pass.get().strip()
        room = self.entry_room.get().strip() or "movie"
        pub_ip = self.entry_public_ip.get().strip() or "5.232.118.106"

        # Telegram-optimized formatting with markdown code blocks (click-to-copy, zero https://)
        formatted_message = (
            "🎬 مشخصات اتصال به سرور سینک‌پلی:\n\n"
            "🔹 آدرس سرور (Server address):\n"
            f"`{pub_ip}:{port}`\n\n"
            "🔹 رمز عبور (Server password):\n"
            f"`{pwd}`\n\n"
            "🔹 نام اتاق (Default room):\n"
            f"`{room}`\n\n"
            "💡 راهنما: برنامه Syncplay را باز کنید و مقادیر بالا را وارد کنید (در تلگرام روی هر کادر تیره بالا ضربه بزنید خودکار کپی می‌شود)."
        )

        self.root.clipboard_clear()
        self.root.clipboard_append(formatted_message)
        messagebox.showinfo(
            "کپی شد! 🎉",
            "پیام آماده برای ارسال به دوستتان با فرمت هوشمند تلگرام در کلیپ‌بورد کپی شد!\nکافیست در تلگرام برایش ارسال کنید."
        )

    def start_monitoring_thread(self):
        def _monitor():
            while self.is_monitoring:
                try:
                    pid = get_syncplay_pid()
                    is_running = (pid is not None)

                    if is_running and "خاموش" in self.status_lbl.cget("text"):
                        if not self.server_start_time:
                            self.server_start_time = time.time()
                        self.root.after(0, self.set_ui_online)
                    elif not is_running and "روشن" in self.status_lbl.cget("text"):
                        self.root.after(0, self.set_ui_offline)

                    if is_running:
                        p = psutil.Process(pid)

                        # 1. Connected Clients Breakdown
                        port_int = self.running_port
                        try:
                            conns = [c for c in p.net_connections(kind='tcp') if c.status == 'ESTABLISHED' and c.laddr.port == port_int]
                            client_count = len(conns)

                            local_count = 0
                            external_count = 0
                            external_ips = []
                            for c in conns:
                                r_ip = c.raddr.ip if c.raddr else ""
                                if r_ip in ("127.0.0.1", "::1", self.local_ip):
                                    local_count += 1
                                else:
                                    external_count += 1
                                    external_ips.append(r_ip)
                        except Exception:
                            client_count = 0
                            local_count = 0
                            external_count = 0
                            external_ips = []

                        # Sound alerts on connection count change
                        if client_count > self.last_client_count:
                            self.play_chime(is_join=True)
                            self.log(f"یک کلاینت جدید متصل شد! (تعداد کل: {client_count})")
                        elif client_count < self.last_client_count and self.last_client_count > 0:
                            self.play_chime(is_join=False)
                            self.log(f"یک کلاینت قطع شد! (تعداد کل: {client_count})")
                        self.last_client_count = client_count

                        # 2. RAM Usage
                        try:
                            mem_mb = p.memory_info().rss / (1024 * 1024)
                            ram_str = f"{mem_mb:.1f} MB"
                        except Exception:
                            ram_str = "0 MB"

                        # 3. Process Socket I/O
                        try:
                            io = p.io_counters()
                            current_socket_bytes = io.other_bytes
                        except Exception:
                            current_socket_bytes = 0

                        current_time = time.time()

                        if self.initial_proc_io is None:
                            self.initial_proc_io = current_socket_bytes
                            self.last_proc_io = current_socket_bytes
                            self.last_io_time = current_time

                        total_bytes = max(0, current_socket_bytes - self.initial_proc_io)

                        if client_count == 0:
                            speed_bps = 0.0
                        else:
                            dt = current_time - (self.last_io_time or current_time)
                            if dt > 0 and self.last_proc_io is not None:
                                delta = max(0, current_socket_bytes - self.last_proc_io)
                                speed_bps = delta / dt
                            else:
                                speed_bps = 0.0

                        self.last_proc_io = current_socket_bytes
                        self.last_io_time = current_time

                        # 4. Uptime
                        if self.server_start_time:
                            up_sec = int(time.time() - self.server_start_time)
                            h, r = divmod(up_sec, 3600)
                            m, s = divmod(r, 60)
                            uptime_str = f"مدت زمان فعالیت سرور: {h:02d}:{m:02d}:{s:02d}"
                        else:
                            uptime_str = "مدت زمان فعالیت سرور: 00:00:00"

                        # Friendly, respectful client breakdown (Never generic 'Guest')
                        if external_count > 0 and local_count > 0:
                            if external_count == 1:
                                client_title = "۲ نفر آنلاین 🟢"
                                detail_str = "شما + ۱ دوست از اینترنت"
                            else:
                                client_title = f"{client_count} نفر آنلاین 🟢"
                                detail_str = f"شما + {external_count} دوست از اینترنت"
                        elif external_count > 0:
                            client_title = f"{external_count} دوست متصل 🟢"
                            detail_str = f"آی‌پی: {external_ips[0]}" if len(external_ips) == 1 else "دوستان از اینترنت"
                        elif local_count > 0:
                            client_title = "۱ نفر آنلاین 🟢"
                            detail_str = "فقط خودتان (روی سرور)"
                        else:
                            client_title = "۰ نفر"
                            detail_str = "منتظر اتصال"

                        def _update_ui(c_title, det_str, sp_str, tot_str, r_str, u_str, is_online):
                            self.lbl_clients.config(text=c_title, fg=self.accent_green if is_online else self.text_color)
                            self.lbl_clients_detail.config(text=det_str, fg=self.accent_cyan if is_online else "#6c7094")
                            self.lbl_speed.config(text=sp_str)
                            self.lbl_total_data.config(text=tot_str)
                            self.lbl_ram.config(text=r_str)
                            self.lbl_uptime.config(text=u_str)

                        self.root.after(0, _update_ui, client_title, detail_str, format_speed(speed_bps), format_bytes(total_bytes), ram_str, uptime_str, client_count > 0)
                except Exception:
                    pass

                time.sleep(1)

        threading.Thread(target=_monitor, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = SyncplayManagerApp(root)
    root.mainloop()
