# 🎬 Syncplay Server Host Manager (Windows) `v1.0.8`

<p align="center">
  <img src="assets/icon.png" width="128" height="128" alt="Syncplay Server Host Manager Icon" />
</p>

<p align="center">
  <b>یک کنترل پنل سبک، مدرن، حرفه‌ای و متن‌باز برای مدیریت و میزبانی سرورهای خصوصی Syncplay روی ویندوز</b><br>
  <i>A lightweight, modern, and open-source desktop control panel for hosting private Syncplay servers on Windows with DDNS and System Tray support.</i>
</p>

<p align="center">
  <a href="https://t.me/vpnclashfa"><img src="https://img.shields.io/badge/Telegram-Channel-229ED9?style=flat&logo=telegram&logoColor=white" alt="Telegram Channel" /></a>
  <img src="https://img.shields.io/badge/Version-1.0.8-blue.svg" alt="Version 1.0.8" />
  <img src="https://img.shields.io/badge/Python-3.8+-brightgreen.svg" alt="Python 3.8+" />
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=flat&logo=windows&logoColor=white" alt="Windows" />
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT" /></a>
</p>

---

## ✨ امکانات و قابلیت‌ها (Key Features)

- **⚡ فوق‌العاده سبک و بهینه (Ultra-Lightweight):** مصرف حافظه رم کمتر از ۳۰ مگابایت؛ ساخته شده با پایتون و Tkinter بومی بدون نیاز به مرورگرهای سنگین یا الکترون.
- **📥 اجرای پس‌زمینه در سیستم‌تری (Minimize to System Tray):** امکان بستن پنجره و هدایت برنامه به کنار ساعت ویندوز جهت ادامه فعالیت پایدار سرور بدون مزاحمت، دارای منوی راست‌کلیک فارسی با دسترسی سریع به وضعیت، کپی مشخصات تلگرامی، روشن/خاموش کردن سرور و خروج کامل.
- **▶️ روشن و خاموش کردن تک‌کلیکی سرور (One-Click Server Control):** اجرای ایزوله و مطمئن پردازه `syncplayServer.exe` بدون پنجره‌های مزاحم CMD.
- **🌐 پشتیبانی کامل از دامنه ثابت و داینامیک (DDNS & DuckDNS Integration):** اتصال خودکار سرور به دامنه‌های رایگان DuckDNS یا هر دامنه دلخواه اینترنتی، تا نیازی به ارسال مکرر آی‌پی‌های متغیر مودم به دوستان نباشد؛ به همراه به‌روزرسانی خودکار آی‌پی در پس‌زمینه هنگام روشن شدن سرور.
- **🛡️ استعلام آنی آی‌پی عمومی بدون نیاز به فیلترشکن (Zero-VPN Public IP Detection):** شناسایی بلادرنگ آی‌پی اینترنت از طریق سرورهای پایدار و پرسرعت (حتی در زمان قطعی کامل فیلترشکن یا مسدود بودن اینترنت بین‌الملل) با دور زدن خودکار پروکسی‌های مرده ویندوز.
- **📁 شناسایی خودکار و انعطاف‌پذیر مسیر سینک‌پلی (Flexible Path Detection):** جستجوی خودکار در تمامی مسیرهای استاندارد ویندوز (`Program Files`، `Program Files (x86)`، پوشه محلی `AppData`، و پوشه کنار برنامه) با قابلیت انتخاب دستی.
- **🔍 تست چندلایه‌ای پورت و عیب‌یابی هوشمند (Multi-Layer Port Testing):** تست باز بودن پورت مودم از اینترنت با پشتیبانی از سرورهای بین‌المللی و فال‌بک خودکار به عیب‌یابی سلامت سوکت و فایروال محلی در صورت اختلال شبکه خارجی.
- **📊 آمار کاملاً تفکیک‌شده و اختصاصی سرور (Isolated Process Metrics):** اندازه‌گیری دقیق و لحظه‌ای سرعت آپلود/دانلود و حجم ترافیک تبادل‌شده تنها برای خود پردازه سرور سینک‌پلی.
- **👥 نمایش زنده تفکیک کاربران آنلاین (Connected Clients Breakdown):** تشخیص بلادرنگ تعداد نفرات حاضر در اتاق و تفکیک کاربر محلی و دوستان متصل از اینترنت.
- **🔔 اعلان صوتی هوشمند (Audio Chime Alerts):** پخش صدای اعلان ملایم ویندوز به محض ورود یا خروج دوستان به اتاق (با امکان فعال/غیرفعال‌سازی).
- **📋 کپی آسان و یک‌کلیکی گزارش‌ها (Log Clipboard Copy):** دکمه اختصاصی برای کپی کردن کل لاگ رویدادها در کلیپ‌بورد ویندوز جهت اشتراک‌گذاری یا بررسی سریع.
- **📱 قالب هوشمند اشتراک‌گذاری در تلگرام (Telegram One-Tap Copy):** دکمه کپی اختصاصی با فرمت کدهای مارک‌داون تلگرام (بدون اضافه شدن مزاحم https://) بر پایه دامنه یا آی‌پی، تا دوست شما تنها با یک بار لمس مشخصات، آن را کپی کند.
- **🛡️ بررسی واقعی و ثبت خودکار فایروال (Automated Windows Firewall):** بررسی بلادرنگ باز بودن پورت در فایروال ویندوز به همراه دکمه ثبت پورت با دسترسی Administrator.
- **📖 راهنمای داخلی تشخیص CGNAT و تنظیم انواع مودم‌ها:** آموزش جامع بررسی نات اپراتورها و نحوه پورت فورواردینگ در انواع برندهای مودم (U.Tel, TP-Link, D-Link, Huawei, Tenda, Zyxel).
- **📢 لینک اختصاصی به کانال تلگرام:** دسترسی سریع به کانال حامی پروژه ([@vpnclashfa](https://t.me/vpnclashfa)).

---

## 📥 دانلود فایل اجرایی آماده (بدون نیاز به نصب پایتون)

اگر نمی‌خواهید درگیر نصب پایتون و پیش‌نیازها شوید، نسخه کامپایل‌شده و تک‌فایلی برنامه را مستقیماً دانلود و اجرا کنید:

👉 **[دانلود آخرین نسخه SyncplayServerHostManager.exe از بخش Releases گیت‌هاب](https://github.com/10ium/Syncplay-Server-Host-Manager/releases)**

---

## 🚀 راهنمای اجرای سورس‌کد با پایتون (Manual Setup)

اگر مایلید مستقیماً از سورس‌کد پایتون استفاده کنید:
1. پایتون نسخه ۳.۸ یا بالاتر نصب باشد ([Python.org](https://www.python.org/downloads/)).
2. برنامه رسمی **Syncplay** روی سیستم نصب باشد ([Syncplay.pl](https://syncplay.pl/)).
3. نصب پیش‌نیازها:
```bash
pip install -r requirements.txt
```

### اجرا:
کافیست فایل `Run_Manager.bat` یا `server_manager.py` را باز کنید:
```bash
python server_manager.py
```

---

## 🌐 آموزش فوروارد پورت و تشخیص CGNAT

برای اینکه دوستانتان از طریق اینترنت به سرور متصل شوند:
1. پورت پیش‌فرض سینک‌پلی (`8999 TCP`) یا پورت دلخواه خود را در مودم به سمت آی‌پی داخلی سیستم (Local IP) فوروارد (Virtual Server) کنید.
2. مطمئن شوید خط شما پشت CGNAT (آی‌پی‌های شروع شونده با `100.64.x.x`) نیست.
3. در برنامه از دکمه **«📖 راهنمای مودم و CGNAT»** برای مشاهده دستورالعمل دقیق تنظیم انواع مودم‌ها استفاده کنید.

---

## ⚙️ ساختار فایل‌های پروژه (Repository Structure)

- `server_manager.py`: سورس‌کد اصلی برنامه گرافیکی (نسخه v1.0.6).
- `assets/`: حاوی آیکون‌های برنامه (`icon.png` و `icon.ico`).
- `config.example.json`: فایل نمونه تنظیمات برای عموم کاربران (پورت پیش‌فرض ۸۹۹۹).
- `config.json`: فایل تنظیمات شخصی شما (در فایل `.gitignore` نادیده گرفته شده تا رمز عبور و آی‌پی شما محفوظ بماند).
- `add_firewall.bat`: اسکریپت باز کردن پورت در فایروال ویندوز.
- `remove_firewall.bat`: اسکریپت حذف پورت از فایروال ویندوز.
- `.gitignore`: لیست فایل‌های محافظت‌شده شخصی و فایل‌های کش پایتون.
- `README.md`: مستندات جامع پروژه به زبان فارسی و انگلیسی.
- `LICENSE`: مجوز متن‌باز MIT.

---

## 📢 ارتباط و کانال تلگرام (Community)

برای دریافت آموزش‌ها، راهنماها و به‌روزرسانی‌ها به کانال تلگرام ما بپیوندید:  
👉 **[کانال تلگرام @vpnclashfa](https://t.me/vpnclashfa)**

---

## 📜 مجوز (License)

این پروژه تحت مجوز آزاد [MIT License](LICENSE) منتشر شده است و استفاده و توسعه آن برای همگان رایگان و بلامانع است.
