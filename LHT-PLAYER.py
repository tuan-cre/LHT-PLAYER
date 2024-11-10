from tkinter import *
from tkinter import filedialog, simpledialog
import os
from pytubefix import YouTube
from tkinter import messagebox, filedialog
from tkinter import ttk
from pydub import AudioSegment
import shutil
import lyricsgenius
import pygame
import vlc

class MusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Player")
        self.root.geometry("900x600") 
        self.root.resizable(False, False) 
        self.genius = lyricsgenius.Genius("I1Skzzd5zK9eEuzOojzk-t_z_cFb9FhkAykiHQKFTRhpwpj-gcOYRgX23Dz2pWOT7jF9H9Nd-p3gKAnMEMUSOg")

        self.music_directory = "music"
        self.songs = []
        self.video_directory = "video"
        self.videos = []

        # Create a basic vlc instance
        self.instance = vlc.Instance()
        self.media = None
        # Create an empty vlc media player
        self.mediaplayer = self.instance.media_player_new()

        self.song_title = StringVar()
        self.artist_name = StringVar()

        self.highlighted_label = None
        self.current_playing_label = None 
        self.create_widgets()

        pygame.mixer.init()

    def create_widgets(self):
        """Set up the GUI widgets with ttk.Notebook for tab control."""

        # Navbar frame
        self.navbar = Frame(self.root, bg="white", width=200)
        self.navbar.pack(fill=Y, side=LEFT, padx=5)  # Ensure it's visible by packing

        # Buttons in navbar
        Button(self.navbar, text="Music", width=20, padx=10, pady=10, background='green', command=lambda: self.change_tab(1), bd=0).pack(padx=10, pady=10)   
        Button(self.navbar, text="Video", width=20, padx=10, pady=10, background='green', command=lambda: self.change_tab(2), bd=0).pack(padx=10, pady=0)
        Button(self.navbar, text="Lyrics", width=20, padx=10, pady=10, background='green', command=lambda: self.change_tab(3), bd=0).pack(padx=10, pady=10)

        # Create a style to hide the tab buttons
        style = ttk.Style()
        style.configure("TNotebook.Tab", padding=[0, 0], width=0, anchor="center", relief="flat")
        style.configure("TNotebook", tabposition="none")  # This will hide the tab buttons

        # Create the notebook for tabs (without visible tabs)
        self.notebook = ttk.Notebook(self.root, style="TNotebook")

        # Use pack() to position the notebook
        self.notebook.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # Create tabs for the notebook
        self.music_tab = Frame(self.notebook, bg="gray")
        self.video_tab = Frame(self.notebook, bg="gray")
        self.lyrics_tab = Frame(self.notebook, bg="gray")

        # Add tabs to the notebook (content only, no visible tabs)
        self.notebook.add(self.music_tab, text="Music")
        self.notebook.add(self.video_tab, text="Video")
        self.notebook.add(self.lyrics_tab, text="Lyric")
        self.notebook.place(relwidth=0.8, relheight=1.1, x=190, y=-22)

        self.setup_music_library()
        self.setup_lyrics_tab()
        self.setup_video_tab()
        # Initially display the Music tab
        self.notebook.select(self.music_tab)

    def setup_music_library(self):
        """Set up the Music Library tab content."""
        # Configuration frame for Music Library

        self.config_frame = Frame(self.music_tab, bg="gray")
        self.config_frame.pack(fill=X, pady=5)

        add_song_folder = Button(self.config_frame, text="Thêm bài hát từ thư mục", command=lambda: self.add_to_library(1), bd=0, width=20, background='white')
        add_song_folder.pack(side=LEFT, padx=10, pady=10)
        add_mp3_file = Button(self.config_frame, text="Thêm tệp mp3", command=lambda: self.add_to_library(2), bd=0, width=20, background='white')
        add_mp3_file.pack(side=LEFT, padx=10, pady=10)
        download_mp3_file = Button(self.config_frame, text="Tải bài hát từ youtube", command=lambda: self.download_to_library(1), bd=0, width=20, background='white')
        download_mp3_file.pack(side=LEFT, padx=10, pady=10)
        delete_selected_song= Button(self.config_frame, text="Xóa bài hát được chọn", command=lambda: self.delete_selected_file(1), bd=0, width=20, background='white')
        delete_selected_song.pack(side=LEFT, padx=10, pady=10)

        # Song list frame
        self.songlist_frame = Frame(self.music_tab, bg="white")
        self.songlist_frame.pack(fill=BOTH, expand=True, padx=10, pady=0)

        self.songlist_canvas = Canvas(self.songlist_frame, bg="gray", highlightthickness=0)
        self.songlist_canvas.pack(side=LEFT, fill=BOTH, expand=True, padx=2, pady=2)

        self.scrollbar = Scrollbar(self.songlist_frame, orient=VERTICAL, command=self.songlist_canvas.yview)
        self.songlist_canvas.config(yscrollcommand=self.scrollbar.set)

        self.song_container = Frame(self.songlist_canvas, bg="gray")
        self.songlist_canvas.create_window((0, 0), window=self.song_container, anchor="nw")
        self.song_container.bind("<Configure>", lambda e: self.songlist_canvas.configure(scrollregion=self.songlist_canvas.bbox("all")))
        self.songlist_canvas.bind_all("<MouseWheel>", self.mouse_wheel)

        # Control buttons frame
        self.control_frame = Frame(self.music_tab, bg="gray")
        self.control_frame.pack(fill=X, pady=(0, 35))
        Button(self.control_frame, text="Play", width=20, background='white', bd=0, command=self.play_song).pack(side=LEFT, padx=10, pady=10)
        Button(self.control_frame, text="Stop", width=20, background='white', bd=0, command=self.stop_song).pack(side=LEFT, padx=10, pady=10)
        Button(self.control_frame, text="Pause", width=20, background='white', bd=0, command=self.pause_song).pack(side=LEFT, padx=10, pady=10)
        Button(self.control_frame, text="Resume", width=20, background='white', bd=0, command=self.resume_song).pack(side=LEFT, padx=10, pady=10)

        # self.load_songs()
        self.display_songs()

    def setup_video_tab(self):
        """Set up the Video tab content."""
        # Download video section
        self.config_frame = Frame(self.video_tab, bg="gray")
        self.config_frame.pack(fill=X, pady=5)

        add__video_folder = Button(self.config_frame, text="Thêm video từ thư mục", command=lambda: self.add_to_library(3), bd=0, width=20, background='white')
        add__video_folder.pack(side=LEFT, padx=10, pady=10)
        add_mp4_file = Button(self.config_frame, text="Thêm tệp mp4", command=lambda: self.add_to_library(4), bd=0, width=20, background='white')
        add_mp4_file.pack(side=LEFT, padx=10, pady=10)
        download_mp4_file = Button(self.config_frame, text="Tải video từ youtube", command=lambda: self.download_to_library(2), bd=0, width=20, background='white')
        download_mp4_file.pack(side=LEFT, padx=10, pady=10)
        delete_selected_video= Button(self.config_frame, text="Xóa video được chọn", command=lambda: self.delete_selected_file(2), bd=0, width=20, background='white')
        delete_selected_video.pack(side=LEFT, padx=10, pady=10)

        # Video display frame
        self.video_frame = Frame(self.video_tab, bg="white")
        self.video_frame.pack(fill=BOTH, expand=True, padx=10, pady=0)

        # Video list canvas with scrollbar
        self.video_canvas = Canvas(self.video_frame, bg="gray", highlightthickness=0)
        self.video_canvas.pack(side=LEFT, fill=BOTH, expand=True, padx=2, pady=2)

        # Video container frame
        self.video_container = Frame(self.video_canvas, bg="gray")
        self.video_canvas.create_window((0, 0), window=self.video_container, anchor="nw")
        
        self.control_frame = Frame(self.video_tab, bg="gray")
        self.control_frame.pack(fill=X, pady=(0, 35))
        Button(self.control_frame, text="Play", width=20, background='white', bd=0, command=self.play_video).pack(side=LEFT, padx=10, pady=10)
        Button(self.control_frame, text="Stop", width=20, background='white', bd=0, command=self.stop_video).pack(side=LEFT, padx=10, pady=10)
        Button(self.control_frame, text="Pause", width=20, background='white', bd=0, command=self.pause_video).pack(side=LEFT, padx=10, pady=10)
        Button(self.control_frame, text="Resume", width=20, background='white', bd=0, command=self.resume_video).pack(side=LEFT, padx=10, pady=10)

        # Bind mouse wheel for scrolling
        self.video_container.bind("<Configure>", lambda e: self.video_canvas.configure(scrollregion=self.video_canvas.bbox("all")))
        self.video_canvas.bind_all("<MouseWheel>", self.mouse_wheel)

        # Call display_videos to populate the video list
        self.display_videos()

    def setup_lyrics_tab(self):
        """Set up the Lyrics tab content."""
        
        self.config_frame = Frame(self.lyrics_tab, bg="gray")
        self.config_frame.pack(fill=X, pady=5)

        get_lyric_button = Button(self.config_frame, text="Get lyric", command=self.fetch_lyric, bd=0, width=20, background='white')
        get_lyric_button.pack(side=LEFT, padx=10, pady=10)
        input_song_title = Entry(self.config_frame, textvariable=self.song_title, width=25, background='white')
        input_song_title.pack(side=LEFT, padx=10, pady=10)
        input_artist_name = Entry(self.config_frame, textvariable=self.artist_name, width=25, background='white')
        input_artist_name.pack(side=LEFT, padx=10, pady=10)

        self.lyrics_frame = Frame(self.lyrics_tab, bg="white")
        self.lyrics_frame.pack(fill=BOTH, expand=True, padx=10, pady=(0, 45))

        self.lyrics_canvas = Canvas(self.lyrics_frame, bg="gray", highlightthickness=0)
        self.lyrics_canvas.pack(side=LEFT, fill=BOTH, expand=True, padx=2, pady=2)

        self.lyrics_container = Frame(self.lyrics_canvas, bg="gray")
        self.lyrics_canvas.create_window((0, 0), window=self.lyrics_container, anchor="nw")

        self.lyrics_canvas.bind("<Configure>", lambda e: self.lyrics_canvas.configure(scrollregion=self.lyrics_canvas.bbox("all")))
        self.lyrics_canvas.bind_all("<MouseWheel>", self.mouse_wheel)

    def play_song(self):
        if self.highlighted_label:
            song_name = self.highlighted_label.cget("text")
            song_path = os.path.join(self.music_directory, song_name)
            pygame.mixer.music.load(song_path)
            pygame.mixer.music.play()
            self.current_playing_label = self.highlighted_label
        
    def stop_song(self):
        pygame.mixer.music.stop()
        if self.current_playing_label:
            self.current_playing_label.config(bg="lightgray")
            self.current_playing_label = None

    def pause_song(self):
        pygame.mixer.music.pause()

    def resume_song(self):
        pygame.mixer.music.unpause()

    def play_video(self):
        if self.highlighted_label:
            video_name = self.highlighted_label.cget("text")
            video_path = os.path.join(self.video_directory, video_name)
            self.media = self.instance.media_new(video_path)
            self.mediaplayer.set_media(self.media)
            for widget in self.video_container.winfo_children():
                widget.destroy()
            self.video_container.config(background="black")
            self.video_canvas.config(background="black")
            video_frame_id = self.video_frame.winfo_id()  # Get the window ID of the canvas
            self.mediaplayer.set_hwnd(video_frame_id)  # Set the window ID where the video will be displayed
            
            self.mediaplayer.play()

    def stop_video(self):
        self.mediaplayer.stop()
        self.video_container.config(background="gray")
        self.video_canvas.config(background="gray")
        self.display_videos()

    def pause_video(self):
        self.mediaplayer.pause()

    def resume_video(self):
        self.mediaplayer.play()

    def change_tab(self, tab_index):
        """Change the selected tab based on the index."""
        if tab_index == 1:
            self.notebook.select(self.music_tab)
        elif tab_index == 2:
            self.notebook.select(self.video_tab)
        elif tab_index == 3:
            self.notebook.select(self.lyrics_tab)

    def add_to_library(self, n):
        if n == 1:
            """Load songs from a selected directory."""
            directory = filedialog.askdirectory()
            if self.music_directory:
                for widget in self.song_container.winfo_children():
                    widget.destroy() 
                for file in os.listdir(self.music_directory):
                    if file.endswith(".mp3"):
                        source_path = os.path.join(directory, file)
                        destination_path = os.path.join(self.music_directory, file)
                        # Copy the file to the music directory if it doesn’t already exist
                        if not os.path.exists(destination_path):
                            shutil.copy(source_path, destination_path)
                        self.songs.append(file)
                self.display_songs()
        elif n == 2:
            """Load songs from selected files."""
            files = filedialog.askopenfilenames(filetypes=[("MP3 files", "*.mp3")])
            if files:
                for widget in self.song_container.winfo_children():
                    widget.destroy() 
                for file in files:
                    file_name = os.path.basename(file)
                    destination_path = os.path.join(self.music_directory, file_name)
                    if not os.path.exists(destination_path):
                        shutil.copy(file, destination_path)
                    self.songs.append(file.split("/")[-1])
                self.display_songs() 
        elif n == 3:
            """Load videos from a selected directory."""
            directory = filedialog.askdirectory()
            if self.video_directory:
                for widget in self.video_container.winfo_children():
                     widget.destroy() 
                for file in os.listdir(self.video_directory):
                    if file.endswith(".mp4"):
                        source_path = os.path.join(directory, file)
                        destination_path = os.path.join(self.video_directory, file)
                        if not os.path.exists(destination_path):
                            shutil.copy(source_path, destination_path)
                        self.videos.append(file)
                self.display_videos()
        elif n == 4:
            """Load videos from selected files."""
            files = filedialog.askopenfilenames(filetypes=[("MP4 files", "*.mp4")])
            if files:
                for widget in self.video_container.winfo_children():
                    widget.destroy() 
                for file in files:
                    file_name = os.path.basename(file)
                    destination_path = os.path.join(self.video_directory, file_name)
                    if not os.path.exists(destination_path):
                        shutil.copy(file, destination_path)
                        self.videos.append(file.split("/")[-1])
                self.display_videos()

    def download_to_library(self, n):
        if n == 1:
            link = simpledialog.askstring("Input", "Enter the link of the song you want to download:")
            video = YouTube(link)
            stream = video.streams.filter(file_extension='mp4', progressive=True).order_by('resolution').desc().first()
            downloaded_video_path = stream.download(self.video_directory)
            mp3_file_path = os.path.join(self.music_directory, os.path.splitext(os.path.basename(downloaded_video_path))[0] + ".mp3")
            AudioSegment.from_file(downloaded_video_path).export(mp3_file_path, format="mp3")
            messagebox.showinfo("Download", "Download and conversion to mp3 completed.")
            self.songs.append(os.path.basename(mp3_file_path))
            self.display_songs()
        elif n == 2:
            link = simpledialog.askstring("Input", "Enter the link of the video you want to download:")
            video = YouTube(link)
            stream = video.streams.filter(file_extension='mp4', progressive=True).order_by('resolution').desc().first()
            downloaded_video_path = stream.download(self.video_directory)
            messagebox.showinfo("Download", "Download completed.")
            self.videos.append(os.path.basename(downloaded_video_path))
            self.display_videos()

    def delete_selected_file(self, n):
        if n == 1:
            if self.highlighted_label:
                song_name = self.highlighted_label.cget("text")
                song_path = os.path.join(self.music_directory, song_name)
                os.remove(song_path)
                self.songs.remove(song_name)
                self.highlighted_label.destroy()
        elif n == 2:
            if self.highlighted_label:
                video_name = self.highlighted_label.cget("text")
                video_path = os.path.join(self.video_directory, video_name)
                os.remove(video_path)
                self.videos.remove(video_name)
                self.highlighted_label.destroy()

    def fetch_lyric(self):
        song_title = self.song_title.get()
        artist_name = self.artist_name.get()
        if not song_title or not artist_name:
            messagebox.showerror("Error", "Please enter both the song title and artist name.")
            return

        song = self.genius.search_song(song_title, artist_name)
        if song:
            lyrics = song.lyrics
            self.display_lyrics(lyrics)
        else:
            messagebox.showerror("Error", "Lyrics not found.")

    def convert_mp4_to_mp3(self, mp4_path):
        # Load the .mp4 file (as an audio file)
        audio = AudioSegment.from_file(mp4_path, format="mp4")
        # Replace .mp4 with .mp3 in the file path
        mp3_path = mp4_path.replace(".mp4", ".mp3")
        # Export to .mp3 format
        audio.export(mp3_path, format="mp3")
        return mp3_path

    # def load_songs(self):
    #     """Load songs from the music directory."""
        
    def display_songs(self):
        """Display the loaded songs in the song container."""
        for file in os.listdir(self.music_directory):
            if file.endswith(".mp3") and file not in self.songs:
                self.songs.append(file)
                
        for song_name in self.songs:
            song_label = Label(self.song_container, text=song_name, bg="lightgray", width=94, anchor="w", padx=10, pady=5)
            song_label.pack(fill=X, padx=5, pady=5)
            song_label.bind("<Button-1>", lambda e, lbl=song_label: self.highlight_label(lbl))

        self.songlist_canvas.update_idletasks()
        self.songlist_canvas.config(scrollregion=self.songlist_canvas.bbox("all"))

    def display_videos(self):
        """Display the loaded videos in the video container."""
        # Add any new videos to the list
        for file in os.listdir(self.video_directory):
            if file.endswith(".mp4") and file not in self.videos:
                self.videos.append(file)

        # Create a label for each video
        for video_name in self.videos:
            video_label = Label(self.video_container, text=video_name, bg="lightgray", width=94, anchor="w", padx=10, pady=5)
            video_label.pack(fill=X, padx=5, pady=5)
            video_label.bind("<Button-1>", lambda e, lbl=video_label: self.highlight_label(lbl))

        # Update the canvas scroll region after adding new content
        self.video_canvas.update_idletasks()
        self.video_canvas.config(scrollregion=self.video_canvas.bbox("all"))

    def display_lyrics(self, lyrics):
        """Display the fetched lyrics in the lyrics container."""
        # Clear the previous lyrics
        for widget in self.lyrics_container.winfo_children():
            widget.destroy()

        # Split the lyrics into lines
        lines = lyrics.split("\n")

        # Create a label for each line of lyrics
        for line in lines:
            lyric_label = Label(self.lyrics_container, text=line, bg="gray", width=94, anchor="w", padx=10, pady=0)
            lyric_label.pack(fill=X, padx=5, pady=5)

        # Update the canvas scroll region after adding new content
        self.lyrics_canvas.update_idletasks()
        self.lyrics_canvas.config(scrollregion=self.lyrics_canvas.bbox("all"))

    def highlight_label(self, label):
        """Highlight the selected song label."""
        if self.highlighted_label is not None and self.highlighted_label.winfo_exists():
            self.highlighted_label.config(bg="lightgray")  

        label.config(bg="yellow")  
        self.highlighted_label = label

    def mouse_wheel(self, event):
        self.songlist_canvas.yview_scroll(-1 * (event.delta // 120), "units")
        self.video_canvas.yview_scroll(-1 * (event.delta // 120), "units")
        self.lyrics_canvas.yview_scroll(-1 * (event.delta // 120), "units")
        # Prevent scrolling beyond the top limit
        if self.songlist_canvas.yview()[0] <= 0:
            self.songlist_canvas.yview_moveto(0)
        if self.video_canvas.yview()[0] <= 0:
            self.video_canvas.yview_moveto(0)

if __name__ == "__main__":
    root = Tk()
    app = MusicPlayer(root)
    root.mainloop()