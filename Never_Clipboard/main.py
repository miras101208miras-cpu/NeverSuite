import os
import sys
import time
import random
import string
import ctypes

# Защита от дубликатов (Single Instance Mutex)
_clip_mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Never_Clipboard_Mutex")
if ctypes.windll.kernel32.GetLastError() == 183:
    sys.exit(0)

import keyboard
import threading
import tkinter as tk
import customtkinter as ctk

ctk.set_appearance_mode("dark")

class NeverClipboard(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Never Clipboard")
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        self.TRANS_COLOR = "#000001"
        self.config(bg=self.TRANS_COLOR)
        self.attributes("-transparentcolor", self.TRANS_COLOR)

        self.width = 420
        self.height = 460
        self.is_visible = False

        self.screen_w = self.winfo_screenwidth()
        self.screen_h = self.winfo_screenheight()

        # История буфера (максимум 35 элементов)
        self.history = []
        self.last_clipboard = ""

        # Главная карточка
        self.card = ctk.CTkFrame(
            self,
            corner_radius=18,
            fg_color="#0e111a",
            border_width=2,
            border_color="#38bdf8"
        )
        self.card.pack(fill="both", expand=True, padx=4, pady=4)

        # Шапка
        self.header = ctk.CTkFrame(self.card, fg_color="transparent")
        self.header.pack(fill="x", padx=16, pady=(12, 6))

        self.title_lbl = ctk.CTkLabel(
            self.header,
            text="📋 Never Clipboard",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#38bdf8"
        )
        self.title_lbl.pack(side="left")

        self.close_btn = ctk.CTkButton(
            self.header,
            text="✕",
            width=26,
            height=26,
            fg_color="#1e1e2f",
            hover_color="#ef4444",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.hide_clipboard
        )
        self.close_btn.pack(side="right")

        # Поиск по истории
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_history)

        self.search_entry = ctk.CTkEntry(
            self.card,
            textvariable=self.search_var,
            font=ctk.CTkFont(size=12),
            fg_color="#181c27",
            border_color="#2b3347",
            placeholder_text="🔍 Поиск по скопированному..."
        )
        self.search_entry.pack(fill="x", padx=14, pady=(0, 8))

        # Список карточек истории
        self.scroll_list = ctk.CTkScrollableFrame(
            self.card,
            fg_color="#121622",
            corner_radius=10
        )
        self.scroll_list.pack(fill="both", expand=True, padx=14, pady=(0, 8))

        # Нижняя панель с доп. функциями
        self.footer = ctk.CTkFrame(self.card, fg_color="transparent")
        self.footer.pack(fill="x", padx=14, pady=(0, 12))

        self.gen_pwd_btn = ctk.CTkButton(
            self.footer,
            text="🔑 Сгенерировать пароль",
            height=28,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#7c3aed",
            hover_color="#6d28d9",
            command=self.generate_password
        )
        self.gen_pwd_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.clear_btn = ctk.CTkButton(
            self.footer,
            text="🧹 Очистить",
            height=28,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#334155",
            hover_color="#475569",
            command=self.clear_history
        )
        self.clear_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))

        self.bind("<Escape>", lambda e: self.hide_clipboard())
        self.bind("<FocusOut>", self.on_focus_out)

        self.withdraw()

        # Фоновый мониторинг буфера обмена Windows
        threading.Thread(target=self.clipboard_monitor_loop, daemon=True).start()

        # Слушатель горячей клавиши Alt + C
        threading.Thread(target=self.hotkey_worker, daemon=True).start()

    def hotkey_worker(self):
        try:
            keyboard.add_hotkey("alt+c", self.toggle_safe, suppress=True)
            keyboard.wait()
        except Exception as e:
            print("Clipboard hotkey error:", e)

    def toggle_safe(self):
        self.after(0, self.toggle_clipboard)

    def toggle_clipboard(self):
        if self.is_visible:
            self.hide_clipboard()
        else:
            self.show_clipboard()

    def show_clipboard(self):
        self.is_visible = True
        self.search_var.set("")
        self.render_history()

        # Позиционирование возле курсора или по правому краю
        x = min(self.screen_w - self.width - 20, max(20, self.winfo_pointerx() - self.width // 2))
        y = min(self.screen_h - self.height - 50, max(40, self.winfo_pointery() - 60))

        self.geometry(f"{self.width}x{self.height}+{x}+{y}")
        self.deiconify()
        self.lift()
        self.focus_force()
        self.search_entry.focus()

    def hide_clipboard(self):
        self.is_visible = False
        self.withdraw()

    def on_focus_out(self, event):
        self.after(120, lambda: self.hide_clipboard() if not self.focus_get() else None)

    def clipboard_monitor_loop(self):
        while True:
            try:
                # Читаем буфер
                text = self.clipboard_get()
                if text and text != self.last_clipboard and text.strip():
                    self.last_clipboard = text
                    self.add_to_history(text.strip())
            except Exception:
                pass
            time.sleep(0.4)

    def add_to_history(self, text):
        # Удаляем дубликат, если уже есть
        self.history = [item for item in self.history if item["text"] != text]

        # Тип содержимого
        icon = "📝"
        if text.startswith("http://") or text.startswith("https://"):
            icon = "🔗"
        elif any(c in text for c in ["{", "}", "def ", "class ", "function", "const ", "import "]):
            icon = "💻"
        elif text.startswith("#") and len(text) in (4, 7, 9):
            icon = "🎨"

        self.history.insert(0, {
            "text": text,
            "time": time.strftime("%H:%M"),
            "icon": icon
        })

        # Ограничение до 35 записей
        if len(self.history) > 35:
            self.history.pop()

        if self.is_visible:
            self.after(0, self.render_history)

    def filter_history(self, *args):
        self.render_history(query=self.search_var.get().strip().lower())

    def render_history(self, query=""):
        # Очистка старых виджетов списка
        for widget in self.scroll_list.winfo_children():
            widget.destroy()

        filtered = [item for item in self.history if query in item["text"].lower()] if query else self.history

        if not filtered:
            empty_lbl = ctk.CTkLabel(
                self.scroll_list,
                text="Буфер пуст или ничего не найдено\nСкопируйте любой текст (Ctrl+C)",
                font=ctk.CTkFont(size=12),
                text_color="#64748b"
            )
            empty_lbl.pack(pady=40)
            return

        for item in filtered:
            raw_text = item["text"]
            preview = raw_text.replace("\n", " ")
            if len(preview) > 55:
                preview = preview[:55] + "..."

            card = ctk.CTkFrame(self.scroll_list, fg_color="#181c27", corner_radius=8)
            card.pack(fill="x", pady=3)

            icon_lbl = ctk.CTkLabel(card, text=item["icon"], font=ctk.CTkFont(size=14))
            icon_lbl.pack(side="left", padx=(10, 6), pady=8)

            txt_btn = ctk.CTkButton(
                card,
                text=preview,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color="#cbd5e1",
                fg_color="transparent",
                hover_color="#2b3347",
                anchor="w",
                command=lambda t=raw_text: self.paste_text(t)
            )
            txt_btn.pack(side="left", fill="x", expand=True, padx=2)

            time_lbl = ctk.CTkLabel(card, text=item["time"], font=ctk.CTkFont(size=10), text_color="#64748b")
            time_lbl.pack(side="right", padx=(4, 10))

    def paste_text(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.last_clipboard = text
        self.hide_clipboard()

    def generate_password(self):
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        pwd = "".join(random.choice(chars) for _ in range(16))
        self.clipboard_clear()
        self.clipboard_append(pwd)
        self.last_clipboard = pwd
        self.add_to_history(pwd)
        self.hide_clipboard()

    def clear_history(self):
        self.history.clear()
        self.render_history()


if __name__ == "__main__":
    clip = NeverClipboard()
    clip.mainloop()
