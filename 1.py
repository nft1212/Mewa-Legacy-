import os
import tkinter as tk
from tkinter import filedialog, Listbox, END, messagebox
import pygame
import threading
import time

# ---------- ULTIMATE RETRO PLAYER 2006 - PURPLE EDITION ----------
class UltimateRetroPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenMP")
        self.root.geometry("520x620")
        self.root.configure(bg="#0d0014")
        self.root.resizable(False, False)

        # ---------- переменные ----------
        self.playlist = []
        self.current_index = -1
        self.is_playing = False
        self.paused = False
        self.loop_enabled = False
        self.track_length = 0
        self.current_position = 0
        self.seeking = False
        self.user_seeking = False

        # ---------- инициализация pygame ----------
        # Отключаем вывод приветствия для старых систем
        import contextlib
        with contextlib.redirect_stdout(None):
            pygame.init()
            pygame.mixer.init()

        # ---------- стили ----------
        self.bg_dark = "#0d0014"
        self.bg_mid = "#1a0030"
        self.bg_light = "#2d004f"
        self.accent = "#b44dff"
        self.accent_bright = "#d580ff"
        self.text_color = "#e6ccff"
        self.text_dim = "#9966cc"
        self.glow_color = "#7a00cc"

        # ---------- создание UI ----------
        self.create_widgets()

        # ---------- обработка закрытия окна ----------
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # ---------- старт обновления прогресса ----------
        self.update_progress()

    def create_widgets(self):
        # ===== ГЛАВНЫЙ КОНТЕЙНЕР С ОБЪЁМНОЙ РАМКОЙ =====
        main_frame = tk.Frame(self.root, bg=self.bg_dark, bd=0, highlightthickness=0)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # объёмная внешняя рамка
        outer_frame = tk.Frame(main_frame, bg=self.glow_color, bd=3, relief="raised")
        outer_frame.pack(fill="both", expand=True, padx=2, pady=2)

        inner_frame = tk.Frame(outer_frame, bg=self.bg_mid, bd=2, relief="sunken")
        inner_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # ===== ЗАГОЛОВОК =====
        title_frame = tk.Frame(inner_frame, bg=self.bg_dark, bd=2, relief="ridge")
        title_frame.pack(fill="x", padx=8, pady=(8, 4))

        self.title_label = tk.Label(title_frame, text="OpenMP - Winora Company",
                                    bg=self.bg_dark, fg=self.accent_bright,
                                    font=("Courier", 14, "bold"))
        self.title_label.pack(pady=4)

        # ===== ИНФО О ТРЕКЕ =====
        info_frame = tk.Frame(inner_frame, bg=self.bg_mid, bd=2, relief="groove")
        info_frame.pack(fill="x", padx=8, pady=4)

        self.track_name_label = tk.Label(info_frame, text="No Track Loaded",
                                         bg=self.bg_mid, fg=self.text_color,
                                         font=("Courier", 9, "bold"),
                                         anchor="w", padx=6)
        self.track_name_label.pack(fill="x", pady=(4, 0))

        self.time_label = tk.Label(info_frame, text="00:00 / 00:00",
                                   bg=self.bg_mid, fg=self.text_dim,
                                   font=("Courier", 8), anchor="e", padx=6)
        self.time_label.pack(fill="x", pady=(0, 4))

        # ===== ПРОГРЕССБАР С ПЕРЕМОТКОЙ =====
        progress_frame = tk.Frame(inner_frame, bg=self.bg_mid)
        progress_frame.pack(fill="x", padx=8, pady=2)

        # кастомный прогрессбар
        self.progress_canvas = tk.Canvas(progress_frame, height=20,
                                         bg=self.bg_dark,
                                         highlightthickness=2,
                                         highlightbackground=self.accent,
                                         bd=0)
        self.progress_canvas.pack(fill="x", padx=2, pady=2)

        # рисуем начальный прогрессбар
        self.progress_bg = self.progress_canvas.create_rectangle(0, 0, 0, 20,
                                                                 fill=self.bg_light,
                                                                 outline="")
        self.progress_fg = self.progress_canvas.create_rectangle(0, 0, 0, 20,
                                                                 fill=self.accent,
                                                                 outline="")
        self.progress_handle = self.progress_canvas.create_rectangle(0, 0, 8, 20,
                                                                     fill=self.accent_bright,
                                                                     outline=self.glow_color,
                                                                     width=1)

        # биндим события мыши для перемотки
        self.progress_canvas.bind("<Button-1>", self.on_progress_click)
        self.progress_canvas.bind("<B1-Motion>", self.on_progress_drag)
        self.progress_canvas.bind("<ButtonRelease-1>", self.on_progress_release)

        # ===== КНОПКИ УПРАВЛЕНИЯ (ОБЪЁМНЫЕ) =====
        control_frame = tk.Frame(inner_frame, bg=self.bg_mid, bd=2, relief="ridge")
        control_frame.pack(fill="x", padx=8, pady=4)

        button_frame = tk.Frame(control_frame, bg=self.bg_mid)
        button_frame.pack(pady=6)

        # стиль кнопок с 3D эффектом (без width, чтобы не конфликтовало)
        btn_config = {
            "bg": self.bg_light,
            "fg": self.accent_bright,
            "font": ("Courier", 10, "bold"),
            "relief": "raised",
            "bd": 3,
            "activebackground": self.accent,
            "activeforeground": "#ffffff"
        }

        self.prev_btn = tk.Button(button_frame, text="◀◀", command=self.prev_track,
                                  width=4, **btn_config)
        self.prev_btn.pack(side="left", padx=3)

        self.play_btn = tk.Button(button_frame, text="▶", command=self.play_pause,
                                  width=5, **btn_config)
        self.play_btn.pack(side="left", padx=3)

        self.stop_btn = tk.Button(button_frame, text="■", command=self.stop_music,
                                  width=4, fg="#ff6666", **{k:v for k,v in btn_config.items() if k != 'fg'})
        self.stop_btn.pack(side="left", padx=3)

        self.next_btn = tk.Button(button_frame, text="▶▶", command=self.next_track,
                                  width=4, **btn_config)
        self.next_btn.pack(side="left", padx=3)

        # кнопка лупа отдельно
        loop_frame = tk.Frame(control_frame, bg=self.bg_mid)
        loop_frame.pack(pady=(0, 6))

        self.loop_btn = tk.Button(loop_frame, text="🔁 LOOP OFF",
                                  bg=self.bg_light, fg=self.text_dim,
                                  font=("Courier", 8, "bold"),
                                  relief="raised", bd=2, width=12,
                                  activebackground=self.accent,
                                  activeforeground="#ffffff",
                                  command=self.toggle_loop)
        self.loop_btn.pack()

        # ===== ПЛЕЙЛИСТ С ОБЪЁМНЫМ ОФОРМЛЕНИЕМ =====
        playlist_label_frame = tk.Frame(inner_frame, bg=self.bg_mid)
        playlist_label_frame.pack(fill="x", padx=8, pady=(6, 0))

        tk.Label(playlist_label_frame, text="▼ PLAYLIST ▼",
                bg=self.bg_mid, fg=self.accent_bright,
                font=("Courier", 10, "bold")).pack(pady=2)

        playlist_container = tk.Frame(inner_frame, bg=self.glow_color, bd=2, relief="sunken")
        playlist_container.pack(fill="both", expand=True, padx=8, pady=4)

        # скроллбар для плейлиста
        scrollbar = tk.Scrollbar(playlist_container, bg=self.bg_light,
                                 troughcolor=self.bg_dark,
                                 activebackground=self.accent)
        scrollbar.pack(side="right", fill="y")

        self.listbox = Listbox(playlist_container,
                               bg=self.bg_dark,
                               fg=self.text_color,
                               selectbackground=self.accent,
                               selectforeground="#ffffff",
                               font=("Courier", 9),
                               relief="flat",
                               bd=0,
                               highlightthickness=0,
                               yscrollcommand=scrollbar.set,
                               height=12)
        self.listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)

        self.listbox.bind("<Double-Button-1>", lambda e: self.play_selected())

        # ===== КНОПКИ УПРАВЛЕНИЯ ПЛЕЙЛИСТОМ =====
        playlist_btn_frame = tk.Frame(inner_frame, bg=self.bg_mid)
        playlist_btn_frame.pack(fill="x", padx=8, pady=6)

        small_btn_config = {
            "bg": self.bg_light,
            "fg": self.accent_bright,
            "font": ("Courier", 9, "bold"),
            "relief": "raised",
            "bd": 2,
            "width": 10,
            "activebackground": self.accent,
            "activeforeground": "#ffffff"
        }

        self.add_files_btn = tk.Button(playlist_btn_frame, text="+ FILES",
                                       command=self.add_files, **small_btn_config)
        self.add_files_btn.pack(side="left", padx=2)

        self.add_folder_btn = tk.Button(playlist_btn_frame, text="📁 FOLDER",
                                        command=self.add_folder, **small_btn_config)
        self.add_folder_btn.pack(side="left", padx=2)

        self.remove_btn = tk.Button(playlist_btn_frame, text="− REMOVE",
                                    command=self.remove_selected,
                                    fg="#ff6666", **{k:v for k,v in small_btn_config.items() if k != 'fg'})
        self.remove_btn.pack(side="left", padx=2)

        self.clear_btn = tk.Button(playlist_btn_frame, text="✖ CLEAR",
                                   command=self.clear_playlist,
                                   fg="#ff6666", **{k:v for k,v in small_btn_config.items() if k != 'fg'})
        self.clear_btn.pack(side="left", padx=2)

        # ===== СТАТУСНАЯ СТРОКА =====
        status_frame = tk.Frame(inner_frame, bg=self.bg_dark, bd=1, relief="sunken")
        status_frame.pack(fill="x", padx=8, pady=4)

        self.status_label = tk.Label(status_frame, text="[ READY ]",
                                     bg=self.bg_dark, fg=self.text_dim,
                                     font=("Courier", 8), anchor="w", padx=4)
        self.status_label.pack(fill="x")

    def update_progress(self):
        """Обновление прогрессбара и таймера."""
        try:
            if self.is_playing and not self.paused and not self.user_seeking:
                if pygame.mixer.music.get_busy():
                    self.current_position = pygame.mixer.music.get_pos() / 1000.0
                    self.update_progress_bar()
                    self.update_time_display()
                elif self.track_length > 0:
                    # трек закончился
                    if self.loop_enabled:
                        self.play_current()
                    else:
                        self.root.after(100, self.next_track)
        except Exception:
            pass
        self.root.after(100, self.update_progress)

    def update_progress_bar(self):
        """Обновление визуального прогрессбара."""
        if self.track_length > 0:
            canvas_width = self.progress_canvas.winfo_width()
            if canvas_width > 0:
                progress_ratio = min(self.current_position / self.track_length, 1.0)
                fill_width = canvas_width * progress_ratio
                handle_x = fill_width - 4

                self.progress_canvas.coords(self.progress_fg, 0, 0, fill_width, 20)
                self.progress_canvas.coords(self.progress_handle,
                                           handle_x, 0, handle_x + 8, 20)

    def update_time_display(self):
        """Обновление отображения времени."""
        current = self.format_time(self.current_position)
        total = self.format_time(self.track_length)
        self.time_label.config(text=f"{current} / {total}")

    def format_time(self, seconds):
        """Форматирование времени в MM:SS."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def on_progress_click(self, event):
        """Нажатие на прогрессбар для перемотки."""
        self.user_seeking = True
        self.seek_to_position(event.x)

    def on_progress_drag(self, event):
        """Перетаскивание ползунка прогрессбара."""
        if self.user_seeking:
            self.seek_to_position(event.x)

    def on_progress_release(self, event):
        """Отпускание ползунка - применяем перемотку."""
        if self.user_seeking and self.current_index >= 0:
            self.seek_to_position(event.x)
            # применяем перемотку в музыке
            if self.is_playing:
                try:
                    pygame.mixer.music.play(start=self.current_position)
                    if self.paused:
                        pygame.mixer.music.pause()
                except Exception as e:
                    self.status_label.config(text=f"[ seek error: {e} ]")
        self.user_seeking = False

    def seek_to_position(self, x):
        """Расчёт позиции на основе клика."""
        canvas_width = self.progress_canvas.winfo_width()
        if canvas_width > 0 and self.track_length > 0:
            ratio = max(0, min(x / canvas_width, 1.0))
            self.current_position = ratio * self.track_length
            self.update_progress_bar()
            self.update_time_display()

    def get_audio_length(self, filepath):
        """Получение длительности аудиофайла через pygame."""
        try:
            # временно загружаем для получения длины
            sound = pygame.mixer.Sound(filepath)
            length = sound.get_length()
            return length
        except Exception:
            return 0

    def add_files(self):
        """Добавление отдельных файлов."""
        files = filedialog.askopenfilenames(
            title="Select Audio Files",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.ogg *.flac *.m4a"),
                ("All Files", "*.*")
            ]
        )
        added = 0
        for file in files:
            if file not in self.playlist:
                self.playlist.append(file)
                self.listbox.insert(END, os.path.basename(file))
                added += 1
        if added > 0:
            self.status_label.config(text=f"[ Added {added} file(s) ]")
        else:
            self.status_label.config(text="[ No new files added ]")

    def add_folder(self):
        """Добавление всей папки с музыкой."""
        folder = filedialog.askdirectory(title="Select Music Folder")
        if folder:
            added = 0
            supported = (".mp3", ".wav", ".ogg", ".flac", ".m4a")
            try:
                for root_dir, dirs, files in os.walk(folder):
                    for file in sorted(files):
                        if file.lower().endswith(supported):
                            full_path = os.path.join(root_dir, file)
                            if full_path not in self.playlist:
                                self.playlist.append(full_path)
                                # показываем относительный путь для вложенных папок
                                rel_path = os.path.relpath(full_path, folder)
                                self.listbox.insert(END, rel_path)
                                added += 1
            except Exception as e:
                self.status_label.config(text=f"[ Folder error: {e} ]")
                return

            if added > 0:
                self.status_label.config(text=f"[ Added {added} tracks from folder ]")
            else:
                self.status_label.config(text="[ No audio found in folder ]")

    def remove_selected(self):
        """Удаление выбранного трека."""
        selected = self.listbox.curselection()
        if selected:
            index = selected[0]
            self.listbox.delete(index)
            del self.playlist[index]
            if index == self.current_index:
                self.stop_music()
            elif index < self.current_index:
                self.current_index -= 1
            self.status_label.config(text="[ Track removed ]")

    def clear_playlist(self):
        """Очистка плейлиста."""
        self.stop_music()
        self.listbox.delete(0, END)
        self.playlist.clear()
        self.current_index = -1
        self.reset_progress()
        self.status_label.config(text="[ Playlist cleared ]")

    def reset_progress(self):
        """Сброс прогрессбара."""
        self.track_length = 0
        self.current_position = 0
        self.progress_canvas.coords(self.progress_fg, 0, 0, 0, 20)
        self.progress_canvas.coords(self.progress_handle, 0, 0, 8, 20)
        self.time_label.config(text="00:00 / 00:00")
        self.track_name_label.config(text="No Track Loaded")

    def play_selected(self):
        """Воспроизведение выбранного трека."""
        selected = self.listbox.curselection()
        if selected:
            self.current_index = selected[0]
            self.play_current()

    def play_current(self):
        """Запуск текущего трека."""
        if self.current_index >= 0 and self.current_index < len(self.playlist):
            filepath = self.playlist[self.current_index]

            def play_thread():
                try:
                    pygame.mixer.music.load(filepath)
                    pygame.mixer.music.play()
                    self.is_playing = True
                    self.paused = False
                    self.play_btn.config(text="⏸")
                    self.current_position = 0

                    # получаем длительность трека
                    self.track_length = self.get_audio_length(filepath)
                    self.update_time_display()
                    self.update_progress_bar()

                    track_name = os.path.basename(filepath)
                    self.track_name_label.config(text=track_name)

                    self.listbox.selection_clear(0, END)
                    self.listbox.selection_set(self.current_index)
                    self.listbox.activate(self.current_index)
                    self.listbox.see(self.current_index)

                    self.status_label.config(text=f"[ Now Playing ]")
                except Exception as e:
                    self.status_label.config(text=f"[ Error: {str(e)[:50]} ]")

            threading.Thread(target=play_thread, daemon=True).start()

    def play_pause(self):
        """Play / Pause с возобновлением."""
        if not self.is_playing and self.current_index >= 0:
            if self.paused:
                pygame.mixer.music.unpause()
                self.paused = False
                self.is_playing = True
                self.play_btn.config(text="⏸")
                self.status_label.config(text="[ Resumed ]")
            else:
                self.play_current()
        elif self.is_playing:
            if not self.paused:
                pygame.mixer.music.pause()
                self.paused = True
                self.play_btn.config(text="▶")
                self.status_label.config(text="[ Paused ]")
            else:
                pygame.mixer.music.unpause()
                self.paused = False
                self.play_btn.config(text="⏸")
                self.status_label.config(text="[ Resumed ]")

    def stop_music(self):
        """Полная остановка."""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.paused = False
        self.play_btn.config(text="▶")
        self.reset_progress()
        self.status_label.config(text="[ Stopped ]")

    def next_track(self):
        """Следующий трек."""
        if self.playlist:
            self.current_index = (self.current_index + 1) % len(self.playlist)
            self.play_current()

    def prev_track(self):
        """Предыдущий трек."""
        if self.playlist:
            self.current_index = (self.current_index - 1) % len(self.playlist)
            self.play_current()

    def toggle_loop(self):
        """Переключение зацикливания."""
        self.loop_enabled = not self.loop_enabled
        if self.loop_enabled:
            self.loop_btn.config(text="🔁 LOOP ON", fg=self.accent_bright)
            self.status_label.config(text="[ Loop: ON ]")
        else:
            self.loop_btn.config(text="🔁 LOOP OFF", fg=self.text_dim)
            self.status_label.config(text="[ Loop: OFF ]")

    def on_close(self):
        """Закрытие приложения."""
        try:
            pygame.mixer.music.stop()
            pygame.quit()
        except Exception:
            pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = UltimateRetroPlayer(root)
    root.mainloop()
