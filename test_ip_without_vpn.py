import os
import sys
import time
import socket
import urllib.request
import ssl
import re
from collections import Counter

# 1. Clear ghost proxy environment variables so python connects 100% direct
for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy']:
    os.environ.pop(var, None)

print("=" * 65)
print("   PUBLIC IP DETECTION DIAGNOSTIC TEST (DIRECT / NO-VPN)   ")
print("=" * 65)
print("NOTE: Dead proxies and registry ProxyServer bypassed successfully.\n")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Explicit empty ProxyHandler disables Windows registry ProxyServer & WinINet
direct_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

targets = [
    ("api.ip.sb (HTTP direct)", "http://api.ip.sb/ip"),
    ("icanhazip (HTTP direct)", "http://icanhazip.com"),
    ("ident.me (HTTP direct)", "http://ident.me"),
    ("l2.io (HTTP direct)", "http://www.l2.io/ip"),
    ("api.myip.la (HTTP direct)", "http://api.myip.la"),
    ("1.1.1.1 (HTTP trace)", "http://1.1.1.1/cdn-cgi/trace"),
    ("1.1.1.1 (HTTPS trace)", "https://1.1.1.1/cdn-cgi/trace"),
    ("api.ip.sb (HTTPS)", "https://api.ip.sb/ip"),
    ("icanhazip (HTTPS)", "https://icanhazip.com"),
    ("get.geojs.io (HTTP)", "http://get.geojs.io/v1/ip"),
    ("get.geojs.io (HTTPS)", "https://get.geojs.io/v1/ip")
]

report = []
report.append("==================================================")
report.append("  PUBLIC IP DETECTION DIAGNOSTIC LOG (NO-VPN)     ")
report.append("==================================================")
report.append(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
report.append(f"Python Version: {sys.version.split()[0]}")
report.append("-" * 50)

successful_ips = []
results_per_target = []

for label, url in targets:
    sys.stdout.write(f"Testing {label:<26} ... ")
    sys.stdout.flush()
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with direct_opener.open(req, timeout=6) as r:
            raw = r.read().decode('utf-8', errors='ignore').strip()
            dt = time.time() - t0
            
            # Accurate regex parsing: trace endpoint vs plain text
            if 'trace' in url:
                m = re.search(r'ip=([0-9\.]+)', raw)
                candidate_ip = m.group(1) if m else None
            else:
                m = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', raw)
                candidate_ip = m.group(0) if m else None

            if candidate_ip:
                # Filter out DNS resolvers and private/fake-IP ranges
                if candidate_ip in ("1.1.1.1", "1.0.0.1") or candidate_ip.startswith(("198.18.", "127.", "169.254.", "192.168.", "10.")):
                    line = f"[FILTERED / FAKE-IP] {dt:.2f}s -> {candidate_ip}"
                    print(line)
                    report.append(f"{label:<26} : FILTERED in {dt:.2f}s | {candidate_ip}")
                else:
                    successful_ips.append(candidate_ip)
                    results_per_target.append((label, dt, candidate_ip))
                    line = f"[SUCCESS] {dt:.2f}s -> IP: {candidate_ip}"
                    print(line)
                    report.append(f"{label:<26} : SUCCESS in {dt:.2f}s | IP: {candidate_ip}")
            else:
                line = f"[INVALID DATA] {dt:.2f}s -> {raw[:30]}"
                print(line)
                report.append(f"{label:<26} : INVALID in {dt:.2f}s | {raw[:30]}")
    except socket.timeout:
        dt = time.time() - t0
        print(f"[TIMEOUT] after {dt:.2f}s")
        report.append(f"{label:<26} : TIMEOUT after {dt:.2f}s")
    except Exception as e:
        dt = time.time() - t0
        err = str(e)
        print(f"[ERROR] {dt:.2f}s -> {err[:50]}")
        report.append(f"{label:<26} : ERROR in {dt:.2f}s | {err}")

report.append("-" * 50)
if successful_ips:
    # Consensus detection
    counts = Counter(successful_ips)
    consensus_ip, consensus_count = counts.most_common(1)[0]
    report.append(f"Summary: Verified Public IP is: {consensus_ip} (consensus: {consensus_count}/{len(successful_ips)} votes)")
    print(f"\n>>> RESULT: Verified Public IP: {consensus_ip} ({consensus_count}/{len(successful_ips)} endpoints agreed)")
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
    print(f"\n[OK] Diagnostic log file saved to:\n     {log_path}")
except Exception as e:
    print(f"[WARN] Could not save to Desktop: {e}")

print("\nPress Enter to exit...")
input()
