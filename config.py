import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent

DIRECTORIES = {
    "music": BASE_DIR / "music",
    "video": BASE_DIR / "video",
    "lyrics": BASE_DIR / "lyrics",
}

load_dotenv()

def get_genius_api_key():
    key = os.getenv("GENIUS_API_KEY")
    if not key:
        raise ValueError("GENIUS_API_KEY not found in .env file")
    return key

def init_directories():
    for dir_path in DIRECTORIES.values():
        dir_path.mkdir(exist_ok=True)

def get_music_dir():
    return DIRECTORIES["music"]

def get_video_dir():
    return DIRECTORIES["video"]

def get_lyrics_dir():
    return DIRECTORIES["lyrics"]