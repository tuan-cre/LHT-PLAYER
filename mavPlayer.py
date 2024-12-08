from tkinter import *
from tkinter import filedialog, simpledialog, messagebox, ttk
from pytubefix import YouTube
from pydub import AudioSegment
import lyricsgenius
import vlc
import os, shutil

class MusicPlayer:
    def __init__(self, root):

        self.root = root
        self.root.title("mavPlayer")
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = int(screen_width / 2 - 900 / 2)
        center_y = int(screen_height / 2 - 600/ 2)
        root.geometry(f'900x600+{center_x}+{center_y}')
        self.root.resizable(False, False) 

        self.genius = lyricsgenius.Genius("I1Skzzd5zK9eEuzOojzk-t_z_cFb9FhkAykiHQKFTRhpwpj-gcOYRgX23Dz2pWOT7jF9H9Nd-p3gKAnMEMUSOg")

        os.makedirs("music", exist_ok=True)
        os.makedirs("video", exist_ok=True)
        os.makedirs("lyrics", exist_ok=True)

        self.music_directory = "music"
        self.video_directory = "video"
        self.lyric_directory = "lyrics"

        self.videos = []
        self.songs = []

        self.instance = vlc.Instance()
        self.mediaplayer = self.instance.media_player_new()
        self.songplayer = self.instance.media_player_new()

        self.song_title = StringVar()
        self.artist_name = StringVar()

        self.highlighted_label = None

        self.create_widgets()

    def create_widgets(self):

        self.navbar = Frame(self.root, bg="#FCF7D2", width=200)
        self.navbar.pack(fill=Y, side=LEFT)

        Button(self.navbar, text="♫ Music ♫", width=20, padx=10, pady=10, background='lightblue', command=lambda: self.change_tab("music"), bd=2, relief=RAISED, fg='black', font=('Consolas', 10, 'bold')).pack(padx=10, pady=10)
        Button(self.navbar, text="▶ Video ▶", width=20, padx=10, pady=10, background='lightblue', command=lambda: self.change_tab("video"), bd=2, relief=RAISED, fg='black', font=('Consolas', 10, 'bold')).pack(padx=10, pady=0)
        Button(self.navbar, text="𝄙 Lyric 𝄙", width=20, padx=10, pady=10, background='lightblue', command=lambda: self.change_tab("lyric"), bd=2, relief=RAISED, fg='black', font=('Consolas', 10, 'bold')).pack(padx=10, pady=10)

        self.notebook = ttk.Notebook(self.root, style="TNotebook")
        self.notebook.pack(fill=BOTH, expand=True)

        self.music_tab = Frame(self.notebook, bg="gray")
        self.video_tab = Frame(self.notebook, bg="gray")
        self.lyrics_tab = Frame(self.notebook, bg="gray")

        self.notebook.add(self.music_tab, text="Music")
        self.notebook.add(self.video_tab, text="Video")
        self.notebook.add(self.lyrics_tab, text="Lyric")
        self.notebook.place(relwidth=0.8, relheight=1.1, x=185, y=-23)

        self.setup_music_tab()
        self.setup_lyrics_tab()
        self.setup_video_tab()
        self.notebook.select(self.music_tab)

    def setup_music_tab(self):

        self.config_frame = Frame(self.music_tab, bg="gray")
        self.config_frame.pack(fill=X, pady=5)

        Button(self.config_frame, text="🗁 Thêm thư mục", command=self.add_song_folder, bd=0, width=20, background='white').pack(side=LEFT, padx=10, pady=10)
        Button(self.config_frame, text="♪ Thêm tệp mp3", command=self.add_mp3_file, bd=0, width=20, background='white').pack(side=LEFT, padx=25, pady=10)
        Button(self.config_frame, text="⬇ Tải từ youtube", command=lambda: self.download_mp3(), bd=0, width=20, background='white').pack(side=LEFT, padx=(13, 25), pady=10)
        Button(self.config_frame, text="✘ Xóa bài hát", command=lambda: self.delete_selected_file("mp3"), bd=0, width=20, background='white').pack(side=RIGHT, padx=10, pady=10)

        self.song_frame = Frame(self.music_tab, bg="white")
        self.song_frame.pack(fill=BOTH, expand=True, padx=10, pady=0)

        self.song_canvas = Canvas(self.song_frame, bg="gray", highlightthickness=0)
        self.song_canvas.pack(side=LEFT, fill=BOTH, expand=True, padx=2, pady=2)

        self.scrollbar = Scrollbar(self.song_frame, orient=VERTICAL, command=self.song_canvas.yview)
        self.song_canvas.config(yscrollcommand=self.scrollbar.set)

        self.song_container = Frame(self.song_canvas, bg="gray")
        self.song_canvas.create_window((0, 0), window=self.song_container, anchor="nw")
        self.song_container.bind("<Configure>", lambda e: self.song_canvas.configure(scrollregion=self.song_canvas.bbox("all")))
        self.song_canvas.bind_all("<MouseWheel>", self.mouse_wheel)

        self.control_frame = Frame(self.music_tab, bg="gray")
        self.control_frame.pack(fill=X, pady=(0, 35))

        Button(self.control_frame, text="Play", width=20, background='white', bd=0, command=self.play_song).pack(side=LEFT, padx=10, pady=10)
        Button(self.control_frame, text="⏮", width=6, background='white', bd=2, command=self.rewind_song).pack(side=LEFT, padx=(100, 10), pady=10)
        Button(self.control_frame, text="[▷]", width=6, background='white', bd=2, command=self.pause_resume_song).pack(side=LEFT, padx=10, pady=10)
        Button(self.control_frame, text="⏭", width=6, background='white', bd=2, command=self.fast_forward_song).pack(side=LEFT, padx=(10, 100), pady=10)
        Button(self.control_frame, text="Stop", width=20, background='white', bd=0, command=self.stop_song).pack(side=RIGHT, padx=10, pady=10)

        self.display_songs()

    def setup_video_tab(self):
        self.config_frame = Frame(self.video_tab, bg="gray")
        self.config_frame.pack(fill=X, pady=5)

        Button(self.config_frame, text="🗁 Thêm thư mục", command=self.add_video_folder, bd=0, width=20, background='white').pack(side=LEFT, padx=10, pady=10)
        Button(self.config_frame, text="▷Thêm tệp mp4", command=self.add_mp4_file, bd=0, width=20, background='white').pack(side=LEFT, padx=25, pady=10)
        Button(self.config_frame, text="⬇ Tải từ youtube", command=lambda: self.download_mp4(), bd=0, width=20, background='white').pack(side=LEFT, padx=(13, 25), pady=10)
        Button(self.config_frame, text="✘ Xóa video", command=lambda: self.delete_selected_file("mp4"), bd=0, width=20, background='white').pack(side=RIGHT, padx=10, pady=10)

        self.video_frame = Frame(self.video_tab, bg="white")
        self.video_frame.pack(fill=BOTH, expand=True, padx=10, pady=0)

        self.video_canvas = Canvas(self.video_frame, bg="gray", highlightthickness=0)
        self.video_canvas.pack(side=LEFT, fill=BOTH, expand=True, padx=2, pady=2)

        self.video_container = Frame(self.video_canvas, bg="gray")
        self.video_canvas.create_window((0, 0), window=self.video_container, anchor="nw")
        
        self.control_frame = Frame(self.video_tab, bg="gray")
        self.control_frame.pack(fill=X, pady=(0, 35))

        Button(self.control_frame, text="Play", width=20, background='white', bd=0, command=self.play_video).pack(side=LEFT, padx=10, pady=10)
        Button(self.control_frame, text="⏮", width=6, background='white', bd=2, command=self.rewind_video).pack(side=LEFT, padx=(100, 10), pady=10)
        Button(self.control_frame, text="[▷]", width=6, background='white', bd=2, command=self.pause_resume_video).pack(side=LEFT, padx=10, pady=10)
        Button(self.control_frame, text="⏭", width=6, background='white', bd=2, command=self.fast_forward_video).pack(side=LEFT, padx=(10, 100), pady=10)
        Button(self.control_frame, text="Stop", width=20, background='white', bd=0, command=self.stop_video).pack(side=RIGHT, padx=10, pady=10)

        self.video_container.bind("<Configure>", lambda e: self.video_canvas.configure(scrollregion=self.video_canvas.bbox("all")))
        self.video_canvas.bind_all("<MouseWheel>", self.mouse_wheel)

        self.display_videos()

    def setup_lyrics_tab(self):
        
        self.config_frame = Frame(self.lyrics_tab, bg="gray")
        self.config_frame.pack(fill=X, pady=5)

        Button(self.config_frame, text="📜 Trích xuất lời bài hát", command=self.fetch_lyric, bd=0, width=20, background='white').pack(side=LEFT, padx=10, pady=10)
        song_title_input = Entry(self.config_frame, textvariable=self.song_title, width=25 , background='white')
        song_title_input.pack(side=LEFT, padx=10, pady=10)
        self.add_placeholder(song_title_input, "Nhập tên bài hát")
        artist_name_input = Entry(self.config_frame, textvariable=self.artist_name, width=25, background='white')
        artist_name_input.pack(side=LEFT, padx=10, pady=10)
        self.add_placeholder(artist_name_input, "Nhập tên nghệ sĩ")
        Label(self.config_frame, text="💡Để trống nếu không rõ nghệ sĩ", bg="gray", fg="darkred").pack(side=LEFT, padx=0, pady=10)

        self.lyrics_frame = Frame(self.lyrics_tab, bg="white")
        self.lyrics_frame.pack(fill=BOTH, expand=True, padx=10, pady=(0))

        self.lyrics_canvas = Canvas(self.lyrics_frame, bg="gray", highlightthickness=0)
        self.lyrics_canvas.pack(side=LEFT, fill=BOTH, expand=True, padx=2, pady=2)

        self.lyrics_container = Frame(self.lyrics_canvas, bg="gray")
        self.lyrics_canvas.create_window((0, 0), window=self.lyrics_container, anchor="nw")

        self.saveload_frame = Frame(self.lyrics_tab, bg="gray")
        self.saveload_frame.pack(fill=X, pady=(2, 37))
        
        Button(self.saveload_frame, text="💾 Lưu lời bài hát", command=self.save_lyrics, bd=0, width=20, background='white').pack(side=LEFT, padx=10, pady=10)
        Button(self.saveload_frame, text="📂 Tải lời bài hát", command=self.load_lyrics, bd=0, width=20, background='white').pack(side=RIGHT, padx=10, pady=10)

        self.lyrics_canvas.bind("<Configure>", lambda e: self.lyrics_canvas.configure(scrollregion=self.lyrics_canvas.bbox("all")))
        self.lyrics_canvas.bind_all("<MouseWheel>", self.mouse_wheel)

    def play_song(self):
        if self.highlighted_label:
            song_name = self.highlighted_label.cget("text")
            if not song_name.endswith(".mp3"):
                return
            song_path = os.path.join(self.music_directory, song_name)
            self.media = self.instance.media_new(song_path)
            self.songplayer.set_media(self.media)
            self.songplayer.play()

    def stop_song(self):
        self.songplayer.stop()
        self.time = 0

    def pause_resume_song(self):
        if self.songplayer.is_playing():
            self.songplayer.pause()
        else:
            self.songplayer.play()
    
    def rewind_song(self):
        self.songplayer.set_time(self.songplayer.get_time() - 10000)

    def fast_forward_song(self):
        self.songplayer.set_time(self.songplayer.get_time() + 10000)

    def play_video(self):
        if self.highlighted_label:
            video_name = self.highlighted_label.cget("text")
            if not video_name.endswith(".mp4"):
                return
            video_path = os.path.join(self.video_directory, video_name)
            self.media = self.instance.media_new(video_path)
            self.mediaplayer.set_media(self.media)
            for widget in self.video_container.winfo_children():
                widget.destroy()
            self.video_container.config(background="black")
            self.video_canvas.config(background="black")
            video_frame_id = self.video_frame.winfo_id()  
            self.mediaplayer.set_hwnd(video_frame_id)
            self.mediaplayer.play()

    def stop_video(self):
        self.mediaplayer.stop()
        self.video_container.config(background="gray")
        self.video_canvas.config(background="gray")
        self.display_videos()

    def pause_resume_video(self):
        if self.mediaplayer.is_playing():
            self.mediaplayer.pause()
        else:
            self.mediaplayer.play()

    def rewind_video(self):
        self.mediaplayer.set_time(self.mediaplayer.get_time() - 10000)

    def fast_forward_video(self):
        self.mediaplayer.set_time(self.mediaplayer.get_time() + 10000)

    def change_tab(self, tab):
        if tab == "music":
            self.notebook.select(self.music_tab)
        elif tab == "video":
            self.notebook.select(self.video_tab)
        elif tab == "lyric":
            self.notebook.select(self.lyrics_tab)

    def add_song_folder(self):
        directory = filedialog.askdirectory()
        if directory:
            for file in os.listdir(directory):
                if file.endswith(".mp3"):
                    source_path = os.path.join(directory, file)
                    destination_path = os.path.join(self.music_directory, file)
                    if not os.path.exists(destination_path):
                        shutil.copy(source_path, destination_path)
            self.display_songs()

    def add_mp3_file(self):
        files = filedialog.askopenfilenames(filetypes=[("MP3 files", "*.mp3")])
        if files:
            for file in files:
                file_name = os.path.basename(file)
                destination_path = os.path.join(self.music_directory, file_name)
                if not os.path.exists(destination_path):
                    shutil.copy(file, destination_path)
            self.display_songs()
    
    def add_video_folder(self):
        directory = filedialog.askdirectory()
        if directory:
            for file in os.listdir(directory):
                if file.endswith(".mp4"):
                    source_path = os.path.join(directory, file)
                    destination_path = os.path.join(self.video_directory, file)
                    if not os.path.exists(destination_path):
                        shutil.copy(source_path, destination_path)
            self.display_videos()
    
    def add_mp4_file(self):
        files = filedialog.askopenfilenames(filetypes=[("MP4 files", "*.mp4")])
        if files:
            for file in files:
                file_name = os.path.basename(file)
                destination_path = os.path.join(self.video_directory, file_name)
                if not os.path.exists(destination_path):
                    shutil.copy(file, destination_path)
            self.display_videos()

    def download_mp3(self):
        link = simpledialog.askstring("Link", "Nhập link của bài hát bạn muốn tải:")
        if link:
            try:
                video = YouTube(link)
                stream = video.streams.filter(file_extension='mp4', progressive=True).order_by('resolution').desc().first()
                downloaded_video_path = stream.download(self.video_directory)
                mp3_file_path = os.path.join(self.music_directory, os.path.splitext(os.path.basename(downloaded_video_path))[0] + ".mp3")
                AudioSegment.from_file(downloaded_video_path).export(mp3_file_path, format="mp3")
                messagebox.showinfo("MP3", "Tải thành công.")
                self.display_songs()
                self.display_videos()
            except Exception as e:
                messagebox.showerror("Lỗi", e)

    def download_mp4(self):
        link = simpledialog.askstring("Link", "Nhập link của video bạn muốn tải:")
        if link:
            try:
                video = YouTube(link)
                stream = video.streams.filter(file_extension='mp4', progressive=True).order_by('resolution').desc().first()
                downloaded_video_path = stream.download(self.video_directory)
                messagebox.showinfo("MP4", "Tải thành công.")
                self.display_videos()
            except Exception as e:
                messagebox.showerror("Lỗi", e)

    def delete_selected_file(self, file):
        try:
            if file == "mp3":
                if self.highlighted_label:
                    song_name = self.highlighted_label.cget("text")
                    song_path = os.path.join(self.music_directory, song_name)
                    os.remove(song_path)
                    self.songs.remove(song_name)
                    self.highlighted_label.destroy()
                else:
                    raise Exception("Hãy chọn item cần xóa.")
            elif file == "mp4":
                if self.highlighted_label:
                    video_name = self.highlighted_label.cget("text")
                    video_path = os.path.join(self.video_directory, video_name)
                    os.remove(video_path)
                    self.videos.remove(video_name)
                    self.highlighted_label.destroy()
                else:
                    raise Exception("Hãy chọn item cần xóa.")
        except Exception as e:
            messagebox.showerror("Lỗi", "Hãy chọn item cần xóa.")

    def fetch_lyric(self):
        song_title = self.song_title.get()
        artist_name = self.artist_name.get()
        if artist_name == "Nhập tên nghệ sĩ":
            artist_name = ""
        if not song_title or song_title == "Nhập tên bài hát":
            messagebox.showerror("Lỗi", "Hãy nhập tên bài hát.")
            return
        try:
            song = self.genius.search_song(song_title, artist_name)
        except Exception as e:
            messagebox.showerror("Lỗi", e)
            return
        if song:
            lyrics = song.lyrics
            self.display_lyrics(lyrics)
        else:
            messagebox.showerror("Lỗi", "Không tim thấy lời bài hát.")

    def save_lyrics(self):
        if not self.lyrics_container.winfo_children():
            messagebox.showwarning("Thông báo", "Không có lời bài hát để lưu.")
            return

        file_name = simpledialog.askstring("Lưu lời bài hát", "Nhập tên file:")
        if file_name:
            file_path = os.path.join(self.lyric_directory, file_name + ".txt")
            lyrics = ""
            for widget in self.lyrics_container.winfo_children():
                lyrics += widget.cget("text") + "\n"

            with open(file_path, "w", encoding="utf-8") as file:
                file.write(lyrics)
            messagebox.showinfo("Thành công", f"Lời bài hát đã được lưu tại: {file_path}")
    
    def load_lyrics(self):
        file_path = filedialog.askopenfilename(initialdir=self.lyric_directory, title="Chọn file lời bài hát", filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as file:
                lyrics = file.readlines()

            for widget in self.lyrics_container.winfo_children():
                widget.destroy()

            for line in lyrics:
                lyric_label = Label(self.lyrics_container, text=line.strip(), bg="gray", width=94, anchor="w", padx=10, pady=0)
                lyric_label.pack(fill=X, padx=5, pady=5)

            self.lyrics_canvas.update_idletasks()
            self.lyrics_canvas.config(scrollregion=self.lyrics_canvas.bbox("all"))
            messagebox.showinfo("Thành công", "Tải lời bài hát thành công!")

    def convert_mp4_to_mp3(self, mp4_path):
        audio = AudioSegment.from_file(mp4_path, format="mp4")
        mp3_path = mp4_path.replace(".mp4", ".mp3")
        audio.export(mp3_path, format="mp3")
        return mp3_path
        
    def display_songs(self):
        for widget in self.song_container.winfo_children():
            widget.destroy()

        for file in os.listdir(self.music_directory):
            if file.endswith(".mp3") and file not in self.songs:
                self.songs.append(file)
                
        for song_name in self.songs:
            song_label = Label(self.song_container, text=song_name, bg="#E0A469", width=94, anchor="w", padx=10, pady=5)
            song_label.pack(fill=X, padx=5, pady=5)
            song_label.bind("<Button-1>", lambda e, lbl=song_label: self.highlight_label(lbl))

        self.song_canvas.update_idletasks()
        self.song_canvas.config(scrollregion=self.song_canvas.bbox("all"))

    def display_videos(self):
        for widget in self.video_container.winfo_children():
            widget.destroy()

        for file in os.listdir(self.video_directory):
            if file.endswith(".mp4") and file not in self.videos:
                self.videos.append(file)

        for video_name in self.videos:
            video_label = Label(self.video_container, text=video_name, bg="#E0A469", width=94, anchor="w", padx=10, pady=5)
            video_label.pack(fill=X, padx=5, pady=5)
            video_label.bind("<Button-1>", lambda e, lbl=video_label: self.highlight_label(lbl))

        self.video_canvas.update_idletasks()
        self.video_canvas.config(scrollregion=self.video_canvas.bbox("all"))

    def display_lyrics(self, lyrics):
        for widget in self.lyrics_container.winfo_children():
            widget.destroy()
        lines = lyrics.split("\n")
        for line in lines:
            lyric_label = Label(self.lyrics_container, text=line, bg="gray", width=94, anchor="w", padx=10, pady=0)
            lyric_label.pack(fill=X, padx=5, pady=5)
        self.lyrics_canvas.update_idletasks()
        self.lyrics_canvas.config(scrollregion=self.lyrics_canvas.bbox("all"))

    def highlight_label(self, label):
        if self.highlighted_label is not None and self.highlighted_label.winfo_exists():
            self.highlighted_label.config(bg="#E0A469")  
        label.config(bg="#AAE54A")  
        self.highlighted_label = label

    def mouse_wheel(self, event):
        self.song_canvas.yview_scroll(-1 * (event.delta // 120), "units")
        self.video_canvas.yview_scroll(-1 * (event.delta // 120), "units")
        self.lyrics_canvas.yview_scroll(-1 * (event.delta // 120), "units")
        if self.song_canvas.yview()[0] <= 0:
            self.song_canvas.yview_moveto(0)
        if self.video_canvas.yview()[0] <= 0:
            self.video_canvas.yview_moveto(0)

    def add_placeholder(self, entry, placeholder):
        entry.insert(0, placeholder)
        entry.config(fg='grey')
        def on_focus_in(event):
            if entry.get() == placeholder:
                entry.delete(0, END)
                entry.config(fg='black')
        def on_focus_out(event):
            if not entry.get():
                entry.insert(0, placeholder)
                entry.config(fg='grey')
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

if __name__ == "__main__":
    root = Tk()
    app = MusicPlayer(root)
    root.mainloop()