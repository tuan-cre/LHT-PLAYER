from tkinter import *
from tkinter import filedialog, simpledialog, messagebox
import os
import pygame
from pytube import YouTube
from tkinter import ttk

class MusicPlayer:
    def __init__(self, root):
        pygame.mixer.init()

        self.root = root
        self.root.title("Music Player")
        self.root.geometry("830x500")
        
        self.songs = []
        self.highlighted_label = None
        self.current_playing_label = None 
        self.directory = "music"
        self.playlist = []
        self.video = ""
        self.video_Link = StringVar()
        self.download_Path = StringVar()

        self.create_widgets()

    def create_widgets(self):
        """Set up the GUI widgets using Notebook for tab control."""

        style = ttk.Style()
        style.theme_use('default')
        style.configure("Custom.TNotebook", tabmargins=[2, 5, 2, 0])
        style.configure("Custom.TNotebook.Tab", font=("Arial", 12, "bold"), padding=[10, 5], width=15, background="#88c999")
        style.map("Custom.TNotebook.Tab", background=[("selected", "#4caf50")], foreground=[("selected", "#ffffff")])

        style.layout("Custom.TNotebook.Tab", [
            ("Notebook.tab", {"sticky": "nswe", "children": [
                ("Notebook.padding", {"side": "top", "sticky": "nswe", "children": [
                    ("Notebook.focus", {"side": "top", "sticky": "nswe", "children": [
                        ("Notebook.label", {"side": "top", "sticky": "nswe"})
                    ]})
                ]})
            ]})
        ])

        # Notebook for tab control
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=BOTH, expand=True)

        # Create tabs
        self.music_tab = Frame(self.notebook, bg="gray")
        self.lyrics_tab = Frame(self.notebook, bg="gray")
        self.video_tab = Frame(self.notebook, bg="gray")

        # Add tabs to the notebook
        self.notebook.add(self.music_tab, text= "Music Library")
        self.notebook.add(self.lyrics_tab, text="Lyric")
        self.notebook.add(self.video_tab, text= "Video")

        # Initialize each tab's content
        self.setup_music_library()
        self.setup_lyrics_tab()
        self.setup_video_tab()

    def setup_music_library(self):
        """Set up the Music Library tab content."""
        # Configuration frame for Music Library

        self.config_frame = Frame(self.music_tab, bg="gray")
        self.config_frame.pack(fill=X, pady=5)

        add_folder = Button(self.config_frame, text="Thêm thư mục", command=self.add_folder, bd=0, width=20, background='white')
        add_folder.pack(side=LEFT, padx=10, pady=10)
        add_file = Button(self.config_frame, text="Thêm tệp mp3", command=self.add_file, bd=0, width=20, background='white')
        add_file.pack(side=LEFT, padx=10, pady=10)

        # Song list frame
        self.songlist_frame = Frame(self.music_tab, bg="white")
        self.songlist_frame.pack(fill=BOTH, expand=True, padx=10, pady=0)

        self.songlist_canvas = Canvas(self.songlist_frame, bg="gray", highlightthickness=0)
        self.songlist_canvas.pack(side=LEFT, fill=BOTH, expand=True, padx=2, pady=2)

        # self.scrollbar = Scrollbar(self.songlist_frame, orient=VERTICAL, command=self.songlist_canvas.yview)
        # self.songlist_canvas.config(yscrollcommand=self.scrollbar.set)

        self.song_container = Frame(self.songlist_canvas, bg="gray")
        self.songlist_canvas.create_window((0, 0), window=self.song_container, anchor="nw")
        # self.song_container.bind("<Configure>", lambda e: self.songlist_canvas.configure(scrollregion=self.songlist_canvas.bbox("all")))
        # self.songlist_canvas.bind_all("<MouseWheel>", self.mouse_wheel)

        # Control buttons frame
        self.control_frame = Frame(self.music_tab, bg="gray")
        self.control_frame.pack(fill=X, pady=5)
        Button(self.control_frame, text="Play", width=20, background='white', bd=0).pack(side=LEFT, padx=10, pady=10)
        Button(self.control_frame, text="Stop", width=20, background='white', bd=0).pack(side=LEFT, padx=10, pady=10)
        Button(self.control_frame, text="Pause", width=20, background='white', bd=0).pack(side=LEFT, padx=10, pady=10)
        Button(self.control_frame, text="Resume", width=20, background='white', bd=0).pack(side=LEFT, padx=10, pady=10)

        self.load_songs()
        self.display_songs()

    def setup_lyrics_tab(self):
        """Set up the Lyrics tab content."""
        create_button = Button(self.lyrics_tab, text="Get lyrics", bd=0, width=20, background='white')
        create_button.pack(pady=10)

        self.lyrics_frame = Frame(self.lyrics_tab, bg="white")
        self.lyrics_frame.pack(fill=BOTH, expand=True, padx=10, pady=0)

        self.lyrics_canvas = Canvas(self.lyrics_frame, bg="gray", highlightthickness=0)
        self.lyrics_canvas.pack(side=LEFT, fill=BOTH, expand=True, padx=2, pady=2)

        self.lyrics_container = Frame(self.lyrics_canvas, bg="gray")
        self.lyrics_canvas.create_window((0, 0), window=self.lyrics_container, anchor="nw")

    def setup_video_tab(self):
        """Set up the Video tab content."""
        # Download video section
        self.config_frame = Frame(self.video_tab, bg="gray")
        self.config_frame.pack(fill=X, pady=5)

        load_button = Button(self.config_frame, text="Download video", bd=0, width=20, background='white')
        load_button.pack(side=LEFT, padx=10, pady=10)
        Entry(self.config_frame, textvariable=self.video_Link, width=50).pack(side=LEFT, padx=10, pady=10)

        self.video_frame = Frame(self.video_tab, bg="white")
        self.video_frame.pack(fill=BOTH, expand=True, padx=10, pady=0)

        self.video_canvas = Canvas(self.video_frame, bg="gray", highlightthickness=0)
        self.video_canvas.pack(side=LEFT, fill=BOTH, expand=True, padx=2, pady=2)

    # Rest of your functions remain mostly the same, no need to destroy widgets anymore.
    def add_folder(self):
        """Load songs from a selected directory."""
        self.directory = filedialog.askdirectory()
        if self.directory:
            for widget in self.song_container.winfo_children():
                widget.destroy() 
            
            # self.songs.clear() 

            for file in os.listdir(self.directory):
                if file.endswith(".mp3"):
                    self.songs.append(file)

            self.display_songs() 

    def add_file(self):
        """Load songs from selected files."""
        files = filedialog.askopenfilenames(filetypes=[("MP3 files", "*.mp3")])
        if files:
            for widget in self.song_container.winfo_children():
                widget.destroy() 
            
            # self.songs.clear() 

            for file in files:
                self.songs.append(file.split("/")[-1])

            self.display_songs()

    def load_songs(self):
        """Load songs from the music directory."""
        for file in os.listdir(self.directory):
            if file.endswith(".mp3"):
                self.songs.append(file)

    def display_songs(self):
        """Display the loaded songs in the song container."""
        for song_name in self.songs:
            song_label = Label(self.song_container, text=song_name, bg="lightgray", anchor="w", padx=10, pady=5)
            song_label.pack(fill=X, padx=5, pady=2)
            song_label.bind("<Button-1>", lambda e, lbl=song_label: self.highlight_label(lbl))

        self.songlist_canvas.update_idletasks()
        self.songlist_canvas.config(scrollregion=self.songlist_canvas.bbox("all"))

    def highlight_label(self, label):
        """Highlight the selected song label."""
        if self.highlighted_label is not None and self.highlighted_label.winfo_exists():
            self.highlighted_label.config(bg="lightgray")  

        label.config(bg="yellow")  
        self.highlighted_label = label  

if __name__ == "__main__":
    root = Tk()
    app = MusicPlayer(root)
    root.mainloop()
