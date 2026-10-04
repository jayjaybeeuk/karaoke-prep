import time
from pathlib import Path
import tempfile
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
import pipeline
from pipeline import process_song, CACHE_DIR, MEDIA_DIR

def run_benchmark():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        pipeline.CACHE_DIR = temp_dir_path / "cache"
        pipeline.MEDIA_DIR = temp_dir_path / "media"
        pipeline.CACHE_DIR.mkdir(exist_ok=True)
        pipeline.MEDIA_DIR.mkdir(exist_ok=True)

        mp3_path = temp_dir_path / "test - song.mp3"
        mp3_path.touch()

        original_extract = pipeline.extract_metadata
        pipeline.extract_metadata = lambda p: {"artist": "The Beatles", "title": "Yesterday"}

        original_separate = pipeline.separate_vocals
        pipeline.separate_vocals = lambda m, d: m
        original_generate = pipeline.generate_video
        pipeline.generate_video = lambda a, l, o: None

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
            pipeline.extract_metadata = original_extract
            pipeline.separate_vocals = original_separate
            pipeline.generate_video = original_generate

if __name__ == "__main__":
    run_benchmark()
