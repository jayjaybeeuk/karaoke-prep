"""Watch incoming directory for new MP3s and process them."""

import os
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from pipeline import process_song

INCOMING_DIR = os.environ.get("INCOMING_DIR", "/incoming")


class MP3Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.lower().endswith(".mp3"):
            print(f"[karaoke-prep] New file detected: {event.src_path}")
            try:
                process_song(Path(event.src_path))
            except Exception as e:
                print(f"[karaoke-prep] Error processing {event.src_path}: {e}")


def main():
    print(f"[karaoke-prep] Watching {INCOMING_DIR} for new MP3s...")
    Path(INCOMING_DIR).mkdir(parents=True, exist_ok=True)

    observer = Observer()
    observer.schedule(MP3Handler(), INCOMING_DIR, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
