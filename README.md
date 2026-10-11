# WhatsApp Bulk Messenger

A desktop application for sending personalized WhatsApp messages in bulk via WhatsApp Web. Built with Python, Tkinter, and Playwright.

---

## 🎯 Features

- **Bulk Messaging** — Send personalized messages to multiple contacts at once
- **Personalization** — Use `{name}` placeholder for custom greetings
- **Persistent Session** — Scan QR code once; session saved locally
- **Anti-Ban Delays** — Randomized human-like delays (8–14s) between messages
- **WhatsApp-Inspired UI** — Clean, familiar interface with live statistics
- **Cross-Platform** — Works on Windows (tested on Windows 11)
- **No Cloud Dependencies** — Runs entirely on your machine; no data leaves your computer

---

## 📋 Requirements

- **Python 3.10+**
- **Windows 10/11** (primary target)
- **Internet connection**
- **WhatsApp account** on your phone

### Python Dependencies

```bash
pip install playwright pandas openpyxl
playwright install chromium
```

---

## 🚀 Quick Start

### Option 1: Run from Source (Recommended)

```bash
# Clone the repo
git clone https://github.com/agrwl-utkarsh/wbm.git
cd wbm

# Install dependencies
pip install playwright pandas openpyxl
playwright install chromium

# Run
python whatsapp_automation.py
```

### Option 2: Portable Executable

Download `WhatsAppBulkMessenger-Portable.zip` from Releases, extract, and run `WhatsAppBulkMessenger.exe`.

---

## 📁 Contact File Format

Prepare a **CSV** or **Excel (.xlsx)** file with these columns:

| Name | Phone |
|------|-------|
| John Doe | 9876543210 |
| Jane Smith | 9123456789 |

**Phone number formats accepted:**
- 10 digits → auto-prefixed with `91` (India): `9876543210` → `919876543210`
- 12 digits starting with `91`: `919876543210` (kept as-is)
- Other formats preserved as entered

A sample file `sample_contacts.csv` is included.

---

## 💬 Message Template

Write your message using the `{name}` placeholder for personalization:

```
Hello {name},

Thanks for your interest in our product!

Regards,
Team ABC
```

Each contact receives the message with their name substituted.

---

## 🖥️ Usage

1. **Launch** the application
2. **Select** your contact file (CSV/Excel)
3. **Write** your message template with `{name}`
4. **Click** "Start Campaign"
5. **Scan** the QR code with your WhatsApp mobile app (first run only)
6. **Wait** — messages send automatically with progress tracking
7. **Review** results in the Activity Log and Live Statistics

### Controls

| Button | Action |
|--------|--------|
| **Start Campaign** | Begin sending messages |
| **Stop** | Gracefully stop after current message |
| **Progress Bar** | Shows completion percentage |
| **Live Stats** | Real-time Sent / Failed / Total counters |

---

## 🔒 Privacy & Security

- **No data collection** — Everything runs locally
- **Session stored locally** — `wa_saved_session/` folder in app directory
- **No cloud sync** — Contacts and messages never leave your machine
- **Playwright automation** — Uses official WhatsApp Web interface

---

## ⚙️ Configuration

The app creates a `wa_saved_session/` folder next to the script/exe for persistent login. To reset:

```bash
# Delete the session folder
rm -rf wa_saved_session
# Or on Windows:
rmdir /s wa_saved_session
```

Next run will prompt for QR scan again.

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "WhatsApp Web not loaded" | Scan QR within 2 minutes; check internet |
| Messages fail to send | Verify phone format; ensure contact exists on WhatsApp |
| Blurry UI on Windows | App sets DPI awareness automatically |
| "No module named numpy/dateutil" | Run `pip install numpy python-dateutil` |
| App won't start | Run as Administrator; disable antivirus temporarily |

---

## 🏗️ Architecture

```
whatsapp_automation.py    # Main application (single file)
├── WhatsAppAutomationApp  # Tkinter GUI + logic
├── _build_ui()            # WhatsApp-inspired interface
├── _run_automation()      # Playwright browser automation
├── _create_card()         # Reusable card widget
├── _create_button()       # Themed button factory
└── Session management     # Persistent login via Playwright
```

**Tech Stack:**
- **GUI:** Tkinter (stdlib) + ttk theming
- **Automation:** Playwright (Chromium)
- **Data:** pandas + openpyxl (CSV/Excel parsing)
- **Packaging:** PyInstaller (optional)

---

## 📦 Building Executable

```bash
pip install pyinstaller
pyinstaller --clean --noconfirm --windowed \
  --name WhatsAppBulkMessenger \
  --add-data "C:\Users\<user>\AppData\Local\ms-playwright;ms-playwright" \
  --hidden-import=playwright.sync_api \
  --hidden-import=pandas \
  --hidden-import=openpyxl \
  --hidden-import=numpy \
  whatsapp_automation.py
```

Output: `dist/WhatsAppBulkMessenger.exe`

---

## 📄 License

MIT License — free for personal and commercial use.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Open a Pull Request

---

## 📞 Support

For issues, open a GitHub Issue or check existing discussions.

---

**Built with ❤️ using Python, Tkinter & Playwright**