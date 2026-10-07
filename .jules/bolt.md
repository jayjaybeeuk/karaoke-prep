## 2023-10-27 - File-based caching for expensive operations
**Learning:** In audio/video processing pipelines like Karaoke Prep, intermediate and final outputs take significant time to generate (e.g. Demucs vocal separation and FFmpeg video generation).
**Action:** Always check if the final output files or intermediate stems exist on disk before re-running expensive external processes to dramatically speed up subsequent runs on identical inputs.

## 2024-10-07 - Mutagen EasyID3 vs MP3 parsing speed
**Learning:** Using `mutagen.mp3.MP3` parses the entire file structure (MPEG frame headers) to calculate the duration, bitrate, etc., which is relatively slow. Using `mutagen.easyid3.EasyID3` or `mutagen.id3.ID3` only loads the ID3 tags, providing a measurable speedup for metadata extraction.
**Action:** When extracting only ID3 metadata like Title and Artist, use `mutagen.easyid3.EasyID3` or `mutagen.id3.ID3` directly to avoid expensive parsing of the entire file.
