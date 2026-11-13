"""
⚡ NEVER HUB — Central Tray Center & Theme Engine v1.0
Part of the Never Suite Ecosystem.

Features:
- System Tray integration with pystray (icon, menus, quick toggles, themes, exit all).
- Modern Glassmorphic / Cyberpunk CustomTkinter launcher (Alt+H or Win+N).
- Real-time ecosystem RAM meter monitoring all Never Suite python processes.
- ON/OFF switches for all 9 ecosystem modules.
- One-Click Theme presets (Tokyo Sakura Lo-Fi, Cyberpunk 2077, Deep Space Minimal).
- Windows Registry Autostart management.
- Desktop shortcut creation.
"""

import os
import sys
import json
import time
import ctypes
import winreg
import threading
import subprocess
import tempfile
import psutil
from PIL import Image, ImageDraw
import customtkinter as ctk
import keyboard
import pystray
from pystray import MenuItem as item, Menu

# ---------------------------------------------------------
# Single-Instance Mutex
# ---------------------------------------------------------
WINDOW_TITLE = "⚡ Never Hub — Tray Center & Theme Engine"
_hub_mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Never_Hub_Mutex")
if ctypes.windll.kernel32.GetLastError() == 183:
    # Already running: attempt to bring the window to front and exit
    hwnd = ctypes.windll.user32.FindWindowW(None, WINDOW_TITLE)
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        ctypes.windll.user32.SetForegroundWindow(hwnd)
    sys.exit(0)

# Base Paths
SCRATCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HUB_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(HUB_DIR, "assets")
THEME_FILE = os.path.join(SCRATCH_DIR, "never_theme.json")
ICON_ICO = os.path.join(ASSETS_DIR, "never_hub.ico")
ICON_PNG = os.path.join(ASSETS_DIR, "never_hub.png")

# Python Executables
PYTHON_EXE = sys.executable
PYTHONW = os.path.join(os.path.dirname(PYTHON_EXE), "pythonw.exe")
if not os.path.exists(PYTHONW):
    PYTHONW = PYTHON_EXE

# Registry Autostart Config
REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
REG_NAME = "NeverHub"

# ---------------------------------------------------------
# Module Definitions (All 9 ecosystem modules)
# ---------------------------------------------------------
MODULES = [
    {
        "id": "island",
        "name": "Never Island",
        "emoji": "🏝️",
        "folder": "Dynamic_Island",
        "script_name": "main.py",
        "hotkey": "Экранный остров",
        "desc": "Динамический островок: медиаплеер SMTC, AI-глазки, фокус Pomodoro, OCR",
        "full_path": os.path.join(SCRATCH_DIR, "Dynamic_Island", "main.py")
    },
    {
        "id": "pet",
        "name": "Never Cyber Pet",
        "emoji": "🐾",
        "folder": "Cyber_Pet",
        "script_name": "main.py",
        "hotkey": "Всегда на экране",
        "desc": "Интерактивный питомец: Аниме-тян, Крипер, Слизень, кормление, реакция на фокус",
        "full_path": os.path.join(SCRATCH_DIR, "Cyber_Pet", "main.py")
    },
    {
        "id": "sakura",
        "name": "Never Sakura FX",
        "emoji": "🌸",
        "folder": "Never_Sakura",
        "script_name": "main.py",
        "hotkey": "Alt + S",
        "desc": "Живой интерактивный фон: лепестки сакуры или Матрица от курсора мыши",
        "full_path": os.path.join(SCRATCH_DIR, "Never_Sakura", "main.py")
    },
    {
        "id": "drop",
        "name": "Never Drop",
        "emoji": "⚡",
        "folder": "Never_Drop",
        "script_name": "never_drop.py",
        "hotkey": "Alt + D / Drop zone",
        "desc": "AirDrop для ПК: сверхбыстрая передача файлов между телефоном и ПК по Wi-Fi",
        "full_path": os.path.join(SCRATCH_DIR, "Never_Drop", "never_drop.py")
    },
    {
        "id": "spotlight",
        "name": "Never Spotlight",
        "emoji": "🔍",
        "folder": "Never_Spotlight",
        "script_name": "main.py",
        "hotkey": "Alt + Пробел",
        "desc": "Умная поисковая строка, быстрый запуск программ, калькулятор и конвертер валют",
        "full_path": os.path.join(SCRATCH_DIR, "Never_Spotlight", "main.py")
    },
    {
        "id": "clipboard",
        "name": "Never Clipboard",
        "emoji": "📋",
        "folder": "Never_Clipboard",
        "script_name": "main.py",
        "hotkey": "Alt + C",
        "desc": "Умная история буфера обмена (Ctrl+C), сниппеты, поиск и генератор надежных паролей",
        "full_path": os.path.join(SCRATCH_DIR, "Never_Clipboard", "main.py")
    },
    {
        "id": "radial",
        "name": "Never Radial Menu",
        "emoji": "⭕",
        "folder": "Never_Radial_Menu",
        "script_name": "main.py",
        "hotkey": "Alt + Q",
        "desc": "Неоновое круговое меню быстрых действий вокруг курсора мыши",
        "full_path": os.path.join(SCRATCH_DIR, "Never_Radial_Menu", "main.py")
    },
    {
        "id": "customizer",
        "name": "Windows Customizer",
        "emoji": "🎨",
        "folder": "Windows_Customizer",
        "script_name": "main.py",
        "hotkey": "По клику",
        "desc": "Галерея 4K обоев, стеклянная прозрачность, неоновые стили и твики Windows",
        "full_path": os.path.join(SCRATCH_DIR, "Windows_Customizer", "main.py")
    },
    {
        "id": "booster",
        "name": "PC Master & Booster",
        "emoji": "🚀",
        "folder": "PC_Master_Booster",
        "script_name": "main.py",
        "hotkey": "По клику",
        "desc": "Очистка оперативной памяти в 1 клик, оптимизация игр и системный монитор",
        "full_path": os.path.join(SCRATCH_DIR, "PC_Master_Booster", "main.py")
    }
]

# ---------------------------------------------------------
# Theme Presets
# ---------------------------------------------------------
THEME_PRESETS = {
    "sakura": {
        "id": "sakura",
        "name": "🌸 Tokyo Sakura Lo-Fi",
        "short_name": "Tokyo Sakura",
        "accent": "#ff6b8b",
        "accent_hover": "#fb7185",
        "secondary": "#f472b6",
        "bg": "#120c16",
        "card_bg": "#1c1424",
        "card_border": "#3b224c",
        "text": "#fff1f2",
        "text_muted": "#fbcfe8",
        "badge_bg": "#341738"
    },
    "cyberpunk": {
        "id": "cyberpunk",
        "name": "⚡ Cyberpunk 2077",
        "short_name": "Cyberpunk 2077",
        "accent": "#00f0ff",
        "accent_hover": "#38bdf8",
        "secondary": "#fcee0a",
        "bg": "#090a10",
        "card_bg": "#111422",
        "card_border": "#1e293b",
        "text": "#f8fafc",
        "text_muted": "#94a3b8",
        "badge_bg": "#132338"
    },
    "space": {
        "id": "space",
        "name": "🌌 Deep Space Minimal",
        "short_name": "Deep Space",
        "accent": "#818cf8",
        "accent_hover": "#6366f1",
        "secondary": "#38bdf8",
        "bg": "#070a13",
        "card_bg": "#0f172a",
        "card_border": "#1e293b",
        "text": "#f8fafc",
        "text_muted": "#94a3b8",
        "badge_bg": "#16203a"
    }
}

# ---------------------------------------------------------
# Autostart Helpers
# ---------------------------------------------------------
def is_autostart_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_READ) as key:
            val, _ = winreg.QueryValueEx(key, REG_NAME)
            return True
    except Exception:
        return False

def set_autostart_enabled(enable: bool):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if enable:
                cmd = f'"{PYTHONW}" "{os.path.abspath(__file__)}"'
                winreg.SetValueEx(key, REG_NAME, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, REG_NAME)
                except FileNotFoundError:
                    pass
    except Exception as e:
        print(f"Error setting autostart: {e}")

# ---------------------------------------------------------
# Desktop Shortcut Creation
# ---------------------------------------------------------
def ensure_desktop_shortcut():
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    shortcut_path = os.path.join(desktop, "Never Hub.lnk")
    if os.path.exists(shortcut_path):
        return

    main_script = os.path.abspath(__file__)
    vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")
Set oShortcut = WshShell.CreateShortcut(strDesktop & "\\Never Hub.lnk")
oShortcut.TargetPath = "{PYTHONW}"
oShortcut.Arguments = """{main_script}"""
oShortcut.WorkingDirectory = "{HUB_DIR}"
oShortcut.WindowStyle = 1
oShortcut.IconLocation = "{ICON_ICO}, 0"
oShortcut.Description = "Never Hub - Central Tray & Theme Launcher for Never Suite"
oShortcut.Save
'''
    vbs_path = os.path.join(tempfile.gettempdir(), "create_hub_lnk_auto.vbs")
    try:
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(vbs_content)
        subprocess.run(["cscript.exe", "//Nologo", vbs_path], check=True)
    except Exception as e:
        print(f"Failed to create shortcut: {e}")
    finally:
        if os.path.exists(vbs_path):
            try:
                os.remove(vbs_path)
            except Exception:
                pass


# ---------------------------------------------------------
# Main Never Hub Application
# ---------------------------------------------------------
class NeverHubApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # General Window Configuration
        self.title(WINDOW_TITLE)
        self.geometry("760x780")
        self.minsize(720, 680)
        
        # Center Window on Desktop
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 760) // 2
        y = (screen_height - 780) // 2 - 20
        self.geometry(f"760x780+{x}+{y}")

        # Glassmorphism Translucency
        try:
            self.attributes("-alpha", 0.96)
        except Exception:
            pass

        # Load Active Theme
        self.current_theme_id = self.load_current_theme_id()
        self.active_theme = THEME_PRESETS.get(self.current_theme_id, THEME_PRESETS["cyberpunk"])

        # Configure CustomTkinter Appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=self.active_theme["bg"])

        # Window Icon
        if os.path.exists(ICON_ICO):
            try:
                self.iconbitmap(ICON_ICO)
            except Exception:
                pass

        # Internal State
        self.is_running = True
        self.module_widgets = {}
        self.theme_buttons = {}

        # Build User Interface
        self.build_ui()

        # System Tray Integration
        self.tray_icon = None
        self.setup_tray()

        # Global Hotkeys (Alt+H, Win+N)
        self.setup_hotkeys()

        # Handle Window Close (minimize to tray)
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        # Ensure Desktop Shortcut Exists
        ensure_desktop_shortcut()

        # Start Background Process & RAM Monitoring Loop
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

    # -----------------------------------------------------
    # Theme Persistence
    # -----------------------------------------------------
    def load_current_theme_id(self):
        if os.path.exists(THEME_FILE):
            try:
                with open(THEME_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    tid = data.get("id") or data.get("theme")
                    if tid in THEME_PRESETS:
                        return tid
            except Exception:
                pass
        return "cyberpunk"

    def set_theme(self, theme_id):
        if theme_id not in THEME_PRESETS:
            return
        self.current_theme_id = theme_id
        self.active_theme = THEME_PRESETS[theme_id]

        # Write to shared theme configuration
        payload = {
            "theme": theme_id,
            "id": theme_id,
            "name": self.active_theme["name"],
            "accent": self.active_theme["accent"],
            "accent_hover": self.active_theme["accent_hover"],
            "secondary": self.active_theme["secondary"],
            "bg": self.active_theme["bg"],
            "card_bg": self.active_theme["card_bg"],
            "card_border": self.active_theme["card_border"],
            "text": self.active_theme["text"],
            "text_muted": self.active_theme["text_muted"]
        }
        try:
            with open(THEME_FILE, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving theme: {e}")

        # Update Hub Visual Theme
        self.apply_theme_to_ui()
        self.show_toast(f"✨ Тема «{self.active_theme['name']}» активирована!")

    def apply_theme_to_ui(self):
        thm = self.active_theme
        self.configure(fg_color=thm["bg"])
        self.header_frame.configure(fg_color=thm["card_bg"], border_color=thm["card_border"])
        self.brand_title.configure(text_color=thm["accent"])
        self.ram_badge.configure(border_color=thm["accent"])
        self.theme_section.configure(fg_color=thm["card_bg"], border_color=thm["card_border"])
        self.scroll_frame.configure(fg_color=thm["bg"])

        # Update theme selector buttons
        for tid, btn in self.theme_buttons.items():
            if tid == self.current_theme_id:
                btn.configure(
                    fg_color=thm["accent"],
                    text_color="#000000" if tid == "cyberpunk" else "#ffffff",
                    border_color="#ffffff",
                    border_width=2
                )
            else:
                btn.configure(
                    fg_color="#1e293b",
                    text_color="#94a3b8",
                    border_color=thm["card_border"],
                    border_width=1
                )

        # Update module cards
        for mid, w in self.module_widgets.items():
            w["card"].configure(fg_color=thm["card_bg"], border_color=thm["card_border"])
            w["hotkey_badge"].configure(text_color=thm["accent"])
            w["switch"].configure(progress_color=thm["accent"])

    # -----------------------------------------------------
    # UI Building
    # -----------------------------------------------------
    def build_ui(self):
        thm = self.active_theme

        # TOP HEADER
        self.header_frame = ctk.CTkFrame(
            self,
            corner_radius=14,
            fg_color=thm["card_bg"],
            border_width=1,
            border_color=thm["card_border"]
        )
        self.header_frame.pack(fill="x", padx=18, pady=(16, 10))

        # Brand row
        brand_left = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        brand_left.pack(side="left", padx=16, pady=12)

        self.brand_title = ctk.CTkLabel(
            brand_left,
            text="⚡ NEVER SUITE v1.0",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=thm["accent"]
        )
        self.brand_title.pack(anchor="w")

        self.brand_subtitle = ctk.CTkLabel(
            brand_left,
            text="Центральный хаб, системный трей и движок оформления",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8"
        )
        self.brand_subtitle.pack(anchor="w")

        # Live RAM & Module Meter (Right side of header)
        ram_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        ram_box.pack(side="right", padx=16, pady=10)

        self.ram_badge = ctk.CTkFrame(
            ram_box,
            corner_radius=8,
            fg_color="#0f172a",
            border_width=1,
            border_color=thm["accent"]
        )
        self.ram_badge.pack(anchor="e")

        self.ram_label = ctk.CTkLabel(
            self.ram_badge,
            text="⚡ Вся экосистема: ~0 МБ ОЗУ",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#38bdf8",
            padx=12,
            pady=4
        )
        self.ram_label.pack()

        self.active_count_label = ctk.CTkLabel(
            ram_box,
            text="🔥 Онлайн: 0 / 9 модулей  •  [Alt+H / Win+N]",
            font=ctk.CTkFont(size=10),
            text_color="#a855f7"
        )
        self.active_count_label.pack(anchor="e", pady=(3, 0))

        # MASTER CONTROLS BAR
        master_bar = ctk.CTkFrame(self, fg_color="transparent")
        master_bar.pack(fill="x", padx=18, pady=(0, 10))

        btn_start_all = ctk.CTkButton(
            master_bar,
            text="🚀 Запустить всё",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            height=34,
            command=self.start_all
        )
        btn_start_all.pack(side="left", fill="x", expand=True, padx=(0, 5))

        btn_stop_all = ctk.CTkButton(
            master_bar,
            text="🛑 Остановить всё",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#dc2626",
            hover_color="#b91c1c",
            height=34,
            command=self.stop_all
        )
        btn_stop_all.pack(side="left", fill="x", expand=True, padx=(5, 5))

        btn_restart_all = ctk.CTkButton(
            master_bar,
            text="🔄 Перезапустить",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#334155",
            hover_color="#475569",
            height=34,
            command=self.restart_all
        )
        btn_restart_all.pack(side="left", fill="x", expand=True, padx=(5, 5))

        # Autostart Checkbox
        self.autostart_var = ctk.BooleanVar(value=is_autostart_enabled())
        self.autostart_chk = ctk.CTkCheckBox(
            master_bar,
            text="Автозапуск с Windows",
            font=ctk.CTkFont(size=11),
            variable=self.autostart_var,
            command=self.on_autostart_toggle,
            checkbox_width=20,
            checkbox_height=20,
            corner_radius=4,
            fg_color=thm["accent"]
        )
        self.autostart_chk.pack(side="left", padx=(10, 0))

        # THEME PRESETS BAR
        self.theme_section = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=thm["card_bg"],
            border_width=1,
            border_color=thm["card_border"]
        )
        self.theme_section.pack(fill="x", padx=18, pady=(0, 10))

        theme_head = ctk.CTkFrame(self.theme_section, fg_color="transparent")
        theme_head.pack(fill="x", padx=14, pady=(8, 6))

        ctk.CTkLabel(
            theme_head,
            text="🎨 ТЕМЫ ОФОРМЛЕНИЯ (ONE-CLICK THEMES)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#e2e8f0"
        ).pack(side="left")

        self.toast_label = ctk.CTkLabel(
            theme_head,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#10b981"
        )
        self.toast_label.pack(side="right")

        theme_btns_frame = ctk.CTkFrame(self.theme_section, fg_color="transparent")
        theme_btns_frame.pack(fill="x", padx=12, pady=(0, 10))

        for tid, p in THEME_PRESETS.items():
            btn = ctk.CTkButton(
                theme_btns_frame,
                text=p["name"],
                font=ctk.CTkFont(size=11, weight="bold"),
                height=32,
                corner_radius=8,
                command=lambda t=tid: self.set_theme(t)
            )
            btn.pack(side="left", fill="x", expand=True, padx=4)
            self.theme_buttons[tid] = btn

        # MODULES SCROLLABLE LIST
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            corner_radius=12,
            fg_color=thm["bg"]
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=18, pady=(0, 12))

        for mod in MODULES:
            self.create_module_card(mod)

        # FOOTER / MINIMIZE HINT
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=18, pady=(0, 12))

        ctk.CTkLabel(
            footer,
            text="📌 Закрытие окна сворачивает Hub в трей. Для полного выхода: правый клик по трею → «Выход».",
            font=ctk.CTkFont(size=10),
            text_color="#64748b"
        ).pack(side="left")

        ctk.CTkButton(
            footer,
            text="🔽 Свернуть в трей",
            font=ctk.CTkFont(size=11),
            width=120,
            height=26,
            fg_color="#1e293b",
            hover_color="#334155",
            command=self.hide_to_tray
        ).pack(side="right")

        # Initial theme button highlight
        self.apply_theme_to_ui()

    def create_module_card(self, mod):
        thm = self.active_theme
        mid = mod["id"]

        card = ctk.CTkFrame(
            self.scroll_frame,
            corner_radius=10,
            fg_color=thm["card_bg"],
            border_width=1,
            border_color=thm["card_border"]
        )
        card.pack(fill="x", pady=4, padx=2)

        # Left Column: Info
        left = ctk.CTkFrame(card, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=12, pady=8)

        title_row = ctk.CTkFrame(left, fg_color="transparent")
        title_row.pack(anchor="w")

        icon_lbl = ctk.CTkLabel(title_row, text=mod["emoji"], font=ctk.CTkFont(size=16))
        icon_lbl.pack(side="left", padx=(0, 6))

        name_lbl = ctk.CTkLabel(
            title_row,
            text=mod["name"],
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#f8fafc"
        )
        name_lbl.pack(side="left", padx=(0, 8))

        hotkey_badge = ctk.CTkLabel(
            title_row,
            text=f" {mod['hotkey']} ",
            font=ctk.CTkFont(size=9, weight="bold"),
            fg_color="#1e293b",
            text_color=thm["accent"],
            corner_radius=6
        )
        hotkey_badge.pack(side="left")

        desc_lbl = ctk.CTkLabel(
            left,
            text=mod["desc"],
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8"
        )
        desc_lbl.pack(anchor="w", pady=(2, 0))

        # Right Column: Controls
        right = ctk.CTkFrame(card, fg_color="transparent")
        right.pack(side="right", padx=12, pady=8)

        status_badge = ctk.CTkLabel(
            right,
            text="⚫ ОСТАНОВЛЕН",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#94a3b8",
            fg_color="#1e293b",
            corner_radius=6,
            width=90,
            height=24
        )
        status_badge.pack(side="left", padx=8)

        switch_var = ctk.BooleanVar(value=False)
        switch = ctk.CTkSwitch(
            right,
            text="",
            width=46,
            height=22,
            variable=switch_var,
            progress_color=thm["accent"],
            command=lambda m=mod: self.on_switch_toggle(m)
        )
        switch.pack(side="left", padx=6)

        btn_restart = ctk.CTkButton(
            right,
            text="🔄",
            width=28,
            height=24,
            fg_color="#1e293b",
            hover_color="#334155",
            font=ctk.CTkFont(size=11),
            command=lambda m=mod: self.restart_module(m)
        )
        btn_restart.pack(side="left", padx=(2, 0))

        self.module_widgets[mid] = {
            "card": card,
            "status_badge": status_badge,
            "switch": switch,
            "switch_var": switch_var,
            "hotkey_badge": hotkey_badge,
            "mod": mod,
            "is_user_toggling": False
        }

    # -----------------------------------------------------
    # Toast notification
    # -----------------------------------------------------
    def show_toast(self, message):
        self.toast_label.configure(text=message)
        self.after(3500, lambda: self.toast_label.configure(text=""))

    # -----------------------------------------------------
    # Autostart Handler
    # -----------------------------------------------------
    def on_autostart_toggle(self):
        val = self.autostart_var.get()
        set_autostart_enabled(val)
        if val:
            self.show_toast("⚡ Автозапуск с Windows включен!")
        else:
            self.show_toast("⚪ Автозапуск с Windows отключен.")

    # -----------------------------------------------------
    # Process Management
    # -----------------------------------------------------
    def is_module_running(self, mod):
        folder = mod["folder"].lower()
        script = mod["script_name"].lower()
        for p in psutil.process_iter(['name', 'cmdline']):
            try:
                name = (p.info['name'] or '').lower()
                if 'python' in name:
                    cmd = p.info.get('cmdline') or []
                    cmd_str = " ".join(cmd).lower()
                    if script in cmd_str and folder in cmd_str:
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False

    def start_module(self, mod):
        script_path = mod["full_path"]
        if not os.path.exists(script_path):
            print(f"File not found: {script_path}")
            return False

        if self.is_module_running(mod):
            return True

        DETACHED_PROCESS = 0x00000008
        CREATE_NO_WINDOW = 0x08000000
        flags = DETACHED_PROCESS | CREATE_NO_WINDOW
        cwd = os.path.dirname(script_path)
        try:
            subprocess.Popen([PYTHONW, script_path], cwd=cwd, creationflags=flags)
            return True
        except Exception as e:
            print(f"Error launching {mod['name']}: {e}")
            return False

    def stop_module(self, mod):
        folder = mod["folder"].lower()
        script = mod["script_name"].lower()
        stopped = False
        for p in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                name = (p.info['name'] or '').lower()
                if 'python' in name:
                    cmd = p.info.get('cmdline') or []
                    cmd_str = " ".join(cmd).lower()
                    if script in cmd_str and folder in cmd_str:
                        p.terminate()
                        stopped = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return stopped

    def restart_module(self, mod):
        self.stop_module(mod)
        self.after(500, lambda: self.start_module(mod))

    def on_switch_toggle(self, mod):
        mid = mod["id"]
        w = self.module_widgets[mid]
        w["is_user_toggling"] = True
        is_on = w["switch_var"].get()

        if is_on:
            self.start_module(mod)
        else:
            self.stop_module(mod)

        self.after(600, lambda: self._clear_toggling(mid))

    def _clear_toggling(self, mid):
        if mid in self.module_widgets:
            self.module_widgets[mid]["is_user_toggling"] = False

    def toggle_module_by_id(self, mid):
        for mod in MODULES:
            if mod["id"] == mid:
                if self.is_module_running(mod):
                    self.stop_module(mod)
                else:
                    self.start_module(mod)
                break

    def start_all(self):
        for mod in MODULES:
            self.start_module(mod)
        self.show_toast("🚀 Запуск всех модулей экосистемы...")

    def stop_all(self):
        for mod in MODULES:
            self.stop_module(mod)
        self.show_toast("🛑 Все модули остановлены.")

    def restart_all(self):
        self.stop_all()
        self.after(700, self.start_all)
        self.show_toast("🔄 Перезапуск всей экосистемы...")

    # -----------------------------------------------------
    # Process & RAM Monitoring Loop
    # -----------------------------------------------------
    def monitor_loop(self):
        while self.is_running:
            try:
                running_ids = set()
                total_rss_bytes = 0

                for p in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
                    try:
                        name = (p.info['name'] or '').lower()
                        if 'python' in name:
                            cmd = p.info.get('cmdline') or []
                            cmd_str = " ".join(cmd).lower()

                            # Check which modules are running
                            is_ecosystem_proc = False
                            for mod in MODULES:
                                if mod["script_name"].lower() in cmd_str and mod["folder"].lower() in cmd_str:
                                    running_ids.add(mod["id"])
                                    is_ecosystem_proc = True

                            # Also include Never Hub and never_focus in ecosystem RAM
                            if not is_ecosystem_proc:
                                if "never_hub" in cmd_str or "never_focus" in cmd_str:
                                    is_ecosystem_proc = True

                            if is_ecosystem_proc:
                                mem = p.info.get('memory_info')
                                if mem:
                                    total_rss_bytes += mem.rss
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                ram_mb = total_rss_bytes / (1024 * 1024)
                self.after(0, self.update_monitor_ui, running_ids, ram_mb)
            except Exception as e:
                pass

            time.sleep(1.2)

    def update_monitor_ui(self, running_ids, ram_mb):
        if not self.is_running:
            return

        # Update RAM & Count Labels
        self.ram_label.configure(text=f"⚡ Вся экосистема: ~{ram_mb:.0f} МБ ОЗУ")
        self.active_count_label.configure(
            text=f"🔥 Онлайн: {len(running_ids)} / {len(MODULES)} модулей  •  [Alt+H / Win+N]"
        )

        # Update each module card
        for mid, w in self.module_widgets.items():
            is_active = mid in running_ids
            if is_active:
                w["status_badge"].configure(
                    text="🟢 РАБОТАЕТ",
                    text_color="#10b981",
                    fg_color="#064e3b"
                )
            else:
                w["status_badge"].configure(
                    text="⚫ ОСТАНОВЛЕН",
                    text_color="#94a3b8",
                    fg_color="#1e293b"
                )

            # Sync switch only if user isn't clicking it right now
            if not w["is_user_toggling"]:
                current_val = w["switch_var"].get()
                if current_val != is_active:
                    w["switch_var"].set(is_active)

    # -----------------------------------------------------
    # System Tray & Hotkey Support
    # -----------------------------------------------------
    def get_tray_image(self):
        if os.path.exists(ICON_PNG):
            try:
                return Image.open(ICON_PNG)
            except Exception:
                pass
        # Fallback generated dot/logo
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([4, 4, 60, 60], fill=(14, 165, 233, 255), outline=(56, 189, 248, 255), width=3)
        return img

    def setup_tray(self):
        tray_img = self.get_tray_image()

        def make_toggle_action(mid):
            return lambda icon, itm: self.after(0, lambda: self.toggle_module_by_id(mid))

        def make_theme_action(tid):
            return lambda icon, itm: self.after(0, lambda: self.set_theme(tid))

        menu = Menu(
            item('⚡ Открыть Never Hub', lambda icon, itm: self.after(0, self.show_from_tray), default=True),
            Menu.SEPARATOR,
            item('🚀 Запустить всё', lambda icon, itm: self.after(0, self.start_all)),
            item('🛑 Остановить всё', lambda icon, itm: self.after(0, self.stop_all)),
            Menu.SEPARATOR,
            item('🎨 Темы оформления', Menu(
                item('🌸 Tokyo Sakura Lo-Fi', make_theme_action('sakura')),
                item('⚡ Cyberpunk 2077', make_theme_action('cyberpunk')),
                item('🌌 Deep Space Minimal', make_theme_action('space'))
            )),
            Menu.SEPARATOR,
            item('⚡ Быстрые переключатели', Menu(
                *[item(f"{m['emoji']} {m['name']}", make_toggle_action(m['id'])) for m in MODULES]
            )),
            Menu.SEPARATOR,
            item('❌ Выход из Never Hub (Exit All)', lambda icon, itm: self.after(0, self.quit_app))
        )

        self.tray_icon = pystray.Icon("NeverHub", tray_img, "Never Hub v1.0", menu)
        self.tray_icon.run_detached()

    def setup_hotkeys(self):
        try:
            keyboard.add_hotkey("alt+h", lambda: self.after(0, self.toggle_window_visibility))
        except Exception as e:
            print(f"Alt+H hotkey registration: {e}")

        try:
            keyboard.add_hotkey("win+n", lambda: self.after(0, self.toggle_window_visibility))
        except Exception as e:
            print(f"Win+N hotkey registration: {e}")

    def toggle_window_visibility(self):
        if self.winfo_viewable() and self.state() != "iconic":
            self.hide_to_tray()
        else:
            self.show_from_tray()

    def show_from_tray(self):
        self.deiconify()
        self.state("normal")
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))

    def hide_to_tray(self):
        self.withdraw()

    def quit_app(self):
        self.is_running = False
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        self.after(100, self.destroy)


# ---------------------------------------------------------
# Entry Point
# ---------------------------------------------------------
if __name__ == "__main__":
    app = NeverHubApp()
    app.mainloop()
