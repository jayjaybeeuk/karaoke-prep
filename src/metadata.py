"""Extract metadata (artist, title, etc.) from MP3 files."""

from pathlib import Path
from mutagen.easyid3 import EasyID3


def extract_metadata(mp3_path: Path) -> dict:
    """Extract artist and title from MP3 ID3 tags."""
    meta = {"artist": "Unknown", "title": mp3_path.stem}

    try:
        # Optimization: Use EasyID3 instead of MP3.
        # MP3 loads the entire file structure (MPEG frame headers) to calculate the duration,
        # bitrate, etc., which is relatively slow.
        # EasyID3 only loads the ID3 tags, providing a measurable speedup for metadata extraction.
        tags = EasyID3(str(mp3_path))
        if "artist" in tags:
            meta["artist"] = tags["artist"][0]
        if "title" in tags:
            meta["title"] = tags["title"][0]
        if "album" in tags:
            meta["album"] = tags["album"][0]
    except Exception as e:
        print(f"[metadata] Could not read tags from {mp3_path.name}: {e}")

    return meta
