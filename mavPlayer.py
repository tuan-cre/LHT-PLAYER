import sys
import os
import shutil
import threading
import random
from pathlib import Path
import logging

os.environ.setdefault('QT_QPA_PLATFORM', 'xcb')
os.environ.setdefault('QT_QPA_PLATFORMTHEME', 'generic')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QListWidget, QListWidgetItem, QPushButton, QLineEdit,
    QLabel, QMessageBox, QFileDialog, QInputDialog, QFrame,
    QSlider, QStyle, QSizePolicy
)
from PyQt6.QtCore import Qt, QUrl, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QColor, QPalette, QAction, QMouseEvent

import yt_dlp
import vlc
import requests

import config
from config import (
    init_directories,
    get_music_dir, get_video_dir, get_lyrics_dir
)

init_directories()

class ClickableSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            value = self.valueFromPosition(event.position().x())
            self.setValue(value)
            self.setSliderPosition(value)
            self.sliderPressed.emit()
            event.accept()
            try:
                main_window = self.main_window
                length = main_window.media_player.get_length()
                if length <= 0:
                    length = main_window.media_player.length()
                if length > 0:
                    position = value / 1000 * length
                    main_window.media_player.set_time(int(position))
            except Exception:
                pass
        else:
            super().mousePressEvent(event)

    def valueFromPosition(self, x):
        return int((x / self.width()) * (self.maximum() - self.minimum()) + self.minimum())


class Worker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, func, *args):
        super().__init__()
        self.func = func
        self.args = args

    def run(self):
        try:
            self.func(*self.args)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("mavPlayer")
        self.resize(1000, 700)

        self.current_tab = "music"
        self.currently_playing = None
        self.is_playing = False
        self.is_paused = False
        self.auto_play_next = True
        self.shuffle_mode = False
        self.is_changing_track = False

        # Initialize VLC instance with parameters to ensure it embeds properly
        vlc_args = []
        if sys.platform.startswith('linux'):
            vlc_args.extend(['--no-xlib'])
            # Unset WAYLAND_DISPLAY so VLC doesn't try to use Wayland output
            # which would cause it to ignore set_xwindow and open a new window
            if 'WAYLAND_DISPLAY' in os.environ:
                del os.environ['WAYLAND_DISPLAY']

        self.vlc_instance = vlc.Instance(*vlc_args)
        self.media_player = self.vlc_instance.media_player_new()

        self.setup_ui()
        self.setup_dark_theme()

    def setup_dark_theme(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(50, 50, 50))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(35, 35, 35))
        self.setPalette(dark_palette)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        main_layout.addWidget(self.tabs)

        self.music_tab = QWidget()
        self.video_tab = QWidget()
        self.lyrics_tab = QWidget()

        self.tabs.addTab(self.music_tab, "♫ Music")
        self.tabs.addTab(self.video_tab, "▶ Video")
        self.tabs.addTab(self.lyrics_tab, "𝄙 Lyrics")

        self.tabs.currentChanged.connect(self.on_tab_changed)

        self.setup_music_tab()
        self.setup_video_tab()
        self.setup_lyrics_tab()
        self.setup_controls()

    def on_tab_changed(self, index):
        tabs = ["music", "video", "lyric"]
        if index < len(tabs):
            self.current_tab = tabs[index]

    def setup_controls(self):
        controls = self.create_controls(
            self,
            self.prev_track,
            self.next_track,
            self.stop_playback
        )
        main_layout = self.centralWidget().layout()
        main_layout.addWidget(controls)

    def create_toolbar(self, parent, add_folder_cb, add_file_cb, youtube_cb, delete_cb):
        toolbar = QFrame(parent)
        toolbar.setStyleSheet("background-color: #2d2d2d;")
        toolbar.setFixedHeight(60)
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)

        btn_style = """
            QPushButton {
                background-color: #3d3d3d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
            QPushButton:pressed {
                background-color: #2a5ca6;
            }
        """

        btn_add_folder = QPushButton("🗁 Add Folder")
        btn_add_folder.setStyleSheet(btn_style)
        btn_add_folder.clicked.connect(add_folder_cb)

        btn_add_file = QPushButton("➕ Add Files")
        btn_add_file.setStyleSheet(btn_style)
        btn_add_file.clicked.connect(add_file_cb)

        btn_youtube = QPushButton("⬇ YouTube")
        btn_youtube.setStyleSheet(btn_style)
        btn_youtube.clicked.connect(youtube_cb)

        btn_delete = QPushButton("🗑 Delete")
        btn_delete.setStyleSheet(btn_style)
        btn_delete.clicked.connect(delete_cb)

        layout.addWidget(btn_add_folder)
        layout.addWidget(btn_add_file)
        layout.addWidget(btn_youtube)
        layout.addStretch()
        layout.addWidget(btn_delete)

        return toolbar

    def create_list(self, parent):
        lst = QListWidget(parent)
        lst.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                color: white;
                border: none;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3d3d3d;
            }
            QListWidget::item:selected {
                background-color: #2a5ca6;
            }
            QListWidget::item:hover {
                background-color: #3d3d3d;
            }
        """)
        return lst

    def create_controls(self, parent, prev_cb, next_cb, stop_cb):
        controls = QFrame(parent)
        controls.setStyleSheet("background-color: #2d2d2d;")
        controls.setFixedHeight(90)
        layout = QVBoxLayout(controls)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)

        slider_layout = QHBoxLayout()
        slider_layout.setSpacing(10)

        self.current_time_label = QLabel("0:00")
        self.current_time_label.setStyleSheet("color: white; font-size: 12px;")
        self.current_time_label.setFixedWidth(40)

        self.seek_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.seek_slider.main_window = self
        self.seek_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                background: #555;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                width: 14px;
                margin: -4px 0;
                background: #2a5ca6;
                border-radius: 7px;
            }
            QSlider::sub-page:horizontal {
                background: #2a5ca6;
                border-radius: 3px;
            }
        """)
        self.seek_slider.setRange(0, 1000)
        self.seek_slider.sliderMoved.connect(self.seek_position)
        self.seek_slider.sliderPressed.connect(self.slider_pressed)
        self.seek_slider.sliderReleased.connect(self.slider_released)

        self.total_time_label = QLabel("0:00")
        self.total_time_label.setStyleSheet("color: white; font-size: 12px;")
        self.total_time_label.setFixedWidth(40)

        slider_layout.addWidget(self.current_time_label)
        slider_layout.addWidget(self.seek_slider, 1)
        slider_layout.addWidget(self.total_time_label)

        layout.addLayout(slider_layout)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        btn_style = """
            QPushButton {
                background-color: #3d3d3d;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 50px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
        """

        btn_prev = QPushButton("⏮")
        btn_prev.setStyleSheet(btn_style)
        btn_prev.clicked.connect(prev_cb)

        self.btn_play = QPushButton("▶ Play")
        self.btn_play.setStyleSheet(btn_style)
        self.btn_play.clicked.connect(self.toggle_play_pause)

        btn_next = QPushButton("⏭")
        btn_next.setStyleSheet(btn_style)
        btn_next.clicked.connect(next_cb)

        self.btn_shuffle = QPushButton("🔀")
        self.btn_shuffle.setCheckable(True)
        self.btn_shuffle.setChecked(False)
        self.btn_shuffle.setStyleSheet(btn_style)
        self.btn_shuffle.clicked.connect(self.toggle_shuffle)

        self.btn_auto = QPushButton("🔁")
        self.btn_auto.setCheckable(True)
        self.btn_auto.setChecked(True)
        self.btn_auto.setStyleSheet(btn_style)
        self.btn_auto.clicked.connect(self.toggle_auto_play_next)

        btn_stop = QPushButton("⏹ Stop")
        btn_stop.setStyleSheet(btn_style)
        btn_stop.clicked.connect(stop_cb)

        btn_layout.addWidget(btn_prev)
        btn_layout.addWidget(self.btn_play)
        btn_layout.addWidget(btn_next)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_shuffle)
        btn_layout.addWidget(self.btn_auto)
        btn_layout.addWidget(btn_stop)

        layout.addLayout(btn_layout)

        self.slider_dragging = False
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_slider_position)

        return controls

    def setup_music_tab(self):
        layout = QVBoxLayout(self.music_tab)

        self.music_toolbar = self.create_toolbar(
            self.music_tab,
            self.add_music_folder,
            self.add_music_files,
            self.download_music_youtube,
            self.delete_music
        )
        layout.addWidget(self.music_toolbar)

        self.music_list = self.create_list(self.music_tab)
        self.music_list.itemDoubleClicked.connect(self.play_music)
        layout.addWidget(self.music_list)

        self.load_music_list()

    def setup_video_tab(self):
        layout = QVBoxLayout(self.video_tab)

        self.video_toolbar = self.create_toolbar(
            self.video_tab,
            self.add_video_folder,
            self.add_video_files,
            self.download_video_youtube,
            self.delete_video
        )
        layout.addWidget(self.video_toolbar)

        self.video_frame = QFrame(self.video_tab)
        self.video_frame.setStyleSheet("background-color: black;")
        self.video_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_frame.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        layout.addWidget(self.video_frame, stretch=2)

        self.video_list = self.create_list(self.video_tab)
        self.video_list.itemDoubleClicked.connect(self.play_video)
        layout.addWidget(self.video_list, stretch=1)

        if sys.platform.startswith('linux'):
            self.media_player.set_xwindow(int(self.video_frame.winId()))
        elif sys.platform == "win32":
            self.media_player.set_hwnd(int(self.video_frame.winId()))
        elif sys.platform == "darwin":
            self.media_player.set_nsobject(int(self.video_frame.winId()))

        self.load_video_list()

    def setup_lyrics_tab(self):
        layout = QVBoxLayout(self.lyrics_tab)

        search_frame = QFrame(self.lyrics_tab)
        search_frame.setStyleSheet("background-color: #2d2d2d;")
        search_frame.setFixedHeight(70)
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(10, 10, 10, 10)
        search_layout.setSpacing(10)

        input_style = """
            QLineEdit {
                background-color: #3d3d3d;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
        """

        self.song_title_input = QLineEdit()
        self.song_title_input.setPlaceholderText("Song title...")
        self.song_title_input.setStyleSheet(input_style)
        self.song_title_input.setFixedWidth(200)

        self.artist_input = QLineEdit()
        self.artist_input.setPlaceholderText("Artist (optional)...")
        self.artist_input.setStyleSheet(input_style)
        self.artist_input.setFixedWidth(200)

        btn_fetch = QPushButton("🔍 Fetch Lyrics")
        btn_fetch.setStyleSheet("""
            QPushButton {
                background-color: #2a5ca6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3a6cc6;
            }
        """)
        btn_fetch.clicked.connect(self.fetch_lyrics)

        btn_save = QPushButton("💾 Save")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
        """)
        btn_save.clicked.connect(self.save_lyrics)

        btn_load = QPushButton("📂 Load")
        btn_load.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
        """)
        btn_load.clicked.connect(self.load_lyrics)

        search_layout.addWidget(QLabel("Title:"))
        search_layout.addWidget(self.song_title_input)
        search_layout.addWidget(QLabel("Artist:"))
        search_layout.addWidget(self.artist_input)
        search_layout.addWidget(btn_fetch)
        search_layout.addStretch()
        search_layout.addWidget(btn_save)
        search_layout.addWidget(btn_load)

        layout.addWidget(search_frame)

        self.lyrics_list = QListWidget(self.lyrics_tab)
        self.lyrics_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                color: #ddd;
                border: none;
                padding: 10px;
                font-size: 14px;
                font-family: 'Sans Serif', Arial;
            }
            QListWidget::item {
                padding: 5px;
            }
        """)
        layout.addWidget(self.lyrics_list)

    def load_music_list(self):
        self.music_list.clear()
        music_dir = get_music_dir()
        for f in sorted(music_dir.iterdir()):
            if f.suffix.lower() == ".mp3":
                self.music_list.addItem(f.name)

    def load_video_list(self):
        self.video_list.clear()
        video_dir = get_video_dir()
        for f in sorted(video_dir.iterdir()):
            if f.suffix.lower() in (".mp4", ".mkv", ".avi", ".webm"):
                self.video_list.addItem(f.name)

    def add_music_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Music Folder")
        if folder:
            src = Path(folder)
            dst = get_music_dir()
            for f in src.iterdir():
                if f.suffix.lower() == ".mp3":
                    shutil.copy(f, dst / f.name)
            self.load_music_list()

    def add_music_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select MP3 Files", "",
            "MP3 Files (*.mp3)"
        )
        if files:
            dst = get_music_dir()
            for f in files:
                shutil.copy(f, dst / Path(f).name)
            self.load_music_list()

    def add_video_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Video Folder")
        if folder:
            src = Path(folder)
            dst = get_video_dir()
            for f in src.iterdir():
                if f.suffix.lower() in (".mp4", ".mkv", ".avi", ".webm"):
                    shutil.copy(f, dst / f.name)
            self.load_video_list()

    def add_video_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Video Files", "",
            "Video Files (*.mp4 *.mkv *.avi *.webm)"
        )
        if files:
            dst = get_video_dir()
            for f in files:
                shutil.copy(f, dst / Path(f).name)
            self.load_video_list()

    def download_music_youtube(self):
        link, ok = QInputDialog.getText(self, "YouTube Download", "Enter YouTube URL:")
        if ok and link:
            self.download_youtube(link, "mp3")

    def download_video_youtube(self):
        link, ok = QInputDialog.getText(self, "YouTube Download", "Enter YouTube URL:")
        if ok and link:
            self.download_youtube(link, "mp4")

    def download_youtube(self, url, fmt):
        QMessageBox.information(self, "Download", f"Downloading {fmt.upper()} from YouTube...")

        def do_download():
            if fmt == "mp3":
                out_dir = get_music_dir()
            else:
                out_dir = get_video_dir()

            ydl_opts = {
                'format': 'best' if fmt == "mp4" else 'bestaudio/best',
                'outtmpl': str(out_dir / '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }] if fmt == "mp3" else [],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        self.worker = Worker(do_download)
        self.worker.finished.connect(lambda: self.on_download_complete(fmt))
        self.worker.error.connect(lambda e: self.on_download_error(e))
        threading.Thread(target=self.worker.run, daemon=True).start()

    def on_download_complete(self, fmt):
        QMessageBox.information(self, "Success", f"Download complete! Saved to {fmt.upper()} directory.")
        if fmt == "mp3":
            self.load_music_list()
        else:
            self.load_video_list()

    def on_download_error(self, error):
        QMessageBox.critical(self, "Error", f"Download failed: {error}")

    def delete_music(self):
        item = self.music_list.currentItem()
        if item:
            file = get_music_dir() / item.text()
            file.unlink()
            self.load_music_list()

    def delete_video(self):
        item = self.video_list.currentItem()
        if item:
            file = get_video_dir() / item.text()
            file.unlink()
            self.load_video_list()

    def play_music(self):
        item = self.music_list.currentItem()
        if item:
            self.currently_playing = get_music_dir() / item.text()
            self.current_tab = "music"
            self.play_file(str(self.currently_playing))
            self.is_playing = True
            self.is_paused = False
            self.btn_play.setText("⏸ Pause")

    def play_video(self):
        item = self.video_list.currentItem()
        if item:
            self.currently_playing = get_video_dir() / item.text()
            self.current_tab = "video"
            self.play_file(str(self.currently_playing))
            self.is_playing = True
            self.is_paused = False
            self.btn_play.setText("⏸ Pause")

    def play_file(self, path):
        logger.debug(f"play_file called with path: {path}")
        self.seek_slider.setValue(0)
        self.current_time_label.setText("0:00")
        self.is_changing_track = False
        if os.path.exists(path):
            media = self.vlc_instance.media_new(path)
            self.media_player.set_media(media)

            if sys.platform.startswith('linux'):
                self.media_player.set_xwindow(int(self.video_frame.winId()))
            elif sys.platform == "win32":
                self.media_player.set_hwnd(int(self.video_frame.winId()))
            elif sys.platform == "darwin":
                self.media_player.set_nsobject(int(self.video_frame.winId()))

            self.media_player.play()
            self.update_timer.start(250)
            logger.debug("Started playback, timer started")
            QTimer.singleShot(1000, self.update_on_play)
        else:
            logger.error(f"File not found: {path}")
            QMessageBox.warning(self, "Error", f"File not found: {path}")

    def update_on_play(self):
        try:
            length = self.media_player.get_length()
            logger.debug(f"update_on_play: get_length returned {length}")
            if length > 0:
                self.total_time_label.setText(self.format_time(length))
                logger.debug(f"Total time set to: {self.format_time(length)}")
            else:
                logger.warning("update_on_play: length <= 0")
        except Exception as e:
            logger.error(f"update_on_play error: {e}")

    def prev_track(self):
        if self.current_tab == "music":
            self.prev_music()
        elif self.current_tab == "video":
            self.prev_video()

    def next_track(self):
        if self.current_tab == "music":
            self.next_music()
        elif self.current_tab == "video":
            self.next_video()

    def stop_playback(self):
        if self.current_tab == "music":
            self.stop_music()
        elif self.current_tab == "video":
            self.stop_video()

    def toggle_shuffle(self):
        self.shuffle_mode = self.btn_shuffle.isChecked()
        if self.shuffle_mode:
            self.btn_shuffle.setStyleSheet("""
                QPushButton {
                    background-color: #2a5ca6;
                    color: white;
                    border: none;
                    padding: 8px 12px;
                    border-radius: 4px;
                    font-size: 14px;
                    min-width: 50px;
                }
            """)
        else:
            self.btn_shuffle.setStyleSheet("""
                QPushButton {
                    background-color: #3d3d3d;
                    color: white;
                    border: none;
                    padding: 8px 12px;
                    border-radius: 4px;
                    font-size: 14px;
                    min-width: 50px;
                }
            """)

    def toggle_auto_play_next(self):
        self.auto_play_next = self.btn_auto.isChecked()

    def prev_music(self):
        current_row = self.music_list.currentRow()
        if current_row > 0:
            self.music_list.setCurrentRow(current_row - 1)
            self.play_music()

    def prev_video(self):
        current_row = self.video_list.currentRow()
        if current_row > 0:
            self.video_list.setCurrentRow(current_row - 1)
            self.play_video()

    def next_music(self):
        if self.shuffle_mode and self.music_list.count() > 1:
            choices = list(range(self.music_list.count()))
            current = self.music_list.currentRow()
            choices.remove(current)
            self.music_list.setCurrentRow(random.choice(choices))
            self.play_music()
        else:
            current_row = self.music_list.currentRow()
            if current_row < self.music_list.count() - 1:
                self.music_list.setCurrentRow(current_row + 1)
                self.play_music()

    def next_video(self):
        if self.shuffle_mode and self.video_list.count() > 1:
            choices = list(range(self.video_list.count()))
            current = self.video_list.currentRow()
            choices.remove(current)
            self.video_list.setCurrentRow(random.choice(choices))
            self.play_video()
        else:
            current_row = self.video_list.currentRow()
            if current_row < self.video_list.count() - 1:
                self.video_list.setCurrentRow(current_row + 1)
                self.play_video()

    def stop_music(self):
        self.is_changing_track = True
        self.media_player.stop()
        self.update_timer.stop()
        self.currently_playing = None
        self.is_playing = False
        self.is_paused = False
        self.btn_play.setText("▶ Play")
        self.seek_slider.setValue(0)
        self.current_time_label.setText("0:00")
        QTimer.singleShot(500, lambda: self.__dict__.update({'is_changing_track': False}))
        self.total_time_label.setText("0:00")

    def stop_video(self):
        self.media_player.stop()
        self.update_timer.stop()
        self.currently_playing = None
        self.is_playing = False
        self.is_paused = False
        self.btn_play.setText("▶ Play")
        self.seek_slider.setValue(0)
        self.current_time_label.setText("0:00")
        self.total_time_label.setText("0:00")

    def toggle_play_pause(self):
        if self.is_paused:
            self.media_player.play()
            self.is_paused = False
            self.is_playing = True
            self.btn_play.setText("⏸ Pause")
        elif self.is_playing:
            self.media_player.pause()
            self.is_paused = True
            self.is_playing = False
            self.btn_play.setText("▶ Play")
        elif self.currently_playing:
            self.play_file(str(self.currently_playing))
            self.is_playing = True
            self.is_paused = False
            self.btn_play.setText("⏸ Pause")

    def format_time(self, ms):
        if ms <= 0:
            return "0:00"
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"

    def update_slider_position(self):
        try:
            length = self.media_player.get_length()
            current = self.media_player.get_time()
            
            logger.debug(f"update_slider: length={length}, current={current}")
            
            if length <= 0:
                length = self.media_player.length()
                logger.debug(f"update_slider: fallback length={length}")
            
            if length > 0 and current >= 0 and not self.slider_dragging:
                self.seek_slider.blockSignals(True)
                self.seek_slider.setValue(int(current / length * 1000))
                self.seek_slider.blockSignals(False)
                self.current_time_label.setText(self.format_time(current))
                self.total_time_label.setText(self.format_time(length))
                
                if self.auto_play_next and current >= length - 2000 and not self.is_changing_track:
                    logger.debug("Playback ending soon, triggering next track")
                    self.is_changing_track = True
                    QTimer.singleShot(0, self.next_track)
                    QTimer.singleShot(500, lambda: self.__dict__.update({'is_changing_track': False}))
            elif length > 0 and not self.slider_dragging:
                self.total_time_label.setText(self.format_time(length))
        except Exception as e:
            logger.error(f"update_slider_position error: {e}")

    def slider_pressed(self):
        self.slider_dragging = True

    def slider_released(self):
        self.slider_dragging = False
        try:
            length = self.media_player.get_length()
            if length <= 0:
                length = self.media_player.length()
            if length > 0:
                position = self.seek_slider.value() / 1000 * length
                self.media_player.set_time(int(position))
        except Exception as e:
            pass

    def seek_position(self, value):
        try:
            length = self.media_player.get_length()
            if length <= 0:
                length = self.media_player.length()
            if length > 0:
                position = value / 1000 * length
                self.current_time_label.setText(self.format_time(int(position)))
        except Exception as e:
            pass

    def fetch_lyrics(self):
        title = self.song_title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Error", "Please enter a song title")
            return

        artist = self.artist_input.text().strip()

        def do_fetch():
            try:
                artist_param = artist.replace(" ", "%20") if artist else ""
                title_param = title.replace(" ", "%20")
                url = f"https://api.lyrics.ovh/v1/{artist_param}/{title_param}" if artist else f"https://api.lyrics.ovh/v1/{title_param}"
                
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if "lyrics" in data:
                        QTimer.singleShot(0, lambda: self.display_lyrics(data["lyrics"]))
                    else:
                        QTimer.singleShot(0, lambda: self.on_lyrics_error("No lyrics found"))
                else:
                    QTimer.singleShot(0, lambda: self.on_lyrics_error(f"Status: {response.status_code}"))
            except Exception as e:
                QTimer.singleShot(0, lambda: self.on_lyrics_error(str(e)))

        threading.Thread(target=do_fetch, daemon=True).start()

    def on_lyrics_error(self, error):
        logger.error(f"Lyrics fetch error: {error}")
        QMessageBox.critical(self, "Error", f"Failed to fetch lyrics: {error}")

    def display_lyrics(self, lyrics):
        self.lyrics_list.clear()
        for line in lyrics.split('\n'):
            self.lyrics_list.addItem(line)

    def save_lyrics(self):
        if self.lyrics_list.count() == 0:
            QMessageBox.warning(self, "Error", "No lyrics to save")
            return

        name, ok = QInputDialog.getText(self, "Save Lyrics", "Enter filename:")
        if ok and name:
            lyrics = ""
            for i in range(self.lyrics_list.count()):
                lyrics += self.lyrics_list.item(i).text() + "\n"

            file_path = get_lyrics_dir() / f"{name}.txt"
            file_path.write_text(lyrics, encoding="utf-8")
            QMessageBox.information(self, "Success", f"Saved to {file_path}")

    def load_lyrics(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Lyrics", str(get_lyrics_dir()),
            "Text Files (*.txt)"
        )
        if file_path:
            lyrics = Path(file_path).read_text(encoding="utf-8")
            self.display_lyrics(lyrics)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()