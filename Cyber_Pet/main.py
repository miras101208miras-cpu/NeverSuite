import os
import sys
import time
import math
import random
import ctypes

# Защита от дубликатов (Single Instance Mutex)
_pet_mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Never_Pet_Mutex")
if ctypes.windll.kernel32.GetLastError() == 183:
    sys.exit(0)

import subprocess
import tkinter as tk
from PIL import Image, ImageTk

PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)
import never_focus

# ⚡ Never Drop integration
NEVER_DROP_DIR = os.path.join(PARENT_DIR, "Never_Drop")
if NEVER_DROP_DIR not in sys.path:
    sys.path.insert(0, NEVER_DROP_DIR)

try:
    import windnd as _windnd_pet
    _HAS_WINDND_PET = True
except ImportError:
    _HAS_WINDND_PET = False

def _pet_share_file(file_path):
    """Launch Never Drop to share a file. Called from drag-drop or context menu."""
    never_drop_script = os.path.join(NEVER_DROP_DIR, "never_drop.py")
    if not os.path.exists(never_drop_script):
        return
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    exe = pythonw if os.path.exists(pythonw) else sys.executable
    subprocess.Popen([exe, never_drop_script, file_path])

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, "assets")

class NeverPetsApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Never Cyber Pets")
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        self.TRANS_COLOR = "#000001"
        self.config(bg=self.TRANS_COLOR)
        self.attributes("-transparentcolor", self.TRANS_COLOR)

        self.w = 150
        self.h = 145
        self.screen_w = self.winfo_screenwidth()
        self.screen_h = self.winfo_screenheight()

        # Положение над нижней панелью задач
        self.x = self.screen_w - 270
        self.ground_y = self.screen_h - 180
        self.y = self.ground_y

        # Текущий питомец: "pink_anime", "slime", "creeper", "marin", "robot"
        self.pet_type = "pink_anime"

        # Текущий наряд для розовой тян: "dress", "school", "hoodie"
        self.anime_outfit = "dress"

        self.direction = -1
        self.speed = 2.0
        self.state = "idle"  # idle, walk, chase_food, chase_ball
        self.state_timer = 50

        # Тамагочи: Еда и Мячик
        self.active_food = None  # {type, x, y, vy, on_ground}
        self.active_ball = None  # {x, y, vx, vy, r, ground_y}
        self.ball_held = False

        # Загрузка кадров нарядов для аниме-тян
        self.load_all_anime_outfits()

        # Физика слизня
        self.slime_phase = "idle"
        self.slime_timer = 30
        self.slime_vy = 0.0
        self.slime_squash = 1.0
        self.slime_splashes = []

        # Логика крипера
        self.creeper_exploding = False
        self.creeper_fuse = 0
        self.creeper_dead = False
        self.creeper_cooldown = 120
        self.creeper_particles = []
        self.creeper_walk_phase = 0.0

        # Анимация розовой аниме тян
        self.pink_walk_phase = 0.0
        self.pink_bob = 0
        self.hearts = []

        # Анимация Марин Китагавы
        self.marin_walk_phase = 0.0
        self.marin_blink = 0

        self.bubble_text = "Приветик, семпай! 🌸"
        self.bubble_timer = 75

        # Focus mode tracking
        self.focus_active = False
        self.focus_check_counter = 0
        self.focus_greeted = False
        self._FOCUS_QUOTES = [
            "Фокус Тайм! 🎧📚",
            "Учимся вместе! 💡✨",
            "Концентрация! 📖🌸",
            "Не отвлекайся! 🎯💪",
            "Ты можешь это! 🌟📚",
            "Усердная работа! 🎧🍅",
        ]

        self.geometry(f"{self.w}x{self.h}+{int(self.x)}+{int(self.y)}")

        self.canvas = tk.Canvas(
            self,
            width=self.w,
            height=self.h,
            bg=self.TRANS_COLOR,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_drop)
        self.canvas.bind("<Button-3>", self.show_context_menu)

        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0

        # ⚡ Never Drop: hook Windows Drag & Drop so files dropped on the pet get shared
        if _HAS_WINDND_PET:
            try:
                _windnd_pet.hook_dropfiles(self, func=self._on_files_dropped_to_pet, force_unicode=True)
            except Exception:
                pass

        self.animate_loop()

    def load_all_anime_outfits(self):
        self.outfit_frames = {}
        outfits = ["dress", "school", "hoodie"]
        actions = ["idle_left", "walk1_left", "walk2_left", "idle_right", "walk1_right", "walk2_right"]

        for o in outfits:
            self.outfit_frames[o] = {}
            for a in actions:
                p = os.path.join(ASSETS_DIR, f"pink_{o}_{a}.png")
                if os.path.exists(p):
                    img = Image.open(p)
                    self.outfit_frames[o][a] = ImageTk.PhotoImage(img)

    def set_pet(self, ptype):
        self.pet_type = ptype
        self.creeper_exploding = False
        self.creeper_dead = False
        self.creeper_fuse = 0
        self.creeper_cooldown = 150
        self.creeper_particles.clear()
        self.slime_splashes.clear()
        self.hearts.clear()
        self.slime_phase = "idle"
        self.slime_squash = 1.0
        self.y = self.ground_y
        self.geometry(f"{self.w}x{self.h}+{int(self.x)}+{int(self.y)}")

        dialogs = {
            "pink_anime": "🌸 Тян: Приветик, семпай! Я с тобой! ✨",
            "slime": "🟢 Слизень: Хлюп! Шлёп!",
            "creeper": "💣 Крипер: Tsssss... Я спокоен!",
            "marin": "✨ Марин: Приветик, Годзё-кун! 💖",
            "robot": "🤖 Робот: Все системы активны!"
        }
        self.say(dialogs.get(ptype, "Привет!"))

    def set_outfit(self, outfit_name):
        self.anime_outfit = outfit_name
        names = {
            "dress": "👗 Белое бальное платьице",
            "school": "🎒 Школьная форма с галстуком",
            "hoodie": "🧸 Уютное оверсайз-худи"
        }
        self.say(f"✨ Наряд: {names.get(outfit_name, 'Новый стиль!')}")
        for _ in range(4):
            self.hearts.append({
                "x": self.w // 2 + random.randint(-15, 15),
                "y": self.h // 2,
                "vy": -random.uniform(2, 4),
                "vx": random.uniform(-1, 1),
                "life": 25,
                "symbol": "✨"
            })

    def say(self, text):
        self.bubble_text = text
        self.bubble_timer = 70

    # -------------------------------------------------------------
    # ТАМАГОЧИ: КОРМЛЕНИЕ
    # -------------------------------------------------------------
    def feed_pet(self, food_type):
        # Спавним еду сверху окна питомца
        emoji_map = {"strawberry": "🍓", "cake": "🍰", "apple": "🍏"}
        self.active_food = {
            "type": food_type,
            "emoji": emoji_map.get(food_type, "🍓"),
            "x": random.randint(30, self.w - 30),
            "y": 10,
            "vy": 2.0,
            "on_ground": False
        }
        self.say(f"Ого, {self.active_food['emoji']}! Бегу кушать!")

    # -------------------------------------------------------------
    # ТАМАГОЧИ: МЯЧИК
    # -------------------------------------------------------------
    def throw_ball(self):
        # Спавн мячика с физикой отскока
        self.active_ball = {
            "x": random.randint(25, self.w - 25),
            "y": 20,
            "vx": random.choice([-3.5, 3.5]),
            "vy": -4.0,
            "r": 9
        }
        self.say("🎾 Мячик! Лови его!")

    def on_click(self, event):
        # Проверяем, кликнули ли по мячику
        if self.active_ball:
            bx, by = self.active_ball["x"], self.active_ball["y"]
            r = self.active_ball["r"]
            if (event.x - bx)**2 + (event.y - by)**2 <= (r + 8)**2:
                # Пнули мячик!
                self.active_ball["vy"] = -7.5
                self.active_ball["vx"] = random.uniform(-5.0, 5.0)
                self.say("⚽ Пас! Высокий полёт!")
                return

        self.is_dragging = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y

        if self.pet_type == "pink_anime":
            for _ in range(4):
                self.hearts.append({
                    "x": self.w // 2 + random.randint(-20, 20),
                    "y": self.h // 2,
                    "vy": -random.uniform(1.8, 3.8),
                    "vx": random.uniform(-1.0, 1.0),
                    "life": 28,
                    "symbol": random.choice(["💖", "✨", "🌸", "💕", "🎀"])
                })
            quotes = [
                "Приветик, семпай! 🌸",
                "Я твоя карманная принцесса! ✨",
                "Ты так усердно работаешь! Горжусь! 💖",
                "Сделай перерыв на чаёк! ☕",
                "Ва-а-ай! Ты меня смущаешь! (⁄ ⁄•⁄ω⁄•⁄ ⁄)",
                "Буду охранять твой рабочий стол! 🎀",
                "Мурр... Спасибо, что кликнул! (≧◡≦)"
            ]
            self.say(random.choice(quotes))

        elif self.pet_type == "slime":
            self.say("Шлёп! Мега-прыжок!")
            self.slime_phase = "squash"
            self.slime_timer = 5
            self.slime_squash = 0.55
            self.slime_vy = -11.0

        elif self.pet_type == "creeper":
            if self.creeper_exploding:
                self.creeper_exploding = False
                self.creeper_fuse = 0
                self.creeper_cooldown = 200
                self.say("💧 Фух! Разрядил фитиль!")
            elif not self.creeper_dead:
                if random.random() < 0.25 and self.creeper_cooldown <= 0:
                    self.start_creeper_fuse()
                else:
                    replies = [
                        "Tssss... Не тыкай в порох!",
                        "Зелёный и опасный!",
                        "Где мой TNT блок?",
                        "Tss... Я просто гуляю!"
                    ]
                    self.say(random.choice(replies))

        elif self.pet_type == "marin":
            for _ in range(3):
                self.hearts.append({
                    "x": self.w // 2 + random.randint(-15, 15),
                    "y": self.h // 2 - 10,
                    "vy": -random.uniform(1.5, 3.5),
                    "vx": random.uniform(-0.5, 0.5),
                    "life": 25,
                    "symbol": random.choice(["💖", "✨", "💕"])
                })
            marin_quotes = [
                "Годзё-кун! Ты лучший! 💖",
                "Зацени мой новый косплей! ✨",
                "Шизуку-куроэ готова к фото! 📸",
                "Семпай, ты просто краш! 💕"
            ]
            self.say(random.choice(marin_quotes))

        else:
            self.say("❤️ Люблю тебя, босс!")

    def on_drag(self, event):
        self.x = self.winfo_x() - self.drag_start_x + event.x
        self.y = self.winfo_y() - self.drag_start_y + event.y
        self.geometry(f"{self.w}x{self.h}+{int(self.x)}+{int(self.y)}")

    def on_drop(self, event):
        self.is_dragging = False
        if self.y > self.screen_h - 180:
            self.y = self.screen_h - 180
        self.ground_y = self.y
        self.geometry(f"{self.w}x{self.h}+{int(self.x)}+{int(self.y)}")

    def show_context_menu(self, event):
        menu = tk.Menu(self, tearoff=0, bg="#0e111a", fg="#f8fafc", activebackground="#ec4899", activeforeground="#ffffff", font=("Segoe UI", 9))

        # Меню кормления (Тамагочи)
        food_menu = tk.Menu(menu, tearoff=0, bg="#0e111a", fg="#f8fafc", activebackground="#ec4899", activeforeground="#ffffff", font=("Segoe UI", 9))
        food_menu.add_command(label="🍓 Спелая клубничка", command=lambda: self.feed_pet("strawberry"))
        food_menu.add_command(label="🍰 Клубничный тортик", command=lambda: self.feed_pet("cake"))
        food_menu.add_command(label="🍏 Сочное яблочко", command=lambda: self.feed_pet("apple"))
        menu.add_cascade(label="🍴 Покормить питомца", menu=food_menu)

        # Меню игр
        menu.add_command(label="🎾 Бросить мячик (Поиграть)", command=self.throw_ball)

        # Меню нарядов для тян
        if self.pet_type == "pink_anime":
            outfit_menu = tk.Menu(menu, tearoff=0, bg="#0e111a", fg="#f8fafc", activebackground="#ec4899", activeforeground="#ffffff", font=("Segoe UI", 9))
            outfit_menu.add_command(label="👗 Белое бальное платьице", command=lambda: self.set_outfit("dress"))
            outfit_menu.add_command(label="🎒 Школьная форма с галстуком", command=lambda: self.set_outfit("school"))
            outfit_menu.add_command(label="🧸 Уютное оверсайз-худи", command=lambda: self.set_outfit("hoodie"))
            menu.add_cascade(label="🎀 Сменить наряд", menu=outfit_menu)

        menu.add_separator()

        # Выбор питомцев
        pet_submenu = tk.Menu(menu, tearoff=0, bg="#0e111a", fg="#f8fafc", activebackground="#ec4899", activeforeground="#ffffff", font=("Segoe UI", 9))
        pet_submenu.add_command(label="🌸 Аниме-тян (Пиксельная Принцесса)", command=lambda: self.set_pet("pink_anime"))
        pet_submenu.add_command(label="🟢 Слизень (Minecraft Slime)", command=lambda: self.set_pet("slime"))
        pet_submenu.add_command(label="💣 Крипер (Minecraft Creeper)", command=lambda: self.set_pet("creeper"))
        pet_submenu.add_command(label="🎀 Марин Китагава (Kitagawa Marin)", command=lambda: self.set_pet("marin"))
        pet_submenu.add_command(label="🤖 Кибер-робот (Cyber Bot)", command=lambda: self.set_pet("robot"))
        menu.add_cascade(label="🎭 Выбрать питомца", menu=pet_submenu)

        menu.add_separator()
        if self.pet_type == "creeper":
            menu.add_command(label="💥 Зажечь крипера (Tssss... БАБАХ!)", command=self.start_creeper_fuse)
        elif self.pet_type == "slime":
            menu.add_command(label="🚀 Супер-прыжок!", command=lambda: self.on_click(event))

        menu.add_command(label="❤️ Погладить", command=lambda: self.say("🐾 Мурр... Очень приятно!"))
        menu.add_separator()

        # ⚡ Never Drop – Отправить файл на телефон
        menu.add_command(label="⚡ Never Drop – Отправить файл на телефон", command=self.open_never_drop)

        menu.add_separator()
        menu.add_command(label="✕ Закрыть питомца", command=self.destroy)
        menu.post(event.x_root, event.y_root)

    def open_never_drop(self):
        """Open file picker and launch Never Drop to share the selected file."""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="⚡ Never Drop – Выберите файл для отправки на телефон"
        )
        if file_path:
            _pet_share_file(file_path)
            self.say("⚡ Never Drop запущен!")

    def _on_files_dropped_to_pet(self, files):
        """Handle files dragged & dropped onto Cyber Pet → launch Never Drop."""
        if not files:
            return
        first = files[0]
        if isinstance(first, bytes):
            first = first.decode("utf-8", errors="ignore")
        first = first.strip()
        if os.path.exists(first):
            _pet_share_file(first)
            self.after(0, lambda: self.say(f"⚡ Drop! {os.path.basename(first)}"))

    # -------------------------------------------------------------
    # ОБНОВЛЕНИЕ ЕДЫ И МЯЧИКА
    # -------------------------------------------------------------
    def update_tamagotchi_objects(self):
        floor_y = self.h - 22

        # 1. Еда
        if self.active_food:
            f = self.active_food
            if not f["on_ground"]:
                f["y"] += f["vy"]
                f["vy"] += 0.65  # гравитация
                if f["y"] >= floor_y:
                    f["y"] = floor_y
                    f["vy"] = -f["vy"] * 0.45  # упругий отскок
                    if abs(f["vy"]) < 1.0:
                        f["on_ground"] = True
                        f["vy"] = 0

            # Отрисовка еды
            self.canvas.create_text(f["x"], f["y"], text=f["emoji"], font=("Segoe UI Emoji", 15))

            # Логика поедания: если питомец подошел близко к еде
            pet_cx = self.w // 2
            if abs(pet_cx - f["x"]) < 26 and abs((self.h // 2 + 18) - f["y"]) < 45:
                # Скушал!
                for _ in range(5):
                    self.hearts.append({
                        "x": f["x"] + random.randint(-10, 10),
                        "y": f["y"] - 10,
                        "vy": -random.uniform(1.5, 3.5),
                        "vx": random.uniform(-1, 1),
                        "life": 22,
                        "symbol": random.choice(["✨", "💖", "😋", "🌸"])
                    })
                quotes = [
                    "Ням-ням! Вкуснотища! 😋",
                    "М-м-м, спасибо, семпай! 💖",
                    "Идеальное угощение! ✨",
                    "Сил прибавилось на все 100%! 🌟"
                ]
                self.say(random.choice(quotes))
                self.active_food = None

        # 2. Мячик
        if self.active_ball:
            b = self.active_ball
            b["x"] += b["vx"]
            b["y"] += b["vy"]
            b["vy"] += 0.55  # гравитация

            # Отскок от пола
            if b["y"] >= floor_y - b["r"]:
                b["y"] = floor_y - b["r"]
                b["vy"] = -b["vy"] * 0.72
                b["vx"] *= 0.95  # трение
                if abs(b["vy"]) < 1.0:
                    b["vy"] = 0

            # Отскок от боковых стенок окна
            if b["x"] <= b["r"] + 5:
                b["x"] = b["r"] + 5
                b["vx"] = abs(b["vx"]) * 0.8
            elif b["x"] >= self.w - b["r"] - 5:
                b["x"] = self.w - b["r"] - 5
                b["vx"] = -abs(b["vx"]) * 0.8

            # Отрисовка неонового теннисного мячика
            bx, by, br = b["x"], b["y"], b["r"]
            self.canvas.create_oval(bx - br, by - br, bx + br, by + br, fill="#a3e635", outline="#4d7c0f", width=1.5)
            self.canvas.create_arc(bx - br + 2, by - br + 2, bx + br - 2, by + br - 2, start=45, extent=90, style="arc", outline="#ffffff", width=1.5)

            # Питомец ловит мячик, если подбежал вплотную
            pet_cx = self.w // 2
            if abs(pet_cx - bx) < 24 and abs((self.h // 2 + 18) - by) < 40 and abs(b["vy"]) < 3.0:
                # Поймал! Подбрасываем обратно
                b["vy"] = -6.5
                b["vx"] = random.choice([-3.0, 3.0])
                for _ in range(3):
                    self.hearts.append({
                        "x": bx, "y": by - 8,
                        "vy": -2.5, "vx": random.uniform(-1, 1),
                        "life": 18, "symbol": "🎾"
                    })
                self.say("Поймала! Лови пас! 🎾✨")

    # -------------------------------------------------------------
    # ЛОГИКА И ФИЗИКА
    # -------------------------------------------------------------
    def start_creeper_fuse(self):
        if not self.creeper_exploding and not self.creeper_dead:
            self.creeper_exploding = True
            self.creeper_fuse = 0
            self.say("Tsssssssss... 💣!")

    def update_creeper_logic(self):
        if self.creeper_cooldown > 0:
            self.creeper_cooldown -= 1

        if self.creeper_dead:
            return

        if not self.creeper_exploding and not self.is_dragging and self.creeper_cooldown <= 0:
            if random.random() < 0.0006:
                self.start_creeper_fuse()

        if self.creeper_exploding:
            self.creeper_fuse += 1
            if self.creeper_fuse > 45:
                self.creeper_exploding = False
                self.creeper_dead = True
                self.say("💥 БАБАХ!!!")

                cx, cy = self.w // 2, self.h // 2 + 10
                self.creeper_particles.clear()
                colors = ["#70c655", "#4aa237", "#357924", "#111111", "#e2e8f0", "#f97316", "#ef4444"]
                for _ in range(35):
                    ang = random.uniform(0, math.pi * 2)
                    spd = random.uniform(3, 10)
                    self.creeper_particles.append({
                        "x": cx, "y": cy,
                        "vx": math.cos(ang) * spd,
                        "vy": math.sin(ang) * spd - 2,
                        "size": random.randint(3, 7),
                        "life": random.randint(20, 35),
                        "color": random.choice(colors)
                    })
                self.after(2500, self.respawn_creeper)

    def respawn_creeper(self):
        self.creeper_dead = False
        self.creeper_cooldown = 150
        self.say("Крипер возродился! 🧟")

    def update_slime_logic(self):
        if self.is_dragging:
            return

        # Если есть еда или мячик, слизень прыгает в их сторону!
        target_x = None
        if self.active_food: target_x = self.active_food["x"]
        elif self.active_ball: target_x = self.active_ball["x"]

        if target_x is not None:
            self.direction = 1 if target_x > self.w // 2 else -1

        if self.slime_phase == "idle":
            self.slime_timer -= 1
            self.slime_squash = 1.0
            if self.slime_timer <= 0 or (target_x is not None and random.random() < 0.2):
                self.slime_phase = "squash"
                self.slime_timer = 6
                self.slime_squash = 0.65
                if target_x is None:
                    self.direction = random.choice([-1, 1])

        elif self.slime_phase == "squash":
            self.slime_timer -= 1
            if self.slime_timer <= 0:
                self.slime_phase = "jump"
                self.slime_vy = -8.5
                self.slime_squash = 1.35
                cx = self.w // 2
                cy = self.h // 2 + 30
                for _ in range(4):
                    self.slime_splashes.append({
                        "x": cx + random.randint(-15, 15),
                        "y": cy,
                        "vx": random.uniform(-2, 2),
                        "vy": random.uniform(-1, -3),
                        "life": 12,
                        "color": "#79c05a"
                    })

        elif self.slime_phase == "jump":
            self.y += int(self.slime_vy)
            self.slime_vy += 0.75
            self.x += self.direction * 3.5

            if self.x < 15: self.x = 15; self.direction = 1
            elif self.x > self.screen_w - self.w - 15: self.x = self.screen_w - self.w - 15; self.direction = -1

            if self.y >= self.ground_y:
                self.y = self.ground_y
                self.slime_phase = "land"
                self.slime_squash = 0.60
                self.slime_timer = 6
                cx = self.w // 2
                cy = self.h // 2 + 30
                for _ in range(4):
                    self.slime_splashes.append({
                        "x": cx + random.randint(-15, 15),
                        "y": cy,
                        "vx": random.uniform(-3, 3),
                        "vy": random.uniform(-1, -2),
                        "life": 10,
                        "color": "#63ab44"
                    })

            self.geometry(f"{self.w}x{self.h}+{int(self.x)}+{int(self.y)}")

        elif self.slime_phase == "land":
            self.slime_timer -= 1
            if self.slime_timer <= 0:
                self.slime_phase = "idle"
                self.slime_squash = 1.0
                self.slime_timer = random.randint(15, 40) if target_x else random.randint(25, 55)

    def step_walking(self, speed=2.0):
        # Если есть еда или мячик — бежим прямо к ним!
        target_x = None
        if self.active_food:
            target_x = self.active_food["x"]
        elif self.active_ball:
            target_x = self.active_ball["x"]

        if target_x is not None:
            self.state = "walk"
            pet_cx = self.w // 2
            if abs(pet_cx - target_x) > 12:
                self.direction = 1 if target_x > pet_cx else -1
                self.x += self.direction * (speed * 1.35)  # бежит быстрее к еде/мячу!
            else:
                self.state = "idle"
        else:
            self.state_timer -= 1
            if self.state_timer <= 0:
                modes = ["idle", "walk", "walk", "idle"]
                self.state = random.choice(modes)
                self.state_timer = random.randint(45, 95)
                if self.state == "walk":
                    self.direction = random.choice([-1, 1])

            if self.state == "walk":
                self.x += self.direction * speed

        if self.x < 15: self.x = 15; self.direction = 1
        elif self.x > self.screen_w - self.w - 15: self.x = self.screen_w - self.w - 15; self.direction = -1

        self.geometry(f"{self.w}x{self.h}+{int(self.x)}+{int(self.y)}")

    # -------------------------------------------------------------
    # FOCUS STATE POLLING
    # -------------------------------------------------------------
    def poll_focus_state(self):
        """Check never_focus state every ~90 frames (~3 seconds)."""
        self.focus_check_counter += 1
        if self.focus_check_counter < 90:
            return
        self.focus_check_counter = 0
        try:
            st = never_focus.read_state()
            was_active = self.focus_active
            if st.get("active") and not st.get("paused", False):
                rem = st.get("end_timestamp", 0) - __import__("time").time()
                self.focus_active = rem > 0
            else:
                self.focus_active = st.get("active") and st.get("paused", False)

            is_now_active = st.get("active", False)

            if is_now_active and not was_active:
                # Just entered focus mode
                self.focus_greeted = False

            if is_now_active and not self.focus_greeted:
                self.focus_greeted = True
                mode = st.get("mode", "work")
                if mode == "work":
                    self.say(random.choice(self._FOCUS_QUOTES))
                else:
                    self.say("☕ Время отдыха! Расслабляйся~")

            if not is_now_active and was_active:
                self.focus_active = False
                self.focus_greeted = False
                self.say("🎉 Молодец, сессия завершена! ✨")

            self.focus_active = is_now_active
        except Exception:
            self.focus_active = False

    def draw_focus_overlay(self):
        """Draw a cute focus mode indicator when focus is active."""
        try:
            st = never_focus.read_state()
            if not st.get("active"):
                return

            mode = st.get("mode", "work")
            if st.get("paused"):
                rem_str = never_focus.format_time(st.get("remaining_seconds", 0))
                label = f"⏸ {rem_str}"
                color = "#94a3b8"
            elif mode == "work":
                rem = max(0, st.get("end_timestamp", 0) - __import__("time").time())
                rem_str = never_focus.format_time(rem)
                label = f"🍅 {rem_str}"
                color = "#f43f5e"
            else:
                rem = max(0, st.get("end_timestamp", 0) - __import__("time").time())
                rem_str = never_focus.format_time(rem)
                label = f"☕ {rem_str}"
                color = "#38bdf8"

            # Draw timer pill at top-right of pet canvas
            pill_x = self.w - 4
            pill_y = 28
            self.canvas.create_rectangle(
                pill_x - 54, pill_y - 10,
                pill_x, pill_y + 10,
                fill="#0f172a", outline=color, width=1.5
            )
            self.canvas.create_text(
                pill_x - 27, pill_y,
                text=label,
                fill=color,
                font=("Segoe UI", 8, "bold"),
                anchor="center"
            )
        except Exception:
            pass

    # -------------------------------------------------------------
    # ГЛАВНЫЙ ЦИКЛ АНИМАЦИИ
    # -------------------------------------------------------------
    def animate_loop(self):
        self.canvas.delete("all")

        # Poll focus state periodically
        self.poll_focus_state()

        # 1. Обновление тамагочи-объектов (еда и мячик) - SKIP during focus mode
        if not self.focus_active:
            self.update_tamagotchi_objects()

        # 2. Обновление механики питомца - slowed down during focus
        focus_speed_mult = 0.3 if self.focus_active else 1.0

        if self.pet_type == "pink_anime":
            if not self.is_dragging:
                self.step_walking(speed=2.0 * focus_speed_mult)
                if self.state == "walk":
                    self.pink_walk_phase = (self.pink_walk_phase + 0.32 * focus_speed_mult) % (math.pi * 2)
                else:
                    self.pink_walk_phase = 0
            self.pink_bob = int(math.sin(time.time() * 3.5) * 2)

        elif self.pet_type == "slime":
            if not self.focus_active:
                self.update_slime_logic()
        elif self.pet_type == "creeper":
            if not self.focus_active:
                self.update_creeper_logic()
            if not self.is_dragging and not self.creeper_exploding and not self.creeper_dead:
                self.step_walking(speed=1.6 * focus_speed_mult)
                if self.state == "walk":
                    self.creeper_walk_phase = (self.creeper_walk_phase + 0.3 * focus_speed_mult) % (math.pi * 2)
                else:
                    self.creeper_walk_phase = 0
        elif self.pet_type == "marin":
            if not self.is_dragging:
                self.step_walking(speed=2.0 * focus_speed_mult)
                if self.state == "walk":
                    self.marin_walk_phase = (self.marin_walk_phase + 0.28 * focus_speed_mult) % (math.pi * 2)
                else:
                    self.marin_walk_phase = 0
            self.marin_blink = (self.marin_blink + 1) % 90
        else:
            if not self.is_dragging:
                self.step_walking(speed=1.8 * focus_speed_mult)

        # Отрисовка частиц взрыва Крипера
        if self.creeper_particles:
            rem = []
            for p in self.creeper_particles:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                p["vy"] += 0.4
                p["life"] -= 1
                if p["life"] > 0:
                    s = p["size"]
                    self.canvas.create_rectangle(p["x"], p["y"], p["x"]+s, p["y"]+s, fill=p["color"], outline="")
                    rem.append(p)
            self.creeper_particles = rem

        # Отрисовка брызг слизня
        if self.slime_splashes:
            rem = []
            for p in self.slime_splashes:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                p["vy"] += 0.3
                p["life"] -= 1
                if p["life"] > 0:
                    self.canvas.create_rectangle(p["x"]-2, p["y"]-2, p["x"]+2, p["y"]+2, fill=p["color"], outline="")
                    rem.append(p)
            self.slime_splashes = rem

        # Отрисовка сердечек
        if self.hearts:
            rem = []
            for h in self.hearts:
                h["x"] += h.get("vx", 0)
                h["y"] += h["vy"]
                h["life"] -= 1
                if h["life"] > 0:
                    self.canvas.create_text(h["x"], h["y"], text=h["symbol"], font=("Segoe UI Emoji", 10))
                    rem.append(h)
            self.hearts = rem

        # Отрисовка облачка диалога
        if self.bubble_timer > 0:
            self.bubble_timer -= 1
            bx = self.w // 2
            by = 12

            # Focus mode uses different bubble style
            if self.focus_active:
                outline_c = "#f43f5e"
                fill_c = "#1a0a0e"
                text_c = "#fda4af"
            elif self.pet_type == "pink_anime":
                outline_c = "#f472b6"
                fill_c = "#0f172a"
                text_c = "#fbcfe8"
            else:
                outline_c = "#38bdf8"
                fill_c = "#0f172a"
                text_c = "#38bdf8"

            self.canvas.create_rectangle(
                bx - 68, by - 9, bx + 68, by + 12,
                fill=fill_c, outline=outline_c, width=1.5
            )
            self.canvas.create_polygon(
                bx - 4, by + 12, bx + 4, by + 12, bx, by + 16,
                fill=outline_c
            )
            short_txt = (self.bubble_text[:22] + "..") if len(self.bubble_text) > 24 else self.bubble_text
            self.canvas.create_text(
                bx, by + 1,
                text=short_txt,
                fill=text_c,
                font=("Segoe UI", 8, "bold")
            )

        # Focus overlay timer pill
        self.draw_focus_overlay()

        # Отрисовка персонажа
        cx = self.w // 2
        cy = self.h // 2 + 18

        if self.pet_type == "pink_anime":
            self.draw_pink_anime(cx, cy)
        elif self.pet_type == "slime":
            self.draw_minecraft_slime(cx, cy)
        elif self.pet_type == "creeper":
            if not self.creeper_dead:
                self.draw_minecraft_creeper(cx, cy)
            else:
                self.canvas.create_text(cx, cy - 10, text="💀 💥", font=("Segoe UI", 16))
                self.canvas.create_text(cx, cy + 12, text="Возрождение...", fill="#94a3b8", font=("Segoe UI", 8, "italic"))
        elif self.pet_type == "marin":
            self.draw_marin_kitagawa(cx, cy)
        else:
            self.draw_robot(cx, cy)

        self.after(35, self.animate_loop)

    # =============================================================
    # 0. ПИКСЕЛЬНАЯ АНИМЕ-ТЯНКА С ВЫБОРОМ НАРЯДОВ
    # =============================================================
    def draw_pink_anime(self, cx, cy):
        side = "right" if self.direction > 0 else "left"
        outfit = self.anime_outfit

        if self.state == "walk":
            step_idx = int(self.pink_walk_phase / math.pi) % 2
            action = f"walk{step_idx + 1}_{side}"
            dy = int(math.sin(self.pink_walk_phase * 2) * 2)
        else:
            action = f"idle_{side}"
            dy = self.pink_bob

        outfit_dict = self.outfit_frames.get(outfit, self.outfit_frames.get("dress", {}))
        img = outfit_dict.get(action)
        if img:
            self.canvas.create_image(cx, cy + dy, image=img)
        else:
            self.canvas.create_oval(cx - 20, cy - 20, cx + 20, cy + 20, fill="#f472b6")

    # =============================================================
    # 1. АУТЕНТИЧНЫЙ MINECRAFT SLIME
    # =============================================================
    def draw_minecraft_slime(self, cx, cy):
        sq = self.slime_squash
        w = int(24 * (1.0 / math.sqrt(sq)))
        h = int(24 * sq)

        self.canvas.create_rectangle(cx - w, cy - h, cx + w, cy + h, fill="#79c05a", outline="#599b3b", width=2)
        self.canvas.create_line(cx - w + 2, cy - h + 2, cx + w - 2, cy - h + 2, fill="#9be678", width=3)
        self.canvas.create_line(cx - w + 2, cy - h + 2, cx - w + 2, cy + h - 2, fill="#9be678", width=3)
        self.canvas.create_line(cx - w + 2, cy + h - 2, cx + w - 2, cy + h - 2, fill="#4c8532", width=3)
        self.canvas.create_line(cx + w - 2, cy - h + 2, cx + w - 2, cy + h - 2, fill="#4c8532", width=3)

        core_w = int(w * 0.58)
        core_h = int(h * 0.58)
        self.canvas.create_rectangle(cx - core_w, cy - core_h + 3, cx + core_w, cy + core_h + 3, fill="#457c31", outline="#315c21", width=1.5)
        self.canvas.create_line(cx - core_w + 1, cy - core_h + 4, cx + core_w - 1, cy - core_h + 4, fill="#5ba640", width=1.5)

        eye_sz = max(3, int(6 * sq))
        eye_y = cy - int(h * 0.18)
        eye_dx = int(w * 0.50)

        lx = cx - eye_dx
        self.canvas.create_rectangle(lx - eye_sz, eye_y - eye_sz, lx + eye_sz, eye_y + eye_sz, fill="#1c3013", outline="")
        self.canvas.create_rectangle(lx - eye_sz + 1, eye_y - eye_sz + 1, lx, eye_y, fill="#529438", outline="")

        rx = cx + eye_dx - eye_sz
        self.canvas.create_rectangle(rx - eye_sz, eye_y - eye_sz, rx + eye_sz, eye_y + eye_sz, fill="#1c3013", outline="")
        self.canvas.create_rectangle(rx - eye_sz + 1, eye_y - eye_sz + 1, rx, eye_y, fill="#529438", outline="")

        mouth_y = cy + int(h * 0.28)
        mouth_sz = max(2, int(3 * sq))
        self.canvas.create_rectangle(cx - mouth_sz, mouth_y - mouth_sz, cx + mouth_sz, mouth_y + mouth_sz, fill="#1c3013", outline="")

    # =============================================================
    # 2. АУТЕНТИЧНЫЙ MINECRAFT CREEPER
    # =============================================================
    def draw_minecraft_creeper(self, cx, cy):
        is_flash = (self.creeper_exploding and (self.creeper_fuse % 4 in (1, 2)))
        scale = 1.0 + (self.creeper_fuse * 0.012 if self.creeper_exploding else 0)

        c_green = "#ffffff" if is_flash else "#56ab3a"
        c_light = "#ffffff" if is_flash else "#70c655"
        c_dark  = "#ffffff" if is_flash else "#367824"
        c_deep  = "#ffffff" if is_flash else "#245217"
        c_face  = "#ffffff" if is_flash else "#0d140d"

        leg_w = 7
        leg_h = 13
        leg_y = cy + 18
        leg1_off = int(math.sin(self.creeper_walk_phase) * 4)
        leg2_off = int(math.sin(self.creeper_walk_phase + math.pi) * 4)

        self.canvas.create_rectangle(cx - 15, leg_y + leg2_off, cx - 15 + leg_w, leg_y + leg_h + leg2_off, fill=c_deep, outline="")
        self.canvas.create_rectangle(cx + 8, leg_y + leg1_off, cx + 8 + leg_w, leg_y + leg_h + leg1_off, fill=c_deep, outline="")

        self.canvas.create_rectangle(cx - 12, leg_y + leg1_off, cx - 12 + leg_w, leg_y + leg_h + leg1_off, fill=c_dark, outline=c_deep, width=1)
        self.canvas.create_rectangle(cx + 5, leg_y + leg2_off, cx + 5 + leg_w, leg_y + leg_h + leg2_off, fill=c_dark, outline=c_deep, width=1)
        self.canvas.create_rectangle(cx - 12, leg_y + leg_h + leg1_off - 3, cx - 12 + leg_w, leg_y + leg_h + leg1_off, fill=c_face, outline="")
        self.canvas.create_rectangle(cx + 5, leg_y + leg_h + leg2_off - 3, cx + 5 + leg_w, leg_y + leg_h + leg2_off, fill=c_face, outline="")

        body_w = int(11 * scale)
        body_h = int(16 * scale)
        body_y = cy + 2
        self.canvas.create_rectangle(cx - body_w, body_y - body_h, cx + body_w, body_y + body_h, fill=c_green, outline=c_dark, width=1.5)
        if not is_flash:
            self.canvas.create_rectangle(cx - body_w + 3, body_y - 8, cx - body_w + 8, body_y - 2, fill=c_light, outline="")
            self.canvas.create_rectangle(cx + 2, body_y + 1, cx + body_w - 2, body_y + 8, fill=c_dark, outline="")
            self.canvas.create_rectangle(cx - 5, body_y + 4, cx, body_y + 11, fill=c_deep, outline="")

        hw = int(18 * scale)
        hh = int(18 * scale)
        head_y = cy - 24

        self.canvas.create_rectangle(cx - hw, head_y - hh, cx + hw, head_y + hh, fill=c_green, outline=c_dark, width=2)
        if not is_flash:
            self.canvas.create_rectangle(cx - hw + 2, head_y - hh + 2, cx - hw + 8, head_y - hh + 8, fill=c_light, outline="")
            self.canvas.create_rectangle(cx + hw - 8, head_y - hh + 2, cx + hw - 2, head_y - hh + 7, fill=c_dark, outline="")
            self.canvas.create_rectangle(cx - hw + 2, head_y + hh - 8, cx - hw + 7, head_y + hh - 2, fill=c_deep, outline="")

        ps = max(2, int(3.5 * scale))
        self.canvas.create_rectangle(cx - ps*4, head_y - ps*2, cx - ps*2, head_y, fill=c_face, outline="")
        self.canvas.create_rectangle(cx + ps*2, head_y - ps*2, cx + ps*4, head_y, fill=c_face, outline="")
        self.canvas.create_rectangle(cx - ps, head_y - ps, cx + ps, head_y + ps, fill=c_face, outline="")
        self.canvas.create_rectangle(cx - ps*2, head_y + ps, cx + ps*2, head_y + ps*2, fill=c_face, outline="")
        self.canvas.create_rectangle(cx - ps*3, head_y + ps, cx - ps*2, head_y + ps*3.5, fill=c_face, outline="")
        self.canvas.create_rectangle(cx + ps*2, head_y + ps, cx + ps*3, head_y + ps*3.5, fill=c_face, outline="")

    # =============================================================
    # 3. МАРИН КИТАГАВА
    # =============================================================
    def draw_marin_kitagawa(self, cx, cy):
        c_gold_hair = "#fcd34d"
        c_gold_dark = "#f59e0b"
        c_pink_tips = "#fb7185"
        c_pink_deep = "#e11d48"
        c_skin      = "#ffedd5"
        c_eyes      = "#be123c"
        c_choker    = "#18181b"
        c_tie       = "#2563eb"

        hair_sway = math.sin(time.time() * 3.5) * 2.5
        leg1_off = int(math.sin(self.marin_walk_phase) * 3) if self.state == "walk" else 0
        leg2_off = int(math.sin(self.marin_walk_phase + math.pi) * 3) if self.state == "walk" else 0

        self.canvas.create_polygon(
            cx - 22, cy - 20, cx - 14, cy - 10,
            cx - 24 + hair_sway, cy + 22, cx - 30 + hair_sway, cy + 18,
            fill=c_gold_hair, outline=c_gold_dark
        )
        self.canvas.create_polygon(
            cx - 24 + hair_sway, cy + 22, cx - 30 + hair_sway, cy + 18,
            cx - 28 + hair_sway, cy + 34, cx - 22 + hair_sway, cy + 32,
            fill=c_pink_tips, outline=c_pink_deep
        )

        self.canvas.create_polygon(
            cx + 14, cy - 10, cx + 22, cy - 20,
            cx + 30 - hair_sway, cy + 18, cx + 24 - hair_sway, cy + 22,
            fill=c_gold_hair, outline=c_gold_dark
        )
        self.canvas.create_polygon(
            cx + 24 - hair_sway, cy + 22, cx + 30 - hair_sway, cy + 18,
            cx + 28 - hair_sway, cy + 34, cx + 22 - hair_sway, cy + 32,
            fill=c_pink_tips, outline=c_pink_deep
        )

        self.canvas.create_line(cx - 7, cy + 22, cx - 7, cy + 34 + leg1_off, fill="#0f172a", width=3)
        self.canvas.create_oval(cx - 10, cy + 33 + leg1_off, cx - 4, cy + 37 + leg1_off, fill="#334155", outline="")

        self.canvas.create_line(cx + 7, cy + 22, cx + 7, cy + 34 + leg2_off, fill="#0f172a", width=3)
        self.canvas.create_oval(cx + 4, cy + 33 + leg2_off, cx + 10, cy + 37 + leg2_off, fill="#334155", outline="")

        skirt_sway = int(math.sin(self.marin_walk_phase) * 2) if self.state == "walk" else 0
        self.canvas.create_polygon(
            cx - 15 + skirt_sway, cy + 22,
            cx + 15 + skirt_sway, cy + 22,
            cx + 10, cy + 10,
            cx - 10, cy + 10,
            fill="#1e1b4b", outline="#0f172a"
        )
        self.canvas.create_line(cx - 5 + skirt_sway, cy + 10, cx - 7 + skirt_sway, cy + 22, fill="#312e81")
        self.canvas.create_line(cx + 5 + skirt_sway, cy + 10, cx + 7 + skirt_sway, cy + 22, fill="#312e81")

        self.canvas.create_rectangle(cx - 10, cy + 1, cx + 10, cy + 11, fill="#f8fafc", outline="#cbd5e1", width=1)
        self.canvas.create_polygon(
            cx - 2, cy + 2, cx + 2, cy + 2,
            cx + 3, cy + 9, cx, cy + 14, cx - 3, cy + 9,
            fill=c_tie, outline="#1d4ed8"
        )
        self.canvas.create_polygon(cx - 8, cy + 1, cx - 2, cy + 5, cx - 2, cy + 1, fill="#f1f5f9", outline="#94a3b8")
        self.canvas.create_polygon(cx + 8, cy + 1, cx + 2, cy + 5, cx + 2, cy + 1, fill="#f1f5f9", outline="#94a3b8")

        self.canvas.create_oval(cx - 13, cy + 6, cx - 9, cy + 12, fill=c_skin, outline="")
        self.canvas.create_oval(cx + 9, cy + 6, cx + 13, cy + 12, fill=c_skin, outline="")
        self.canvas.create_rectangle(cx - 12, cy + 10, cx - 10, cy + 12, fill="#f43f5e", outline="")
        self.canvas.create_rectangle(cx + 10, cy + 10, cx + 12, cy + 12, fill="#f43f5e", outline="")

        self.canvas.create_rectangle(cx - 4, cy - 4, cx + 4, cy + 2, fill=c_skin, outline="")
        self.canvas.create_rectangle(cx - 5, cy - 2, cx + 5, cy, fill=c_choker, outline="")
        self.canvas.create_oval(cx - 1.5, cy - 1, cx + 1.5, cy + 2, fill="#cbd5e1", outline="")

        self.canvas.create_oval(cx - 19, cy - 13, cx - 14, cy - 6, fill=c_skin, outline="")
        self.canvas.create_oval(cx + 14, cy - 13, cx + 19, cy - 6, fill=c_skin, outline="")
        self.canvas.create_oval(cx - 18, cy - 10, cx - 16, cy - 7, outline="#e2e8f0", width=1.5)
        self.canvas.create_oval(cx + 16, cy - 10, cx + 18, cy - 7, outline="#e2e8f0", width=1.5)

        self.canvas.create_oval(cx - 16, cy - 23, cx + 16, cy + 1, fill=c_skin, outline="")

        is_blinking = (self.marin_blink > 84)
        if is_blinking:
            self.canvas.create_arc(cx - 13, cy - 11, cx - 4, cy - 4, start=20, extent=140, style="arc", width=2.5, outline="#881337")
            self.canvas.create_arc(cx + 4, cy - 11, cx + 13, cy - 4, start=20, extent=140, style="arc", width=2.5, outline="#881337")
        else:
            self.canvas.create_oval(cx - 13, cy - 14, cx - 4, cy - 3, fill="#ffffff", outline="")
            self.canvas.create_oval(cx + 4, cy - 14, cx + 13, cy - 3, fill="#ffffff", outline="")
            self.canvas.create_oval(cx - 12, cy - 13, cx - 5, cy - 4, fill=c_eyes, outline="")
            self.canvas.create_oval(cx + 5, cy - 13, cx + 12, cy - 4, fill=c_eyes, outline="")
            self.canvas.create_oval(cx - 10, cy - 11, cx - 7, cy - 6, fill="#4c0519", outline="")
            self.canvas.create_oval(cx + 7, cy - 11, cx + 10, cy - 6, fill="#4c0519", outline="")
            self.canvas.create_oval(cx - 11, cy - 13, cx - 8, cy - 9, fill="#ffffff", outline="")
            self.canvas.create_oval(cx - 7, cy - 7, cx - 5, cy - 5, fill="#ffffff", outline="")
            self.canvas.create_oval(cx + 6, cy - 13, cx + 9, cy - 9, fill="#ffffff", outline="")
            self.canvas.create_oval(cx + 10, cy - 7, cx + 12, cy - 5, fill="#ffffff", outline="")
            self.canvas.create_line(cx - 14, cy - 13, cx - 4, cy - 14, fill="#4c0519", width=2)
            self.canvas.create_line(cx + 4, cy - 14, cx + 14, cy - 13, fill="#4c0519", width=2)

        self.canvas.create_oval(cx - 14, cy - 5, cx - 8, cy - 1, fill="#fda4af", outline="")
        self.canvas.create_oval(cx + 8, cy - 5, cx + 14, cy - 1, fill="#fda4af", outline="")
        self.canvas.create_line(cx - 12, cy - 4, cx - 10, cy - 2, fill="#f43f5e")
        self.canvas.create_line(cx + 10, cy - 4, cx + 12, cy - 2, fill="#f43f5e")

        self.canvas.create_arc(cx - 4, cy - 4, cx + 4, cy + 2, start=0, extent=-180, style="arc", width=2, outline="#9f1239")
        self.canvas.create_polygon(cx - 1, cy - 1, cx + 2, cy - 1, cx + 0.5, cy + 1, fill="#ffffff", outline="")

        self.canvas.create_arc(cx - 17, cy - 25, cx + 17, cy - 9, start=0, extent=180, fill=c_gold_hair, outline=c_gold_dark)
        self.canvas.create_polygon(cx - 10, cy - 20, cx - 4, cy - 12, cx - 1, cy - 18, fill=c_gold_hair, outline="")
        self.canvas.create_polygon(cx - 2, cy - 18, cx + 3, cy - 11, cx + 6, cy - 19, fill=c_gold_hair, outline="")
        self.canvas.create_polygon(cx + 4, cy - 19, cx + 10, cy - 13, cx + 13, cy - 19, fill=c_gold_hair, outline="")

        self.canvas.create_polygon(cx - 16, cy - 15, cx - 12, cy - 5, cx - 14, cy + 2, cx - 18, cy - 8, fill=c_gold_hair, outline="")
        self.canvas.create_polygon(cx - 14, cy + 2, cx - 12, cy + 7, cx - 16, cy + 8, cx - 17, cy + 3, fill=c_pink_tips, outline="")
        self.canvas.create_polygon(cx + 16, cy - 15, cx + 12, cy - 5, cx + 14, cy + 2, cx + 18, cy - 8, fill=c_gold_hair, outline="")
        self.canvas.create_polygon(cx + 14, cy + 2, cx + 12, cy + 7, cx + 16, cy + 8, cx + 17, cy + 3, fill=c_pink_tips, outline="")

    # =============================================================
    # 4. КИБЕР-РОБОТ
    # =============================================================
    def draw_robot(self, cx, cy):
        ant_top_y = cy - 36
        bobble_color = "#38bdf8" if int(time.time() * 3) % 2 == 0 else "#22d3ee"
        self.canvas.create_line(cx, cy - 24, cx, ant_top_y, fill="#64748b", width=2)
        self.canvas.create_oval(cx - 4, ant_top_y - 4, cx + 4, ant_top_y + 4, fill=bobble_color, outline="")

        leg1_dy = math.sin(time.time() * 5) * 3 if self.state == "walk" else 0
        leg2_dy = math.sin(time.time() * 5 + math.pi) * 3 if self.state == "walk" else 0

        self.canvas.create_oval(cx - 18, cy + 18 + leg1_dy, cx - 8, cy + 28 + leg1_dy, fill="#1e293b", outline="#38bdf8")
        self.canvas.create_oval(cx + 8, cy + 18 + leg2_dy, cx + 18, cy + 28 + leg2_dy, fill="#1e293b", outline="#38bdf8")

        self.canvas.create_rectangle(cx - 24, cy - 22, cx + 24, cy + 20, fill="#0f172a", outline="#38bdf8", width=2)
        self.canvas.create_rectangle(cx - 18, cy - 14, cx + 18, cy + 10, fill="#020617", outline="#1e293b", width=1)

        self.canvas.create_oval(cx - 13, cy - 6, cx - 5, cy + 2, fill="#00f0ff", outline="")
        self.canvas.create_oval(cx + 5, cy - 6, cx + 13, cy + 2, fill="#00f0ff", outline="")


if __name__ == "__main__":
    app = NeverPetsApp()
    app.mainloop()
