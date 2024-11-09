from tkinter import *
from tkinter import filedialog, simpledialog
import os
import pygame
from pytube import YouTube
from tkinter import messagebox, filedialog

class MusicPlayer:
    def __init__(self, root):
        pygame.mixer.init()

        self.root = root
        self.root.title("Music Player")
        self.root.geometry("830x500")
        
        self.songs = []
        self.highlighted_label = None
        self.current_playing_label = None 
        self.directory = ""
        self.playlist = []
        self.current_tab = "music_library"
        self.video = ""
        self.video_Link = StringVar()
        self.download_Path = StringVar()

        self.create_widgets()
        self.show_music_library()  

    def create_widgets(self):
        """Set up the GUI widgets."""
        # Navbar frame
        self.navbar = Frame(self.root, bg="white", width=200)
        Button(self.navbar, text="Music Library", width=20, padx=10, pady=10, background='green', bd=0, command=self.show_music_library).pack(padx=10, pady=10)
        Button(self.navbar, text="Lyrics", width=20, padx=10, pady=10, background='green', bd=0, command=self.show_lyrics).pack(padx=10, pady=0)
        Button(self.navbar, text="Video", width=20, padx=10, pady=10, background='green', bd=0, command=self.show_video).pack(padx=10, pady=10)
        self.navbar.pack(fill=Y, side=LEFT)

        # Content frame
        self.content_frame = Frame(self.root, bg="gray")
        self.content_frame.pack(side=TOP, fill=BOTH, expand=True)

    def show_music_library(self):
        """Display the music library content."""
        self.current_tab = "music_library" 
        
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.highlighted_label = None

        # Configuration frame
        self.config_frame = Frame(self.content_frame, bg="gray")
        self.config_frame.pack(fill=X, pady=5)

        load_button = Button(self.config_frame, text="Load Songs", command=self.load_songs, bd=0, width=20, background='white')
        load_button.pack(side=LEFT, padx=10, pady=10)

        self.songlist_frame = Frame(self.content_frame, bg="white")
        self.songlist_frame.pack(fill=BOTH, expand=True, padx=10, pady=0)

        self.songlist_canvas = Canvas(self.songlist_frame, bg="gray", highlightthickness=0)
        self.songlist_canvas.pack(side=LEFT, fill=BOTH, expand=True, padx=2, pady=2)

        self.scrollbar = Scrollbar(self.songlist_frame, orient=VERTICAL, command=self.songlist_canvas.yview)
        self.songlist_canvas.config(yscrollcommand=self.scrollbar.set)

        self.song_container = Frame(self.songlist_canvas, bg="gray")
        self.songlist_canvas.create_window((0, 0), window=self.song_container, anchor="nw")

        self.song_container.bind("<Configure>", lambda e: self.songlist_canvas.configure(scrollregion=self.songlist_canvas.bbox("all")))
        self.songlist_canvas.bind_all("<MouseWheel>", self.mouse_wheel)

        if self.songs:
            self.display_songs()  
            if self.highlighted_label is not None:
                self.highlighted_label.config(bg="yellow")

        # Control buttons frame
        self.control_frame = Frame(self.content_frame, bg="gray")
        self.control_frame.pack(fill=X, pady=5)
        self.create_control_buttons()

    def show_lyrics(self):
        """Display the lyrics content (currently empty)."""
        self.current_tab = "lyrics" 

        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.highlighted_label = None

        # Show lyrics section
        self.config_frame = Frame(self.content_frame, bg="gray")
        self.config_frame.pack(fill=X, pady=5)

        create_button = Button(self.config_frame, text="Get lyrics", command=self.get_lyrics, bd=0, width=20, background='white')
        create_button.pack(side=LEFT, padx=10, pady=10)

        self.lyrics_frame = Frame(self.content_frame, bg="white")
        self.lyrics_frame.pack(fill=BOTH, expand=True, padx=10, pady=0)

        self.lyrics_canvas = Canvas(self.lyrics_frame, bg="gray", highlightthickness=0)
        self.lyrics_canvas.pack(side=LEFT, fill=BOTH, expand=True, padx=2, pady=2)

        self.lyrics_container = Frame(self.lyrics_canvas, bg="gray")
        self.lyrics_canvas.create_window((0, 0), window=self.lyrics_container, anchor="nw")

        self.control_frame = Frame(self.content_frame, bg="gray")
        self.control_frame.pack(fill=X, pady=5)

    def show_video(self):
        """Display the video content (currently empty)."""
        self.current_tab = "video" 

        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.highlighted_label = None

        # Show video section
        self.config_frame = Frame(self.content_frame, bg="gray")
        self.config_frame.pack(fill=X, pady=5)

        load_button = Button(self.config_frame, text="Download video", command=self.down_load, bd=0, width=20, background='white')
        load_button.pack(side=LEFT, padx=10, pady=10)
        Entry(self.config_frame, textvariable=self.video_Link, width=50).pack(side=LEFT, padx=10, pady=10)

        self.video_frame = Frame(self.content_frame, bg="white")
        self.video_frame.pack(fill=BOTH, expand=True, padx=10, pady=0)

        self.video_canvas = Canvas(self.video_frame, bg="gray", highlightthickness=0)
        self.video_canvas.pack(side=LEFT, fill=BOTH, expand=True, padx=2, pady=2)

        self.video_container = Frame(self.video_canvas, bg="gray")
        self.video_canvas.create_window((0, 0), window=self.video_container, anchor="nw")

        self.control_frame = Frame(self.content_frame, bg="gray")
        self.play_video_button = Button(self.control_frame, text="Play Video", command=self.play_video, bd=0, width=20, background='white')
        self.control_frame.pack(fill=X, pady=5)

    def load_songs(self):
        """Load songs from a selected directory."""
        self.directory = filedialog.askdirectory()
        if self.directory:
            for widget in self.song_container.winfo_children():
                widget.destroy() 
            
            self.songs.clear() 

            for file in os.listdir(self.directory):
                if file.endswith(".mp3"):
                    self.songs.append(file)

            self.display_songs() 

    def load_video(self):
        """Load a video from a selected directory."""
        self.video = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4")])
        if self.video:
            for widget in self.video_container.winfo_children():
                widget.destroy() 

            video_label = Label(self.video_container, text=self.video, bg="lightgray", anchor="w", padx=10, pady=5)
            video_label.pack(fill=X, padx=5, pady=2)
            video_label.bind("<Button-1>", lambda e, lbl=video_label: self.highlight_label(lbl))

    def display_songs(self):
        """Display the loaded songs in the song container."""
        for song_name in self.songs:
            song_label = Label(self.song_container, text=song_name, bg="lightgray", anchor="w", padx=10, pady=5)
            song_label.pack(fill=X, padx=5, pady=2)
            song_label.bind("<Button-1>", lambda e, lbl=song_label: self.highlight_label(lbl))

        self.songlist_canvas.update_idletasks()
        self.songlist_canvas.config(scrollregion=self.songlist_canvas.bbox("all"))

    def get_lyrics(self):
        """Get lyric of a song."""

    def display_lyrics(self):
        """Display the created lyrics in the lyrics container."""
        for playlist_name in self.playlist:
            playlist_label = Label(self.playlist_container, text=playlist_name, bg="lightgray", anchor="w", padx=10, pady=5)
            playlist_label.pack(fill=X, padx=5, pady=2)
            playlist_label.bind("<Button-1>", lambda e, lbl=playlist_label: self.highlight_label(lbl))

        self.playlist_canvas.update_idletasks()
        self.playlist_canvas.config(scrollregion=self.playlist_canvas.bbox("all"))

    def create_control_buttons(self):
        """Create control buttons for playing music."""
        Button(self.control_frame, text="Play", width=20, background='white', bd=0, command=self.play_song).pack(side=LEFT, padx=10, pady=10)
        Button(self.control_frame, text="Stop", width=20, background='white', bd=0, command=self.stop_song).pack(side=LEFT, padx=10, pady=10)
        Button(self.control_frame, text="Pause", width=20, background='white', bd=0, command=self.pause_song).pack(side=LEFT, padx=10, pady=10)
        Button(self.control_frame, text="Resume", width=20, background='white', bd=0, command=self.resume_song).pack(side=LEFT, padx=10, pady=10)

    def mouse_wheel(self, event):
        """Scroll the canvas using mouse wheel."""
        self.songlist_canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def highlight_label(self, label):
        """Highlight the selected song label."""
        if self.highlighted_label is not None and self.highlighted_label.winfo_exists():
            self.highlighted_label.config(bg="lightgray")  

        label.config(bg="yellow")  
        self.highlighted_label = label  

    def play_song(self):
        """Play the selected song using Pygame."""
        if self.highlighted_label:
            song_name = self.highlighted_label.cget("text") 
            song_path = os.path.join(self.directory, song_name)  
            pygame.mixer.music.load(song_path)  
            pygame.mixer.music.play()
            
            if self.current_playing_label is not None and self.current_playing_label.winfo_exists():
                self.current_playing_label.config(bg="lightgray")  

            self.current_playing_label = self.highlighted_label
            self.current_playing_label.config(bg="orange")  

    def stop_song(self):
        """Stop the currently playing song."""
        pygame.mixer.music.stop()
        if self.current_playing_label is not None and self.current_playing_label.winfo_exists():
            self.current_playing_label.config(bg="lightgray")  
            self.current_playing_label = None  

    def pause_song(self):
        """Pause the currently playing song."""
        pygame.mixer.music.pause()

    def resume_song(self):
        """Resume the currently paused song."""
        pygame.mixer.music.unpause()

    def play_video(self):
        """Play the selected video."""

    def down_load(self):
        """Download the video."""
        download_Directory = filedialog.askdirectory(
        initialdir="YOUR DIRECTORY PATH", title="Save Video")
        self.download_Path.set(download_Directory)
        Youtube_link = self.video_Link.get()
        download_Folder = self.download_Path.get()
        getVideo = YouTube(Youtube_link)
        videoStream = getVideo.streams.first()
        videoStream.download(download_Folder)
        messagebox.showinfo("SUCCESSFULLY","DOWNLOADED AND SAVED IN\n"+ download_Folder)

if __name__ == "__main__":
    root = Tk()
    app = MusicPlayer(root)
    root.mainloop()
