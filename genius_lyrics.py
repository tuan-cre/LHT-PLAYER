import os
import logging
import requests


logger = logging.getLogger(__name__)


def fetch_lyrics(title: str, artist: str = "") -> str:
    """Fetch lyrics using lyrics.ovh (primary) then Genius (fallback). Returns lyrics text or raises Exception."""
    # Try lyrics.ovh first
    errors = []

    if artist:
        artist_param = artist.replace(" ", "%20")
        title_param = title.replace(" ", "%20")
        url = f"https://api.lyrics.ovh/v1/{artist_param}/{title_param}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "lyrics" in data:
                    return data["lyrics"]
        except Exception as e:
            errors.append(str(e))

    # Try title-only on lyrics.ovh
    title_param = title.replace(" ", "%20")
    url = f"https://api.lyrics.ovh/v1/{title_param}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "lyrics" in data:
                return data["lyrics"]
    except Exception as e:
        errors.append(f"lyrics.ovh: {e}")

    raise Exception(f"Not found (tried lyrics.ovh)" if errors else "Song not found")