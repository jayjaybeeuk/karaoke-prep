"""Main processing pipeline: metadata → lyrics → stems → video."""

import os
import re
import subprocess
from pathlib import Path

from lyrics import fetch_lyrics
from metadata import extract_metadata

MEDIA_DIR = Path(os.environ.get("MEDIA_DIR", "/media"))
CACHE_DIR = Path(os.environ.get("CACHE_DIR", "/cache"))
STEM_ENGINE = os.environ.get("STEM_ENGINE", "demucs")

LRC_PATTERN = re.compile(r"\[(\d+):(\d+\.\d+)\](.*)")


def process_song(mp3_path: Path) -> Path:
    """Full pipeline: MP3 → karaoke video."""
    print(f"[pipeline] Processing: {mp3_path.name}")

    # 1. Extract metadata
    meta = extract_metadata(mp3_path)
    artist = meta.get("artist", "Unknown")
    title = meta.get("title", mp3_path.stem)

    # Sanitize to prevent path traversal
    raw_name = f"{artist} - {title}"
    safe_name = re.sub(r'[^a-zA-Z0-9_\- ]', '', raw_name).strip()
    # If the resulting name is empty or just dashes/spaces, use fallback
    if not safe_name.replace("-", "").strip():
        safe_name = "unknown_song"

    output_path = MEDIA_DIR / f"{safe_name}.mp4"
    if output_path.exists():
        print(f"[pipeline] Output video already exists: {output_path}")
        return output_path

    song_cache = CACHE_DIR / safe_name
    song_cache.mkdir(parents=True, exist_ok=True)

    # 2. Fetch lyrics
    lrc_path = song_cache / "lyrics.lrc"
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

    # 3. Vocal removal
    instrumental_path = separate_vocals(mp3_path, song_cache)

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
        if expected_out.exists():
            print(f"[pipeline] Using cached instrumental: {expected_out}")
            return expected_out

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
                str(mp3_path),
            ],
            check=True,
        )
        return expected_out
    else:
        # Spleeter fallback
        expected_out = output_dir / mp3_path.stem / "accompaniment.wav"
        if expected_out.exists():
            print(f"[pipeline] Using cached instrumental: {expected_out}")
            return expected_out

        subprocess.run(
            ["spleeter", "separate", "-o", str(output_dir), "-p", "spleeter:2stems", str(mp3_path)],
            check=True,
        )
        return expected_out


def _escape_ffmpeg_path(path: str) -> str:
    """Escape file path for FFmpeg filtergraph syntax."""
    # First level escaping (for the filter option value)
    s = path.replace('\\', '\\\\')
    s = s.replace(':', '\\:')
    s = s.replace("'", "\\'")

    # Second level escaping (for the filtergraph description)
    s2 = ""
    for c in s:
        if c in ['\\', ',', ';', '[', ']', '=', "'"]:
            s2 += '\\' + c
        else:
            s2 += c
    return s2


def generate_video(audio_path: Path, lrc_path: Path, output_path: Path):
    """Render karaoke video with lyrics overlay using FFmpeg."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert LRC to ASS subtitle format for FFmpeg
    ass_path = lrc_path.with_suffix(".ass")
    lrc_to_ass(lrc_path, ass_path)

    escaped_ass_path = _escape_ffmpeg_path(str(ass_path))

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=1920x1080:r=30",
        "-i", str(audio_path),
        "-vf", f"ass={escaped_ass_path}",
        "-shortest",
        "-c:v", "libx264", "-preset", "fast",
        "-c:a", "aac", "-b:a", "192k",
        str(output_path),
    ]
    subprocess.run(cmd, check=True)


def lrc_to_ass(lrc_path: Path, ass_path: Path):
    """Convert LRC lyrics to ASS subtitle format."""
    lines = lrc_path.read_text(encoding="utf-8").strip().splitlines()
    events = []

    timestamps = []
    texts = []
    for line in lines:
        m = LRC_PATTERN.match(line)
        if m:
            minutes, seconds, text = m.groups()
            time_s = int(minutes) * 60 + float(seconds)
            timestamps.append(time_s)
            texts.append(text.strip())

    # Build ASS events
    for i, (ts, text) in enumerate(zip(timestamps, texts)):
        if not text:
            continue
        end = timestamps[i + 1] if i + 1 < len(timestamps) else ts + 5.0
        start_ass = _seconds_to_ass(ts)
        end_ass = _seconds_to_ass(end)
        events.append(f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{text}")

    ass_content = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n\n"
        "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,"
        "OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,"
        "Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
        "Style: Default,Arial,64,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,"
        "-1,0,0,0,100,100,0,0,1,3,1,2,50,50,50,1\n\n"
        "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n"
    )
    ass_content += "\n".join(events)
    ass_path.write_text(ass_content, encoding="utf-8")


def _seconds_to_ass(s: float) -> str:
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f"{h}:{m:02d}:{sec:05.2f}"
