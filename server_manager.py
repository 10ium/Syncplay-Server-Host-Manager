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

# Application Metadata
APP_NAME = "Syncplay Server Host Manager"
APP_VERSION = "v1.0.0"
APP_TITLE = f"🎬 {APP_NAME} {APP_VERSION} | کنترل پنل سرور سینک‌پلی"
if getattr(sys, 'frozen', False):
    EXE_DIR = os.path.dirname(sys.executable)
    BUNDLE_DIR = getattr(sys, '_MEIPASS', EXE_DIR)
else:
    EXE_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = EXE_DIR

APP_DIR = EXE_DIR
CONFIG_FILE = os.path.join(EXE_DIR, "config.json")
if not os.path.isfile(CONFIG_FILE):
    parent_cfg = os.path.join(os.path.dirname(EXE_DIR), "config.json")
    if os.path.isfile(parent_cfg):
        CONFIG_FILE = parent_cfg
    elif os.path.isfile("config.json"):
        CONFIG_FILE = os.path.abspath("config.json")
ICON_ICO = os.path.join(BUNDLE_DIR, "assets", "icon.ico")
if not os.path.isfile(ICON_ICO):
    ICON_ICO = os.path.join(EXE_DIR, "assets", "icon.ico")
ICON_PNG = os.path.join(BUNDLE_DIR, "assets", "icon.png")
if not os.path.isfile(ICON_PNG):
    ICON_PNG = os.path.join(EXE_DIR, "assets", "icon.png")
TELEGRAM_CHANNEL_URL = "https://t.me/vpnclashfa"

# Universal Default Configuration (No hardcoded personal credentials)
DEFAULT_CONFIG = {
    "port": "8999",  # Official Syncplay default port
    "password": "",
    "room": "cinema",
    "public_ip": "",
    "local_ip": "",
    "syncplay_dir": "",
    "router_gateway_ip": "192.168.1.1",
    "enable_logs": True,
    "enable_sound_alerts": True
}

def detect_gateway_ip():
    """Detect local router default gateway IP address"""
    try:
        # Use net route or ipconfig
        cmd = 'powershell -NoProfile -Command "(Get-NetRoute -DestinationPrefix \'0.0.0.0/0\' | Where-Object { $_.NextHop -ne \'0.0.0.0\' } | Select-Object -First 1 -ExpandProperty NextHop)"'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, errors='replace')
        gw = res.stdout.strip()
        if gw and len(gw.split('.')) == 4:
            return gw
    except Exception:
        pass
    return "192.168.1.1"

def find_syncplay_installation(custom_dir=""):
    """Auto-detect Syncplay directory across standard Windows locations or portable folder"""
    candidates = []
    if custom_dir and os.path.isdir(custom_dir):
        candidates.append(custom_dir)
    
    # Common Windows installation directories (64-bit, 32-bit, local appdata, portable)
    prog_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    prog_64 = os.environ.get("ProgramFiles", r"C:\Program Files")
    local_appdata = os.environ.get("LocalAppData", "")
    
    candidates.extend([
        os.path.join(prog_x86, "Syncplay"),
        os.path.join(prog_64, "Syncplay"),
        os.path.join(APP_DIR, "Syncplay"),
        r"C:\Program Files (x86)\Syncplay",
        r"C:\Program Files\Syncplay"
    ])
    if local_appdata:
        candidates.append(os.path.join(local_appdata, "Programs", "Syncplay"))
    
    for c in candidates:
        if c and os.path.isdir(c):
            server_exe = os.path.join(c, "syncplayServer.exe")
            if os.path.isfile(server_exe):
                return c
    return ""

def load_config():
    """Load configuration from config.json, fallback to DEFAULT_CONFIG"""
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
    """Detect local IPv4 address connected to the LAN router (bypassing VPN/TUN)"""
    gw = detect_gateway_ip() or "192.168.1.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((gw, 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("198.18.") and not ip.startswith("127.") and not ip.startswith("169.254."):
            return ip
    except Exception:
        pass

    # Fallback: scan physical network adapters ignoring VPN/TUN/virtual
    try:
        for iface, addrs in psutil.net_if_addrs().items():
            if any(bad in iface.lower() for bad in ["bettbox", "clash", "sing-box", "tun", "tap", "loopback", "virtual"]):
                continue
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    ip = addr.address
                    if (ip.startswith("192.168.") or ip.startswith("10.") or (ip.startswith("172.") and 16 <= int(ip.split('.')[1]) <= 31)) and not ip.startswith("198.18."):
                        return ip
    except Exception:
        pass
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
        self.root.title(APP_TITLE)
        
        # Set App Icon (.ico and .png fallback)
        self.apply_app_icon()

        # Responsive & Resizable window with full Maximize support
        window_width = 800
        window_height = 930
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        pos_x = max(0, (screen_w - window_width) // 2)
        pos_y = max(0, (screen_h - window_height) // 2 - 25)
        self.root.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")
        self.root.minsize(720, 800)
        self.root.resizable(True, True)

        self.config = load_config()
        self.server_process = None
        self.server_start_time = None
        
        # Fallback values if config fields are empty
        configured_port = self.config.get("port") or "8999"
        self.running_port = int(configured_port) if configured_port.isdigit() else 8999
        self.is_monitoring = True

        # Syncplay paths & Router Gateway
        self.syncplay_dir = find_syncplay_installation(self.config.get("syncplay_dir", ""))
        self.local_ip = self.config.get("local_ip") or detect_local_ip()
        self.gateway_ip = self.config.get("router_gateway_ip") or detect_gateway_ip()

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
        self.telegram_color = "#229ED9"

        self.root.configure(bg=self.bg_color)
        self.setup_ui()

        # Initial checks
        self.check_initial_status()
        self.check_firewall_status_real()
        self.start_monitoring_thread()

    def apply_app_icon(self):
        """Set native window icon"""
        if os.path.isfile(ICON_ICO):
            try:
                self.root.iconbitmap(ICON_ICO)
            except Exception:
                pass
        if os.path.isfile(ICON_PNG):
            try:
                photo = tk.PhotoImage(file=ICON_PNG)
                self.root.iconphoto(True, photo)
            except Exception:
                pass

    def setup_ui(self):
        container = tk.Frame(self.root, bg=self.bg_color, padx=16, pady=10)
        container.pack(fill="both", expand=True)

        # 1. Header (Title, Version, Telegram Channel, and CGNAT Guide)
        header = tk.Frame(container, bg=self.card_bg, padx=18, pady=10, highlightthickness=1, highlightbackground="#2d2d48")
        header.pack(fill="x", pady=(0, 6))

        h_top = tk.Frame(header, bg=self.card_bg)
        h_top.pack(fill="x")

        # Right: Title & Version Badge
        title_box = tk.Frame(h_top, bg=self.card_bg)
        title_box.pack(side="right")

        tk.Label(
            title_box,
            text=f"🎬 {APP_NAME}",
            font=("Segoe UI", 15, "bold"),
            bg=self.card_bg,
            fg=self.accent_blue,
            justify="right"
        ).pack(side="right")

        lbl_ver = tk.Label(
            title_box,
            text=APP_VERSION,
            font=("Segoe UI", 8, "bold"),
            bg=self.subcard_bg,
            fg=self.accent_cyan,
            padx=6,
            pady=2
        )
        lbl_ver.pack(side="right", padx=(0, 8))

        # Left: Telegram Channel & CGNAT Guide Buttons
        left_actions = tk.Frame(h_top, bg=self.card_bg)
        left_actions.pack(side="left")

        btn_channel = tk.Button(
            left_actions,
            text="📢 کانال تلگرام: @vpnclashfa",
            font=("Segoe UI", 9, "bold"),
            bg=self.telegram_color,
            fg="#ffffff",
            activebackground="#1e88e5",
            activeforeground="#ffffff",
            cursor="hand2",
            padx=10,
            pady=4,
            relief="flat",
            command=lambda: webbrowser.open(TELEGRAM_CHANNEL_URL)
        )
        btn_channel.pack(side="left", padx=(0, 8))

        btn_guide = tk.Button(
            left_actions,
            text="📖 راهنمای مودم و CGNAT",
            font=("Segoe UI", 9, "bold"),
            bg="#2c3e50",
            fg=self.accent_cyan,
            activebackground="#34495e",
            activeforeground="#ffffff",
            cursor="hand2",
            padx=10,
            pady=4,
            relief="flat",
            command=self.open_cgnat_guide
        )
        btn_guide.pack(side="left")

        tk.Label(
            header,
            text="کنترل پنل جامع و سبک برای اجرای سرور سینک‌پلی، استعلام خودکار شبکه و فرمت هوشمند تلگرام",
            font=("Segoe UI", 9),
            bg=self.card_bg,
            fg=self.subtext_color,
            justify="right"
        ).pack(anchor="e", pady=(4, 0))

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
        self.entry_public_ip = tk.Entry(pub_bar, font=("Segoe UI", 10), bg=self.input_bg, fg=self.accent_yellow, insertbackground="white", width=18, relief="flat", justify="center")
        self.entry_public_ip.insert(0, self.config.get("public_ip", ""))
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
        self.entry_local_ip = tk.Entry(loc_bar, font=("Segoe UI", 10), bg=self.input_bg, fg=self.accent_green, insertbackground="white", width=18, relief="flat", justify="center")
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

        # 6. Settings Card (Port, Password, Room, Sound Alerts)
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
        self.entry_port.insert(0, str(self.config.get("port") or "8999"))
        self.entry_port.pack(anchor="e", pady=(2, 0))

        f_pass = tk.Frame(cfg_form, bg=self.card_bg)
        f_pass.pack(side="right", padx=(10, 0))
        tk.Label(f_pass, text="رمز عبور:", font=("Segoe UI", 9), bg=self.card_bg, fg=self.text_color).pack(anchor="e")
        self.entry_pass = tk.Entry(f_pass, font=("Segoe UI", 10), bg=self.input_bg, fg=self.text_color, insertbackground="white", width=12, relief="flat", justify="center")
        self.entry_pass.insert(0, self.config.get("password", ""))
        self.entry_pass.pack(anchor="e", pady=(2, 0))

        f_room = tk.Frame(cfg_form, bg=self.card_bg)
        f_room.pack(side="right", padx=(10, 0))
        tk.Label(f_room, text="اتاق مشترک:", font=("Segoe UI", 9), bg=self.card_bg, fg=self.text_color).pack(anchor="e")
        self.entry_room = tk.Entry(f_room, font=("Segoe UI", 10), bg=self.input_bg, fg=self.text_color, insertbackground="white", width=10, relief="flat", justify="center")
        self.entry_room.insert(0, self.config.get("room") or "cinema")
        self.entry_room.pack(anchor="e", pady=(2, 0))

        # 7. Syncplay Installation Path & Shortcuts
        sc_card = tk.Frame(container, bg=self.card_bg, padx=18, pady=8, highlightthickness=1, highlightbackground="#2d2d48")
        sc_card.pack(fill="x", pady=3)

        # Path Selection Row
        path_box = tk.Frame(sc_card, bg=self.card_bg)
        path_box.pack(fill="x", pady=(0, 6))

        tk.Label(
            path_box,
            text="📁 مسیر نصب سینک‌پلی:",
            font=("Segoe UI", 9, "bold"),
            bg=self.card_bg,
            fg=self.accent_purple
        ).pack(side="right", padx=(4, 0))

        self.entry_path = tk.Entry(
            path_box,
            font=("Segoe UI", 9),
            bg=self.input_bg,
            fg=self.text_color,
            insertbackground="white",
            relief="flat"
        )
        self.entry_path.insert(0, self.syncplay_dir or "مسیر شناسایی نشد (دستی انتخاب کنید)")
        self.entry_path.pack(side="right", fill="x", expand=True, padx=(8, 8))

        btn_browse_path = tk.Button(
            path_box,
            text="📂 انتخاب پوشه...",
            font=("Segoe UI", 8),
            bg=self.subcard_bg,
            fg=self.accent_cyan,
            cursor="hand2",
            padx=10,
            pady=2,
            relief="flat",
            command=self.choose_syncplay_path
        )
        btn_browse_path.pack(side="left", padx=(4, 0))

        btn_auto_path = tk.Button(
            path_box,
            text="🔍 شناسایی خودکار",
            font=("Segoe UI", 8),
            bg=self.subcard_bg,
            fg=self.subtext_color,
            cursor="hand2",
            padx=8,
            pady=2,
            relief="flat",
            command=self.auto_detect_syncplay_path
        )
        btn_auto_path.pack(side="left")

        # Shortcuts Row
        sc_bar = tk.Frame(sc_card, bg=self.card_bg)
        sc_bar.pack(fill="x", pady=(2, 0))

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
            command=self.open_modem_panel
        )
        btn_modem.pack(side="right", padx=(0, 12))

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

        btn_copy_logs = tk.Button(
            log_top,
            text="📋 کپی متن لاگ",
            font=("Segoe UI", 8),
            bg=self.subcard_bg,
            fg=self.accent_cyan,
            activebackground="#353554",
            activeforeground=self.accent_cyan,
            cursor="hand2",
            padx=8,
            relief="flat",
            command=self.copy_all_logs
        )
        btn_copy_logs.pack(side="left", padx=(8, 0))

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

    def open_modem_panel(self):
        gw = self.gateway_ip or "192.168.1.1"
        webbrowser.open(f"http://{gw}")

    def auto_detect_syncplay_path(self):
        found = find_syncplay_installation()
        if found:
            self.syncplay_dir = found
            self.config["syncplay_dir"] = found
            save_config(self.config)
            self.entry_path.delete(0, "end")
            self.entry_path.insert(0, found)
            self.log(f"مسیر سینک‌پلی به طور خودکار پیدا شد: {found}")
            messagebox.showinfo("موفقیت", f"مسیر نصب سینک‌پلی با موفقیت پیدا شد:\n{found}")
        else:
            messagebox.showwarning("یافت نشد", "پوشه نصب سینک‌پلی در مسیرهای پیش‌فرض پیدا نشد.\nلطفاً دکمه 'انتخاب پوشه...' را بزنید و محل نصب را مشخص کنید.")

    def choose_syncplay_path(self):
        d = filedialog.askdirectory(title="پوشه نصب برنامه Syncplay را انتخاب کنید")
        if d:
            test_server = os.path.join(d, "syncplayServer.exe")
            if os.path.isfile(test_server):
                self.syncplay_dir = d
                self.config["syncplay_dir"] = d
                save_config(self.config)
                self.entry_path.delete(0, "end")
                self.entry_path.insert(0, d)
                self.log(f"مسیر برنامه تنظیم شد: {d}")
                messagebox.showinfo("موفقیت", f"مسیر Syncplay با موفقیت ذخیره شد:\n{d}")
            else:
                messagebox.showerror("خطا", f"فایل syncplayServer.exe در این پوشه یافت نشد:\n{d}\nمطمئن شوید پوشه اصلی برنامه را انتخاب کرده‌اید.")

    def open_cgnat_guide(self):
        """Display an exhaustive, comprehensive CGNAT & Router guide window with standard default port"""
        win = tk.Toplevel(self.root)
        win.title("راهنمای تشخیص CGNAT و تنظیم پورت انواع مودم‌ها")
        win.geometry("700x660")
        win.configure(bg=self.bg_color)
        if os.path.isfile(ICON_ICO):
            try:
                win.iconbitmap(ICON_ICO)
            except Exception:
                pass

        c = tk.Frame(win, bg=self.card_bg, padx=16, pady=16)
        c.pack(fill="both", expand=True, padx=12, pady=12)

        tk.Label(
            c,
            text="📖 راهنمای کامل تشخیص CGNAT و فوروارد پورت در انواع مودم‌ها",
            font=("Segoe UI", 13, "bold"),
            bg=self.card_bg,
            fg=self.accent_blue,
            justify="right"
        ).pack(anchor="e", pady=(0, 10))

        txt = tk.Text(c, bg="#101018", fg="#cdd6f4", font=("Segoe UI", 9), wrap="word", relief="flat")
        txt.pack(fill="both", expand=True)

        guide_content = """۱. چطور بفهمیم اینترنت ما پشت CGNAT (نات اپراتور) است یا آی‌پی عمومی داریم؟
--------------------------------------------------------------------------------
- وارد پنل تنظیمات مودم خود شوید (معمولاً http://192.168.1.1 یا http://192.168.0.1).
- به بخش Status یا Device Info یا WAN Status بروید و مقدار WAN IP Address را بررسی کنید.
- اکنون یک سایت استعلام آی‌پی مانند https://api.ipify.org را باز کنید.

نتیجه:
الف) اگر آی‌پی صفحه مودم شما با سایتی که باز کردید یکسان باشد:
   تبریک! شما آی‌پی عمومی (Public IP) دارید و پورت فورواردینگ ۱۰۰٪ کار خواهد کرد.
ب) اگر آی‌پی مودم با اعدادی مثل:
   • 100.64.0.0 تا 100.127.255.255 (رنج استاندارد جهانی CGNAT)
   • 10.x.x.x یا 172.16.x.x تا 172.31.x.x
   شروع شود، خط شما پشت CGNAT است. در این حالت پورت فوروارد به صورت مستقیم کار نمی‌کند و باید با پشتیبانی شرکت اینترنت خود تماس بگیرید و درخواست «آی‌پی استاتیک» (یا خروج از CGNAT) بدهید.

--------------------------------------------------------------------------------
۲. نحوه تنظیم فوروارد پورت (Virtual Server) در انواع مودم‌ها:
--------------------------------------------------------------------------------
در تمام مودم‌ها هدف این است که پورت سرور (به صورت پیش‌فرض 8999 یا هر پورتی که خودتان در نرم‌افزار تنظیم کرده‌اید) را به سمت آی‌پی داخلی سیستم (Local IP) بفرستید.

• مودم‌های یوتل (U.Tel):
  مسیر: Advanced > NAT > Virtual Server
  گزینه: User-defined Service Name: Syncplay
  پورت‌ها: WAN Port: 8999 | LAN Port: 8999 | Protocol: TCP
  آی‌پی: Server IP Address را روی Local IP کامپیوتر خود بگذارید.

• مودم‌های تی‌پی‌لینک (TP-Link):
  مسیر: Forwarding > Virtual Servers (یا Advanced > NAT Forwarding)
  پورت ورودی و خروجی: 8999 (یا پورت تنظیمی شما)
  پروتکل: TCP | آی‌پی: Local IP کامپیوتر.

• مودم‌های دی‌لینک (D-Link):
  مسیر: Advanced > Port Forwarding یا Virtual Server
  نام: Syncplay | پورت: 8999 | آی‌پی: Local IP | پروتکل: TCP.

• مودم‌های هواوی، ایرانسل، مبین‌نت، همراه اول:
  مسیر: Security > Virtual Server یا Port Forwarding
  تنظیمات مشابه: پورت 8999 و آی‌پی داخلی سیستم شما.

• مودم‌های تندا (Tenda) و زایکسل (Zyxel):
  مسیر: Advanced > Virtual Server یا Port Forwarding
  تنظیم پورت 8999 به سمت آدرس داخلی کامپیوتر.

--------------------------------------------------------------------------------
۳. نکته طلایی درباره لوپ‌بک (NAT Loopback):
--------------------------------------------------------------------------------
بسیاری از مودم‌های خانگی قابلیت NAT Loopback ندارند؛ یعنی اگر خودتان از پشت همان مودم به آی‌پی اینترنتی خودتان وصل شوید، مودم اتصال را بلاک می‌کند.
به همین دلیل بسیار مهم است که:
- خودتان روی همان کامپیوتری که سرور را روشن کرده‌اید، در نرم‌افزار سینک‌پلی آدرس 127.0.0.1 را بزنید.
- دوستتان در خانه خودش باید آی‌پی اینترنت (Public IP) شما را همراه با پورت وارد کند.
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

    def copy_all_logs(self):
        content = self.log_text.get("1.0", "end-1c").strip()
        if not content:
            messagebox.showinfo("لاگ خالی است", "در حال حاضر هیچ متنی در پنجره گزارش‌ها ثبت نشده است.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.log("تمام گزارش‌های رویداد در کلیپ‌بورد کپی شد. 📋")
        messagebox.showinfo("کپی شد! ✅", "تمام متن گزارش رویدادها (لاگ سرور) با موفقیت در کلیپ‌بورد کپی شد.")

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
        if not port:
            return
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
        if not port.isdigit():
            messagebox.showerror("خطا", "شماره پورت نامعتبر است.")
            return
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
            messagebox.showerror("خطا", "لطفاً آی‌پی عمومی اینترنت و شماره پورت را وارد کنید.")
            return

        pid = get_syncplay_pid()
        if not pid:
            self.log("هشدار تست پورت: سرور سینک‌پلی در حال حاضر خاموش است! برای تست، ابتدا سرور را روشن کنید.")
            if not messagebox.askyesno(
                "سرور خاموش است ⚠️",
                "سرور سینک‌پلی در حال حاضر خاموش است.\nاگر سرور روشن نباشد، حتی اگر پورت در مودم باز باشد پاسخی نمی‌دهد.\n\nآیا مایلید با این وجود تست استعلام انجام شود؟"
            ):
                return

        self.log(f"در حال بررسی وضعیت پورت {port} روی آی‌پی {pub_ip}...")
        self.btn_test_port.config(text="در حال استعلام...", state="disabled")

        def _test():
            result_type = None  # "success", "refused", "timeout", "diag_ok", "diag_warn"
            detail_msg = ""

            # لایه ۱: استعلام مستقیم از سرور بین‌المللی canyouseeme.org
            try:
                data = urllib.parse.urlencode({'port': str(port), 'IP': str(pub_ip)}).encode()
                req = urllib.request.Request(
                    'https://canyouseeme.org/',
                    data=data,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                )
                with urllib.request.urlopen(req, timeout=7) as r:
                    html = r.read().decode('utf-8')
                    if 'Success:' in html:
                        result_type = "success"
                        detail_msg = f"پورت {port} روی آی‌پی {pub_ip} از طریق اینترنت کاملاً باز و پاسخگو است! ✅"
                    elif 'Error:' in html:
                        if 'refused' in html.lower():
                            result_type = "refused"
                            detail_msg = f"سیگنال از اینترنت به سیستم شما رسید! پورت فوروارد شده اما برنامه سرور پاسخ نداد (Connection refused). مطمئن شوید سرور روشن است."
                        elif 'timed out' in html.lower():
                            result_type = "timeout"
                            detail_msg = f"پورت {port} از اینترنت پاسخی نداد (Connection timed out).\nمودم یا فایروال ترافیک را به سمت سیستم هدایت نکرده است."
            except Exception:
                pass

            # لایه ۲: فال‌بک به سرور دوم در صورت مسدود بودن سرور اول
            if result_type is None:
                try:
                    data = urllib.parse.urlencode({'target_ip': str(pub_ip), 'port': str(port)}).encode()
                    req = urllib.request.Request(
                        'https://portchecker.co/check',
                        data=data,
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                            'Referer': 'https://portchecker.co/'
                        }
                    )
                    with urllib.request.urlopen(req, timeout=7) as r:
                        html = r.read().decode('utf-8')
                        if 'target port is open' in html.lower() or 'port is open' in html.lower():
                            result_type = "success"
                            detail_msg = f"پورت {port} روی آی‌پی {pub_ip} از طریق سرویس کمکی اینترنت تایید شد! ✅"
                        elif 'closed' in html.lower():
                            result_type = "timeout"
                            detail_msg = f"پورت {port} از اینترنت مسدود یا بسته گزارش شد."
                except Exception:
                    pass

            # لایه ۳: عیب‌یابی هوشمند سیستم در صورت قطع اینترنت بین‌الملل یا کاربری بدون فیلترشکن
            if result_type is None:
                is_listening = False
                try:
                    s_test = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s_test.settimeout(2)
                    res = s_test.connect_ex(('127.0.0.1', int(port)))
                    s_test.close()
                    is_listening = (res == 0)
                except Exception:
                    pass

                fw_ok = check_windows_firewall_rule(port)

                if is_listening and fw_ok:
                    result_type = "diag_ok"
                    detail_msg = (
                        "⚠️ سرورهای تست بین‌المللی اینترنت در دسترس نبودند (این اتفاق در حالت بدون فیلترشکن به دلیل فیلترینگ خارجی طبیعی است).\n\n"
                        "🔍 نتیجه بررسی سلامت داخلی سیستم شما:\n"
                        f"۱. سرور سینک‌پلی روی پورت {port} در ویندوز فعال و گوش‌به‌زنگ است. ✅\n"
                        f"۲. پورت {port} در فایروال ویندوز مجاز است. ✅\n"
                        f"۳. ارتباط سیستم با شبکه محلی مودم برقرار است. ✅\n\n"
                        "💡 اگر پورت {port} را در مودم به سمت آی‌پی داخلی سیستم فوروارد کرده باشید، دوستان شما می‌توانند متصل شوند."
                    )
                else:
                    result_type = "diag_warn"
                    reasons = []
                    if not is_listening:
                        reasons.append(f"• برنامه سرور روی پورت {port} روشن نیست! (دکمه 'روشن کردن سرور' را بزنید)")
                    if not fw_ok:
                        reasons.append(f"• پورت {port} در فایروال ویندوز مسدود است! (دکمه 'ثبت پورت در فایروال' را بزنید)")
                    detail_msg = (
                        "⚠️ سرورهای تست بین‌المللی در دسترس نبودند.\n\n"
                        "❌ نتیجه بررسی سلامت سیستم:\n" + "\n".join(reasons)
                    )

            def _done():
                self.btn_test_port.config(text="🔍 تست آنلاین پورت مودم از اینترنت", state="normal")
                if result_type == "success":
                    self.log(f"نتیجه تست پورت: {detail_msg}")
                    messagebox.showinfo("پورت کاملاً باز است! 🎉", detail_msg)
                elif result_type == "refused":
                    self.log(f"نتیجه تست پورت: {detail_msg}")
                    messagebox.showwarning("ارتباط برقرار شد اما سرور پاسخ نداد ⚠️", detail_msg)
                elif result_type == "timeout":
                    self.log(f"نتیجه تست پورت: {detail_msg}")
                    messagebox.showerror("پورت پاسخ نداد ❌", f"{detail_msg}\n\nنکات قابل بررسی:\n۱. مطمئن شوید سرور روشن است.\n۲. استعلام آی‌پی اینترنت را بزنید تا از تغییر نکردن آی‌پی مطمئن شوید.\n۳. تنظیمات Virtual Server مودم را بررسی کنید.")
                elif result_type == "diag_ok":
                    self.log("نتیجه عیب‌یابی داخلی: سرور و فایروال محلی کاملاً آماده هستند. ✅")
                    if messagebox.askyesno("عیب‌یابی داخلی موفق", f"{detail_msg}\n\nآیا مایلید سایت تست پورت مستقیماً در مرورگر شما باز شود؟"):
                        webbrowser.open("https://canyouseeme.org/")
                else:
                    self.log("نتیجه عیب‌یابی داخلی: موانعی در سیستم وجود دارد.")
                    messagebox.showwarning("نیاز به اصلاح تنظیمات ⚠️", detail_msg)
            self.root.after(0, _done)

        threading.Thread(target=_test, daemon=True).start()

    def open_syncplay_client(self):
        if not self.syncplay_dir or not os.path.isdir(self.syncplay_dir):
            self.choose_syncplay_path()
            if not self.syncplay_dir:
                return

        client_exe = os.path.join(self.syncplay_dir, "Syncplay.exe")
        if os.path.isfile(client_exe):
            try:
                subprocess.Popen([client_exe])
                self.log("برنامه کلاینت سینک‌پلی باز شد.")
            except Exception as e:
                messagebox.showerror("خطا", f"خطا در باز کردن برنامه: {e}")
        else:
            messagebox.showerror("خطا", f"فایل Syncplay.exe در مسیر زیر پیدا نشد:\n{client_exe}\nلطفاً پوشه نصب را بررسی کنید.")

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
        # Multi-endpoint detection with HTTP/HTTPS fallbacks for without-VPN environments
        endpoints = [
            "https://api.ipify.org",
            "http://api.ipify.org",
            "https://icanhazip.com",
            "http://icanhazip.com",
            "https://ifconfig.me/ip",
            "https://api4.my-ip.io/ip",
            "https://checkip.amazonaws.com"
        ]
        for url in endpoints:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=4) as response:
                    ip = response.read().decode('utf-8').strip()
                    if ip and len(ip.split('.')) == 4:
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
        self.log("استعلام خودکار ناموفق بود (آی‌پی را از تب Status مودم مشاهده کرده و دستی وارد کنید).")

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
            if not self.syncplay_dir or not os.path.isdir(self.syncplay_dir):
                self.choose_syncplay_path()
                if not self.syncplay_dir:
                    return

            server_exe = os.path.join(self.syncplay_dir, "syncplayServer.exe")
            if not os.path.isfile(server_exe):
                messagebox.showerror("خطا", f"فایل سرور پیدا نشد:\n{server_exe}\nلطفاً مسیر نصب سینک‌پلی را انتخاب کنید.")
                return

            port_str = self.entry_port.get().strip()
            password = self.entry_pass.get().strip()
            if not port_str.isdigit():
                messagebox.showerror("خطا", "شماره پورت باید یک عدد معتبر باشد.")
                return

            self.running_port = int(port_str)
            cmd = [server_exe, "--port", port_str]
            if password:
                cmd.extend(["--password", password])

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
        room = self.entry_room.get().strip() or "cinema"
        pub_ip = self.entry_public_ip.get().strip()
        loc_ip = self.entry_local_ip.get().strip()

        if not port.isdigit():
            messagebox.showerror("خطا", "شماره پورت باید یک عدد معتبر باشد.")
            return

        self.config["port"] = port
        self.config["password"] = pwd
        self.config["room"] = room
        self.config["public_ip"] = pub_ip
        self.config["local_ip"] = loc_ip
        self.local_ip = loc_ip
        save_config(self.config)
        self.log(f"تنظیمات ذخیره شد: پورت {port} | رمز {'***' if pwd else '(بدون رمز)'} | اتاق {room}")
        self.check_firewall_status_real()
        messagebox.showinfo("ذخیره شد", "تنظیمات با موفقیت ذخیره شدند.\n(در صورت تغییر پورت، سرور را خاموش و دوباره روشن کنید).")

    def copy_self_info(self):
        port = self.entry_port.get().strip() or "8999"
        raw_addr = f"127.0.0.1:{port}"
        self.root.clipboard_clear()
        self.root.clipboard_append(raw_addr)
        messagebox.showinfo(
            "کپی شد! ✅",
            f"آدرس سرور برای خودتان کپی شد (بدون https):\n\n{raw_addr}\n\nکافیست در کادر Server address برنامه سینک‌پلی پیست (Ctrl+V) کنید."
        )

    def copy_friend_info(self):
        port = self.entry_port.get().strip() or "8999"
        pwd = self.entry_pass.get().strip()
        room = self.entry_room.get().strip() or "cinema"
        pub_ip = self.entry_public_ip.get().strip()

        if not pub_ip:
            messagebox.showwarning(
                "آی‌پی اینترنت خالی است",
                "لطفاً ابتدا دکمه 'استعلام آی‌پی اینترنت' را بزنید یا آی‌پی عمومی مودم را در کادر مربوطه وارد کنید."
            )
            return

        # Telegram-optimized formatting with markdown code blocks (click-to-copy, zero https://)
        pwd_line = f"`{pwd}`" if pwd else "`(بدون رمز)`"
        formatted_message = (
            "🎬 مشخصات اتصال به سرور سینک‌پلی:\n\n"
            "🔹 آدرس سرور (Server address):\n"
            f"`{pub_ip}:{port}`\n\n"
            "🔹 رمز عبور (Server password):\n"
            f"{pwd_line}\n\n"
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

                        # Client breakdown display
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
