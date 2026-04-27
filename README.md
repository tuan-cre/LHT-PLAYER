# mavPlayer

Music, Video & Lyrics Player

## Features

- **Music Playback** - Play MP3 with controls (play/pause/seek/shuffle/loop)
- **Video Playback** - Play video with native Qt video widget
- **Local Library** - Add/remove music and video files
- **YouTube Download** - Download MP4 or convert to MP3
- **Lyrics** - Fetch lyrics from lyrics.ovh API
- **Save/Load Lyrics** - Save lyrics to .txt files

## Tech Stack

- **PyQt6** - GUI framework with native QMediaPlayer
- **yt-dlp** - YouTube download
- **requests** - HTTP client for lyrics API

## Install

```bash
# Create venv and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
source .venv/bin/activate
python mavPlayer.py
```

## Project Structure

```
LHT-PLAYER/
├── mavPlayer.py       # Main application
├── config.py         # Configuration
├── genius_lyrics.py # Lyrics fetching
├── requirements.txt
├── music/           # Music files
├── video/           # Video files
└── lyrics/          # Lyrics files
```

## Controls

- **⏮** - Previous track
- **⏯/⏸** - Play/Pause
- **⏭** - Next track
- **🔀** - Shuffle
- **🔂** - Loop current track
- **⏹** - Stop

## Troubleshooting

### No video playback
Install ffmpeg: `sudo pacman -S ffmpeg` (Arch) or `sudo apt install ffmpeg` (Debian)

### YouTube download fails
Update yt-dlp: `pip install -U yt-dlp`