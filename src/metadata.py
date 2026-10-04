"""Extract metadata (artist, title, etc.) from MP3 files."""

from pathlib import Path
from mutagen.mp3 import MP3


def extract_metadata(mp3_path: Path) -> dict:
    """Extract artist and title from MP3 ID3 tags."""
    meta = {"artist": "Unknown", "title": mp3_path.stem}

    try:
        audio = MP3(str(mp3_path))
        tags = audio.tags
        if tags:
            if "TPE1" in tags:
                meta["artist"] = str(tags["TPE1"])
            if "TIT2" in tags:
                meta["title"] = str(tags["TIT2"])
            if "TALB" in tags:
                meta["album"] = str(tags["TALB"])
    except Exception as e:
        print(f"[metadata] Could not read tags from {mp3_path.name}: {e}")

    return meta
