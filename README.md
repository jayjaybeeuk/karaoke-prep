# Karaoke Prep

A sidecar pipeline service that turns any MP3 into a karaoke-ready video — vocal removal, synced lyrics lookup, and video generation — designed to feed into [Karaoke Mugen](https://mugen.karaokes.moe/).

## Architecture

```
MP3 input / URL
       ↓
 metadata detection
       ↓
   lyrics lookup (LRCLIB → fallbacks)
       ↓
  vocal removal (Demucs / Spleeter)
       ↓
 karaoke video generation (FFmpeg)
       ↓
 import into Karaoke Mugen library
```

## How It Works

1. **Drop MP3s** into the `/incoming` directory
2. **Lyrics lookup** — queries [LRCLIB](https://lrclib.net/) for synced (timed) lyrics; falls back to Karaoke Mugen repos, user-provided `.lrc` files, or a manual sync editor
3. **Vocal removal** — runs [Demucs](https://github.com/facebookresearch/demucs) (quality) or [Spleeter](https://github.com/deezer/spleeter) (speed) to isolate the instrumental track
4. **Video rendering** — generates a karaoke `.mp4` with lyrics burned in via FFmpeg
5. **Import** — places the generated video into the Karaoke Mugen media library for playback

## Docker Compose

```yaml
services:
  karaoke-mugen:
    image: karaoke-mugen-or-desktop-wrapper
    volumes:
      - ./karaoke-data:/data
      - ./media:/media
    ports:
      - "1337:1337"

  karaoke-prep:
    build: ./karaoke-prep
    volumes:
      - ./incoming:/incoming
      - ./media:/media
      - ./cache:/cache
    environment:
      - LYRICS_PROVIDER=lrclib
      - STEM_ENGINE=demucs
      - GPU=false
```

> **Note:** Full Karaoke Mugen playback requires the desktop app connected to a display. The headless/server mode can manage playlists but cannot play karas. Dockerise the prep pipeline; run KM desktop on the TV machine.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LYRICS_PROVIDER` | `lrclib` | Primary lyrics source (`lrclib`, `local`) |
| `STEM_ENGINE` | `demucs` | Vocal separation engine (`demucs`, `spleeter`) |
| `GPU` | `false` | Enable GPU acceleration for stem separation |
| `INCOMING_DIR` | `/incoming` | Watch directory for new MP3s |
| `MEDIA_DIR` | `/media` | Output directory (Karaoke Mugen media mount) |
| `CACHE_DIR` | `/cache` | Cache for intermediate files |

## Output Per Song

```
song.mp3              # Original
instrumental.wav      # Vocals removed
lyrics.lrc            # Synced lyrics (LRC format)
karaoke.mp4           # Final video with burned-in lyrics
```

## Feasibility Notes

| Feature | Status | Notes |
|---------|--------|-------|
| Dynamic MP3 import | ✅ Yes | Via sidecar watch + import workflow |
| Vocal removal | ✅ Yes | Demucs (quality) or Spleeter (speed) |
| Real-time processing | ⚠️ Maybe | GPU needed; pre-processing is much more reliable |
| Free synced lyrics | ⚠️ Sometimes | LRCLIB is best first stop but coverage varies |
| Fully automatic | ⚠️ Mostly | Expect occasional misses, bad syncs, manual fixes |

## Tech Stack

- **Python** — pipeline orchestration
- **Demucs / Spleeter** — AI vocal separation
- **FFmpeg** — video rendering with lyric overlay
- **LRCLIB API** — free synced lyrics
- **Docker** — containerised deployment

## Getting Started

```bash
# Clone
git clone https://github.com/jayjaybeeuk/karaoke-prep.git
cd karaoke-prep

# Install dependencies
pip install -r requirements.txt

# Run the watcher
python src/watcher.py
```

## License

MIT
