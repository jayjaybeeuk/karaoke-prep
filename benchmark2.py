import time
from pathlib import Path
import tempfile
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
import pipeline
from pipeline import process_song

def run_benchmark():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        pipeline.CACHE_DIR = temp_dir_path / "cache"
        pipeline.MEDIA_DIR = temp_dir_path / "media"
        pipeline.CACHE_DIR.mkdir(exist_ok=True)
        pipeline.MEDIA_DIR.mkdir(exist_ok=True)

        mp3_path = temp_dir_path / "test - song.mp3"
        mp3_path.touch()

        pipeline.extract_metadata = lambda p: {"artist": "The Beatles", "title": "Yesterday"}

        # Mock fetch_lyrics to return something so it creates the lyrics file
        pipeline.fetch_lyrics = lambda a, b: "[00:01.00] test"

        # Mock the subprocess run to simulate 2 seconds of work,
        # and create the output file so subsequent checks can find it
        original_subprocess_run = pipeline.subprocess.run

        def mock_subprocess_run(args, **kwargs):
            time.sleep(2)  # Simulate expensive operation
            if "demucs" in args:
                out_dir = Path(args[args.index("-o")+1])
                out = out_dir / "htdemucs" / mp3_path.stem / "no_vocals.wav"
                out.parent.mkdir(parents=True, exist_ok=True)
                out.touch()

        pipeline.subprocess.run = mock_subprocess_run

        def mock_generate_video(a, l, o):
            time.sleep(1) # simulate video gen
            o.touch()

        pipeline.generate_video = mock_generate_video

        try:
            print("--- Run 1: First time (no cache) ---")
            start = time.time()
            process_song(mp3_path)
            duration1 = time.time() - start
            print(f"Run 1 duration: {duration1:.3f} seconds\n")

            print("--- Run 2: Second time (should use cache) ---")
            start = time.time()
            process_song(mp3_path)
            duration2 = time.time() - start
            print(f"Run 2 duration: {duration2:.3f} seconds\n")

            print(f"Improvement: {duration1 - duration2:.3f} seconds faster")
            if duration2 < duration1:
                print(f"Speedup: {duration1 / (duration2 or 0.0001):.1f}x")
        finally:
            pipeline.subprocess.run = original_subprocess_run

if __name__ == "__main__":
    run_benchmark()
