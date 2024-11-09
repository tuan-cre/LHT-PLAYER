import tkinter as tk
from tkinter import filedialog, messagebox
import pygame
import os
import ctypes

class MusicLyricsApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Music Lyrics Player")
        self.master.geometry("400x200")
        self.current_lyric_index = 0
        self.lyric_labels = []
        self.lyric_window = None  # We'll reuse this window
        self.lyric_label = None  # The label that displays the lyric text
        self.song_file_path = None
        self.lyric_file_path = None
        
        self.create_widgets()

    def create_widgets(self):
        self.select_song_button = tk.Button(self.master, text="Select Song", command=self.select_song)
        self.select_song_button.pack(pady=5)
        
        self.select_lyric_button = tk.Button(self.master, text="Select Lyric", command=self.select_lyric)
        self.select_lyric_button.pack(pady=5)
        
        self.start_button = tk.Button(self.master, text="Start", command=self.start_lyrics)
        self.start_button.pack(pady=5)
        
        self.stop_button = tk.Button(self.master, text="Stop", command=self.stop_lyrics)
        self.stop_button.pack(pady=5)

    def select_song(self):
        self.song_file_path = filedialog.askopenfilename(title="Select Song File", filetypes=[("Audio Files", "*.mp3;*.wav")])

    def select_lyric(self):
        self.lyric_file_path = filedialog.askopenfilename(title="Select Lyric File", filetypes=[("Text Files", "*.txt")])
        if self.lyric_file_path:
            self.load_lyrics(self.lyric_file_path)

    def load_lyrics(self, file_path):
        self.lyric_labels = parse_lyrics_file(file_path)

    def start_lyrics(self):
        if not self.song_file_path or not self.lyric_file_path:
            messagebox.showerror("Error", "Please select both a song and a lyric file.")
            return

        # Initialize pygame mixer for music playback
        pygame.mixer.init()
        pygame.mixer.music.load(self.song_file_path)
        pygame.mixer.music.play()

        # Start displaying lyrics
        self.display_next_lyric()

        pygame.mixer.music.set_endevent(pygame.USEREVENT)
        self.master.bind(pygame.USEREVENT, self.restart_lyrics)

    def stop_lyrics(self):
        pygame.mixer.music.stop()
        self.current_lyric_index = 0
        self.destroy_lyric_window()

    def restart_lyrics(self, event):
        self.current_lyric_index = 0
        self.display_next_lyric()

    def display_next_lyric(self):
        if self.current_lyric_index < len(self.lyric_labels):
            next_lyric = self.lyric_labels[self.current_lyric_index]
            current_time = pygame.mixer.music.get_pos() / 1000.0  # Get the current time in seconds
            lyric_start_time = next_lyric["start_time"]

            if current_time >= lyric_start_time:
                self.show_lyric(next_lyric["text"])
                self.current_lyric_index += 1

            # Continue checking the timing in the next cycle
            self.master.after(100, self.display_next_lyric)

    def show_lyric(self, text):
        if not self.lyric_window:
            self.lyric_window = tk.Toplevel(self.master)
            self.lyric_window.overrideredirect(True)
            self.lyric_window.lift()
            self.lyric_window.wm_attributes("-topmost", True)
            self.lyric_window.wm_attributes("-disabled", True)
            self.lyric_window.wm_attributes("-transparentcolor", "black")
            self.lyric_window.configure(bg="black")

            screen_width = self.lyric_window.winfo_screenwidth()
            self.lyric_window.geometry(f"{screen_width}x50")
            
            self.lyric_label = tk.Label(self.lyric_window, font=('consolas', 30), fg='white', bg='black', justify='center')
            self.lyric_label.pack(anchor='center')

        self.lyric_label.config(text=text)

    def destroy_lyric_window(self):
        if self.lyric_window:
            self.lyric_window.destroy()
            self.lyric_window = None
            self.lyric_label = None

def parse_lyrics_file(file_path):
    lyric_labels = []
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    for i in range(0, len(lines), 2):
        lyric_text = lines[i + 1].strip()
        time_str = lines[i].strip()
        
        # Skip non-lyric lines like contributors or "Embed" text
        if "Contributor" in lyric_text or "Embed" in lyric_text:
            continue
        
        try:
            minutes, seconds = map(int, time_str.split(':'))
            start_time = minutes * 60 + seconds
            lyric_labels.append({"text": lyric_text, "start_time": start_time})
        except ValueError:
            pass  # Ignore lines that don't contain a valid timestamp

    return lyric_labels

def main():
    root = tk.Tk()
    app = MusicLyricsApp(root)
    root.mainloop()

if __name__ == "__main__":
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    main()
