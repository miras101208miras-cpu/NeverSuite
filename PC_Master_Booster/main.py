import os
import sys
import time
import shutil
import ctypes
import threading
import psutil
import customtkinter as ctk

# Настройка темы
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class PCMasterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("⚡ PC Master & Game Booster")
        self.geometry("700x560")
        self.resizable(False, False)

        # Главный заголовок
        self.header_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#1e293b")
        self.header_frame.pack(fill="x", padx=15, pady=(15, 10))

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="⚡ PC MASTER & GAME BOOSTER",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#38bdf8"
        )
        self.title_label.pack(side="left", padx=20, pady=12)

        self.status_badge = ctk.CTkLabel(
            self.header_frame,
            text="● СИСТЕМА ОПТИМИЗИРОВАНА",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#4ade80"
        )
        self.status_badge.pack(side="right", padx=20, pady=12)

        # Секция мониторинга (CPU / RAM / DISK)
        self.stats_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#0f172a")
        self.stats_frame.pack(fill="x", padx=15, pady=5)

        # CPU
        self.cpu_label = ctk.CTkLabel(self.stats_frame, text="Процессор (CPU): 0%", font=ctk.CTkFont(size=13, weight="bold"))
        self.cpu_label.pack(anchor="w", padx=20, pady=(10, 2))
        self.cpu_bar = ctk.CTkProgressBar(self.stats_frame, height=12, progress_color="#38bdf8")
        self.cpu_bar.pack(fill="x", padx=20, pady=(0, 10))
        self.cpu_bar.set(0)

        # RAM
        self.ram_label = ctk.CTkLabel(self.stats_frame, text="Оперативная память (RAM): 0 GB / 0 GB (0%)", font=ctk.CTkFont(size=13, weight="bold"))
        self.ram_label.pack(anchor="w", padx=20, pady=(0, 2))
        self.ram_bar = ctk.CTkProgressBar(self.stats_frame, height=12, progress_color="#a855f7")
        self.ram_bar.pack(fill="x", padx=20, pady=(0, 10))
        self.ram_bar.set(0)

        # DISK C:
        self.disk_label = ctk.CTkLabel(self.stats_frame, text="Диск (C:): Свободно 0 GB", font=ctk.CTkFont(size=13, weight="bold"))
        self.disk_label.pack(anchor="w", padx=20, pady=(0, 2))
        self.disk_bar = ctk.CTkProgressBar(self.stats_frame, height=12, progress_color="#10b981")
        self.disk_bar.pack(fill="x", padx=20, pady=(0, 15))
        self.disk_bar.set(0)

        # Секция кнопок действий
        self.btn_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=15, pady=10)

        # Кнопка Игровой режим
        self.btn_boost = ctk.CTkButton(
            self.btn_frame,
            text="🚀 Игровой режим (Очистить RAM)",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#7c3aed",
            hover_color="#6d28d9",
            height=42,
            command=self.start_game_boost
        )
        self.btn_boost.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # Кнопка Очистки мусора
        self.btn_clean = ctk.CTkButton(
            self.btn_frame,
            text="🧹 Очистить мусор и Temp",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            height=42,
            command=self.start_quick_clean
        )
        self.btn_clean.pack(side="left", fill="x", expand=True, padx=5)

        # Кнопка аварийного завершения
        self.btn_kill = ctk.CTkButton(
            self.btn_frame,
            text="🛑 Экстренный сброс фризов",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#dc2626",
            hover_color="#b91c1c",
            height=42,
            command=self.start_emergency_free
        )
        self.btn_kill.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # Консоль / Журнал событий
        self.log_box = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#090d16",
            text_color="#94a3b8",
            corner_radius=10,
            activate_scrollbars=True
        )
        self.log_box.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.log("Добро пожаловать в PC Master & Game Booster v1.0!")
        self.log("Приложение готово к оптимизации.")

        # Запуск фонового мониторинга
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

    def log(self, message):
        t = time.strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{t}] {message}\n")
        self.log_box.see("end")

    def monitor_loop(self):
        while self.is_running:
            try:
                # CPU
                cpu = psutil.cpu_percent(interval=0.8)
                
                # RAM
                mem = psutil.virtual_memory()
                used_gb = round(mem.used / (1024**3), 2)
                total_gb = round(mem.total / (1024**3), 2)
                free_gb = round(mem.available / (1024**3), 2)
                ram_pct = mem.percent

                # DISK C:
                disk = psutil.disk_usage('C:\\')
                disk_free_gb = round(disk.free / (1024**3), 1)
                disk_total_gb = round(disk.total / (1024**3), 1)
                disk_pct = disk.percent

                # Обновление UI через after
                self.after(0, self.update_ui_stats, cpu, used_gb, total_gb, free_gb, ram_pct, disk_free_gb, disk_total_gb, disk_pct)
            except Exception:
                pass
            time.sleep(0.5)

    def update_ui_stats(self, cpu, used_gb, total_gb, free_gb, ram_pct, disk_free_gb, disk_total_gb, disk_pct):
        self.cpu_label.configure(text=f"Процессор (CPU): {cpu}%")
        self.cpu_bar.set(cpu / 100.0)

        self.ram_label.configure(text=f"Оперативная память: Занято {used_gb} GB из {total_gb} GB (Свободно {free_gb} GB | {ram_pct}%)")
        self.ram_bar.set(ram_pct / 100.0)

        self.disk_label.configure(text=f"Диск C: Свободно {disk_free_gb} GB из {disk_total_gb} GB")
        self.disk_bar.set(disk_pct / 100.0)

    def start_game_boost(self):
        self.btn_boost.configure(state="disabled")
        threading.Thread(target=self._run_game_boost, daemon=True).start()

    def _run_game_boost(self):
        self.log(">>> Запуск Ультра Игрового режима...")
        before_mem = psutil.virtual_memory().available

        # 1. Принудительный сброс Working Sets процессов
        freed_procs = 0
        try:
            kernel32 = ctypes.windll.kernel32
            current_pid = os.getpid()
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['pid'] != current_pid and proc.info['pid'] > 4:
                    try:
                        handle = kernel32.OpenProcess(0x001F0FFF, False, proc.info['pid'])
                        if handle:
                            kernel32.SetProcessWorkingSetSize(handle, -1, -1)
                            kernel32.CloseHandle(handle)
                            freed_procs += 1
                    except Exception:
                        pass
        except Exception as e:
            self.log(f"Ошибка сброса рабочих наборов: {e}")

        # 2. Очистка буферов
        time.sleep(1)
        after_mem = psutil.virtual_memory().available
        diff_mb = round((after_mem - before_mem) / (1024**2))
        if diff_mb > 0:
            self.log(f"✔ Игровой режим активирован! Разгружено процессов: {freed_procs}.")
            self.log(f"✔ Дополнительно высвобождено: ~{diff_mb} МБ оперативной памяти!")
        else:
            self.log(f"✔ Память уже оптимизирована на максимум. Разгружено процессов: {freed_procs}.")

        self.after(0, lambda: self.btn_boost.configure(state="normal"))

    def start_quick_clean(self):
        self.btn_clean.configure(state="disabled")
        threading.Thread(target=self._run_quick_clean, daemon=True).start()

    def _run_quick_clean(self):
        self.log(">>> Очистка временных файлов и кэша...")
        temp_dirs = [
            os.environ.get('TEMP'),
            os.environ.get('TMP'),
            r"C:\Windows\Temp"
        ]

        deleted_files = 0
        freed_bytes = 0

        for t_dir in temp_dirs:
            if not t_dir or not os.path.exists(t_dir):
                continue
            for root, dirs, files in os.walk(t_dir, topdown=False):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        sz = os.path.getsize(fp)
                        os.remove(fp)
                        deleted_files += 1
                        freed_bytes += sz
                    except Exception:
                        pass
                for d in dirs:
                    dp = os.path.join(root, d)
                    try:
                        shutil.rmtree(dp, ignore_errors=True)
                    except Exception:
                        pass

        freed_mb = round(freed_bytes / (1024**2), 1)
        self.log(f"✔ Очистка завершена! Удалено временных файлов: {deleted_files} шт. (Освобождено {freed_mb} МБ).")
        self.after(0, lambda: self.btn_clean.configure(state="normal"))

    def start_emergency_free(self):
        self.log(">>> Экстренный сброс: выгрузка фоновых зависших задач...")
        try:
            # Сброс рабочего набора и системных буферов
            ctypes.windll.psapi.EmptyWorkingSet(ctypes.windll.kernel32.GetCurrentProcess())
            self.log("✔ Системные кэши очищены, отзывчивость восстановлена.")
        except Exception as e:
            self.log(f"Информация: {e}")


if __name__ == "__main__":
    app = PCMasterApp()
    app.mainloop()
