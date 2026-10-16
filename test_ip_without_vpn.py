import os
import sys
import time
import socket
import urllib.request
import ssl
import re

# 1. Clear any system/user proxy environment variables so python connects 100% direct
for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy']:
    os.environ.pop(var, None)

print("=" * 60)
print("  COMPREHENSIVE PUBLIC IP CHECKER (DIRECT NO-VPN TEST)  ")
print("=" * 60)
print("NOTE: Ghost proxy settings (127.0.0.1:7890) have been bypassed.\n")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Explicit empty ProxyHandler disables Windows registry ProxyServer & WinINet
direct_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

targets = [
    ("api.ip.sb (HTTP)", "http://api.ip.sb/ip"),
    ("icanhazip (HTTP)", "http://icanhazip.com"),
    ("get.geojs.io (HTTP)", "http://get.geojs.io/v1/ip"),
    ("get.geojs.io (HTTPS)", "https://get.geojs.io/v1/ip"),
    ("api.myip.la (HTTP)", "http://api.myip.la"),
    ("ident.me (HTTP)", "http://ident.me"),
    ("1.1.1.1 (HTTP trace)", "http://1.1.1.1/cdn-cgi/trace"),
    ("1.0.0.1 (HTTP trace)", "http://1.0.0.1/cdn-cgi/trace"),
    ("l2.io (HTTP)", "http://www.l2.io/ip"),
    ("1.1.1.1 (HTTPS trace)", "https://1.1.1.1/cdn-cgi/trace")
]

report = []
report.append("==================================================")
report.append("  PUBLIC IP DETECTION DIAGNOSTIC LOG (NO-VPN)     ")
report.append("==================================================")
report.append(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
report.append(f"Python Version: {sys.version.split()[0]}")
report.append("-" * 50)

successful_ips = []

for label, url in targets:
    sys.stdout.write(f"Testing {label:<24} ... ")
    sys.stdout.flush()
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with direct_opener.open(req, timeout=8) as r:
            raw = r.read().decode('utf-8', errors='ignore').strip()
            dt = time.time() - t0
            m = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', raw)
            if m:
                ip = m.group(0)
                if not ip.startswith("198.18.") and not ip.startswith("127."):
                    successful_ips.append(ip)
                    line = f"[SUCCESS] {dt:.2f}s -> IP: {ip}"
                    print(line)
                    report.append(f"{label:<24} : SUCCESS in {dt:.2f}s | IP: {ip}")
                else:
                    line = f"[TUN FAKE-IP] {dt:.2f}s -> {ip}"
                    print(line)
                    report.append(f"{label:<24} : FAKE-IP in {dt:.2f}s | IP: {ip}")
            else:
                line = f"[INVALID DATA] {dt:.2f}s -> {raw[:30]}"
                print(line)
                report.append(f"{label:<24} : INVALID in {dt:.2f}s | {raw[:30]}")
    except socket.timeout:
        dt = time.time() - t0
        print(f"[TIMEOUT] after {dt:.2f}s")
        report.append(f"{label:<24} : TIMEOUT after {dt:.2f}s")
    except Exception as e:
        dt = time.time() - t0
        err = str(e)
        print(f"[ERROR] {dt:.2f}s -> {err[:50]}")
        report.append(f"{label:<24} : ERROR in {dt:.2f}s | {err}")

report.append("-" * 50)
if successful_ips:
    report.append(f"Summary: Verified Public IP is: {successful_ips[0]} (passed {len(successful_ips)}/{len(targets)} tests)")
    print(f"\n>>> RESULT: Public IP detected: {successful_ips[0]}")
else:
    report.append("Summary: All endpoints failed.")
    print("\n>>> RESULT: All endpoints failed.")

full_text = "\n".join(report)

# Save log to Desktop
desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
log_path = os.path.join(desktop_dir, "ip_test_log.txt")
try:
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(full_text)
    print(f"\n[OK] Log file successfully saved to:\n     {log_path}")
except Exception as e:
    print(f"\n[WARN] Failed to write log to desktop: {e}")

# Copy to clipboard
try:
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    root.clipboard_clear()
    root.clipboard_append(full_text)
    root.update()
    root.destroy()
    print("[OK] Full report has been copied to your Windows Clipboard!")
except Exception:
    pass

print("\n" + "=" * 60)
print("Finished. Press Enter to exit...")
input()
