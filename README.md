# 🌸 Never Suite v1.0 — Community Edition

<div align="center">

[![Release](https://img.shields.io/badge/release-v1.0.0-blueviolet?style=for-the-badge&logo=github)](https://github.com/miras101208miras-cpu/NeverSuite/releases/tag/v1.0.0)
[![License: MIT](https://img.shields.io/badge/License-MIT-pink?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-blue?style=for-the-badge&logo=windows)](https://github.com/miras101208miras-cpu/NeverSuite)
[![Python](https://img.shields.io/badge/Python-3.10%2B-yellow?style=for-the-badge&logo=python)](https://www.python.org/)
[![GitHub Pages](https://img.shields.io/badge/Website-Live-brightgreen?style=for-the-badge&logo=github-pages)](https://miras101208miras-cpu.github.io/NeverSuite/)
[![Stars](https://img.shields.io/github/stars/miras101208miras-cpu/NeverSuite?style=for-the-badge&color=gold)](https://github.com/miras101208miras-cpu/NeverSuite/stargazers)

**A beautiful, modular Windows desktop enhancement suite — glassmorphic, animated, and built for power users.**

[🌐 Website](https://miras101208miras-cpu.github.io/NeverSuite/) · [📦 Download ZIP](https://github.com/miras101208miras-cpu/NeverSuite/releases/tag/v1.0.0) · [🐛 Report Bug](https://github.com/miras101208miras-cpu/NeverSuite/issues) · [💡 Request Feature](https://github.com/miras101208miras-cpu/NeverSuite/issues)

![Never Suite Banner](docs/assets/banner.png)

</div>

---

## 📋 Table of Contents

- [✨ Overview](#-overview)
- [🏗️ Architecture](#️-architecture)
- [🧩 Modules](#-modules)
  - [Never Hub](#1-never-hub)
  - [Dynamic Island](#2-dynamic-island)
  - [Cyber Pet](#3-cyber-pet)
  - [Never Drop](#4-never-drop)
  - [Never Sakura FX](#5-never-sakura-fx)
  - [Never Spotlight](#6-never-spotlight)
  - [Never Clipboard](#7-never-clipboard)
  - [Never Radial Menu](#8-never-radial-menu)
  - [Windows Customizer](#9-windows-customizer)
  - [PC Master Booster](#10-pc-master-booster)
- [⌨️ Hotkey Cheat Sheet](#️-hotkey-cheat-sheet)
- [🚀 Installation](#-installation)
- [⚙️ System Requirements](#️-system-requirements)
- [🎨 Themes](#-themes)
- [📄 License](#-license)

---

## ✨ Overview

**Never Suite** is a collection of 10 sleek, Python-powered Windows desktop tools with a unified glassmorphic aesthetic. Inspired by macOS Dynamic Island, anime desktop companions, and modern productivity apps — reimagined for Windows.

> *"Make your Windows desktop feel alive."*

---

## 🏗️ Architecture

```
Never Suite v1.0
│
├── Never Hub (System Tray Controller)
│   ├── Master on/off switches for all modules
│   ├── Real-time RAM usage monitor
│   └── Unified settings & theme management
│
├── UI Layer (Tkinter / CustomTkinter)
│   ├── Dynamic Island (top-center overlay)
│   ├── Cyber Pet (desktop companion)
│   ├── Never Sakura FX (particle canvas)
│   └── Never Radial Menu (pie launcher)
│
├── Productivity Layer
│   ├── Never Spotlight (launcher / calculator)
│   ├── Never Clipboard (history manager)
│   └── Focus Mode (Pomodoro timer — shared state)
│
├── Utility Layer
│   ├── Never Drop (Wi-Fi AirDrop via QR)
│   ├── Windows Customizer (wallpaper + theming)
│   └── PC Master Booster (RAM/disk optimizer)
│
└── Shared Infrastructure
    ├── never_focus.py (focus state manager)
    ├── never_theme.json (unified theme config)
    └── requirements.txt (dependencies)
```

---

## 🧩 Modules

### 1. Never Hub
> 🗂️ *The central control tower of Never Suite*

- **System tray icon** — always running, never in your way
- Master toggle switches for every module
- **Real-time RAM gauge** updated every 2 seconds
- One-click launch/stop any component
- Unified settings panel with theme picker

---

### 2. Dynamic Island
> 🎵 *macOS Dynamic Island — but make it Windows*

- Persistent top-center glassmorphic pill overlay
- **SMTC media player controls** (play/pause/next/prev, album art)
- Animated **sound wave visualizer**
- Quick toggles: Wi-Fi, Bluetooth, Do Not Disturb
- **Pomodoro Focus Mode** with countdown timer & progress bar
- Expands on hover, collapses elegantly when idle

| Feature | Detail |
|---------|--------|
| Media Controls | Windows SMTC (Spotify, YouTube, etc.) |
| Animation | Smooth expand/collapse transitions |
| Focus Timer | 25-min work / 5-min break cycles |
| Hotkey | `Alt + H` |

---

### 3. Cyber Pet
> 🐾 *Your animated anime desktop companion*

- Adorable pixel-art anime character that **walks across your screen**
- Multiple outfits: Pink Hoodie, School Uniform, Pink Dress
- Reacts to **Focus Mode** — shows study pose + motivational quotes
- **Drag-and-drop AirDrop**: drop a file on her → instantly shares via Never Drop
- Right-click menu: feed, change outfit, send to corner
- Balloon thought bubbles with random cute quotes

---

### 4. Never Drop
> 📡 *Instant Wi-Fi file sharing — phone ↔ PC*

- Detects local LAN IP automatically
- Spins up a **mobile-friendly HTTP download server**
- Generates a **QR code** — scan with phone to download instantly
- Glassmorphic popup: filename, size, URL, Copy Link button
- Drag a file onto Cyber Pet or Dynamic Island to trigger sharing
- No cables, no Bluetooth pairing, no apps required

---

### 5. Never Sakura FX
> 🌸 *Zen cherry blossom petals raining on your desktop*

- Full-screen transparent canvas overlay
- Physics-based **falling petal particles** with rotation & drift
- **Focus Mode aware**: automatically softens speed & shifts to calm pastels
- Seasonal color themes: Spring Pink, Autumn Orange, Winter White, Neon Cyber
- Zero CPU impact when minimized

---

### 6. Never Spotlight
> 🔍 *Lightning-fast app launcher & calculator*

- `Win + N` to summon the spotlight search bar
- Launches apps, files, and URLs instantly
- **Built-in calculator** — type math expressions directly
- Custom hotkey shortcuts support
- Results ranked by frequency of use

---

### 7. Never Clipboard
> 📋 *Your clipboard has memory now*

- Persistent clipboard history (survives reboots)
- Pin important snippets permanently
- Search & filter through your history
- One-click paste any item
- `Ctrl + Alt + V` to open the history panel

---

### 8. Never Radial Menu
> 🥧 *Pie launcher at your fingertips*

- Right-click hold → beautiful radial pie menu appears
- 8 configurable quick-launch slots
- Smooth animated open/close
- Fully customizable shortcuts
- `Middle-click` or configurable hotkey trigger

---

### 9. Windows Customizer
> 🎨 *Make Windows look stunning without registry hacks*

- **Glassmorphism window** with live alpha slider (75-100%)
- Built-in curated **8 × 4K wallpaper gallery**:
  - Cyberpunk City Neon
  - Anime Sakura Lo-Fi
  - Minimalist Dark Space
  - Synthwave Sunset
  - And more...
- 1-click wallpaper preview & apply (via Windows API)
- Drag-and-drop **custom wallpaper** import
- Animated hover glow on wallpaper cards
- Animated tab transitions

---

### 10. PC Master Booster
> ⚡ *Free RAM and clean junk in one click*

- **RAM cleaner**: trims working set of background processes
- **Disk junk cleaner**: removes temp files, recycle bin, browser cache
- **Process optimizer**: adjusts priorities for gaming/productivity
- Before/after RAM comparison display
- Safe — no registry edits, no driver installs

---

## ⌨️ Hotkey Cheat Sheet

| Hotkey | Action |
|--------|--------|
| `Alt + H` | Toggle Dynamic Island |
| `Win + N` | Open Never Spotlight |
| `Ctrl + Alt + V` | Open Never Clipboard |
| `Ctrl + Alt + F` | Toggle Focus / Pomodoro Mode |
| `Ctrl + Alt + S` | Toggle Sakura FX |
| `Middle Click` / Custom | Open Radial Menu |
| `Right-click tray icon` | Open Never Hub menu |

---

## 🚀 Installation

### Quick Start (Recommended)

1. **Download** [`NeverSuite-v1.0-Release.zip`](https://github.com/miras101208miras-cpu/NeverSuite/releases/tag/v1.0.0)
2. **Extract** the ZIP anywhere (e.g., `C:\NeverSuite\`)
3. **Double-click** `Install_Never_Suite.bat` to auto-install Python dependencies
4. **Double-click** `Start_Never_Hub.bat` to launch the suite

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/miras101208miras-cpu/NeverSuite.git
cd NeverSuite

# Install dependencies
pip install -r requirements.txt

# Launch Never Hub
python Never_Hub/main.py
```

### Dependencies

All dependencies are auto-installed by `Install_Never_Suite.bat`:

```
customtkinter
Pillow
psutil
qrcode
pyperclip
keyboard
pynput
winsdk
```

---

## ⚙️ System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| OS | Windows 10 (20H2+) | Windows 11 |
| Python | 3.10 | 3.11+ |
| RAM | 4 GB | 8 GB |
| Suite RAM Usage | ~45 MB | ~65 MB |
| Disk Space | 150 MB | 200 MB |
| Screen | 1366×768 | 1920×1080 |

---

## 🎨 Themes

Never Suite ships with three built-in themes configurable in `never_theme.json`:

| Theme | Description |
|-------|-------------|
| 🌸 **Tokyo Sakura** | Warm pinks, soft purples, anime-inspired |
| 🤖 **Cyberpunk 2077** | Neon yellow, electric blue, dark backgrounds |
| 🌌 **Deep Space** | Deep navy, starfield gradients, minimal |

---

## 📄 License

```
MIT License

Copyright (c) 2024 miras101208miras-cpu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<div align="center">

Made with 💜 by [miras101208miras-cpu](https://github.com/miras101208miras-cpu)

⭐ Star this repo if you love it!

</div>
