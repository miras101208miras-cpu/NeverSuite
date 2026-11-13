import os
import re
import sys
import math
import time
import ctypes

# Защита от дубликатов (Single Instance Mutex)
_spot_mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Never_Spotlight_Mutex")
if ctypes.windll.kernel32.GetLastError() == 183:
    sys.exit(0)

import webbrowser
import urllib.parse
import keyboard
import threading
import tkinter as tk
import customtkinter as ctk

ctk.set_appearance_mode("dark")

DESKTOP = os.path.expanduser(r"~\Desktop")
LOCALAPPDATA = os.environ.get("LOCALAPPDATA", "")
APPDATA = os.environ.get("APPDATA", "")

RATES_TO_USD = {
    "usd": 1.0,
    "kzt": 0.0020,  # 1 USD ~ 500 KZT
    "rub": 0.0105,  # 1 USD ~ 95 RUB
    "eur": 1.08,    # 1 EUR ~ 1.08 USD
}

def silent_open_calc():
    ctypes.windll.shell32.ShellExecuteW(None, "open", "calc.exe", None, None, 1)

KNOWN_APPS = [
    {
        "keywords": ["mine", "minecraft", "майн", "майнкрафт", "миллида", "millida"],
        "title": "🎮 Запустить Minecraft (Millida Launcher)",
        "action": lambda: os.startfile(os.path.join(DESKTOP, "Millida Launcher.lnk"))
    },
    {
        "keywords": ["code", "vs", "vscode", "код", "студио"],
        "title": "💻 Запустить Visual Studio Code",
        "action": lambda: os.startfile(os.path.join(LOCALAPPDATA, r"Programs\Microsoft VS Code\Code.exe"))
    },
    {
        "keywords": ["tg", "tele", "telegram", "телега", "тг"],
        "title": "💬 Запустить Telegram Desktop",
        "action": lambda: os.startfile(os.path.join(APPDATA, r"Telegram Desktop\Telegram.exe"))
    },
    {
        "keywords": ["boost", "буст", "чистка", "master", "pc"],
        "title": "🚀 Запустить PC Master & Booster",
        "action": lambda: os.startfile(os.path.join(DESKTOP, "PC Master & Booster.lnk"))
    },
    {
        "keywords": ["island", "остров", "never"],
        "title": "🏝️ Запустить Never Island",
        "action": lambda: os.startfile(os.path.join(DESKTOP, "Never Island.lnk"))
    },
    {
        "keywords": ["файл", "файлы", "storage", "хранилище"],
        "title": "📁 Открыть Хранилище файлов",
        "action": lambda: os.startfile(os.path.join(DESKTOP, "Хранилище файлов"))
    },
    {
        "keywords": ["calc", "калькулятор"],
        "title": "🧮 Открыть калькулятор Windows",
        "action": silent_open_calc
    }
]

class NeverSpotlight(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Never Spotlight")
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        self.TRANS_COLOR = "#000001"
        self.config(bg=self.TRANS_COLOR)
        self.attributes("-transparentcolor", self.TRANS_COLOR)

        self.width = 640
        self.base_h = 68
        self.expanded_h = 175
        self.current_h = self.base_h
        self.is_visible = False
        self.pending_action = None

        self.screen_w = self.winfo_screenwidth()
        self.screen_h = self.winfo_screenheight()

        self.update_geometry()

        # Главная карточка
        self.card = ctk.CTkFrame(
            self,
            corner_radius=18,
            fg_color="#0d1117",
            border_width=2,
            border_color="#38bdf8"
        )
        self.card.pack(fill="both", expand=True, padx=4, pady=4)

        # Верхняя строка ввода
        self.input_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.input_frame.pack(fill="x", padx=16, pady=12)

        self.search_icon = ctk.CTkLabel(
            self.input_frame,
            text="⚡",
            font=ctk.CTkFont(size=20),
            text_color="#38bdf8"
        )
        self.search_icon.pack(side="left", padx=(0, 10))

        self.entry_var = tk.StringVar()
        self.entry_var.trace_add("write", self.on_text_change)

        self.entry = ctk.CTkEntry(
            self.input_frame,
            textvariable=self.entry_var,
            font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
            fg_color="transparent",
            border_width=0,
            text_color="#f8fafc",
            placeholder_text="Поиск, вычисления (150 * 45 / 2), yt lofi, валюты..."
        )
        self.entry.pack(side="left", fill="x", expand=True)

        self.badge_lbl = ctk.CTkLabel(
            self.input_frame,
            text="Enter ↵",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#64748b"
        )
        self.badge_lbl.pack(side="right")

        # Контейнер для результата / подсказок
        self.result_frame = ctk.CTkFrame(self.card, fg_color="#161b22", corner_radius=10)

        self.result_title = ctk.CTkLabel(
            self.result_frame,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color="#38bdf8",
            anchor="w"
        )
        self.result_title.pack(fill="x", padx=16, pady=(10, 2))

        self.result_subtitle = ctk.CTkLabel(
            self.result_frame,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#94a3b8",
            anchor="w"
        )
        self.result_subtitle.pack(fill="x", padx=16, pady=(0, 10))

        self.entry.bind("<Return>", self.on_enter)
        self.bind("<Escape>", lambda e: self.hide_spotlight())
        self.bind("<FocusOut>", self.on_focus_out)

        self.withdraw()

        # Слушатель глобального Alt + Space
        threading.Thread(target=self.hotkey_worker, daemon=True).start()

    def update_geometry(self):
        x = (self.screen_w - self.width) // 2
        y = (self.screen_h // 4)
        self.geometry(f"{self.width}x{self.current_h}+{x}+{y}")

    def hotkey_worker(self):
        try:
            keyboard.add_hotkey("alt+space", self.toggle_safe, suppress=True)
            keyboard.wait()
        except Exception as e:
            print("Hotkey error:", e)

    def toggle_safe(self):
        self.after(0, self.toggle_spotlight)

    def toggle_spotlight(self):
        if self.is_visible:
            self.hide_spotlight()
        else:
            self.show_spotlight()

    def show_spotlight(self):
        self.is_visible = True
        self.entry_var.set("")
        self.set_expanded(False)
        self.update_geometry()
        self.deiconify()
        self.lift()
        self.focus_force()
        self.entry.focus()

    def hide_spotlight(self):
        self.is_visible = False
        self.withdraw()

    def on_focus_out(self, event):
        self.after(120, lambda: self.hide_spotlight() if not self.focus_get() else None)

    def set_expanded(self, expanded):
        if expanded:
            self.current_h = self.expanded_h
            self.result_frame.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        else:
            self.current_h = self.base_h
            self.result_frame.pack_forget()
        self.update_geometry()

    def on_text_change(self, *args):
        query = self.entry_var.get().strip()
        if not query:
            self.set_expanded(False)
            self.pending_action = None
            return

        # 1. Поиск на YouTube (yt ...) - без консоли!
        if query.lower().startswith("yt "):
            yt_term = query[3:].strip()
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(yt_term)}"
            self.show_result(
                f"📺 Найти на YouTube: «{yt_term}»",
                "Нажмите Enter, чтобы открыть видео в браузере",
                action=lambda u=url: webbrowser.open(u)
            )
            return

        # 2. Конвертация валют
        curr_match = re.search(r"(\d+(?:\.\d+)?)\s*([a-zA-Zа-яА-Я]+)\s*(?:в|to|in)\s*([a-zA-Zа-яА-Я]+)", query, re.IGNORECASE)
        if curr_match:
            amount = float(curr_match.group(1))
            c_from = curr_match.group(2).lower()
            c_to = curr_match.group(3).lower()

            res = self.convert_currency(amount, c_from, c_to)
            if res:
                self.show_result(
                    f"💱 {amount:g} {c_from.upper()} = {res}",
                    "Нажмите Enter, чтобы скопировать результат в буфер",
                    action=lambda: self.copy_to_clip(str(res))
                )
                return

        # 3. Вычисления на лету (150 * 45 / 2, 2^8, sqrt)
        if re.search(r"[\d\+\-\*\/\^\(\)\%]", query) and not re.search(r"[a-zA-Zа-яА-Я]{3,}", query):
            try:
                clean_expr = query.replace("^", "**")
                res = eval(clean_expr, {"__builtins__": None, "math": math, "sqrt": math.sqrt, "pi": math.pi, "abs": abs, "round": round})
                if isinstance(res, (int, float)):
                    val_str = f"{res:g}" if isinstance(res, float) else f"{res:,}"
                    self.show_result(
                        f"🧮 Результат: = {val_str}",
                        "Нажмите Enter, чтобы скопировать число в буфер",
                        action=lambda: self.copy_to_clip(val_str)
                    )
                    return
            except Exception:
                pass

        # 4. Запуск приложений
        q_lower = query.lower()
        matched_app = None
        for app in KNOWN_APPS:
            for kw in app["keywords"]:
                if kw in q_lower:
                    matched_app = app
                    break
            if matched_app:
                break

        if matched_app:
            self.show_result(
                matched_app["title"],
                "Нажмите Enter для быстрого запуска",
                action=matched_app["action"]
            )
            return

        # 5. Поиск в Google по умолчанию - без консоли!
        g_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        self.show_result(
            f"🔍 Искать в Google: «{query}»",
            "Нажмите Enter для поиска в Интернете",
            action=lambda u=g_url: webbrowser.open(u)
        )

    def convert_currency(self, amount, f, t):
        norm = {
            "кзт": "kzt", "тенге": "kzt", "тг": "kzt", "kzt": "kzt",
            "usd": "usd", "доллар": "usd", "долларов": "usd", "бакс": "usd", "баксов": "usd", "$": "usd",
            "rub": "rub", "руб": "rub", "рублей": "rub", "р": "rub",
            "eur": "eur", "евро": "eur", "€": "eur"
        }
        f_norm = norm.get(f)
        t_norm = norm.get(t)

        if f_norm and t_norm and f_norm in RATES_TO_USD and t_norm in RATES_TO_USD:
            usd_val = amount * RATES_TO_USD[f_norm]
            res_val = usd_val / RATES_TO_USD[t_norm]
            return f"{res_val:,.2f} {t_norm.upper()}"
        return None

    def show_result(self, title, subtitle, action):
        self.result_title.configure(text=title)
        self.result_subtitle.configure(text=subtitle)
        self.pending_action = action
        self.set_expanded(True)

    def on_enter(self, event=None):
        if self.pending_action:
            action = self.pending_action
            self.hide_spotlight()
            threading.Thread(target=action, daemon=True).start()

    def copy_to_clip(self, val):
        self.clipboard_clear()
        self.clipboard_append(val)


if __name__ == "__main__":
    spotlight = NeverSpotlight()
    spotlight.mainloop()
