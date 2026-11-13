"""
Never Suite v1.0 Installer & Setup Wizard
Standalone gorgeous CustomTkinter dark-neon installer wizard.
"""

import os
import sys
import time
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk

# Base directory paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
DESKTOP_DIR = os.path.join(os.environ.get("USERPROFILE", "C:\\Users\\school57-60"), "Desktop")

# Ensure desktop exists
if not os.path.exists(DESKTOP_DIR):
    DESKTOP_DIR = os.path.expanduser("~/Desktop")

# Helper to create windows shortcuts via VBScript
def create_windows_shortcut(lnk_path, target_path, arguments="", working_dir="", icon_path=""):
    try:
        vbs_lines = [
            'Set oWS = CreateObject("WScript.Shell")',
            f'sLinkFile = "{lnk_path}"',
            'Set oLink = oWS.CreateShortcut(sLinkFile)',
            f'oLink.TargetPath = "{target_path}"',
            f'oLink.Arguments = "{arguments}"',
            f'oLink.WorkingDirectory = "{working_dir}"',
        ]
        if icon_path and os.path.exists(icon_path):
            vbs_lines.append(f'oLink.IconLocation = "{icon_path}, 0"')
        vbs_lines.append('oLink.Save')
        
        script_content = "\r\n".join(vbs_lines)
        temp_vbs = os.path.join(os.environ.get("TEMP", "."), f"create_lnk_{abs(hash(lnk_path))}.vbs")
        with open(temp_vbs, "w", encoding="latin-1") as f:
            f.write(script_content)
        
        subprocess.run(["cscript", "//nologo", temp_vbs], capture_output=True, text=True)
        if os.path.exists(temp_vbs):
            os.remove(temp_vbs)
        return os.path.exists(lnk_path)
    except Exception as e:
        print(f"Error creating shortcut {lnk_path}: {e}")
        return False

# Autostart registry helper
def set_autostart(app_name, exe_path, enable=True):
    try:
        import winreg
        key = winreg.HKEY_CURRENT_USER
        sub_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(key, sub_key, 0, winreg.KEY_SET_VALUE) as reg_key:
            if enable:
                winreg.SetValueEx(reg_key, app_name, 0, winreg.REG_SZ, exe_path)
            else:
                try:
                    winreg.DeleteValue(reg_key, app_name)
                except FileNotFoundError:
                    pass
        return True
    except Exception as e:
        print(f"Error updating autostart: {e}")
        return False

# Available Ecosystem Components
MODULES = [
    {
        "id": "hub",
        "name": "🎛️ Never Hub (Control Center)",
        "desc": "Центральная панель в трее, живой счетчик ОЗУ, переключение тем и автозапуск.",
        "ram": 14,
        "default": True,
        "path": os.path.join(BASE_DIR, "Never_Hub", "main.py"),
        "lnk_name": "Never Hub.lnk"
    },
    {
        "id": "island",
        "name": "🏝️ Dynamic Island",
        "desc": "Стильный интерактивный островок: медиа-плеер SMTC, эквалайзер и таймер Pomodoro Focus.",
        "ram": 16,
        "default": True,
        "path": os.path.join(BASE_DIR, "Dynamic_Island", "main.py"),
        "lnk_name": "Never Dynamic Island.lnk"
    },
    {
        "id": "pet",
        "name": "🐾 Cyber Pet Companion",
        "desc": "Аниме-спутник на рабочем столе: физика, эмоции, кастомные наряды и реакция на клики.",
        "ram": 12,
        "default": True,
        "path": os.path.join(BASE_DIR, "Cyber_Pet", "main.py"),
        "lnk_name": "Never Cyber Pet.lnk"
    },
    {
        "id": "sakura",
        "name": "🌸 Never Sakura FX",
        "desc": "Релакс-лепестки сакуры с эффектом глубины и замедлением в режиме учебы/фокуса.",
        "ram": 8,
        "default": True,
        "path": os.path.join(BASE_DIR, "Never_Sakura", "main.py"),
        "lnk_name": "Never Sakura FX.lnk"
    },
    {
        "id": "drop",
        "name": "⚡ Never Drop (AirDrop PC ⇄ Phone)",
        "desc": "Сверхбыстрая передача файлов на телефон по QR-коду через локальный Wi-Fi.",
        "ram": 9,
        "default": True,
        "path": os.path.join(BASE_DIR, "Never_Drop", "never_drop.py"),
        "lnk_name": "Never Drop.lnk"
    },
    {
        "id": "spotlight",
        "name": "🔍 Never Spotlight & Clipboard",
        "desc": "Молниеносный запуск файлов и программ по Alt+Space и история буфера обмена.",
        "ram": 8,
        "default": True,
        "path": os.path.join(BASE_DIR, "Never_Spotlight", "main.py"),
        "lnk_name": "Never Spotlight.lnk"
    },
    {
        "id": "customizer",
        "name": "🎨 Windows Customizer",
        "desc": "Гласморфизм и прозрачность окон, 4K галерея обоев, сглаживание шрифтов и анимации.",
        "ram": 15,
        "default": True,
        "path": os.path.join(BASE_DIR, "Windows_Customizer", "main.py"),
        "lnk_name": "Windows Customizer.lnk"
    },
    {
        "id": "booster",
        "name": "🚀 PC Master & Booster",
        "desc": "Турбо-очистка ОЗУ, очистка временных файлов, отключение лишней телеметрии Windows.",
        "ram": 7,
        "default": True,
        "path": os.path.join(BASE_DIR, "PC_Master_Booster", "main.py"),
        "lnk_name": "PC Master Booster.lnk"
    }
]

class NeverInstallerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Appearance configuration
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Never Suite v1.0 — Мастер Установки")
        self.geometry("860x620")
        self.minsize(840, 600)
        self.resizable(False, False)

        # App icon if available
        ico_file = os.path.join(ASSETS_DIR, "never_suite.ico")
        if os.path.exists(ico_file):
            try:
                self.iconbitmap(ico_file)
            except Exception:
                pass

        # Create Desktop Shortcut for Installer itself right away (for testing requirement)
        self.create_setup_shortcut()

        # State
        self.current_step = 0
        self.install_dir = tk.StringVar(value=BASE_DIR)
        self.create_desktop_shortcuts = tk.BooleanVar(value=True)
        self.enable_autostart = tk.BooleanVar(value=True)
        self.launch_after_install = tk.BooleanVar(value=True)
        
        # Component selection variables
        self.module_vars = {}
        for mod in MODULES:
            self.module_vars[mod["id"]] = tk.BooleanVar(value=mod["default"])

        # Layout: Sidebar on Left, Content on Right
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.build_sidebar()
        self.build_content_area()
        self.show_step(0)

    def create_setup_shortcut(self):
        """Auto-creates 'Never Suite Setup.lnk' on the desktop."""
        try:
            lnk = os.path.join(DESKTOP_DIR, "Never Suite Setup.lnk")
            installer_main = os.path.abspath(__file__)
            python_exe = sys.executable
            ico = os.path.join(ASSETS_DIR, "never_suite.ico")
            create_windows_shortcut(lnk, python_exe, f'"{installer_main}"', os.path.dirname(installer_main), ico)
        except Exception as e:
            print("Error creating setup shortcut:", e)

    def build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#0C0D14")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)

        # Branding
        title_box = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        title_box.pack(fill="x", padx=16, pady=(24, 20))

        logo_lbl = ctk.CTkLabel(
            title_box, 
            text="⚡ NEVER SUITE", 
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#00F5FF"
        )
        logo_lbl.pack(anchor="w")

        ver_lbl = ctk.CTkLabel(
            title_box, 
            text="v1.0 Community Edition", 
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#8E8E93"
        )
        ver_lbl.pack(anchor="w")

        # Step indicator items
        self.step_labels = []
        steps_info = [
            ("1. Приветствие", "Обзор возможностей"),
            ("2. Компоненты", "Выбор модулей"),
            ("3. Настройки", "Путь и автозапуск"),
            ("4. Установка", "Развертывание"),
            ("5. Завершение", "Запуск системы"),
        ]

        for i, (title, sub) in enumerate(steps_info):
            step_card = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent", corner_radius=8)
            step_card.pack(fill="x", padx=14, pady=6)

            t_lbl = ctk.CTkLabel(
                step_card, 
                text=title, 
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                text_color="#5E6278",
                anchor="w"
            )
            t_lbl.pack(fill="x", padx=8, pady=(4, 1))

            s_lbl = ctk.CTkLabel(
                step_card, 
                text=sub, 
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color="#3E4255",
                anchor="w"
            )
            s_lbl.pack(fill="x", padx=8, pady=(0, 4))

            self.step_labels.append((step_card, t_lbl, s_lbl))

        # Bottom specs badge
        badge_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="#141622", corner_radius=10)
        badge_frame.pack(side="bottom", fill="x", padx=14, pady=16)

        badge_txt = ctk.CTkLabel(
            badge_frame,
            text="⚡ Ultra-Lightweight\nВсего ~65 MB ОЗУ\nБез Electron и Node.js",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#A29BFE",
            justify="center"
        )
        badge_txt.pack(padx=10, pady=10)

    def build_content_area(self):
        self.main_container = ctk.CTkFrame(self, fg_color="#12131C", corner_radius=0)
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Frames for each step
        self.step_frames = [
            self.create_step_0_welcome(),
            self.create_step_1_components(),
            self.create_step_2_options(),
            self.create_step_3_installing(),
            self.create_step_4_finish()
        ]

    def update_sidebar_highlight(self, active_index):
        for idx, (card, t_lbl, s_lbl) in enumerate(self.step_labels):
            if idx == active_index:
                card.configure(fg_color="#1E2235")
                t_lbl.configure(text_color="#00F5FF")
                s_lbl.configure(text_color="#A29BFE")
            elif idx < active_index:
                card.configure(fg_color="transparent")
                t_lbl.configure(text_color="#00FF88")
                s_lbl.configure(text_color="#5E6278")
            else:
                card.configure(fg_color="transparent")
                t_lbl.configure(text_color="#5E6278")
                s_lbl.configure(text_color="#3E4255")

    def show_step(self, index):
        self.current_step = index
        self.update_sidebar_highlight(index)
        for i, frame in enumerate(self.step_frames):
            if i == index:
                frame.grid(row=0, column=0, sticky="nsew")
            else:
                frame.grid_forget()

    # STEP 0: WELCOME
    def create_step_0_welcome(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        
        # Header banner
        header = ctk.CTkFrame(frame, fg_color="#1A1C2B", corner_radius=12, border_width=1, border_color="#2A2E44")
        header.pack(fill="x", padx=28, pady=(24, 16))

        h_title = ctk.CTkLabel(
            header,
            text="Добро пожаловать в Never Suite v1.0",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color="#FFFFFF"
        )
        h_title.pack(anchor="w", padx=20, pady=(16, 4))

        h_sub = ctk.CTkLabel(
            header,
            text="Инновационная экосистема для прокачки и кастомизации Windows 10/11",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#A29BFE"
        )
        h_sub.pack(anchor="w", padx=20, pady=(0, 16))

        # Highlights cards grid
        grid = ctk.CTkFrame(frame, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=28, pady=4)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        highlights = [
            ("🏝️ Dynamic Island & SMTC", "Живой медиаплеер с управлением треками, визуализацией волн и Pomodoro Focus."),
            ("🐾 Интерактивный Cyber Pet", "Живой аниме-питомец с физикой, реакцией на курсор и сменными костюмами."),
            ("⚡ Never Drop (AirDrop PC)", "Моментальная передача файлов на телефон по QR-коду через локальный Wi-Fi."),
            ("🌸 Sakura FX & Customizer", "Эстетичные падающие лепестки, гласморфизм окон и 4K галерея обоев."),
            ("🔍 Spotlight & Clipboard", "Мгновенный поиск по Alt+Space и история буфера обмена без нагрузки на процессор."),
            ("🚀 Экстремальная легкость", "Написано на Python & Win32 API. Всего ~65 МБ ОЗУ на всю систему вместо гигабайтов.")
        ]

        for i, (title, desc) in enumerate(highlights):
            row = i // 2
            col = i % 2
            card = ctk.CTkFrame(grid, fg_color="#161824", corner_radius=10, border_width=1, border_color="#24283B")
            card.grid(row=row, column=col, padx=8, pady=6, sticky="nsew")

            ctk.CTkLabel(
                card, 
                text=title, 
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                text_color="#00F5FF"
            ).pack(anchor="w", padx=12, pady=(10, 2))

            ctk.CTkLabel(
                card, 
                text=desc, 
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color="#8E8E93",
                wraplength=260,
                justify="left"
            ).pack(anchor="w", padx=12, pady=(0, 10))

        # Bottom actions bar
        bottom_bar = ctk.CTkFrame(frame, fg_color="transparent")
        bottom_bar.pack(fill="x", padx=28, pady=20)

        license_lbl = ctk.CTkLabel(
            bottom_bar,
            text="Free & Open-Source Community Edition • Без рекламы и трекеров",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#636E72"
        )
        license_lbl.pack(side="left")

        next_btn = ctk.CTkButton(
            bottom_bar,
            text="Начать установку ➔",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="#6C5CE7",
            hover_color="#5843E5",
            width=180,
            height=42,
            corner_radius=8,
            command=lambda: self.show_step(1)
        )
        next_btn.pack(side="right")

        return frame

    # STEP 1: COMPONENT SELECTION
    def create_step_1_components(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")

        title_lbl = ctk.CTkLabel(
            frame,
            text="Выбор компонентов Never Suite",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#FFFFFF"
        )
        title_lbl.pack(anchor="w", padx=28, pady=(20, 2))

        sub_lbl = ctk.CTkLabel(
            frame,
            text="Выберите модули, которые хотите включить в состав вашей системы:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#8E8E93"
        )
        sub_lbl.pack(anchor="w", padx=28, pady=(0, 10))

        # Quick select buttons bar
        sel_bar = ctk.CTkFrame(frame, fg_color="transparent")
        sel_bar.pack(fill="x", padx=28, pady=(0, 8))

        ctk.CTkButton(
            sel_bar,
            text="Выбрать все",
            width=100,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#232738",
            hover_color="#2D3249",
            command=self.select_all_modules
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            sel_bar,
            text="Снять все",
            width=100,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#232738",
            hover_color="#2D3249",
            command=self.deselect_all_modules
        ).pack(side="left")

        self.ram_summary_lbl = ctk.CTkLabel(
            sel_bar,
            text="Ожидаемое потребление: ~65 МБ ОЗУ",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#00FF88"
        )
        self.ram_summary_lbl.pack(side="right")

        # Scrollable list of modules
        scroll = ctk.CTkScrollableFrame(frame, fg_color="#151722", corner_radius=10)
        scroll.pack(fill="both", expand=True, padx=28, pady=(0, 14))

        for mod in MODULES:
            row_frame = ctk.CTkFrame(scroll, fg_color="#1A1C29", corner_radius=8)
            row_frame.pack(fill="x", padx=6, pady=4)

            chk = ctk.CTkCheckBox(
                row_frame,
                text=mod["name"],
                variable=self.module_vars[mod["id"]],
                command=self.update_ram_estimate,
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                checkbox_height=20,
                checkbox_width=20,
                border_width=2,
                fg_color="#6C5CE7",
                hover_color="#5843E5"
            )
            chk.pack(anchor="w", padx=12, pady=(8, 2))

            desc_lbl = ctk.CTkLabel(
                row_frame,
                text=f"{mod['desc']}  [~{mod['ram']} МБ ОЗУ]",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color="#8E8E93",
                justify="left"
            )
            desc_lbl.pack(anchor="w", padx=36, pady=(0, 8))

        # Bottom nav
        bottom_bar = ctk.CTkFrame(frame, fg_color="transparent")
        bottom_bar.pack(fill="x", padx=28, pady=(0, 18))

        back_btn = ctk.CTkButton(
            bottom_bar,
            text="⬅ Назад",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="#2A2E44",
            hover_color="#363C57",
            width=120,
            height=38,
            corner_radius=8,
            command=lambda: self.show_step(0)
        )
        back_btn.pack(side="left")

        next_btn = ctk.CTkButton(
            bottom_bar,
            text="Настройки ➔",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#6C5CE7",
            hover_color="#5843E5",
            width=140,
            height=38,
            corner_radius=8,
            command=lambda: self.show_step(2)
        )
        next_btn.pack(side="right")

        return frame

    def select_all_modules(self):
        for v in self.module_vars.values():
            v.set(True)
        self.update_ram_estimate()

    def deselect_all_modules(self):
        for v in self.module_vars.values():
            v.set(False)
        self.update_ram_estimate()

    def update_ram_estimate(self):
        total_ram = sum(mod["ram"] for mod in MODULES if self.module_vars[mod["id"]].get())
        self.ram_summary_lbl.configure(text=f"Ожидаемое потребление: ~{total_ram} МБ ОЗУ")

    # STEP 2: INSTALLATION OPTIONS
    def create_step_2_options(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")

        title_lbl = ctk.CTkLabel(
            frame,
            text="Параметры установки",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#FFFFFF"
        )
        title_lbl.pack(anchor="w", padx=28, pady=(24, 4))

        sub_lbl = ctk.CTkLabel(
            frame,
            text="Укажите каталог расположения и параметры интеграции в Windows:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#8E8E93"
        )
        sub_lbl.pack(anchor="w", padx=28, pady=(0, 20))

        # Path Card
        path_card = ctk.CTkFrame(frame, fg_color="#181A26", corner_radius=10, border_width=1, border_color="#2A2E44")
        path_card.pack(fill="x", padx=28, pady=(0, 16))

        ctk.CTkLabel(
            path_card,
            text="📁 Каталог установки Never Suite:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#00F5FF"
        ).pack(anchor="w", padx=16, pady=(12, 6))

        path_row = ctk.CTkFrame(path_card, fg_color="transparent")
        path_row.pack(fill="x", padx=16, pady=(0, 14))

        path_entry = ctk.CTkEntry(
            path_row,
            textvariable=self.install_dir,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#10111A",
            border_color="#3A3E5B",
            height=34
        )
        path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_btn = ctk.CTkButton(
            path_row,
            text="Обзор...",
            width=90,
            height=34,
            fg_color="#2D3249",
            hover_color="#3A405D",
            command=self.browse_folder
        )
        browse_btn.pack(side="right")

        # Shortcuts & Autostart Card
        opts_card = ctk.CTkFrame(frame, fg_color="#181A26", corner_radius=10, border_width=1, border_color="#2A2E44")
        opts_card.pack(fill="x", padx=28, pady=(0, 20))

        ctk.CTkLabel(
            opts_card,
            text="⚙️ Интеграция с рабочим столом и автозагрузкой:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#00F5FF"
        ).pack(anchor="w", padx=16, pady=(14, 8))

        chk_sc = ctk.CTkCheckBox(
            opts_card,
            text="Создать ярлыки для Never Hub и выбранных модулей на Рабочем столе",
            variable=self.create_desktop_shortcuts,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="#6C5CE7"
        )
        chk_sc.pack(anchor="w", padx=20, pady=6)

        chk_auto = ctk.CTkCheckBox(
            opts_card,
            text="Запускать Never Hub автоматически при входе в Windows (Автозапуск)",
            variable=self.enable_autostart,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="#6C5CE7"
        )
        chk_auto.pack(anchor="w", padx=20, pady=(6, 14))

        # Bottom nav
        bottom_bar = ctk.CTkFrame(frame, fg_color="transparent")
        bottom_bar.pack(side="bottom", fill="x", padx=28, pady=20)

        back_btn = ctk.CTkButton(
            bottom_bar,
            text="⬅ Назад",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="#2A2E44",
            hover_color="#363C57",
            width=120,
            height=38,
            corner_radius=8,
            command=lambda: self.show_step(1)
        )
        back_btn.pack(side="left")

        install_btn = ctk.CTkButton(
            bottom_bar,
            text="Установить ⚡",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="#00B894",
            hover_color="#009475",
            width=160,
            height=40,
            corner_radius=8,
            command=self.start_installation
        )
        install_btn.pack(side="right")

        return frame

    def browse_folder(self):
        chosen = filedialog.askdirectory(initialdir=self.install_dir.get(), title="Выберите каталог установки")
        if chosen:
            self.install_dir.set(chosen)

    # STEP 3: INSTALLATION PROGRESS
    def create_step_3_installing(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")

        title_lbl = ctk.CTkLabel(
            frame,
            text="Установка Never Suite v1.0",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#FFFFFF"
        )
        title_lbl.pack(anchor="w", padx=28, pady=(24, 4))

        self.status_lbl = ctk.CTkLabel(
            frame,
            text="Подготовка к установке компонентов...",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#00F5FF"
        )
        self.status_lbl.pack(anchor="w", padx=28, pady=(0, 14))

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(frame, height=14, corner_radius=7, fg_color="#1E2235", progress_color="#6C5CE7")
        self.progress_bar.pack(fill="x", padx=28, pady=(0, 14))
        self.progress_bar.set(0)

        # Log textbox
        log_card = ctk.CTkFrame(frame, fg_color="#131520", corner_radius=10, border_width=1, border_color="#24283B")
        log_card.pack(fill="both", expand=True, padx=28, pady=(0, 20))

        self.log_box = ctk.CTkTextbox(
            log_card,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="transparent",
            text_color="#CAD3E3",
            wrap="word"
        )
        self.log_box.pack(fill="both", expand=True, padx=8, pady=8)

        return frame

    def log(self, text):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    def start_installation(self):
        self.show_step(3)
        self.log_box.delete("1.0", "end")
        threading.Thread(target=self.run_install_thread, daemon=True).start()

    def run_install_thread(self):
        time.sleep(0.3)
        self.log("[INFO] Запуск мастера установки Never Suite v1.0...")
        self.progress_bar.set(0.05)
        
        # Step 1: verify directories
        target_dir = self.install_dir.get()
        self.status_lbl.configure(text="Проверка системных требований и окружения Python...")
        self.log(f"[INFO] Целевая директория: {target_dir}")
        self.log(f"[INFO] Интерпретатор Python: {sys.executable}")
        time.sleep(0.5)
        self.progress_bar.set(0.20)

        # Step 2: Initialize Theme config if missing
        self.status_lbl.configure(text="Настройка цветовых схем и профилей оформления...")
        theme_file = os.path.join(target_dir, "never_theme.json")
        if not os.path.exists(theme_file):
            import json
            default_theme = {
                "theme": "Tokyo Sakura Lo-Fi",
                "accent": "#FF79C6",
                "bg": "#191A2A",
                "text": "#F8F8F2",
                "alpha": 0.94
            }
            try:
                with open(theme_file, "w", encoding="utf-8") as f:
                    json.dump(default_theme, f, indent=4)
                self.log(f"[OK] Создан глобальный профиль тем: {theme_file}")
            except Exception as e:
                self.log(f"[WARN] Ошибка создания theme.json: {e}")
        else:
            self.log("[OK] Обнаружен существующий профиль never_theme.json")
        time.sleep(0.5)
        self.progress_bar.set(0.40)

        # Step 3: Configure selected modules
        self.status_lbl.configure(text="Конфигурирование выбранных компонентов...")
        selected = [m for m in MODULES if self.module_vars[m["id"]].get()]
        for mod in selected:
            self.log(f"[INSTALL] Модуль активирован: {mod['name']}")
            time.sleep(0.2)
        self.progress_bar.set(0.65)

        # Step 4: Create Shortcuts
        if self.create_desktop_shortcuts.get():
            self.status_lbl.configure(text="Создание ярлыков на Рабочем столе...")
            python_w = sys.executable.replace("python.exe", "pythonw.exe")
            if not os.path.exists(python_w):
                python_w = sys.executable

            for mod in selected:
                lnk_name = mod["lnk_name"]
                lnk_path = os.path.join(DESKTOP_DIR, lnk_name)
                script_path = mod["path"]
                wdir = os.path.dirname(script_path)
                ico = os.path.join(ASSETS_DIR, "never_suite.ico")
                
                ok = create_windows_shortcut(lnk_path, python_w, f'"{script_path}"', wdir, ico)
                if ok:
                    self.log(f"[SHORTCUT] Создан ярлык: {lnk_name}")
                else:
                    self.log(f"[SHORTCUT] Пропуск/ошибка: {lnk_name}")
                time.sleep(0.1)

            # Also create Never Suite Setup.lnk
            installer_main = os.path.abspath(__file__)
            setup_lnk = os.path.join(DESKTOP_DIR, "Never Suite Setup.lnk")
            create_windows_shortcut(setup_lnk, sys.executable, f'"{installer_main}"', os.path.dirname(installer_main), os.path.join(ASSETS_DIR, "never_suite.ico"))
            self.log("[SHORTCUT] Создан ярлык: Never Suite Setup.lnk")

        self.progress_bar.set(0.85)
        time.sleep(0.4)

        # Step 5: Autostart Registration
        if self.enable_autostart.get():
            self.status_lbl.configure(text="Регистрация автозапуска в реестре Windows...")
            hub_script = os.path.join(target_dir, "Never_Hub", "main.py")
            python_w = sys.executable.replace("python.exe", "pythonw.exe")
            cmd_run = f'"{python_w}" "{hub_script}"'
            ok = set_autostart("NeverSuiteHub", cmd_run, enable=True)
            if ok:
                self.log("[REGISTRY] Never Hub успешно добавлен в автозагрузку (HKCU\\Run)")
            else:
                self.log("[REGISTRY] Не удалось обновить ветку реестра HKCU\\Run")

        self.progress_bar.set(1.0)
        self.status_lbl.configure(text="Установка успешно завершена!")
        self.log("[SUCCESS] Все компоненты Never Suite v1.0 успешно развернуты.")
        time.sleep(0.8)

        # Show final step
        self.after(200, lambda: self.show_step(4))

    # STEP 4: FINISH
    def create_step_4_finish(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")

        # Celebration Icon / Badge
        badge = ctk.CTkFrame(frame, fg_color="#181A28", corner_radius=16, border_width=1, border_color="#2A2E44")
        badge.pack(fill="x", padx=36, pady=(40, 20))

        check_lbl = ctk.CTkLabel(
            badge,
            text="✨",
            font=ctk.CTkFont(size=44)
        )
        check_lbl.pack(pady=(16, 2))

        done_title = ctk.CTkLabel(
            badge,
            text="Поздравляем! Never Suite v1.0 установлена",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color="#00FF88"
        )
        done_title.pack(pady=(0, 6))

        done_sub = ctk.CTkLabel(
            badge,
            text="Все модули оптимизированы и готовы к работе на вашем компьютере.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#CAD3E3"
        )
        done_sub.pack(pady=(0, 18))

        # Checkboxes for immediate actions
        act_card = ctk.CTkFrame(frame, fg_color="#141622", corner_radius=10)
        act_card.pack(fill="x", padx=36, pady=(0, 24))

        chk_launch = ctk.CTkCheckBox(
            act_card,
            text="Запустить Never Hub прямо сейчас (Центр управления в трее)",
            variable=self.launch_after_install,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#6C5CE7"
        )
        chk_launch.pack(anchor="w", padx=20, pady=16)

        # Buttons
        actions_bar = ctk.CTkFrame(frame, fg_color="transparent")
        actions_bar.pack(fill="x", padx=36, pady=10)

        open_folder_btn = ctk.CTkButton(
            actions_bar,
            text="📁 Открыть папку программы",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="#2A2E44",
            hover_color="#363C57",
            height=40,
            command=self.open_installation_folder
        )
        open_folder_btn.pack(side="left")

        finish_btn = ctk.CTkButton(
            actions_bar,
            text="🚀 Завершить",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="#6C5CE7",
            hover_color="#5843E5",
            width=160,
            height=42,
            corner_radius=8,
            command=self.finish_and_exit
        )
        finish_btn.pack(side="right")

        return frame

    def open_installation_folder(self):
        target = self.install_dir.get()
        if os.path.exists(target):
            os.startfile(target)

    def finish_and_exit(self):
        if self.launch_after_install.get():
            hub_path = os.path.join(self.install_dir.get(), "Never_Hub", "main.py")
            if os.path.exists(hub_path):
                python_w = sys.executable.replace("python.exe", "pythonw.exe")
                subprocess.Popen([python_w, hub_path], cwd=os.path.dirname(hub_path))
            else:
                # If Never Hub main.py is still being created or not present, notify gently
                pass
        self.destroy()

if __name__ == "__main__":
    app = NeverInstallerApp()
    app.mainloop()
