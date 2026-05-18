import os
import logging
import requests
import re
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)

# Local cache for Vietnamese lyrics
LYRICS_CACHE_DIR = Path(__file__).parent / "lyrics_cache"
LYRICS_CACHE_DIR.mkdir(exist_ok=True)


def _fetch_from_lrclib(artist: str, title: str) -> Optional[str]:
    """Fetch lyrics from LRCLIB API (free, open-source, Vietnamese-friendly)."""
    logger.debug(f"Fetching from LRCLIB: {title} by {artist}")
    
    try:
        search_url = "https://lrclib.net/api/search"
        params = {"artist_name": artist, "track_name": title} if artist else {"track_name": title}
        
        response = requests.get(search_url, params=params, timeout=10)
        logger.debug(f"  Response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                track = data[0]
                if track.get("plainLyrics"):
                    logger.info(f"✓ Found lyrics via LRCLIB")
                    return track["plainLyrics"]
        
        logger.debug(f"  Not found or no lyrics available")
    except requests.Timeout:
        logger.debug(f"  LRCLIB timeout")
    except Exception as e:
        logger.debug(f"  LRCLIB error: {type(e).__name__}: {e}")
    
    return None


def _get_cache_path(title: str, artist: str = "") -> Path:
    """Generate safe cache file path for lyrics."""
    filename = f"{artist}_{title}".strip("_")
    filename = re.sub(r'[^\w\s-]', '', filename)
    filename = re.sub(r'\s+', '_', filename)
    filename = filename[:100]
    return LYRICS_CACHE_DIR / f"{filename}.txt"


def _load_from_cache(title: str, artist: str = "") -> Optional[str]:
    """Load lyrics from local cache."""
    cache_path = _get_cache_path(title, artist)
    if cache_path.exists():
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                lyrics = f.read().strip()
                if lyrics:
                    logger.info(f"✓ Loaded from cache")
                    return lyrics
        except Exception as e:
            logger.debug(f"Cache read error: {e}")
    return None


def _save_to_cache(title: str, artist: str, lyrics: str) -> None:
    """Save lyrics to local cache."""
    try:
        cache_path = _get_cache_path(title, artist)
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(lyrics)
        logger.debug(f"Saved to cache: {cache_path}")
    except Exception as e:
        logger.debug(f"Cache write error: {e}")


def _fetch_from_fallback(title: str, artist: str = "") -> str:
    """Return template with search suggestions."""
    logger.warning(f"Could not find '{title}' in online sources.")
    
    placeholder = f"""[LYRICS NOT FOUND - MANUAL ENTRY NEEDED]

Song: {title}
Artist: {artist if artist else "Unknown"}

Search online: Musixmatch.com, AZLyrics.com, or Genius.com

[Verse 1]
...

[Chorus]
...

[Verse 2]
...

---
Vietnamese characters (diacritics) fully supported.
"""
    return placeholder


def fetch_lyrics(title: str, artist: str = "") -> str:
    """
    Fetch lyrics from cache or LRCLIB API.
    Returns lyrics or template for manual entry.
    """
    title_clean = title.strip()
    artist_clean = artist.strip() if artist else ""
    
    if not title_clean:
        raise Exception("Please provide a song title")
    
    logger.info(f"Fetching lyrics: '{title_clean}' by '{artist_clean or 'Unknown'}'")
    
    # Try cache first
    cached = _load_from_cache(title_clean, artist_clean)
    if cached:
        return cached
    
    # Try LRCLIB API
    lyrics = _fetch_from_lrclib(artist_clean, title_clean)
    if lyrics:
        _save_to_cache(title_clean, artist_clean, lyrics)
        return lyrics
    
    # Fallback
    return _fetch_from_fallback(title_clean, artist_clean)
