"""Main processing pipeline: metadata → lyrics → stems → video."""

import os
import re
import subprocess
import concurrent.futures
from pathlib import Path

from lyrics import fetch_lyrics
from metadata import extract_metadata

MEDIA_DIR = Path(os.environ.get("MEDIA_DIR", "/media"))
CACHE_DIR = Path(os.environ.get("CACHE_DIR", "/cache"))
STEM_ENGINE = os.environ.get("STEM_ENGINE", "demucs")

LRC_PATTERN = re.compile(r"\[(\d+):(\d+\.\d+)\](.*)")
# ⚡ Bolt Optimization: Pre-compile regex at the module level to avoid redundant compilation
# overhead during each function call.
SANITIZE_PATTERN = re.compile(r"[^a-zA-Z0-9_\- ]")

ASS_HEADER = (
    "[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n\n"
    "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,"
    "OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,"
    "Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
    "Style: Default,Arial,64,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,"
    "-1,0,0,0,100,100,0,0,1,3,1,2,50,50,50,1\n\n"
    "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"
)


def process_song(mp3_path: Path) -> Path:
    """Full pipeline: MP3 → karaoke video."""
    print(f"[pipeline] Processing: {mp3_path.name}")

    # 1. Extract metadata
    meta = extract_metadata(mp3_path)
    artist = meta.get("artist", "Unknown")
    title = meta.get("title", mp3_path.stem)

    # Sanitize to prevent path traversal
    raw_name = f"{artist} - {title}"
    safe_name = SANITIZE_PATTERN.sub("", raw_name).strip()
    # If the resulting name is empty or just dashes/spaces, use fallback
    if not safe_name.replace("-", "").strip():
        safe_name = "unknown_song"

    output_path = MEDIA_DIR / f"{safe_name}.mp4"
    if output_path.exists():
        print(f"[pipeline] Output video already exists: {output_path}")
        return output_path

    song_cache = CACHE_DIR / safe_name
    song_cache.mkdir(parents=True, exist_ok=True)

    # ⚡ Bolt Optimization: Use ThreadPoolExecutor to run independent network (lyrics fetch)
    # and CPU (vocal separation) operations concurrently, reducing overall pipeline latency.
    lrc_path = song_cache / "lyrics.lrc"

    if STEM_ENGINE == "demucs":
        # ⚡ Bolt Optimization: Use glob to check if ANY instrumental exists for this track's
        # metadata, ignoring the original filename. This prevents re-running Demucs if renamed.
        cached = next(song_cache.glob("htdemucs/*/no_vocals.wav"), None)
        expected_instrumental = cached or song_cache / "htdemucs" / mp3_path.stem / "no_vocals.wav"
    else:
        cached = next(song_cache.glob("*/accompaniment.wav"), None)
        expected_instrumental = cached or song_cache / mp3_path.stem / "accompaniment.wav"

    def fetch_lyrics_task():
        if lrc_path.exists():
            print(f"[pipeline] Using cached lyrics: {lrc_path}")
        else:
            lyrics = fetch_lyrics(artist, title)
            if lyrics:
                lrc_path.write_text(lyrics, encoding="utf-8")
                print(f"[pipeline] Lyrics saved: {lrc_path}")
            else:
                print(f"[pipeline] No synced lyrics found for {safe_name}")
                lrc_path.write_text("", encoding="utf-8")

    def separate_vocals_task():
        if expected_instrumental.exists():
            print(f"[pipeline] Using cached instrumental: {expected_instrumental}")
            return expected_instrumental
        else:
            return separate_vocals(mp3_path, song_cache)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_lyrics = executor.submit(fetch_lyrics_task)
        future_vocals = executor.submit(separate_vocals_task)

        future_lyrics.result()
        instrumental_path = future_vocals.result()

    # 4. Generate karaoke video
    output_path = MEDIA_DIR / f"{safe_name}.mp4"
    generate_video(instrumental_path, lrc_path, output_path)

    print(f"[pipeline] Done: {output_path}")
    return output_path


def separate_vocals(mp3_path: Path, output_dir: Path) -> Path:
    """Run stem separation and return path to instrumental."""
    if STEM_ENGINE == "demucs":
        stem_dir = output_dir / "htdemucs" / mp3_path.stem
        expected_out = stem_dir / "no_vocals.wav"

        subprocess.run(
            [
                "python",
                "-m",
                "demucs",
                "-n",
                "htdemucs",
                "--two-stems",
                "vocals",
                "-o",
                str(output_dir),
                # ⚡ Bolt Optimization: Use multiprocessing (-j) to drastically speed up
                # CPU-bound Demucs stem separation by fully utilizing available CPU cores.
                "-j",
                str(os.cpu_count() or 1),
                str(mp3_path),
            ],
            check=True,
        )
        return expected_out
    else:
        # Spleeter fallback
        expected_out = output_dir / mp3_path.stem / "accompaniment.wav"

        subprocess.run(
            [
                "spleeter",
                "separate",
                "-o",
                str(output_dir),
                "-p",
                "spleeter:2stems",
                str(mp3_path),
            ],
            check=True,
        )
        return expected_out


def _escape_ffmpeg_path(path: str) -> str:
    """Escape file path for FFmpeg filtergraph syntax."""
    # First level escaping (for the filter option value)
    s = path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")

    # Second level escaping (for the filtergraph description)
    # ⚡ Bolt Optimization: Use chained `.replace()` calls instead of compiled regex with re.sub()
    # because it is measurably faster in Python for escaping multiple characters.
    return (
        s.replace("\\", "\\\\")
        .replace(",", "\\,")
        .replace(";", "\\;")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("=", "\\=")
        .replace("'", "\\'")
    )


def generate_video(audio_path: Path, lrc_path: Path, output_path: Path):
    """Render karaoke video with lyrics overlay using FFmpeg."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # ⚡ Bolt Optimization: Read the file once with try/except to avoid redundant I/O stats
    # and duplicate file reading during lrc_to_ass generation.
    lrc_content = ""
    try:
        lrc_content = lrc_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        pass

    has_lyrics = bool(lrc_content)

    # ⚡ Bolt Optimization: Drop framerate to 1 fps if there are no lyrics (static black screen)
    # This significantly reduces rendering time for unsynced tracks.
    fps = 30 if has_lyrics else 1

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=black:s=1920x1080:r={fps}",
        "-i",
        str(audio_path),
    ]

    if has_lyrics:
        # Convert LRC to ASS subtitle format for FFmpeg
        ass_path = lrc_path.with_suffix(".ass")
        lrc_to_ass(lrc_content, ass_path)
        escaped_ass_path = _escape_ffmpeg_path(str(ass_path))
        # ⚡ Bolt Optimization: Only apply the ASS filter if lyrics exist to avoid overhead.
        cmd.extend(["-vf", f"ass={escaped_ass_path}"])

    cmd.extend(
        [
            "-shortest",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",  # ⚡ Bolt Optimization: ultrafast drastically reduces render time.
            # ⚡ Bolt Optimization: tune stillimage speeds up encoding for static video.
            "-tune",
            "stillimage",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(output_path),
        ]
    )
    subprocess.run(cmd, check=True)


def lrc_to_ass(content: str, ass_path: Path):
    """Convert LRC lyrics to ASS subtitle format."""
    # ⚡ Bolt Optimization: Process in a single O(N) pass to avoid intermediate
    # list allocations for timestamps and texts.
    events = []

    prev_ts = None
    prev_ts_ass = None
    prev_text = None

    for m in LRC_PATTERN.finditer(content):
        minutes, seconds, text = m.groups()
        text = text.strip()
        ts = int(minutes) * 60 + float(seconds)

        # ⚡ Bolt Optimization: Cache the formatted timestamp to avoid recalculating
        # _seconds_to_ass for the same timestamp in the next iteration.
        ts_ass = _seconds_to_ass(ts)

        if prev_ts_ass is not None and prev_text:
            events.append(f"Dialogue: 0,{prev_ts_ass},{ts_ass},Default,,0,0,0,,{prev_text}")

        prev_ts = ts
        prev_ts_ass = ts_ass
        prev_text = text

    # Add the final event
    if prev_ts_ass is not None and prev_text:
        end_ass = _seconds_to_ass(prev_ts + 5.0)
        events.append(f"Dialogue: 0,{prev_ts_ass},{end_ass},Default,,0,0,0,,{prev_text}")

    # ⚡ Bolt Optimization: Unpack elements into a single list for join().
    # String concatenation with another string that's been joined is slower.
    ass_content = "\n".join([ASS_HEADER, *events])
    ass_path.write_text(ass_content, encoding="utf-8")


def _seconds_to_ass(s: float) -> str:
    # ⚡ Bolt Optimization: Use divmod for faster simultaneous quotient/remainder calculation.
    m, sec = divmod(s, 60)
    h, m = divmod(m, 60)
    # ⚡ Bolt Optimization: C-style % string formatting is faster than f-strings
    # for specific float/int conversions by bypassing Python int() overhead.
    return "%d:%02d:%05.2f" % (h, m, sec)
