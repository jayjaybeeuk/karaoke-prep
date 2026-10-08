"""Fetch synced lyrics from LRCLIB and fallback sources."""

import requests

LRCLIB_BASE = "https://lrclib.net/api"


def fetch_lyrics(artist: str, title: str) -> str | None:
    """Try LRCLIB for synced lyrics. Returns LRC string or None."""
    try:
        resp = requests.get(
            f"{LRCLIB_BASE}/get",
            params={"artist_name": artist, "track_name": title},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            synced = data.get("syncedLyrics")
            if synced:
                return synced
            # Fall back to plain lyrics (unsynced)
            plain = data.get("plainLyrics")
            if plain:
                print(
                    f"[lyrics] Only plain (unsynced) lyrics found for {artist} - {title}"
                )
                return None  # Can't use unsynced for karaoke timing
    except Exception as e:
        print(f"[lyrics] LRCLIB error: {e}")

    return None
