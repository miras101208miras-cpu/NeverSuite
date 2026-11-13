import os
import sys
import time
import random
import json
import ctypes
import ctypes.wintypes
import subprocess
import threading
import tkinter as tk
import customtkinter as ctk
from PIL import ImageGrab

# Защита от дубликатов (Single Instance Mutex)
_island_mutex = None

def ensure_single_instance():
    global _island_mutex
    _island_mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Never_Island_Mutex")
    if ctypes.windll.kernel32.GetLastError() == 183:
        sys.exit(0)

PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)
import never_focus

# ⚡ Never Drop integration
NEVER_DROP_DIR = os.path.join(PARENT_DIR, "Never_Drop")
if NEVER_DROP_DIR not in sys.path:
    sys.path.insert(0, NEVER_DROP_DIR)

try:
    import windnd as _windnd_island
    _HAS_WINDND_ISLAND = True
except ImportError:
    _HAS_WINDND_ISLAND = False

def _island_share_file(file_path):
    """Launch Never Drop to share a file. Called from drag-drop or button."""
    never_drop_script = os.path.join(NEVER_DROP_DIR, "never_drop.py")
    if not os.path.exists(never_drop_script):
        return
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    exe = pythonw if os.path.exists(pythonw) else sys.executable
    subprocess.Popen([exe, never_drop_script, file_path])

try:
    import keyboard
except Exception:
    keyboard = None

try:
    from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
    speakers = AudioUtilities.GetSpeakers()
    volume_endpoint = speakers.EndpointVolume
except Exception:
    volume_endpoint = None

ctk.set_appearance_mode("dark")

# =====================================================================
# ЦВЕТОВЫЕ ТЕМЫ (THEME PRESETS)
# =====================================================================
THEMES = {
    "cyberpunk": {
        "id": "cyberpunk",
        "name": "⚡ Cyberpunk 2077",
        "accent": "#00f0ff",
        "accent_hover": "#0284c7",
        "secondary": "#facc15",
        "bg_main": "#0a0a0f",
        "bg_card": "#12121c",
        "border": "#1e1e2f",
        "text": "#f8fafc",
        "text_dim": "#64748b",
        "play_btn": "#7c3aed",
        "play_hover": "#6d28d9",
        "eq_colors": ["#00f0ff", "#38bdf8", "#60a5fa", "#818cf8", "#a855f7", "#c084fc", "#facc15", "#f43f5e"]
    },
    "sakura": {
        "id": "sakura",
        "name": "🌸 Tokyo Sakura Lo-Fi",
        "accent": "#f472b6",
        "accent_hover": "#ec4899",
        "secondary": "#fb7185",
        "bg_main": "#140e17",
        "bg_card": "#1e1422",
        "border": "#3b1e36",
        "text": "#ffe4e6",
        "text_dim": "#a87898",
        "play_btn": "#db2777",
        "play_hover": "#be185d",
        "eq_colors": ["#f472b6", "#fb7185", "#f43f5e", "#fda4af", "#f472b6", "#e879f9", "#c084fc", "#fb7185"]
    },
    "deep_space": {
        "id": "deep_space",
        "name": "🌌 Deep Space Minimal",
        "accent": "#38bdf8",
        "accent_hover": "#0ea5e9",
        "secondary": "#94a3b8",
        "bg_main": "#0a0e17",
        "bg_card": "#111827",
        "border": "#1f2937",
        "text": "#f8fafc",
        "text_dim": "#64748b",
        "play_btn": "#2563eb",
        "play_hover": "#1d4ed8",
        "eq_colors": ["#38bdf8", "#60a5fa", "#818cf8", "#94a3b8", "#cbd5e1", "#38bdf8", "#0284c7", "#60a5fa"]
    }
}


class MarqueeLabel(ctk.CTkLabel):
    """Текстовая метка с плавной бегущей строкой для длинных названий треков."""
    def __init__(self, master, text="", max_len=22, step_ms=280, **kwargs):
        super().__init__(master, text=text, **kwargs)
        self.full_text = text
        self.max_len = max_len
        self.step_ms = step_ms
        self.offset = 0
        self.is_animating = False
        self._update_display()

    def set_marquee_text(self, text):
        if text != self.full_text:
            self.full_text = text
            self.offset = 0
            self._update_display()

    def _update_display(self):
        txt = self.full_text
        if len(txt) <= self.max_len:
            self.configure(text=txt)
            self.is_animating = False
        else:
            spacer = "   •   "
            padded = txt + spacer
            idx = self.offset % len(padded)
            display = (padded + padded)[idx : idx + self.max_len]
            self.configure(text=display)
            self.offset += 1
            if not self.is_animating:
                self.is_animating = True
                self.after(self.step_ms, self._step)

    def _step(self):
        if self.is_animating and len(self.full_text) > self.max_len:
            self._update_display()
            self.after(self.step_ms, self._step)
        else:
            self.is_animating = False


class MusicVisualizer(tk.Canvas):
    """Стильный анимированный эквалайзер музыки в раскрытом режиме (Cava / Linux)."""
    def __init__(self, parent, bg_color="#12121c", num_bars=8, bar_w=5, bar_spacing=3, max_h=24, colors=None, **kwargs):
        width = num_bars * bar_w + (num_bars - 1) * bar_spacing + 4
        super().__init__(parent, bg=bg_color, highlightthickness=0, width=width, height=max_h + 4, **kwargs)
        self.num_bars = num_bars
        self.bar_w = bar_w
        self.bar_spacing = bar_spacing
        self.max_h = max_h
        self.is_playing = False
        self.peak_level = 0.0
        self.heights = [3] * self.num_bars
        self.colors = colors or ["#00f0ff", "#38bdf8", "#60a5fa", "#818cf8", "#a855f7", "#c084fc", "#facc15", "#f43f5e"]
        self.animate_loop()

    def set_playing(self, playing, peak=0.0):
        self.is_playing = playing
        self.peak_level = peak

    def update_theme(self, bg_color, colors):
        self.config(bg=bg_color)
        self.colors = colors

    def animate_loop(self):
        self.delete("all")
        cx = 2
        for i in range(self.num_bars):
            if self.is_playing:
                scale = max(0.25, min(1.0, self.peak_level * 2.5))
                wave_bias = 0.5 + 0.5 * random.random()
                target_h = int(random.randint(5, self.max_h) * (scale * 0.7 + wave_bias * 0.3))
                target_h = max(3, min(self.max_h, target_h))
                self.heights[i] = int(self.heights[i] * 0.35 + target_h * 0.65)
            else:
                self.heights[i] = max(2, int(self.heights[i] * 0.65))

            h = self.heights[i]
            y1 = (self.max_h + 2) - h
            y2 = self.max_h + 2
            x1 = cx
            x2 = cx + self.bar_w

            color = self.colors[i % len(self.colors)]
            self.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
            cx += self.bar_w + self.bar_spacing

        delay = 45 if self.is_playing else 120
        self.after(delay, self.animate_loop)


class CompactMusicVisualizer(tk.Canvas):
    """Мини-эквалайзер для компактного режима Dynamic Island (звуковые волны)."""
    def __init__(self, parent, bg_color="#0a0a0e", **kwargs):
        super().__init__(parent, bg=bg_color, highlightthickness=0, width=30, height=18, **kwargs)
        self.num_bars = 5
        self.bar_w = 4
        self.bar_spacing = 2
        self.max_h = 16
        self.is_playing = False
        self.peak_level = 0.0
        self.heights = [2] * self.num_bars
        self.colors = ["#00f0ff", "#38bdf8", "#818cf8", "#c084fc", "#f43f5e"]
        self.animate_loop()

    def set_playing(self, playing, peak=0.0):
        self.is_playing = playing
        self.peak_level = peak

    def update_theme(self, bg_color, colors):
        self.config(bg=bg_color)
        self.colors = colors[:self.num_bars] if len(colors) >= self.num_bars else colors

    def animate_loop(self):
        self.delete("all")
        cx = 1
        for i in range(self.num_bars):
            if self.is_playing:
                target_h = random.randint(3, self.max_h)
                self.heights[i] = int(self.heights[i] * 0.4 + target_h * 0.6)
            else:
                self.heights[i] = max(2, int(self.heights[i] * 0.7))

            h = self.heights[i]
            y1 = 17 - h
            y2 = 17
            x1 = cx
            x2 = cx + self.bar_w

            color = self.colors[i % len(self.colors)]
            self.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
            cx += self.bar_w + self.bar_spacing

        delay = 50 if self.is_playing else 150
        self.after(delay, self.animate_loop)


class ScreenTextExtractorOverlay(tk.Toplevel):
    """Интерактивное выделение области экрана для распознавания текста (OCR)."""
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.attributes("-fullscreen", True)
        self.attributes("-alpha", 0.28)
        self.attributes("-topmost", True)
        self.config(bg="#000000", cursor="cross")

        self.canvas = tk.Canvas(self, bg="#000000", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.start_x = None
        self.start_y = None
        self.rect = None

        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Escape>", lambda e: self.destroy())

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="#00f0ff", width=2)

    def on_drag(self, event):
        if self.rect:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        x1 = min(self.start_x, event.x)
        y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x)
        y2 = max(self.start_y, event.y)
        self.destroy()

        if (x2 - x1) > 8 and (y2 - y1) > 8:
            self.callback((x1, y1, x2, y2))


class AIEyesCanvas(tk.Canvas):
    """Интерактивные анимированные ИИ-глазки, которые моргают и следят за курсором мыши."""
    def __init__(self, parent, bg_color="#0a0a0e", eye_color="#00f0ff", **kwargs):
        super().__init__(parent, bg=bg_color, highlightthickness=0, width=64, height=32, **kwargs)
        self.bg_color = bg_color
        self.eye_color = eye_color

        self.eye_w = 10
        self.eye_h = 15
        self.center_x = 32
        self.left_cx = 20
        self.right_cx = 44
        self.cy = 16

        self.offset_x = 0
        self.offset_y = 0
        self.blink_scale = 1.0
        self.is_blinking = False
        self.is_happy = False

        self.draw_eyes()
        self.schedule_next_blink()

    def update_theme(self, bg_color, eye_color):
        self.bg_color = bg_color
        self.eye_color = eye_color
        self.config(bg=bg_color)
        self.draw_eyes()

    def draw_eyes(self):
        self.delete("all")
        cur_h = max(2, int(self.eye_h * self.blink_scale))
        dx = self.offset_x
        dy = self.offset_y
        color = self.eye_color if not self.is_happy else "#38bdf8"

        if self.is_happy and self.blink_scale > 0.5:
            self.create_arc(
                self.left_cx - self.eye_w + dx, self.cy - cur_h//2 + dy,
                self.left_cx + self.eye_w + dx, self.cy + cur_h//2 + dy,
                start=0, extent=180, style="arc", width=3, outline=color
            )
            self.create_arc(
                self.right_cx - self.eye_w + dx, self.cy - cur_h//2 + dy,
                self.right_cx + self.eye_w + dx, self.cy + cur_h//2 + dy,
                start=0, extent=180, style="arc", width=3, outline=color
            )
        else:
            self.create_oval(
                self.left_cx - self.eye_w//2 + dx, self.cy - cur_h//2 + dy,
                self.left_cx + self.eye_w//2 + dx, self.cy + cur_h//2 + dy,
                fill=color, outline=""
            )
            self.create_oval(
                self.right_cx - self.eye_w//2 + dx, self.cy - cur_h//2 + dy,
                self.right_cx + self.eye_w//2 + dx, self.cy + cur_h//2 + dy,
                fill=color, outline=""
            )
            if self.blink_scale > 0.6:
                glow_r = 2
                self.create_oval(
                    self.left_cx + dx - 1, self.cy + dy - cur_h//4 - 1,
                    self.left_cx + dx + glow_r, self.cy + dy - cur_h//4 + glow_r,
                    fill="#ffffff", outline=""
                )
                self.create_oval(
                    self.right_cx + dx - 1, self.cy + dy - cur_h//4 - 1,
                    self.right_cx + dx + glow_r, self.cy + dy - cur_h//4 + glow_r,
                    fill="#ffffff", outline=""
                )

    def schedule_next_blink(self):
        delay_ms = random.randint(2200, 4800)
        self.after(delay_ms, self.trigger_blink)

    def trigger_blink(self):
        if self.is_blinking:
            return
        self.is_blinking = True

        def blink_anim(step=0):
            stages = [0.7, 0.2, 0.1, 0.5, 1.0]
            if step < len(stages):
                self.blink_scale = stages[step]
                self.draw_eyes()
                self.after(25, lambda: blink_anim(step + 1))
            else:
                self.blink_scale = 1.0
                self.is_blinking = False
                self.draw_eyes()
                self.schedule_next_blink()

        blink_anim()

    def update_look_at(self, screen_x, screen_y, my_win_x, my_win_y):
        vx = screen_x - (my_win_x + self.center_x + 10)
        vy = screen_y - (my_win_y + self.cy)
        self.offset_x = max(-4, min(4, int(vx / 140)))
        self.offset_y = max(-3, min(3, int(vy / 110)))
        if not self.is_blinking:
            self.draw_eyes()

    def set_happy(self, happy=True):
        self.is_happy = happy
        self.draw_eyes()


class NeverIsland(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("⚡ Never Island")
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        self.TRANS_COLOR = "#000001"
        self.config(bg=self.TRANS_COLOR)
        self.attributes("-transparentcolor", self.TRANS_COLOR)

        self.screen_width = self.winfo_screenwidth()

        # Размеры
        self.w_compact = 240
        self.w_compact_music = 330
        self.h_compact = 38
        self.y_top = 10

        self.w_expanded = 520
        self.h_expanded = 330

        self.current_w = self.w_compact
        self.current_h = self.h_compact
        self.is_expanded = False

        # Состояние медиаплеера
        self.media_is_playing = False
        self.current_track = "Нет активного трека"
        self.current_artist = "Ожидание музыки..."
        self.current_source = "Windows SMTC"
        self.peak_level = 0.0
        self.last_theme_mtime = 0
        self.active_theme_id = "cyberpunk"
        self.theme = THEMES["cyberpunk"]

        self.update_geometry()

        # Главный контейнер
        self.island_frame = ctk.CTkFrame(
            self,
            corner_radius=19,
            fg_color=self.theme["bg_main"],
            border_width=1,
            border_color=self.theme["border"]
        )
        self.island_frame.pack(fill="both", expand=True)

        # ========================================================
        # 1. КОМПАКТНЫЙ РЕЖИМ (ГЛАЗКИ + ЗВУКОВЫЕ ВОЛНЫ + ЧАСЫ + ФОКУС)
        # ========================================================
        self.compact_box = ctk.CTkFrame(self.island_frame, fg_color="transparent")
        self.compact_box.pack(fill="both", expand=True, padx=8, pady=0)

        self.ai_eyes = AIEyesCanvas(self.compact_box, bg_color=self.theme["bg_main"], eye_color=self.theme["accent"])
        self.ai_eyes.pack(side="left", padx=(6, 2), pady=3)

        # Мини звуковые волны / эквалайзер в компактном режиме
        self.compact_visualizer = CompactMusicVisualizer(self.compact_box, bg_color=self.theme["bg_main"])

        # Бегущая строка трека в компактном режиме
        self.compact_media_lbl = MarqueeLabel(
            self.compact_box,
            text="",
            max_len=14,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=self.theme["accent"]
        )

        self.compact_time = ctk.CTkLabel(
            self.compact_box,
            text="12:00",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#f8fafc"
        )
        self.compact_time.pack(side="right", padx=(0, 8), pady=3)

        self.compact_focus_lbl = ctk.CTkLabel(
            self.compact_box,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#f43f5e"
        )

        self.compact_focus_btn = ctk.CTkButton(
            self.compact_box,
            text="🍅",
            width=26,
            height=24,
            corner_radius=12,
            fg_color="#181824",
            hover_color="#2b1a29",
            font=ctk.CTkFont(size=12),
            command=self.quick_toggle_focus
        )
        self.compact_focus_btn.pack(side="right", padx=(0, 4), pady=3)

        # ========================================================
        # 2. РАСКРЫТЫЙ РЕЖИМ (ФОКУС + МУЗЫКА + ЗВУК + ИНСТРУМЕНТЫ)
        # ========================================================
        self.expanded_box = ctk.CTkFrame(self.island_frame, fg_color="transparent")

        # Хедер
        self.exp_header = ctk.CTkFrame(self.expanded_box, fg_color="transparent")
        self.exp_header.pack(fill="x", padx=14, pady=(8, 2))

        self.exp_title = ctk.CTkLabel(
            self.exp_header,
            text="✨ Never Island Studio",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.theme["accent"]
        )
        self.exp_title.pack(side="left")

        self.exp_focus_badge = ctk.CTkLabel(
            self.exp_header,
            text="🍅 ФОКУС",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#64748b"
        )
        self.exp_focus_badge.pack(side="left", padx=(12, 0))

        self.exp_clock = ctk.CTkLabel(
            self.exp_header,
            text="12:00:00",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#94a3b8"
        )
        self.exp_clock.pack(side="right")

        # ----------------------------------------------------
        # СЕКЦИЯ: NEVER FOCUS / POMODORO РЕЖИМ
        # ----------------------------------------------------
        self.focus_panel = ctk.CTkFrame(
            self.expanded_box,
            fg_color=self.theme["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=self.theme["border"]
        )
        self.focus_panel.pack(fill="x", padx=12, pady=(2, 4))

        self.focus_row1 = ctk.CTkFrame(self.focus_panel, fg_color="transparent")
        self.focus_row1.pack(fill="x", padx=8, pady=(4, 2))

        self.focus_status_lbl = ctk.CTkLabel(
            self.focus_row1,
            text="🍅 Режим Фокуса (Pomodoro)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#f43f5e"
        )
        self.focus_status_lbl.pack(side="left")

        self.focus_timer_lbl = ctk.CTkLabel(
            self.focus_row1,
            text="25:00",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#f8fafc"
        )
        self.focus_timer_lbl.pack(side="left", padx=(10, 0))

        # Кнопки управления фокусом
        self.btn_focus_main = ctk.CTkButton(
            self.focus_row1, text="▶ 25м Фокус", width=84, height=24,
            fg_color="#e11d48", hover_color="#be123c", font=ctk.CTkFont(size=11, weight="bold"),
            command=self.focus_start_work
        )
        self.btn_focus_break = ctk.CTkButton(
            self.focus_row1, text="☕ 5м Отдых", width=74, height=24,
            fg_color="#0284c7", hover_color="#0369a1", font=ctk.CTkFont(size=11),
            command=self.focus_start_break
        )
        self.btn_focus_break.pack(side="right", padx=2)
        self.btn_focus_main.pack(side="right", padx=2)

        self.btn_focus_pause = ctk.CTkButton(
            self.focus_row1, text="⏸", width=34, height=24,
            fg_color="#334155", hover_color="#475569", font=ctk.CTkFont(size=11, weight="bold"),
            command=self.focus_toggle_pause
        )
        self.btn_focus_stop = ctk.CTkButton(
            self.focus_row1, text="⏹", width=34, height=24,
            fg_color="#1e293b", hover_color="#334155", font=ctk.CTkFont(size=11),
            command=self.focus_stop
        )

        # Строка прогресс-бара
        self.focus_row2 = ctk.CTkFrame(self.focus_panel, fg_color="transparent")
        self.focus_row2.pack(fill="x", padx=8, pady=(0, 4))

        self.focus_progressbar = ctk.CTkProgressBar(
            self.focus_row2,
            height=6,
            progress_color="#f43f5e",
            fg_color="#1e1e2d"
        )
        self.focus_progressbar.pack(side="left", fill="x", expand=True, padx=(2, 6))
        self.focus_progressbar.set(0.0)

        self.focus_pct_lbl = ctk.CTkLabel(
            self.focus_row2,
            text="0%",
            font=ctk.CTkFont(size=10),
            text_color="#64748b",
            width=30
        )
        self.focus_pct_lbl.pack(side="right", padx=(0, 2))

        # Основной контент: 2 колонки
        self.body_frame = ctk.CTkFrame(self.expanded_box, fg_color="transparent")
        self.body_frame.pack(fill="both", expand=True, padx=12, pady=4)

        # ----------------------------------------------------
        # ЛЕВАЯ КОЛОНКА: СИНХРОНИЗИРОВАННЫЙ МЕДИАПЛЕЕР SMTC
        # ----------------------------------------------------
        self.left_col = ctk.CTkFrame(self.body_frame, fg_color=self.theme["bg_card"], corner_radius=10)
        self.left_col.pack(side="left", fill="both", expand=True, padx=(0, 6), pady=2)

        # Шапка плеера с анимированным эквалайзером
        self.music_hdr = ctk.CTkFrame(self.left_col, fg_color="transparent")
        self.music_hdr.pack(fill="x", padx=10, pady=(6, 2))

        self.music_title = ctk.CTkLabel(
            self.music_hdr,
            text="🎵 МЕДИАПЛЕЕР",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.theme["accent"]
        )
        self.music_title.pack(side="left")

        # Эквалайзер волн музыки в стиле Linux/Cava
        self.visualizer = MusicVisualizer(self.music_hdr, bg_color=self.theme["bg_card"], colors=self.theme["eq_colors"])
        self.visualizer.pack(side="right", padx=(0, 2))

        # Название трека (с поддержкой бегущей строки Marquee)
        self.exp_track_title = MarqueeLabel(
            self.left_col,
            text="🎵 Нет активного трека",
            max_len=24,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=self.theme["text"],
            anchor="w"
        )
        self.exp_track_title.pack(fill="x", padx=10, pady=(2, 0))

        # Имя исполнителя
        self.exp_artist_lbl = ctk.CTkLabel(
            self.left_col,
            text="🎤 Ожидание воспроизведения...",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.theme["text_dim"],
            anchor="w"
        )
        self.exp_artist_lbl.pack(fill="x", padx=10, pady=(0, 4))

        # Кнопки управления треками (0xB1: Prev, 0xB3: Play/Pause, 0xB0: Next)
        self.media_btn_row = ctk.CTkFrame(self.left_col, fg_color="transparent")
        self.media_btn_row.pack(fill="x", padx=8, pady=(0, 4))

        self.btn_prev = ctk.CTkButton(
            self.media_btn_row, text="⏮", width=34, height=26,
            fg_color="#1e1e2f", hover_color="#27273f", font=ctk.CTkFont(size=12),
            command=self.media_prev
        )
        self.btn_prev.pack(side="left", padx=2, fill="x", expand=True)

        self.btn_play = ctk.CTkButton(
            self.media_btn_row, text="▶", width=42, height=26,
            fg_color=self.theme["play_btn"], hover_color=self.theme["play_hover"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.media_play_pause
        )
        self.btn_play.pack(side="left", padx=2, fill="x", expand=True)

        self.btn_next = ctk.CTkButton(
            self.media_btn_row, text="⏭", width=34, height=26,
            fg_color="#1e1e2f", hover_color="#27273f", font=ctk.CTkFont(size=12),
            command=self.media_next
        )
        self.btn_next.pack(side="left", padx=2, fill="x", expand=True)

        # Блок Громкости
        self.vol_header = ctk.CTkFrame(self.left_col, fg_color="transparent")
        self.vol_header.pack(fill="x", padx=10, pady=(2, 0))

        self.vol_title = ctk.CTkLabel(
            self.vol_header,
            text="🔊 Громкость:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.theme["accent"]
        )
        self.vol_title.pack(side="left")

        self.vol_val_lbl = ctk.CTkLabel(self.vol_header, text="70%", font=ctk.CTkFont(size=11), text_color="#cbd5e1")
        self.vol_val_lbl.pack(side="right")

        init_vol = 70
        if volume_endpoint:
            try:
                init_vol = int(round(volume_endpoint.GetMasterVolumeLevelScalar() * 100))
                self.vol_val_lbl.configure(text=f"{init_vol}%")
            except Exception:
                pass

        self.vol_slider = ctk.CTkSlider(
            self.left_col,
            from_=0, to=100,
            number_of_steps=100,
            height=11,
            progress_color=self.theme["accent"],
            button_color=self.theme["accent_hover"],
            command=self.set_volume
        )
        self.vol_slider.pack(fill="x", padx=10, pady=(2, 4))
        self.vol_slider.set(init_vol)

        # Источник медиа
        self.music_status = ctk.CTkLabel(
            self.left_col,
            text="Windows SMTC • Live",
            font=ctk.CTkFont(size=9),
            text_color=self.theme["text_dim"]
        )
        self.music_status.pack(anchor="w", padx=10, pady=(0, 4))

        # ----------------------------------------------------
        # ПРАВАЯ КОЛОНКА: 6 ИНСТРУМЕНТОВ
        # ----------------------------------------------------
        self.right_col = ctk.CTkFrame(self.body_frame, fg_color=self.theme["bg_card"], corner_radius=10)
        self.right_col.pack(side="right", fill="both", expand=True, padx=(6, 0), pady=2)

        self.tools_title = ctk.CTkLabel(
            self.right_col,
            text="🛠️ Инструменты",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.theme["accent"]
        )
        self.tools_title.pack(anchor="w", padx=10, pady=(6, 2))

        # 1. Весь экран (Режим F11)
        self.btn_t1 = ctk.CTkButton(
            self.right_col, text="🖥️ 1. Весь экран (F11)", height=22, font=ctk.CTkFont(size=11),
            fg_color="#1e1e2f", hover_color="#2d2d47", anchor="w",
            command=self.tool_f11_fullscreen
        )
        self.btn_t1.pack(fill="x", padx=8, pady=1)

        # 2. Скриншот
        self.btn_t2 = ctk.CTkButton(
            self.right_col, text="✂️ 2. Скриншот", height=22, font=ctk.CTkFont(size=11),
            fg_color="#1e1e2f", hover_color="#2d2d47", anchor="w",
            command=self.tool_snip
        )
        self.btn_t2.pack(fill="x", padx=8, pady=1)

        # 3. Текст с экрана (OCR)
        self.btn_t3 = ctk.CTkButton(
            self.right_col, text="🔍 3. Текст с экрана (OCR)", height=22, font=ctk.CTkFont(size=11),
            fg_color="#1e1e2f", hover_color="#2d2d47", anchor="w",
            command=self.tool_screen_text_ocr
        )
        self.btn_t3.pack(fill="x", padx=8, pady=1)

        # 4. Чистый текст
        self.btn_t4 = ctk.CTkButton(
            self.right_col, text="📝 4. Чистый текст", height=22, font=ctk.CTkFont(size=11),
            fg_color="#1e1e2f", hover_color="#2d2d47", anchor="w",
            command=self.tool_clean_text
        )
        self.btn_t4.pack(fill="x", padx=8, pady=1)

        # 5. Запись экрана
        self.btn_t5 = ctk.CTkButton(
            self.right_col, text="🎥 5. Запись экрана", height=22, font=ctk.CTkFont(size=11),
            fg_color="#1e1e2f", hover_color="#2d2d47", anchor="w",
            command=self.tool_record_screen
        )
        self.btn_t5.pack(fill="x", padx=8, pady=1)

        # 6. Never Drop — AirDrop for PC
        self.btn_t6 = ctk.CTkButton(
            self.right_col, text="⚡ 6. Never Drop", height=22, font=ctk.CTkFont(size=11),
            fg_color="#0f172a", hover_color="#1e293b", anchor="w",
            text_color="#00f0ff",
            command=self.tool_never_drop
        )
        self.btn_t6.pack(fill="x", padx=8, pady=(1, 4))

        # Статус-бар
        self.status_bar = ctk.CTkLabel(
            self.expanded_box,
            text="Never Island готов к работе",
            font=ctk.CTkFont(size=10),
            text_color="#64748b"
        )
        self.status_bar.pack(side="bottom", pady=(0, 4))

        # События мыши
        self.bind("<Enter>", self.on_hover_enter)
        self.bind("<Leave>", self.on_hover_leave)
        self.island_frame.bind("<Enter>", self.on_hover_enter)
        self.island_frame.bind("<Leave>", self.on_hover_leave)

        self.bind("<Button-3>", self.start_drag)
        self.bind("<B3-Motion>", self.do_drag)

        # ⚡ Never Drop: Windows Drag & Drop hook on Island window
        if _HAS_WINDND_ISLAND:
            try:
                _windnd_island.hook_dropfiles(self, func=self._on_files_dropped_to_island, force_unicode=True)
            except Exception:
                pass

        # Глобальный хоткей Pomodoro (Ctrl+Alt+F)
        if keyboard:
            try:
                keyboard.add_hotkey("ctrl+alt+f", lambda: self.after(0, self.quick_toggle_focus))
            except Exception:
                pass

        self.is_running = True

        # Фоновые потоки: часы/фокус и опрос медиа SMTC
        self.mon_thread = threading.Thread(target=self.system_loop, daemon=True)
        self.mon_thread.start()

        self.media_thread = threading.Thread(target=self.media_poll_loop, daemon=True)
        self.media_thread.start()

        self.theme_thread = threading.Thread(target=self.theme_poll_loop, daemon=True)
        self.theme_thread.start()

        self.tracking_loop()

    # ========================================================
    # ТЕМАТИЧЕСКИЙ ДВИЖОК (THEME ENGINE)
    # ========================================================
    def theme_poll_loop(self):
        """Периодическая проверка never_theme.json и адаптация цветовой палитры."""
        theme_path = os.path.join(PARENT_DIR, "never_theme.json")
        while self.is_running:
            try:
                if os.path.exists(theme_path):
                    mtime = os.path.getmtime(theme_path)
                    if mtime != self.last_theme_mtime:
                        self.last_theme_mtime = mtime
                        with open(theme_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        self.after(0, self.apply_theme_data, data)
            except Exception:
                pass
            time.sleep(1.5)

    def apply_theme_data(self, data):
        """Применить тему из файла конфигурации never_theme.json."""
        target_id = None
        theme_str = ""
        if isinstance(data, dict):
            theme_str = str(data.get("theme", "") or data.get("name", "") or data.get("preset", "")).lower()
        elif isinstance(data, str):
            theme_str = data.lower()

        if any(k in theme_str for k in ["sakura", "сакура", "токио", "pink"]):
            target_id = "sakura"
        elif any(k in theme_str for k in ["space", "космос", "deep", "minimal", "graphite"]):
            target_id = "deep_space"
        elif any(k in theme_str for k in ["cyber", "кибер", "2077", "yellow", "cyan"]):
            target_id = "cyberpunk"

        if target_id and target_id in THEMES:
            self.set_theme(target_id)

    def set_theme(self, theme_id):
        if theme_id not in THEMES:
            return
        self.active_theme_id = theme_id
        t = THEMES[theme_id]
        self.theme = t

        # Обновление контейнера
        self.island_frame.configure(fg_color=t["bg_main"], border_color=t["border"])
        self.ai_eyes.update_theme(t["bg_main"], t["accent"])
        self.compact_visualizer.update_theme(t["bg_main"], t["eq_colors"])
        self.compact_media_lbl.configure(text_color=t["accent"])

        # Обновление раскрытого окна
        self.exp_title.configure(text_color=t["accent"])
        self.focus_panel.configure(fg_color=t["bg_card"], border_color=t["border"])
        self.left_col.configure(fg_color=t["bg_card"])
        self.right_col.configure(fg_color=t["bg_card"])
        self.music_title.configure(text_color=t["accent"])
        self.visualizer.update_theme(t["bg_card"], t["eq_colors"])
        self.exp_track_title.configure(text_color=t["text"])
        self.exp_artist_lbl.configure(text_color=t["text_dim"])
        self.music_status.configure(text_color=t["text_dim"])
        self.vol_title.configure(text_color=t["accent"])
        self.vol_slider.configure(progress_color=t["accent"], button_color=t["accent_hover"])
        self.tools_title.configure(text_color=t["accent"])
        self.btn_play.configure(fg_color=t["play_btn"], hover_color=t["play_hover"])

    # ========================================================
    # СИНХРОНИЗАЦИЯ SMTC И АУДИО ОПРОС
    # ========================================================
    def media_poll_loop(self):
        """Фоновый цикл проверки Windows SMTC, громкости сессий и плееров."""
        # PowerShell скрипт запроса WinRT SMTC
        ps_cmd = """
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
Function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(1200) | Out-Null
    $netTask.Result
}
try {
    [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager, Windows.Media, ContentType=WindowsRuntime] | Out-Null
    $mgr = Await ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync()) ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager])
    if ($mgr) {
        $s = $mgr.GetCurrentSession()
        if ($s) {
            $p = Await ($s.TryGetMediaPropertiesAsync()) ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionMediaProperties])
            $info = $s.GetPlaybackInfo()
            Write-Output ("TITLE=" + $p.Title)
            Write-Output ("ARTIST=" + $p.Artist)
            Write-Output ("STATUS=" + $info.PlaybackStatus)
            Write-Output ("SOURCE=" + $s.SourceAppUserModelId)
        } else {
            Write-Output "NO_SESSION"
        }
    }
} catch {
    Write-Output "ERROR"
}
"""
        smtc_counter = 0

        while self.is_running:
            peak = 0.0
            active_proc = ""

            # 1. Быстрый опрос пиковой громкости через pycaw
            try:
                for session in AudioUtilities.GetAllSessions():
                    proc = session.Process
                    meter = session._ctl.QueryInterface(IAudioMeterInformation)
                    p = meter.GetPeakValue()
                    if p > peak:
                        peak = p
                        if proc:
                            active_proc = proc.name()
            except Exception:
                pass

            self.peak_level = peak

            # 2. Опрос SMTC каждые ~2.5 секунды
            smtc_counter += 1
            if smtc_counter >= 8:
                smtc_counter = 0
                title = ""
                artist = ""
                status_str = ""
                source_str = ""

                try:
                    proc = subprocess.run(
                        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                        capture_output=True,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        timeout=2.0
                    )
                    out = proc.stdout.strip().splitlines()
                    for line in out:
                        if line.startswith("TITLE="):
                            title = line.split("=", 1)[1].strip()
                        elif line.startswith("ARTIST="):
                            artist = line.split("=", 1)[1].strip()
                        elif line.startswith("STATUS="):
                            status_str = line.split("=", 1)[1].strip()
                        elif line.startswith("SOURCE="):
                            source_str = line.split("=", 1)[1].strip()
                except Exception:
                    pass

                # Fallback: проверка заголовков окон Spotify / Chrome / Браузеров
                if not title and not artist:
                    title, artist, detected_status = self._fallback_detect_media(active_proc)
                    if detected_status:
                        status_str = detected_status

                # Определение состояния воспроизведения
                is_playing = False
                if status_str in ("Playing", "4") or (status_str == "" and peak > 0.005):
                    is_playing = True
                elif status_str in ("Paused", "3", "Stopped", "Closed"):
                    is_playing = False
                elif peak > 0.003:
                    is_playing = True

                self.after(0, self.update_media_state, title, artist, source_str, is_playing, peak)

            else:
                # Обновление уровня эквалайзера в реальном времени
                self.after(0, self.update_peak_only, peak)

            time.sleep(0.3)

    def _fallback_detect_media(self, active_proc):
        """Поиск названия трека из заголовка окна Spotify или браузера."""
        title = ""
        artist = ""
        status = ""
        titles_found = []

        def enum_cb(hwnd, lparam):
            if ctypes.windll.user32.IsWindowVisible(hwnd):
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                    titles_found.append(buf.value)
            return True

        EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
        try:
            ctypes.windll.user32.EnumWindows(EnumProc(enum_cb), 0)
        except Exception:
            pass

        for t in titles_found:
            # Spotify: когда играет, заголовок окна: 'Artist - Track'
            if " - " in t and not any(k in t.lower() for k in ["spotify free", "spotify premium", "visual studio", "powershell"]):
                if "spotify" in active_proc.lower() or "chrome" in active_proc.lower() or "firefox" in active_proc.lower():
                    parts = t.split(" - ", 1)
                    artist = parts[0].strip()
                    title = parts[1].replace(" - YouTube", "").replace(" - Google Chrome", "").strip()
                    status = "Playing"
                    break

        if not title and active_proc:
            clean_name = active_proc.replace(".exe", "").capitalize()
            if self.peak_level > 0.003:
                title = "Аудиопоток активен"
                artist = f"Источник: {clean_name}"
                status = "Playing"

        return title, artist, status

    def update_peak_only(self, peak):
        """Быстрое обновление уровня для визулизатора."""
        self.visualizer.set_playing(self.media_is_playing, peak)
        self.compact_visualizer.set_playing(self.media_is_playing, peak)

    def update_media_state(self, title, artist, source, is_playing, peak):
        """Обновить UI с новыми метаданными трека."""
        self.peak_level = peak
        prev_playing = self.media_is_playing
        self.media_is_playing = is_playing

        if title:
            self.current_track = title
        elif not is_playing:
            self.current_track = "Нет активного трека"

        if artist:
            self.current_artist = artist
        elif not is_playing:
            self.current_artist = "Ожидание воспроизведения..."

        if source:
            src_clean = source.split("!")[-1] if "!" in source else source
            self.current_source = src_clean
            self.music_status.configure(text=f"{self.current_source} • Live")

        # Обновление меток в раскрытом режиме
        self.exp_track_title.set_marquee_text(f"🎵 {self.current_track}")
        self.exp_artist_lbl.configure(text=f"🎤 {self.current_artist}")
        self.btn_play.configure(text="⏸" if is_playing else "▶")

        # Передача состояния в эквалайзеры
        self.visualizer.set_playing(is_playing, peak)
        self.compact_visualizer.set_playing(is_playing, peak)

        # Компактный режим: отображение звуковых волн и трека
        if is_playing:
            self.compact_media_lbl.set_marquee_text(f"🎵 {self.current_track}")
            if not self.compact_visualizer.winfo_ismapped():
                self.compact_visualizer.pack(side="left", padx=(2, 4), pady=3)
                self.compact_media_lbl.pack(side="left", padx=(2, 6), pady=3)
                if not self.is_expanded:
                    self.animate_resize(self.w_compact_music, self.h_compact)
        else:
            if self.compact_visualizer.winfo_ismapped():
                self.compact_visualizer.pack_forget()
                self.compact_media_lbl.pack_forget()
                if not self.is_expanded:
                    self.animate_resize(self.w_compact, self.h_compact)

    # --------------------------------------------------------
    # УПРАВЛЕНИЕ МУЗЫКОЙ И ЗВУКОМ
    # --------------------------------------------------------
    def media_prev(self):
        """⏮ Предыдущий трек (VK_MEDIA_PREV_TRACK = 0xB1)."""
        ctypes.windll.user32.keybd_event(0xB1, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0xB1, 0, 2, 0)
        self.set_status("⏮ Предыдущий трек")

    def media_play_pause(self):
        """⏯ Воспроизведение / Пауза (VK_MEDIA_PLAY_PAUSE = 0xB3)."""
        ctypes.windll.user32.keybd_event(0xB3, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0xB3, 0, 2, 0)
        self.media_is_playing = not self.media_is_playing
        self.visualizer.set_playing(self.media_is_playing, self.peak_level)
        self.compact_visualizer.set_playing(self.media_is_playing, self.peak_level)
        self.btn_play.configure(text="⏸" if self.media_is_playing else "▶")
        txt = "▶ Воспроизведение (Эквалайзер включен)" if self.media_is_playing else "⏸ Музыка на паузе"
        self.set_status(txt)

    def media_next(self):
        """⏭ Следующий трек (VK_MEDIA_NEXT_TRACK = 0xB0)."""
        ctypes.windll.user32.keybd_event(0xB0, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0xB0, 0, 2, 0)
        self.set_status("⏭ Следующий трек")

    def set_volume(self, val):
        pct = int(val)
        self.vol_val_lbl.configure(text=f"{pct}%")
        if volume_endpoint:
            try:
                volume_endpoint.SetMasterVolumeLevelScalar(val / 100.0, None)
            except Exception:
                pass

    def set_status(self, text):
        self.status_bar.configure(text=text, text_color=self.theme["accent"])
        self.after(3500, lambda: self.status_bar.configure(text="Never Island готов к работе", text_color="#64748b"))

    # ========================================================
    # УПРАВЛЕНИЕ ГЕОМЕТРИЕЙ И АНИМАЦИИ
    # ========================================================
    def update_geometry(self):
        x = (self.screen_width - self.current_w) // 2
        self.geometry(f"{self.current_w}x{self.current_h}+{x}+{self.y_top}")

    def tracking_loop(self):
        try:
            if not self.is_expanded:
                px = self.winfo_pointerx()
                py = self.winfo_pointery()
                wx = self.winfo_x()
                wy = self.winfo_y()
                self.ai_eyes.update_look_at(px, py, wx, wy)
        except Exception:
            pass
        self.after(35, self.tracking_loop)

    def on_hover_enter(self, event=None):
        if not self.is_expanded:
            self.ai_eyes.set_happy(True)
            self.expand_island()

    def on_hover_leave(self, event=None):
        self.after(400, self.check_leave_mouse)

    def check_leave_mouse(self):
        x, y = self.winfo_pointerx(), self.winfo_pointery()
        win_x = self.winfo_x()
        win_y = self.winfo_y()
        if not (win_x <= x <= win_x + self.current_w and win_y <= y <= win_y + self.current_h):
            if self.is_expanded:
                self.ai_eyes.set_happy(False)
                self.collapse_island()

    def expand_island(self):
        self.is_expanded = True
        self.compact_box.pack_forget()
        self.animate_resize(self.w_expanded, self.h_expanded, callback=self.show_expanded_content)

    def collapse_island(self):
        self.is_expanded = False
        self.expanded_box.pack_forget()
        target_w = self.w_compact_music if self.media_is_playing else self.w_compact
        self.animate_resize(target_w, self.h_compact, callback=self.show_compact_content)

    def show_expanded_content(self):
        self.island_frame.configure(corner_radius=22)
        self.expanded_box.pack(fill="both", expand=True)

    def show_compact_content(self):
        self.island_frame.configure(corner_radius=19)
        self.compact_box.pack(fill="both", expand=True, padx=8, pady=0)

    def animate_resize(self, target_w, target_h, callback=None):
        steps = 6
        dw = (target_w - self.current_w) / steps
        dh = (target_h - self.current_h) / steps

        def step(i=0):
            if i < steps:
                self.current_w += int(dw)
                self.current_h += int(dh)
                self.update_geometry()
                self.after(14, lambda: step(i + 1))
            else:
                self.current_w = target_w
                self.current_h = target_h
                self.update_geometry()
                if callback:
                    callback()

        step()

    def system_loop(self):
        while self.is_running:
            try:
                now_str = time.strftime("%H:%M")
                sec_str = time.strftime("%H:%M:%S")
                self.after(0, self.update_time, now_str, sec_str)
                self.after(0, self.update_focus_tick)
            except Exception:
                pass
            time.sleep(0.5)

    def update_time(self, now_str, sec_str):
        self.compact_time.configure(text=now_str)
        if self.is_expanded:
            self.exp_clock.configure(text=sec_str)

    # --------------------------------------------------------
    # УПРАВЛЕНИЕ ФОКУСОМ (POMODORO)
    # --------------------------------------------------------
    def focus_start_work(self):
        never_focus.start_session(25, "work")
        self.set_status("🍅 Режим фокуса запущен! 25 минут продуктивности.")

    def focus_start_break(self):
        never_focus.start_session(5, "break")
        self.set_status("☕ Перерыв запущен! 5 минут отдыха.")

    def focus_toggle_pause(self):
        st = never_focus.read_state()
        if st.get("active"):
            if st.get("paused"):
                never_focus.resume_session()
                self.set_status("▶ Фокус возобновлен.")
            else:
                never_focus.pause_session()
                self.set_status("⏸ Фокус поставлен на паузу.")

    def focus_stop(self):
        never_focus.stop_session()
        self.set_status("⏹ Режим фокуса остановлен.")

    def quick_toggle_focus(self):
        st = never_focus.read_state()
        if not st.get("active"):
            self.focus_start_work()
        elif st.get("paused"):
            never_focus.resume_session()
            self.set_status("▶ Фокус возобновлен.")
        else:
            self.focus_toggle_pause()

    def update_focus_tick(self):
        try:
            st = never_focus.read_state()
            if st.get("active"):
                if not st.get("paused"):
                    rem = st.get("end_timestamp", 0) - time.time()
                    if rem <= 0:
                        new_st = never_focus.complete_session()
                        if new_st.get("mode") == "break":
                            self.set_status("🔔 Фокус завершен! Начат перерыв на 5 минут ☕")
                        else:
                            self.set_status("🔔 Перерыв завершен! Отличная работа! ✨")
                        return
                else:
                    rem = st.get("remaining_seconds", 0)

                total_sec = max(1, st.get("duration_mins", 25) * 60)
                elapsed_sec = max(0, total_sec - rem)
                pct = max(0.0, min(1.0, elapsed_sec / total_sec))
                rem_str = never_focus.format_time(rem)
                mode = st.get("mode", "work")
                icon = "🍅" if mode == "work" else "☕"
                color = "#f43f5e" if mode == "work" else "#38bdf8"
                paused_tag = " ⏸" if st.get("paused") else ""

                # Компактный режим
                self.compact_focus_lbl.configure(text=f"{icon} {rem_str}{paused_tag}", text_color=color)
                if not self.compact_focus_lbl.winfo_ismapped():
                    self.compact_focus_lbl.pack(side="right", padx=(0, 6), pady=3)

                # Раскрытый режим
                mode_name = "ФОКУС" if mode == "work" else "ОТДЫХ"
                self.exp_focus_badge.configure(text=f"{icon} {mode_name}: {rem_str}", text_color=color)
                self.focus_status_lbl.configure(text=f"{icon} Режим {mode_name} ({int(st.get('duration_mins', 25))}м)", text_color=color)
                self.focus_timer_lbl.configure(text=f"{rem_str}{paused_tag}")

                self.btn_focus_main.pack_forget()
                self.btn_focus_break.pack_forget()

                self.btn_focus_pause.configure(text="▶" if st.get("paused") else "⏸")
                if not self.btn_focus_pause.winfo_ismapped():
                    self.btn_focus_stop.pack(side="right", padx=2)
                    self.btn_focus_pause.pack(side="right", padx=2)

                self.focus_progressbar.set(pct)
                self.focus_progressbar.configure(progress_color=color)
                self.focus_pct_lbl.configure(text=f"{int(pct * 100)}%")

            else:
                # Неактивен
                if self.compact_focus_lbl.winfo_ismapped():
                    self.compact_focus_lbl.pack_forget()

                self.exp_focus_badge.configure(text="🍅 ФОКУС (Ctrl+Alt+F)", text_color="#64748b")
                self.focus_status_lbl.configure(text="🍅 Режим Фокуса (Pomodoro)", text_color="#f43f5e")
                self.focus_timer_lbl.configure(text="25:00")

                self.btn_focus_pause.pack_forget()
                self.btn_focus_stop.pack_forget()

                if not self.btn_focus_main.winfo_ismapped():
                    self.btn_focus_break.pack(side="right", padx=2)
                    self.btn_focus_main.pack(side="right", padx=2)

                self.focus_progressbar.set(0.0)
                self.focus_pct_lbl.configure(text="0%")
        except Exception:
            pass

    # --------------------------------------------------------
    # 6 ИНСТРУМЕНТОВ
    # --------------------------------------------------------
    def tool_f11_fullscreen(self):
        """1. Весь экран: эмуляция F11 (развернуть/свернуть окно на весь экран)."""
        def trigger():
            time.sleep(0.15)
            ctypes.windll.user32.keybd_event(0x7A, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0x7A, 0, 2, 0)
        threading.Thread(target=trigger, daemon=True).start()
        self.set_status("🖥️ Режим F11: весь экран переключен!")

    def tool_snip(self):
        """2. Скриншот: запуск ножниц области."""
        ctypes.windll.shell32.ShellExecuteW(None, "open", "ms-screenclip:", None, None, 1)
        self.set_status("✂ Выделите область для скриншота...")

    def tool_screen_text_ocr(self):
        """3. Текст с экрана: интерактивное выделение и распознавание текста (OCR)."""
        self.set_status("🔍 Выделите прямоугольником текст на экране...")
        self.collapse_island()

        def on_region_selected(bbox):
            self.set_status("⏳ Распознавание текста...")
            threading.Thread(target=self._process_ocr, args=(bbox,), daemon=True).start()

        ScreenTextExtractorOverlay(on_region_selected)

    def _process_ocr(self, bbox):
        try:
            shot = ImageGrab.grab(bbox=bbox)
            temp_img = os.path.join(os.environ.get('TEMP', '.'), 'ocr_capture.png')
            shot.save(temp_img)

            ps_cmd = f"""
            [Windows.Media.Ocr.OcrEngine, Windows.Media.Ocr, ContentType = WindowsRuntime] | Out-Null
            [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType = WindowsRuntime] | Out-Null
            [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime] | Out-Null
            $file = [Windows.Storage.StorageFile]::GetFileFromPathAsync('{temp_img}').GetAwaiter().GetResult()
            $stream = $file.OpenAsync([Windows.Storage.FileAccessMode]::Read).GetAwaiter().GetResult()
            $decoder = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream).GetAwaiter().GetResult()
            $bitmap = $decoder.GetSoftwareBitmapAsync().GetAwaiter().GetResult()
            $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
            $res = $engine.RecognizeAsync($bitmap).GetAwaiter().GetResult()
            $res.Text
            """
            proc = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            recognized_text = proc.stdout.strip()

            if recognized_text:
                self.clipboard_clear()
                self.clipboard_append(recognized_text)
                preview = (recognized_text[:30] + '...') if len(recognized_text) > 30 else recognized_text
                self.after(0, lambda: self.set_status(f"✔ Текст скопирован: «{preview}»"))
            else:
                self.after(0, lambda: self.set_status("Текст не обнаружен. Попробуйте выделить крупнее."))
        except Exception as e:
            self.after(0, lambda: self.set_status(f"Ошибка OCR: {e}"))

    def tool_clean_text(self):
        """4. Чистый текст: очистка буфера от форматирования, тегов и мусора."""
        try:
            raw = self.clipboard_get()
            clean = raw.strip()
            self.clipboard_clear()
            self.clipboard_append(clean)
            self.set_status("📝 Буфер очищен до чистого текста!")
        except Exception:
            self.set_status("Буфер обмена пуст или не содержит текст.")

    def tool_record_screen(self):
        """5. Запись экрана: запуск записи экрана Windows (Win+Alt+R)."""
        def trigger():
            time.sleep(0.15)
            VK_LWIN = 0x5B
            VK_MENU = 0x12
            VK_R = 0x52
            user32 = ctypes.windll.user32
            user32.keybd_event(VK_LWIN, 0, 0, 0)
            user32.keybd_event(VK_MENU, 0, 0, 0)
            user32.keybd_event(VK_R, 0, 0, 0)
            user32.keybd_event(VK_R, 0, 2, 0)
            user32.keybd_event(VK_MENU, 0, 2, 0)
            user32.keybd_event(VK_LWIN, 0, 2, 0)
        threading.Thread(target=trigger, daemon=True).start()
        self.set_status("🎥 Запись экрана запущена (Win+Alt+R)!")

    def tool_never_drop(self):
        """6. Never Drop — открывает Never Drop без файла (можно перетащить)."""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="⚡ Never Drop – Выберите файл для отправки на телефон"
        )
        if file_path:
            _island_share_file(file_path)
            self.set_status(f"⚡ Never Drop запущен: {os.path.basename(file_path)}")
        else:
            never_drop_script = os.path.join(NEVER_DROP_DIR, "never_drop.py")
            if os.path.exists(never_drop_script):
                pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
                exe = pythonw if os.path.exists(pythonw) else sys.executable
                subprocess.Popen([exe, never_drop_script])
                self.set_status("⚡ Never Drop открыт!")

    def _on_files_dropped_to_island(self, files):
        """Обработка перетаскивания файлов на остров → запуск Never Drop."""
        if not files:
            return
        first = files[0]
        if isinstance(first, bytes):
            first = first.decode("utf-8", errors="ignore")
        first = first.strip()
        if os.path.exists(first):
            _island_share_file(first)
            self.after(0, lambda: self.set_status(f"⚡ Never Drop: {os.path.basename(first)}"))

    def start_drag(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def do_drag(self, event):
        x = self.winfo_x() - self._drag_start_x + event.x
        y = self.winfo_y() - self._drag_start_y + event.y
        self.geometry(f"+{x}+{y}")


if __name__ == "__main__":
    ensure_single_instance()
    island = NeverIsland()
    island.mainloop()
