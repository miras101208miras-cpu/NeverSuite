import os
import sys
import time
import shutil
import ctypes
import winreg
import threading
from tkinter import filedialog
from PIL import Image
import customtkinter as ctk

# Настройка темы CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WALLPAPERS_DIR = os.path.join(BASE_DIR, "assets", "wallpapers")
THUMBS_DIR = os.path.join(BASE_DIR, "assets", "thumbs")
os.makedirs(WALLPAPERS_DIR, exist_ok=True)
os.makedirs(THUMBS_DIR, exist_ok=True)

# Исходные встроенные обои с описанием и тегами
WALLPAPER_META = {
    "Synthwave_Sunset.jpg": {"title": "Synthwave Sunset & Neon Grid", "tag": "Synthwave", "color": "#ec4899"},
    "Minimalist_Dark_Space.jpg": {"title": "Minimalist Dark Space Nebula", "tag": "Minimalist", "color": "#8b5cf6"},
    "Anime_Sakura_LoFi.jpg": {"title": "Anime Sakura Lo-Fi Twilight", "tag": "Lo-Fi Art", "color": "#f43f5e"},
    "2_Неоновый_Киберпанк_Город.jpg": {"title": "Cyberpunk Neon Megapolis", "tag": "Cyberpunk", "color": "#06b6d4"},
    "1_Темные_Горы_и_Сияние.jpg": {"title": "Dark Mountain Aurora Borealis", "tag": "Nature Glow", "color": "#10b981"},
    "4_Океаническая_Арка_Закат.jpg": {"title": "4K Oceanic Arch Sunset", "tag": "Ultra HD", "color": "#f59e0b"},
    "3_Темный_Графит_Металлик.jpg": {"title": "Dark Graphite Metallic Wave", "tag": "Abstract", "color": "#64748b"},
    "5_Неоновый_Пурпур.jpg": {"title": "Deep Neon Violet Dimension", "tag": "Neon", "color": "#a855f7"},
}


class WindowsCustomizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("🎨 Windows Customizer & Style Studio — Glass Edition")
        self.geometry("980x680")
        self.minsize(920, 620)

        # Эффект стекла: полупрозрачность окна, чтобы обои рабочего стола просвечивали
        self.window_alpha = 0.94
        try:
            self.attributes("-alpha", self.window_alpha)
        except Exception:
            pass

        # Данные галереи
        self.wallpapers_list = []
        self.thumbnail_images = {}
        self.preview_image_obj = None
        self.selected_wallpaper_path = None
        self.card_frames = {}

        # Создание структуры UI
        self.create_layout()

        # Загрузка обоев
        self.refresh_wallpapers_list()

        # Стартовая вкладка
        self.switch_tab("wallpapers")
        self.log("✨ Windows Customizer Glass Studio успешно запущена!")

    def create_layout(self):
        # Главная сетка: левый сайдбар и правая область контента
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ----------------- ЛЕВЫЙ САЙДБАР (Стеклянная панель управления) -----------------
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#11111b", border_width=1, border_color="#1e1e2e")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)

        # Логотип и заголовок
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.grid(row=0, column=0, padx=16, pady=(20, 15), sticky="w")

        lbl_logo = ctk.CTkLabel(brand_frame, text="🎨", font=ctk.CTkFont(size=28))
        lbl_logo.pack(side="left", padx=(0, 10))

        title_box = ctk.CTkFrame(brand_frame, fg_color="transparent")
        title_box.pack(side="left")
        lbl_title = ctk.CTkLabel(title_box, text="CUSTOMIZER", font=ctk.CTkFont(size=16, weight="bold"), text_color="#cba6f7")
        lbl_title.pack(anchor="w")
        lbl_sub = ctk.CTkLabel(title_box, text="Glass Edition v2.0", font=ctk.CTkFont(size=11), text_color="#a6adc8")
        lbl_sub.pack(anchor="w")

        # Разделитель
        sep1 = ctk.CTkFrame(self.sidebar, height=1, fg_color="#313244")
        sep1.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 15))

        # Навигационные кнопки
        self.nav_buttons = {}
        nav_items = [
            ("wallpapers", "🖼️ Галерея Обоев"),
            ("themes", "🌓 Оформление и Цвета"),
            ("tweaks", "⚡ Эффекты и Твики"),
            ("console", "📜 Журнал событий"),
        ]

        for i, (key, text) in enumerate(nav_items, start=2):
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                font=ctk.CTkFont(size=13, weight="bold"),
                height=42,
                corner_radius=8,
                fg_color="transparent",
                text_color="#cdd6f4",
                hover_color="#1e1e2e",
                anchor="w",
                command=lambda k=key: self.switch_tab(k)
            )
            btn.grid(row=i, column=0, padx=12, pady=4, sticky="ew")
            self.nav_buttons[key] = btn

        # Ползунок прозрачности окна (Acrylic / Glass)
        trans_frame = ctk.CTkFrame(self.sidebar, corner_radius=8, fg_color="#181825", border_width=1, border_color="#313244")
        trans_frame.grid(row=7, column=0, padx=12, pady=(15, 5), sticky="ew")

        trans_title = ctk.CTkLabel(trans_frame, text="🔮 Прозрачность окна", font=ctk.CTkFont(size=11, weight="bold"), text_color="#89b4fa")
        trans_title.pack(anchor="w", padx=10, pady=(8, 2))

        self.alpha_slider = ctk.CTkSlider(
            trans_frame,
            from_=0.75,
            to=1.00,
            number_of_steps=25,
            command=self.on_alpha_change,
            height=16,
            button_color="#cba6f7",
            button_hover_color="#b4befe",
            progress_color="#89b4fa"
        )
        self.alpha_slider.set(self.window_alpha)
        self.alpha_slider.pack(fill="x", padx=10, pady=(2, 4))

        self.alpha_val_lbl = ctk.CTkLabel(trans_frame, text=f"{int(self.window_alpha * 100)}% (Glass Acrylic)", font=ctk.CTkFont(size=10), text_color="#a6adc8")
        self.alpha_val_lbl.pack(anchor="e", padx=10, pady=(0, 6))

        # Нижний статусбар в сайдбаре
        status_card = ctk.CTkFrame(self.sidebar, corner_radius=8, fg_color="#181825", border_width=1, border_color="#313244")
        status_card.grid(row=9, column=0, padx=12, pady=12, sticky="ew")

        lbl_s_title = ctk.CTkLabel(status_card, text="● СИСТЕМА ГОТОВА", font=ctk.CTkFont(size=11, weight="bold"), text_color="#a6e3a1")
        lbl_s_title.pack(anchor="w", padx=10, pady=(8, 2))
        self.lbl_s_sub = ctk.CTkLabel(status_card, text="Обоев доступно: 0", font=ctk.CTkFont(size=10), text_color="#9399b2")
        self.lbl_s_sub.pack(anchor="w", padx=10, pady=(0, 8))

        # ----------------- ПРАВАЯ ОБЛАСТЬ КОНТЕНТА -----------------
        self.content_area = ctk.CTkFrame(self, corner_radius=0, fg_color="#181825")
        self.content_area.grid(row=0, column=1, sticky="nsew")
        self.content_area.grid_rowconfigure(1, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        # Верхний топбар уведомлений / Тост
        self.topbar = ctk.CTkFrame(self.content_area, height=44, corner_radius=8, fg_color="#1e1e2e", border_width=1, border_color="#313244")
        self.topbar.grid(row=0, column=0, padx=16, pady=(12, 6), sticky="ew")

        self.toast_lbl = ctk.CTkLabel(
            self.topbar,
            text="✨ Выберите обои или настройте визуальный стиль системы в 1 клик",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#cdd6f4"
        )
        self.toast_lbl.pack(side="left", padx=16, pady=8)

        # Контейнер для анимированных вкладок
        self.tabs_container = ctk.CTkFrame(self.content_area, corner_radius=0, fg_color="transparent")
        self.tabs_container.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 12))
        self.tabs_container.grid_rowconfigure(0, weight=1)
        self.tabs_container.grid_columnconfigure(0, weight=1)

        # Создаем экраны вкладок
        self.tab_frames = {}
        self.create_wallpapers_tab()
        self.create_themes_tab()
        self.create_tweaks_tab()
        self.create_console_tab()

    # -------------------------------------------------------------
    # АНИМАЦИИ И ПЕРЕКЛЮЧЕНИЕ ВКЛАДОК
    # -------------------------------------------------------------
    def switch_tab(self, target_key):
        for key, btn in self.nav_buttons.items():
            if key == target_key:
                btn.configure(fg_color="#313244", text_color="#cba6f7")
            else:
                btn.configure(fg_color="transparent", text_color="#cdd6f4")

        # Анимация плавного появления новой вкладки
        target_frame = self.tab_frames[target_key]
        for key, frame in self.tab_frames.items():
            if key != target_key:
                frame.place_forget()

        # Эффект плавного скольжения (Slide-up Fade-in Animation)
        self.animate_slide_in(target_frame)

    def animate_slide_in(self, frame, step=0):
        # 5 шагов смещения по rely от 0.03 до 0.0
        offsets = [0.035, 0.022, 0.012, 0.005, 0.0]
        if step < len(offsets):
            frame.place(relx=0, rely=offsets[step], relwidth=1.0, relheight=1.0 - offsets[step])
            self.after(14, lambda: self.animate_slide_in(frame, step + 1))
        else:
            frame.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)

    def on_alpha_change(self, val):
        self.window_alpha = round(val, 2)
        try:
            self.attributes("-alpha", self.window_alpha)
        except Exception:
            pass
        self.alpha_val_lbl.configure(text=f"{int(self.window_alpha * 100)}% (Glass Acrylic)")

    def show_toast(self, message, color="#a6e3a1"):
        self.toast_lbl.configure(text=message, text_color=color)
        # Анимация мигания рамки топбара
        self.topbar.configure(border_color=color)
        self.after(2200, lambda: self.topbar.configure(border_color="#313244"))

    def log(self, text):
        t = time.strftime("%H:%M:%S")
        msg = f"[{t}] {text}\n"
        if hasattr(self, "log_textbox"):
            self.log_textbox.insert("end", msg)
            self.log_textbox.see("end")

    # -------------------------------------------------------------
    # ВКЛАДКА 1: ГАЛЕРЕЯ ОБОЕВ С ЖИВЫМ ПРЕВЬЮ
    # -------------------------------------------------------------
    def create_wallpapers_tab(self):
        tab = ctk.CTkFrame(self.tabs_container, fg_color="transparent")
        self.tab_frames["wallpapers"] = tab

        # Вкладка делится на:
        # Верхний Preview Hero Card (Предпросмотр выбранных обоев)
        # Нижний Scrollable Frame с карточками обоев

        # --- HERO PREVIEW CARD ---
        self.preview_card = ctk.CTkFrame(tab, corner_radius=12, fg_color="#1e1e2e", border_width=1, border_color="#313244")
        self.preview_card.pack(fill="x", pady=(0, 10))

        # Внутренний контейнер для Hero
        hero_box = ctk.CTkFrame(self.preview_card, fg_color="transparent")
        hero_box.pack(fill="x", padx=14, pady=12)

        # Превью картинка
        self.preview_img_lbl = ctk.CTkLabel(hero_box, text="", width=240, height=135)
        self.preview_img_lbl.pack(side="left", padx=(0, 16))

        # Описание превью
        info_col = ctk.CTkFrame(hero_box, fg_color="transparent")
        info_col.pack(side="left", fill="both", expand=True)

        self.preview_badge = ctk.CTkLabel(
            info_col,
            text="АКТИВНЫЕ ОБОИ",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#cba6f7",
            fg_color="#313244",
            corner_radius=4,
            padx=8,
            pady=2
        )
        self.preview_badge.pack(anchor="w", pady=(0, 4))

        self.preview_title_lbl = ctk.CTkLabel(
            info_col,
            text="Выберите обои для предварительного просмотра",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#cdd6f4"
        )
        self.preview_title_lbl.pack(anchor="w", pady=(0, 4))

        self.preview_details_lbl = ctk.CTkLabel(
            info_col,
            text="Разрешение: —  •  Формат: —  •  Путь: —",
            font=ctk.CTkFont(size=12),
            text_color="#a6adc8"
        )
        self.preview_details_lbl.pack(anchor="w", pady=(0, 12))

        # Кнопки действий над выбранными обоями
        btn_action_row = ctk.CTkFrame(info_col, fg_color="transparent")
        btn_action_row.pack(anchor="w")

        self.btn_apply_hero = ctk.CTkButton(
            btn_action_row,
            text="🚀 Установить на рабочий стол",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#89b4fa",
            text_color="#11111b",
            hover_color="#b4befe",
            height=36,
            corner_radius=8,
            command=self.apply_current_preview
        )
        self.btn_apply_hero.pack(side="left", padx=(0, 10))

        btn_add_custom = ctk.CTkButton(
            btn_action_row,
            text="➕ Добавить свои обои...",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#313244",
            hover_color="#45475a",
            height=36,
            corner_radius=8,
            command=self.prompt_add_custom_wallpaper
        )
        btn_add_custom.pack(side="left", padx=(0, 8))

        btn_open_folder = ctk.CTkButton(
            btn_action_row,
            text="📂 Папка с обоями",
            font=ctk.CTkFont(size=12),
            fg_color="#1e1e2e",
            hover_color="#313244",
            border_width=1,
            border_color="#45475a",
            height=36,
            corner_radius=8,
            command=self.open_wallpapers_folder
        )
        btn_open_folder.pack(side="left")

        # --- СЕКЦИЯ ГАЛЕРЕИ (Скроллбар с карточками) ---
        gal_header = ctk.CTkFrame(tab, fg_color="transparent")
        gal_header.pack(fill="x", pady=(4, 6))

        gal_title = ctk.CTkLabel(
            gal_header,
            text="✨ Коллекция HD/4K Обоев (Кликните карточку для применения):",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#cdd6f4"
        )
        gal_title.pack(side="left")

        btn_refresh = ctk.CTkButton(
            gal_header,
            text="🔄 Обновить",
            width=80,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#313244",
            hover_color="#45475a",
            command=self.refresh_wallpapers_list
        )
        btn_refresh.pack(side="right")

        self.gallery_scroll = ctk.CTkScrollableFrame(tab, corner_radius=10, fg_color="#11111b", border_width=1, border_color="#1e1e2e")
        self.gallery_scroll.pack(fill="both", expand=True)
        self.gallery_scroll.grid_columnconfigure((0, 1), weight=1)

    def refresh_wallpapers_list(self):
        # Сканируем папку assets/wallpapers
        exts = (".jpg", ".jpeg", ".png", ".webp", ".bmp")
        files = [f for f in os.listdir(WALLPAPERS_DIR) if f.lower().endswith(exts)]
        self.wallpapers_list = files

        # Обновляем статус
        self.lbl_s_sub.configure(text=f"Обоев доступно: {len(files)}")

        # Очищаем старые карточки
        for widget in self.gallery_scroll.winfo_children():
            widget.destroy()
        self.card_frames.clear()

        # Генерируем карточки в 2 колонки
        for idx, fname in enumerate(files):
            fpath = os.path.join(WALLPAPERS_DIR, fname)
            meta = WALLPAPER_META.get(fname, {
                "title": os.path.splitext(fname)[0].replace("_", " "),
                "tag": "Пользовательские",
                "color": "#89b4fa"
            })

            # Подготовка миниатюры (lazy cache)
            thumb_path = os.path.join(THUMBS_DIR, fname)
            if not os.path.exists(thumb_path):
                try:
                    with Image.open(fpath) as img:
                        img = img.convert("RGB")
                        img.thumbnail((240, 135), Image.Resampling.LANCZOS)
                        img.save(thumb_path, "JPEG", quality=85)
                except Exception as e:
                    self.log(f"Ошибка создания превью {fname}: {e}")

            # Загрузка CTkImage
            if fname not in self.thumbnail_images:
                try:
                    t_img = Image.open(thumb_path)
                    ctk_thumb = ctk.CTkImage(light_image=t_img, dark_image=t_img, size=(190, 105))
                    self.thumbnail_images[fname] = ctk_thumb
                except Exception:
                    self.thumbnail_images[fname] = None

            card = self.create_wallpaper_card(idx, fname, fpath, meta)
            self.card_frames[fpath] = card

        # Если ничего не выбрано, выбираем первую
        if files and not self.selected_wallpaper_path:
            first_path = os.path.join(WALLPAPERS_DIR, files[0])
            self.select_wallpaper(first_path)

    def create_wallpaper_card(self, idx, fname, fpath, meta):
        row = idx // 2
        col = idx % 2

        card = ctk.CTkFrame(
            self.gallery_scroll,
            corner_radius=10,
            fg_color="#1e1e2e",
            border_width=1,
            border_color="#313244",
            cursor="hand2"
        )
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        # Внутренний контейнер
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=10, pady=10)

        # Миниатюра
        thumb_img = self.thumbnail_images.get(fname)
        if thumb_img:
            img_lbl = ctk.CTkLabel(inner, image=thumb_img, text="")
            img_lbl.pack(pady=(0, 8))
        else:
            img_lbl = ctk.CTkLabel(inner, text="🖼️ [Изображение]", height=105)
            img_lbl.pack(pady=(0, 8))

        # Заголовок и тег
        tag_lbl = ctk.CTkLabel(
            inner,
            text=f"● {meta['tag']}",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=meta.get("color", "#cba6f7")
        )
        tag_lbl.pack(anchor="w")

        title_lbl = ctk.CTkLabel(
            inner,
            text=meta["title"],
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#cdd6f4",
            anchor="w",
            wraplength=200,
            justify="left"
        )
        title_lbl.pack(anchor="w", fill="x", pady=(2, 6))

        # Кнопка быстрой установки
        btn_apply = ctk.CTkButton(
            inner,
            text="Применить обои",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=28,
            corner_radius=6,
            fg_color=meta.get("color", "#313244"),
            hover_color="#585b70",
            command=lambda p=fpath, m=meta: self.apply_wallpaper(p, m["title"])
        )
        btn_apply.pack(fill="x", pady=(4, 0))

        # Анимация подсветки при наведении курсора (Hover Glow)
        def on_enter(e, c=card, col=meta.get("color", "#cba6f7")):
            if fpath != self.selected_wallpaper_path:
                c.configure(border_color=col, border_width=2, fg_color="#252538")

        def on_leave(e, c=card):
            if fpath != self.selected_wallpaper_path:
                c.configure(border_color="#313244", border_width=1, fg_color="#1e1e2e")

        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        card.bind("<Button-1>", lambda e, p=fpath: self.select_wallpaper(p))
        if thumb_img:
            img_lbl.bind("<Button-1>", lambda e, p=fpath: self.select_wallpaper(p))
            img_lbl.bind("<Enter>", on_enter)
            img_lbl.bind("<Leave>", on_leave)
        title_lbl.bind("<Button-1>", lambda e, p=fpath: self.select_wallpaper(p))

        return card

    def select_wallpaper(self, fpath):
        if not os.path.exists(fpath):
            return

        # Снимаем выделение со старой карточки
        if self.selected_wallpaper_path and self.selected_wallpaper_path in self.card_frames:
            old_card = self.card_frames[self.selected_wallpaper_path]
            old_card.configure(border_color="#313244", border_width=1, fg_color="#1e1e2e")

        self.selected_wallpaper_path = fpath

        # Подсвечиваем выбранную карточку
        if fpath in self.card_frames:
            new_card = self.card_frames[fpath]
            new_card.configure(border_color="#a6e3a1", border_width=2, fg_color="#242b35")

        # Обновляем Hero Preview Card
        fname = os.path.basename(fpath)
        meta = WALLPAPER_META.get(fname, {
            "title": os.path.splitext(fname)[0].replace("_", " "),
            "tag": "Пользовательские",
            "color": "#89b4fa"
        })

        try:
            with Image.open(fpath) as img:
                w, h = img.size
                preview_thumb = img.convert("RGB")
                preview_thumb.thumbnail((240, 135), Image.Resampling.LANCZOS)
                self.preview_image_obj = ctk.CTkImage(light_image=preview_thumb, dark_image=preview_thumb, size=(240, 135))
                self.preview_img_lbl.configure(image=self.preview_image_obj)
                res_str = f"{w}x{h}"
                if w >= 3840:
                    badge_txt = "4K ULTRA HD"
                elif w >= 1920:
                    badge_txt = "FULL HD 1080P"
                else:
                    badge_txt = "HD READY"
        except Exception as e:
            res_str = "Ошибка чтения"
            badge_txt = "HD"

        self.preview_title_lbl.configure(text=meta["title"])
        self.preview_badge.configure(text=f"● {badge_txt}  •  {meta['tag']}", text_color=meta.get("color", "#cba6f7"))
        size_kb = os.path.getsize(fpath) // 1024
        self.preview_details_lbl.configure(text=f"Разрешение: {res_str}  •  Размер: {size_kb} КБ  •  Файл: {fname}")

    def apply_current_preview(self):
        if self.selected_wallpaper_path:
            fname = os.path.basename(self.selected_wallpaper_path)
            meta = WALLPAPER_META.get(fname, {"title": fname})
            self.apply_wallpaper(self.selected_wallpaper_path, meta["title"])

    def apply_wallpaper(self, path, title):
        if not os.path.exists(path):
            self.log(f"❌ Файл обоев не найден: {path}")
            return

        def task():
            try:
                # SPI_SETDESKWALLPAPER = 20, SPIF_UPDATEINIFILE = 1, SPIF_SENDCHANGE = 2
                abs_path = os.path.abspath(path)
                res = ctypes.windll.user32.SystemParametersInfoW(20, 0, abs_path, 3)
                if res:
                    self.log(f"✔ Обои рабочего стола успешно обновлены: «{title}»!")
                    self.after(0, lambda: self.show_toast(f"🎉 Обои «{title}» применены на рабочий стол!", "#a6e3a1"))
                else:
                    self.log(f"⚠ SystemParametersInfoW вернул статус 0 при установке {title}")
            except Exception as e:
                self.log(f"❌ Ошибка установки обоев: {e}")
                self.after(0, lambda: self.show_toast(f"Ошибка установки обоев: {e}", "#f38ba8"))

        threading.Thread(target=task, daemon=True).start()

    def prompt_add_custom_wallpaper(self):
        filetypes = [
            ("Изображения (Wallpaper Images)", "*.jpg;*.jpeg;*.png;*.webp;*.bmp"),
            ("Все файлы", "*.*")
        ]
        selected = filedialog.askopenfilename(title="Выберите обои для добавления в студию", filetypes=filetypes)
        if selected and os.path.exists(selected):
            fname = os.path.basename(selected)
            dest = os.path.join(WALLPAPERS_DIR, fname)
            try:
                if os.path.abspath(selected) != os.path.abspath(dest):
                    shutil.copy2(selected, dest)
                self.log(f"✔ Новые обои добавлены в коллекцию: {fname}")
                self.refresh_wallpapers_list()
                self.select_wallpaper(dest)
                self.show_toast(f"✨ Обои «{fname}» добавлены в студию!", "#cba6f7")
            except Exception as e:
                self.log(f"❌ Ошибка копирования файла: {e}")

    def open_wallpapers_folder(self):
        try:
            os.startfile(WALLPAPERS_DIR)
        except Exception as e:
            self.log(f"Ошибка открытия папки: {e}")

    # -------------------------------------------------------------
    # ВКЛАДКА 2: ОФОРМЛЕНИЕ И СИСТЕМНЫЕ ТЕМЫ
    # -------------------------------------------------------------
    def create_themes_tab(self):
        tab = ctk.CTkFrame(self.tabs_container, fg_color="transparent")
        self.tab_frames["themes"] = tab

        # Блок системной темы
        box = ctk.CTkFrame(tab, corner_radius=10, fg_color="#1e1e2e", border_width=1, border_color="#313244")
        box.pack(fill="x", pady=8, padx=4)

        lbl = ctk.CTkLabel(box, text="🌓 Системная тема Windows 10/11", font=ctk.CTkFont(size=15, weight="bold"), text_color="#fab387")
        lbl.pack(anchor="w", padx=16, pady=(14, 6))

        sub = ctk.CTkLabel(box, text="Мгновенно переключает системную тему Windows, панели задач и приложений через системный реестр.", font=ctk.CTkFont(size=12), text_color="#a6adc8")
        sub.pack(anchor="w", padx=16, pady=(0, 12))

        btn_row = ctk.CTkFrame(box, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 16))

        btn_dark = ctk.CTkButton(
            btn_row,
            text="🌙 Включить Тёмную тему",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#313244",
            hover_color="#45475a",
            height=38,
            command=lambda: self.set_system_theme(dark=True)
        )
        btn_dark.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_light = ctk.CTkButton(
            btn_row,
            text="☀️ Включить Светлую тему",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#cdd6f4",
            text_color="#11111b",
            hover_color="#bac2de",
            height=38,
            command=lambda: self.set_system_theme(dark=False)
        )
        btn_light.pack(side="left", fill="x", expand=True, padx=(8, 0))

        # Блок акцентных цветов интерфейса
        box_colors = ctk.CTkFrame(tab, corner_radius=10, fg_color="#1e1e2e", border_width=1, border_color="#313244")
        box_colors.pack(fill="x", pady=8, padx=4)

        lbl_c = ctk.CTkLabel(box_colors, text="🎨 Акцентные неоновые палитры Studio", font=ctk.CTkFont(size=15, weight="bold"), text_color="#cba6f7")
        lbl_c.pack(anchor="w", padx=16, pady=(14, 6))

        sub_c = ctk.CTkLabel(box_colors, text="Выберите цветовую гармонию студии кастомизации:", font=ctk.CTkFont(size=12), text_color="#a6adc8")
        sub_c.pack(anchor="w", padx=16, pady=(0, 12))

        color_presets = [
            ("Киберпанк Циан", "#06b6d4"),
            ("Неоновый Мов", "#cba6f7"),
            ("Синтвейв Розовый", "#ec4899"),
            ("Изумрудный Неон", "#10b981"),
            ("Закатный Янтарь", "#f59e0b"),
        ]

        preset_row = ctk.CTkFrame(box_colors, fg_color="transparent")
        preset_row.pack(fill="x", padx=16, pady=(0, 16))

        for name, col in color_presets:
            p_btn = ctk.CTkButton(
                preset_row,
                text=name,
                fg_color=col,
                hover_color="#ffffff",
                height=32,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#11111b",
                command=lambda c=col, n=name: self.set_studio_accent(c, n)
            )
            p_btn.pack(side="left", fill="x", expand=True, padx=4)

    def set_studio_accent(self, color, name):
        self.btn_apply_hero.configure(fg_color=color)
        self.topbar.configure(border_color=color)
        self.show_toast(f"✨ Акцентный цвет изменен: {name} ({color})!", color)
        self.log(f"✔ Применен акцентный стиль интерфейса: {name}")

    def set_system_theme(self, dark=True):
        val = 0 if dark else 1
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, val)
                winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, val)
            mode_name = "Тёмная" if dark else "Светлая"
            self.log(f"✔ Системная тема Windows переключена: {mode_name}!")
            self.show_toast(f"✔ Системная тема изменена: {mode_name}!", "#a6e3a1")
        except Exception as e:
            self.log(f"❌ Ошибка смены темы в реестре: {e}")

    # -------------------------------------------------------------
    # ВКЛАДКА 3: ЭФФЕКТЫ И ПАНЕЛЬ ЗАДАЧ (ТВИКИ)
    # -------------------------------------------------------------
    def create_tweaks_tab(self):
        tab = ctk.CTkFrame(self.tabs_container, fg_color="transparent")
        self.tab_frames["tweaks"] = tab

        # Блок TranslucentTB
        box_tb = ctk.CTkFrame(tab, corner_radius=10, fg_color="#1e1e2e", border_width=1, border_color="#313244")
        box_tb.pack(fill="x", pady=8, padx=4)

        lbl_tb = ctk.CTkLabel(box_tb, text="💎 Прозрачность панели задач (TranslucentTB)", font=ctk.CTkFont(size=15, weight="bold"), text_color="#a6e3a1")
        lbl_tb.pack(anchor="w", padx=16, pady=(14, 6))

        sub_tb = ctk.CTkLabel(box_tb, text="Управляет утилитой TranslucentTB для кристальной прозрачности панели задач Windows 10/11.", font=ctk.CTkFont(size=12), text_color="#a6adc8")
        sub_tb.pack(anchor="w", padx=16, pady=(0, 12))

        tb_row = ctk.CTkFrame(box_tb, fg_color="transparent")
        tb_row.pack(fill="x", padx=16, pady=(0, 16))

        btn_trans = ctk.CTkButton(
            tb_row,
            text="🔄 Перезапустить TranslucentTB",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            height=38,
            command=self.restart_translucent
        )
        btn_trans.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_tb_task = ctk.CTkButton(
            tb_row,
            text="🛑 Завершить процесс TB",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#313244",
            hover_color="#45475a",
            height=38,
            command=self.kill_translucent
        )
        btn_tb_task.pack(side="left", fill="x", expand=True, padx=(8, 0))

        # Блок скорости окон
        box_speed = ctk.CTkFrame(tab, corner_radius=10, fg_color="#1e1e2e", border_width=1, border_color="#313244")
        box_speed.pack(fill="x", pady=8, padx=4)

        lbl_sp = ctk.CTkLabel(box_speed, text="⚡ Оптимизация скорости анимаций Windows", font=ctk.CTkFont(size=15, weight="bold"), text_color="#f59e0b")
        lbl_sp.pack(anchor="w", padx=16, pady=(14, 6))

        sub_sp = ctk.CTkLabel(box_speed, text="Отключение системных задержек меню и всплывающих окон (0 мс) для мгновенного отклика.", font=ctk.CTkFont(size=12), text_color="#a6adc8")
        sub_sp.pack(anchor="w", padx=16, pady=(0, 12))

        sp_row = ctk.CTkFrame(box_speed, fg_color="transparent")
        sp_row.pack(fill="x", padx=16, pady=(0, 16))

        btn_ultra = ctk.CTkButton(
            sp_row,
            text="⚡ Турбо-скорость окон (0 мс задержки)",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#d97706",
            hover_color="#b45309",
            height=38,
            command=self.enable_ultra_speed_ui
        )
        btn_ultra.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_restart_exp = ctk.CTkButton(
            sp_row,
            text="🔄 Перезапустить Проводник Windows",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#313244",
            hover_color="#45475a",
            height=38,
            command=self.restart_explorer
        )
        btn_restart_exp.pack(side="left", fill="x", expand=True, padx=(8, 0))

    def restart_translucent(self):
        try:
            os.system("taskkill /f /im TranslucentTB.exe >nul 2>&1")
            os.system("start explorer.exe shell:AppsFolder\\28017CharlesMilette.TranslucentTB_v826wp6bftszj!TranslucentTB")
            self.log("✔ Прозрачность панели задач перезапущена!")
            self.show_toast("✔ TranslucentTB перезапущен!", "#a6e3a1")
        except Exception as e:
            self.log(f"Ошибка перезапуска TranslucentTB: {e}")

    def kill_translucent(self):
        try:
            os.system("taskkill /f /im TranslucentTB.exe >nul 2>&1")
            self.log("✔ Процесс TranslucentTB остановлен.")
            self.show_toast("TranslucentTB остановлен", "#f38ba8")
        except Exception as e:
            self.log(f"Ошибка: {e}")

    def enable_ultra_speed_ui(self):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop\WindowMetrics", 0, winreg.KEY_SET_VALUE) as k:
                winreg.SetValueEx(k, "MinAnimate", 0, winreg.REG_SZ, "0")
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, winreg.KEY_SET_VALUE) as k:
                winreg.SetValueEx(k, "MenuShowDelay", 0, winreg.REG_SZ, "0")
            self.log("✔ Режим максимальной скорости применен (анимации 0 мс)!")
            self.show_toast("⚡ Режим турбо-скорости активирован!", "#fab387")
        except Exception as e:
            self.log(f"Ошибка реестра: {e}")

    def restart_explorer(self):
        def task():
            self.log("Перезапуск Проводника Windows (explorer.exe)...")
            os.system("taskkill /f /im explorer.exe >nul 2>&1")
            time.sleep(1)
            os.system("start explorer.exe")
            self.log("✔ Проводник Windows успешно перезапущен!")
            self.after(0, lambda: self.show_toast("✔ Проводник перезапущен!", "#a6e3a1"))
        threading.Thread(target=task, daemon=True).start()

    # -------------------------------------------------------------
    # ВКЛАДКА 4: ЖУРНАЛ И КОНСОЛЬ
    # -------------------------------------------------------------
    def create_console_tab(self):
        tab = ctk.CTkFrame(self.tabs_container, fg_color="transparent")
        self.tab_frames["console"] = tab

        box = ctk.CTkFrame(tab, corner_radius=10, fg_color="#1e1e2e", border_width=1, border_color="#313244")
        box.pack(fill="both", expand=True, pady=8, padx=4)

        top_row = ctk.CTkFrame(box, fg_color="transparent")
        top_row.pack(fill="x", padx=16, pady=(12, 6))

        lbl = ctk.CTkLabel(top_row, text="📜 Журнал работы Customizer Studio", font=ctk.CTkFont(size=14, weight="bold"), text_color="#cdd6f4")
        lbl.pack(side="left")

        btn_clear = ctk.CTkButton(
            top_row,
            text="Очистить лог",
            width=90,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#313244",
            hover_color="#45475a",
            command=self.clear_log
        )
        btn_clear.pack(side="right")

        self.log_textbox = ctk.CTkTextbox(
            box,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#11111b",
            text_color="#a6adc8",
            corner_radius=8
        )
        self.log_textbox.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def clear_log(self):
        if hasattr(self, "log_textbox"):
            self.log_textbox.delete("1.0", "end")
            self.log("Журнал очищен.")


if __name__ == "__main__":
    app = WindowsCustomizerApp()
    app.mainloop()
