import os
import sys
import time
import math
import random
import ctypes
from ctypes import wintypes

# Single Instance Mutex
_sakura_mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Never_Sakura_Mutex")
if ctypes.windll.kernel32.GetLastError() == 183:
    sys.exit(0)

import threading
import tkinter as tk
import keyboard

PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)
import never_focus

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

class NeverAtmosphereApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Never Atmosphere FX")
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        self.TRANS_COLOR = "#000001"
        self.config(bg=self.TRANS_COLOR)
        self.attributes("-transparentcolor", self.TRANS_COLOR)

        self.screen_w = self.winfo_screenwidth()
        self.screen_h = self.winfo_screenheight()
        self.geometry(f"{self.screen_w}x{self.screen_h}+0+0")

        # Режим атмосферы: "sakura", "matrix", "off"
        self.mode = "sakura"

        # Focus mode tracking
        self.focus_active = False
        self.focus_check_tick = 0

        # Zen focus petal palette (soft pastels)
        self._ZEN_COLORS = ["#dde7f7", "#c7d9f4", "#b8d4f9", "#cce4f0", "#d8eeff", "#e2f0fb", "#b8d8ea"]
        self._NORMAL_COLORS = ["#fbcfe8", "#f472b6", "#fda4af", "#fb7185", "#f9a8d4", "#ffe4e6"]

        self.canvas = tk.Canvas(
            self,
            width=self.screen_w,
            height=self.screen_h,
            bg=self.TRANS_COLOR,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Применяем Win32 флаги: WS_EX_TRANSPARENT | WS_EX_LAYERED
        # Окно становится 100% прозрачным для кликов мыши (клик-сквозным!)
        self.update_idletasks()
        hwnd = self.winfo_id()
        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x00080000
        WS_EX_TRANSPARENT = 0x00000020
        old_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, old_style | WS_EX_LAYERED | WS_EX_TRANSPARENT)

        # 1. Инициализация лепестков сакуры
        self.init_sakura_petals(count=45)

        # 2. Инициализация дождя Матрицы
        self.init_matrix_columns()

        # Глобальный хоткей: Alt + S переключает режим (Сакура -> Матрица -> Выкл)
        self.setup_hotkey()

        self.animate_loop()

    def setup_hotkey(self):
        def on_toggle():
            if self.mode == "sakura":
                self.mode = "matrix"
            elif self.mode == "matrix":
                self.mode = "off"
            else:
                self.mode = "sakura"
        
        try:
            keyboard.add_hotkey("alt+s", on_toggle)
        except Exception:
            pass

    # =============================================================
    # РЕЖИМ 1: ПАДАЮЩАЯ САКУРА
    # =============================================================
    def init_sakura_petals(self, count=45):
        self.petals = []
        colors = ["#fbcfe8", "#f472b6", "#fda4af", "#fb7185", "#f9a8d4", "#ffe4e6"]
        for _ in range(count):
            self.petals.append({
                "x": random.uniform(0, self.screen_w),
                "y": random.uniform(-self.screen_h, 0),
                "vx": 0.0,
                "vy": random.uniform(1.2, 2.4),
                "size": random.uniform(7, 14),
                "angle": random.uniform(0, math.pi * 2),
                "spin_speed": random.uniform(0.02, 0.06) * random.choice([-1, 1]),
                "flip_phase": random.uniform(0, math.pi * 2),
                "flip_speed": random.uniform(0.03, 0.07),
                "color": random.choice(colors),
                "sway_phase": random.uniform(0, math.pi * 2)
            })

    # =============================================================
    # РЕЖИМ 2: ДОЖДЬ МАТРИЦЫ
    # =============================================================
    def init_matrix_columns(self):
        self.matrix_cols = []
        col_width = 24
        num_cols = self.screen_w // col_width
        matrix_chars = "0123456789ABCDEF$#@%&*+-~<>ｦｱｳｴｵｶｷｹｺｻｼｽｾｿﾀﾂﾃﾅﾆﾇﾈﾊﾋﾎﾏﾐﾑﾒﾓﾔﾕﾗﾘﾜ"

        for i in range(num_cols):
            self.matrix_cols.append({
                "x": i * col_width + 12,
                "y": random.uniform(-self.screen_h, 0),
                "speed": random.uniform(4.0, 9.5),
                "length": random.randint(8, 18),
                "chars": [random.choice(matrix_chars) for _ in range(20)],
                "update_tick": 0
            })

    def animate_loop(self):
        self.canvas.delete("all")

        # Poll focus state every ~90 frames
        self.focus_check_tick += 1
        if self.focus_check_tick >= 90:
            self.focus_check_tick = 0
            try:
                st = never_focus.read_state()
                if st.get("active"):
                    rem = st.get("end_timestamp", 0) - time.time()
                    self.focus_active = rem > 0 or st.get("paused", False)
                else:
                    self.focus_active = False
            except Exception:
                self.focus_active = False

        if self.mode != "off":
            # Получаем координаты курсора мыши
            pt = POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            mx, my = pt.x, pt.y

            if self.mode == "sakura":
                self.update_and_draw_sakura(mx, my)
            elif self.mode == "matrix":
                self.update_and_draw_matrix(mx, my)

        self.after(35, self.animate_loop)

    def update_and_draw_sakura(self, mx, my):
        t = time.time()

        # Focus mode: zen palette + slower falling + reduced repulsion
        if self.focus_active:
            petal_colors = self._ZEN_COLORS
            speed_mult = 0.45          # 45% of normal speed — very slow & gentle
            repel_range = 60           # smaller repulsion zone (less distraction)
            repel_str = 2.5            # gentler burst
            wind_str = 0.5             # calm breeze only
            outline_col = ""           # no outline in focus (subtle)
        else:
            petal_colors = self._NORMAL_COLORS
            speed_mult = 1.0
            repel_range = 120
            repel_str = 6.5
            wind_str = 1.4
            outline_col = "#f43f5e"

        for p in self.petals:
            # Движение вниз и покачивание ветром
            p["sway_phase"] += 0.04 * speed_mult
            wind = math.sin(p["sway_phase"]) * wind_str + (0.4 if self.focus_active else 0.8)

            p["x"] += p["vx"] + wind
            p["y"] += p["vy"] * speed_mult

            # Затухание отталкивания от курсора
            p["vx"] *= 0.92

            # Вращение лепестка в 3D (flip & spin)
            p["angle"] += p["spin_speed"] * speed_mult
            p["flip_phase"] += p["flip_speed"] * speed_mult

            # In focus mode, gradually transition petal colors to zen palette
            if self.focus_active:
                p["color"] = random.choice(petal_colors) if random.random() < 0.003 else p["color"]

            # ИНТЕРАКТИВ С КУРСОРОМ МЫШИ (Разлетаются от мыши!)
            dx = p["x"] - mx
            dy = p["y"] - my
            dist = math.hypot(dx, dy)
            if dist < repel_range and dist > 1:
                repel = (repel_range - dist) / repel_range * repel_str
                p["vx"] += (dx / dist) * repel
                p["y"] += (dy / dist) * (repel * 0.6)

            # Перенос наверх экрана при падении за границу
            if p["y"] > self.screen_h + 20:
                p["y"] = -25
                p["x"] = random.uniform(0, self.screen_w)
                p["vx"] = 0
                # Assign fresh color based on current focus state
                p["color"] = random.choice(petal_colors)
            if p["x"] < -30:
                p["x"] = self.screen_w + 20
            elif p["x"] > self.screen_w + 30:
                p["x"] = -20

            # Отрисовка 3D-лепестка сакуры
            sz = p["size"]
            scale_y = math.sin(p["flip_phase"])  # эффект вращения в пространстве
            ang = p["angle"]

            # Координаты вершин овального лепестка с поворотом
            w_r = sz * 0.55
            h_r = sz * scale_y

            # 4 точки лепестка сакуры (каплевидная форма)
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)

            points = [
                (p["x"] - w_r * cos_a, p["y"] - w_r * sin_a),
                (p["x"] + h_r * sin_a, p["y"] - h_r * cos_a),
                (p["x"] + w_r * cos_a, p["y"] + w_r * sin_a),
                (p["x"] - h_r * sin_a, p["y"] + h_r * cos_a)
            ]
            poly_coords = []
            for px, py in points:
                poly_coords.extend([px, py])

            oc = outline_col if sz > 11 and not self.focus_active else ""
            self.canvas.create_polygon(poly_coords, fill=p["color"], outline=oc, width=1)

    def update_and_draw_matrix(self, mx, my):
        matrix_chars = "0123456789ABCDEF$#@%&*+-~<>ｦｱｳｴｵｶｷｹｺｻｼｽｾｿﾀﾂﾃﾅﾆﾇﾈﾊﾋﾎﾏﾐﾑﾒﾓﾔﾕﾗﾘﾜ"

        for col in self.matrix_cols:
            col["y"] += col["speed"]
            col["update_tick"] += 1

            if col["update_tick"] % 4 == 0:
                # Случайная смена символов
                col["chars"][random.randint(0, len(col["chars"]) - 1)] = random.choice(matrix_chars)

            # Интерактив с курсором мыши: если курсор рядом с колонкой, символы разлетаются
            dist_x = abs(col["x"] - mx)
            push_x = 0
            if dist_x < 90 and abs(col["y"] - my) < 140:
                push_x = (col["x"] - mx) * 0.45

            # Перезапуск колонки сверху
            if col["y"] - (col["length"] * 18) > self.screen_h:
                col["y"] = random.uniform(-150, 0)
                col["speed"] = random.uniform(4.0, 9.5)

            # Отрисовка символов колонки
            cx = col["x"] + push_x
            for i in range(col["length"]):
                char_y = col["y"] - (i * 18)
                if 0 <= char_y <= self.screen_h:
                    ch = col["chars"][i % len(col["chars"])]
                    if i == 0:
                        # Голова луча (яркий белый / неоновый салатовый)
                        fill_c = "#ffffff"
                        f_sz = 11
                    elif i < 3:
                        fill_c = "#86efac"
                        f_sz = 10
                    elif i < 8:
                        fill_c = "#22c55e"
                        f_sz = 9
                    else:
                        fill_c = "#15803d"
                        f_sz = 8

                    self.canvas.create_text(
                        cx, char_y,
                        text=ch,
                        fill=fill_c,
                        font=("Consolas", f_sz, "bold" if i < 2 else "normal")
                    )

if __name__ == "__main__":
    app = NeverAtmosphereApp()
    app.mainloop()
