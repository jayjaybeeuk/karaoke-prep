## 2023-10-27 - File-based caching for expensive operations
**Learning:** In audio/video processing pipelines like Karaoke Prep, intermediate and final outputs take significant time to generate (e.g. Demucs vocal separation and FFmpeg video generation).
**Action:** Always check if the final output files or intermediate stems exist on disk before re-running expensive external processes to dramatically speed up subsequent runs on identical inputs.

## 2024-05-24 - [FFmpeg preset optimization]
**Learning:** The FFmpeg `-preset` option has a large impact on encoding time for karaoke videos, with `ultrafast` providing a ~3x speedup over `fast` on our dummy benchmark. Since these are simple background + text videos, the quality/size tradeoff of `ultrafast` might be perfectly acceptable or even unnoticeable.
**Action:** Change the FFmpeg `-preset` to `ultrafast` in `src/pipeline.py`.
