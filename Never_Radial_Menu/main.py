import os
import sys
import time
import math
import ctypes

# Защита от дубликатов (Single Instance Mutex)
_radial_mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Never_Radial_Mutex")
if ctypes.windll.kernel32.GetLastError() == 183:
    sys.exit(0)

import keyboard
import threading
import tkinter as tk
import customtkinter as ctk

ctk.set_appearance_mode("dark")

# Пути к приложениям пользователя
DESKTOP = os.path.expanduser(r"~\Desktop")
LOCALAPPDATA = os.environ.get("LOCALAPPDATA", "")
APPDATA = os.environ.get("APPDATA", "")

APPS = [
    {
        "name": "Браузер",
        "icon": "🌐",
        "desc": "Открыть Интернет",
        "color": "#38bdf8",
        "action": lambda: os.system("start https://www.google.com")
    },
    {
        "name": "Telegram",
        "icon": "💬",
        "desc": "Мессенджер",
        "color": "#22d3ee",
        "action": lambda: os.startfile(os.path.join(APPDATA, r"Telegram Desktop\Telegram.exe"))
    },
    {
        "name": "Файлы",
        "icon": "📁",
        "desc": "Хранилище файлов",
        "color": "#facc15",
        "action": lambda: os.startfile(os.path.join(DESKTOP, "Хранилище файлов"))
    },
    {
        "name": "PC Буст",
        "icon": "🚀",
        "desc": "Очистка и буст ПК",
        "color": "#ec4899",
        "action": lambda: os.startfile(os.path.join(DESKTOP, "PC Master & Booster.lnk"))
    },
    {
        "name": "VS Code",
        "icon": "💻",
        "desc": "Редактор кода",
        "color": "#a855f7",
        "action": lambda: os.startfile(os.path.join(LOCALAPPDATA, r"Programs\Microsoft VS Code\Code.exe"))
    },
    {
        "name": "Minecraft",
        "icon": "🎮",
        "desc": "Millida / MCModHub",
        "color": "#4ade80",
        "action": lambda: os.startfile(os.path.join(DESKTOP, "Millida Launcher.lnk"))
    }
]

class NeverRadialMenu(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Never Radial Menu")
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        self.TRANS_COLOR = "#000001"
        self.config(bg=self.TRANS_COLOR)
        self.attributes("-transparentcolor", self.TRANS_COLOR)

        self.size = 320
        self.center = self.size // 2
        self.outer_r = 145
        self.inner_r = 46

        self.active_index = -1
        self.is_visible = False

        # Холст для отрисовки футуристичного круга
        self.canvas = tk.Canvas(
            self,
            width=self.size,
            height=self.size,
            bg=self.TRANS_COLOR,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", self.on_click)
        self.bind("<Escape>", lambda e: self.hide_menu())
        self.bind("<FocusOut>", lambda e: self.hide_menu())

        self.withdraw()  # Скрыт по умолчанию

        # Слушатель глобальной горячей клавиши Alt + Q
        threading.Thread(target=self.hotkey_listener, daemon=True).start()

    def hotkey_listener(self):
        # Регистрация глобальной горячей клавиши Alt+Q
        try:
            keyboard.add_hotkey("alt+q", self.toggle_menu_safe)
            keyboard.wait()
        except Exception as e:
            print("Hotkey error:", e)

    def toggle_menu_safe(self):
        self.after(0, self.toggle_menu)

    def toggle_menu(self):
        if self.is_visible:
            self.hide_menu()
        else:
            self.show_menu()

    def show_menu(self):
        self.is_visible = True
        self.active_index = -1

        # Открываем прямо вокруг курсора мыши
        x = self.winfo_pointerx() - self.center
        y = self.winfo_pointery() - self.center

        # Проверка границ экрана
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(10, min(sw - self.size - 10, x))
        y = max(10, min(sh - self.size - 10, y))

        self.geometry(f"{self.size}x{self.size}+{x}+{y}")
        self.deiconify()
        self.lift()
        self.focus_force()
        self.draw_menu()

    def hide_menu(self):
        self.is_visible = False
        self.withdraw()

    def on_mouse_move(self, event):
        dx = event.x - self.center
        dy = event.y - self.center
        dist = math.hypot(dx, dy)

        if dist < self.inner_r or dist > self.outer_r + 15:
            new_idx = -1
        else:
            # Вычисление угла в градусах (0-360)
            angle = (math.degrees(math.atan2(dy, dx)) + 30) % 360
            new_idx = int(angle // 60)

        if new_idx != self.active_index:
            self.active_index = new_idx
            self.draw_menu()

    def on_click(self, event):
        dx = event.x - self.center
        dy = event.y - self.center
        dist = math.hypot(dx, dy)

        if dist < self.inner_r:
            # Клик по центру - закрыть
            self.hide_menu()
            return

        if 0 <= self.active_index < len(APPS):
            app = APPS[self.active_index]
            self.hide_menu()
            threading.Thread(target=app["action"], daemon=True).start()
        else:
            self.hide_menu()

    def draw_menu(self):
        self.delete_all = self.canvas.delete("all")
        cx = self.center
        cy = self.center

        # 6 секторов
        for i in range(6):
            app = APPS[i]
            is_active = (i == self.active_index)

            # Параметры сектора
            start_angle = (i * 60 - 30) % 360
            r_out = self.outer_r + (8 if is_active else 0)

            # Цвета
            fill_color = "#1e1e2f" if not is_active else app["color"]
            outline_color = "#38bdf8" if is_active else "#27273a"

            # Отрисовка дуги сектора
            self.canvas.create_arc(
                cx - r_out, cy - r_out, cx + r_out, cy + r_out,
                start=-start_angle - 60, extent=60,
                fill=fill_color, outline=outline_color, width=2 if not is_active else 3
            )

            # Позиция иконки (по центру сектора)
            mid_angle_deg = i * 60
            mid_angle_rad = math.radians(mid_angle_deg)
            r_label = (self.inner_r + self.outer_r) / 2 + (4 if is_active else 0)

            lx = cx + r_label * math.cos(mid_angle_rad)
            ly = cy + r_label * math.sin(mid_angle_rad)

            # Иконка
            text_color = "#0a0a0e" if is_active else "#f8fafc"
            self.canvas.create_text(
                lx, ly - 8,
                text=app["icon"],
                font=("Segoe UI Emoji", 16)
            )
            # Название
            self.canvas.create_text(
                lx, ly + 11,
                text=app["name"],
                font=("Segoe UI", 9, "bold" if is_active else "normal"),
                fill=text_color
            )

        # Внутренний центральный хаб (перекрывает центр)
        self.canvas.create_oval(
            cx - self.inner_r, cy - self.inner_r, cx + self.inner_r, cy + self.inner_r,
            fill="#0a0a0e", outline="#38bdf8" if self.active_index != -1 else "#27273a", width=2
        )

        # Текст в центре
        if 0 <= self.active_index < len(APPS):
            active_app = APPS[self.active_index]
            self.canvas.create_text(
                cx, cy - 6,
                text=active_app["icon"],
                font=("Segoe UI Emoji", 15)
            )
            self.canvas.create_text(
                cx, cy + 12,
                text=active_app["name"],
                font=("Segoe UI", 9, "bold"),
                fill=active_app["color"]
            )
        else:
            self.canvas.create_text(
                cx, cy - 6,
                text="⚡",
                font=("Segoe UI Emoji", 15),
                fill="#38bdf8"
            )
            self.canvas.create_text(
                cx, cy + 12,
                text="NEVER",
                font=("Segoe UI", 8, "bold"),
                fill="#94a3b8"
            )


if __name__ == "__main__":
    menu = NeverRadialMenu()
    menu.mainloop()
