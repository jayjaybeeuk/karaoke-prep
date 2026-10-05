## 2023-10-27 - File-based caching for expensive operations
**Learning:** In audio/video processing pipelines like Karaoke Prep, intermediate and final outputs take significant time to generate (e.g. Demucs vocal separation and FFmpeg video generation).
**Action:** Always check if the final output files or intermediate stems exist on disk before re-running expensive external processes to dramatically speed up subsequent runs on identical inputs.
