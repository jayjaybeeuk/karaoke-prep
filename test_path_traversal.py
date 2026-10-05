import re
from pathlib import Path

def sanitize_name(artist, title):
    raw_name = f"{artist} - {title}"
    safe_name = re.sub(r'[^a-zA-Z0-9_\- ]', '', raw_name).strip()
    # If the resulting name is empty or just dashes/spaces, use fallback
    if not safe_name.replace("-", "").strip():
        safe_name = "unknown_song"
    return safe_name

def test_sanitization():
    # Test cases
    cases = [
        ("The Beatles", "Let It Be", "The Beatles - Let It Be"),
        ("AC/DC", "Back In Black", "ACDC - Back In Black"),
        ("../../../etc", "passwd", "etc - passwd"),
        ("Bad\\Artist", "Bad*Title?", "BadArtist - BadTitle"),
        ("/", "/", "unknown_song"),
        ("", "", "unknown_song"),
        ("   ", "   ", "unknown_song"),
    ]

    passed = True
    for artist, title, expected in cases:
        result = sanitize_name(artist, title)
        if result != expected:
            print(f"FAILED: sanitize_name('{artist}', '{title}')")
            print(f"  Expected: '{expected}'")
            print(f"  Got:      '{result}'")
            passed = False
        else:
            print(f"OK: '{artist}' / '{title}' -> '{result}'")

    if passed:
        print("All tests passed.")

if __name__ == "__main__":
    test_sanitization()
