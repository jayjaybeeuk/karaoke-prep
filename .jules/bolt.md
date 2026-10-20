## 2023-10-27 - File-based caching for expensive operations
**Learning:** In audio/video processing pipelines like Karaoke Prep, intermediate and final outputs take significant time to generate (e.g. Demucs vocal separation and FFmpeg video generation).
**Action:** Always check if the final output files or intermediate stems exist on disk before re-running expensive external processes to dramatically speed up subsequent runs on identical inputs.

## 2023-11-20 - Pre-compiling Regex
**Learning:** Pre-compiling regex at the module level in python using `re.compile()` avoids redundant regex compilation overhead inside frequently called functions.
**Action:** Always pre-compile regexes that are used within critical, frequently called functions or loops to minimize unnecessary overhead.

## 2023-11-20 - String replace vs Regex for escaping
**Learning:** For escaping multiple specific characters in a string, chaining `.replace()` calls is measurably faster (e.g. ~3.7x in benchmarks) than using `re.sub()` with a compiled regex in Python. The C implementation of string replacement has lower overhead than the regex engine for these exact literal replacements.
**Action:** When escaping a known set of characters, use chained `.replace()` instead of a compiled regular expression.

## 2024-10-07 - Mutagen EasyID3 vs MP3 parsing speed
**Learning:** Using `mutagen.mp3.MP3` parses the entire file structure (MPEG frame headers) to calculate the duration, bitrate, etc., which is relatively slow. Using `mutagen.easyid3.EasyID3` or `mutagen.id3.ID3` only loads the ID3 tags, providing a measurable speedup for metadata extraction.
**Action:** When extracting only ID3 metadata like Title and Artist, use `mutagen.easyid3.EasyID3` or `mutagen.id3.ID3` directly to avoid expensive parsing of the entire file.

## 2024-10-08 - FFmpeg libx264 preset optimization for static videos
**Learning:** For rendering mostly static videos (like karaoke videos which are just a black background with text and audio), using the `-preset ultrafast` for libx264 in FFmpeg drastically reduces video generation time (e.g., 3-4x speedup) with negligible quality loss.
**Action:** When generating simple static or text-based videos, always use the `ultrafast` preset to optimize processing time.

## 2024-10-10 - String replacement chaining vs iteration
**Learning:** For escaping multiple characters in a string, using sequential `.replace()` calls is significantly faster (e.g. ~7x faster in benchmarks) than iterating over every character and building a new string with `+=`, which is a common python anti-pattern due to string immutability overhead.
**Action:** Always prefer string replacement chaining (`.replace(x,y).replace(a,b)`) or regex substitution over character-by-character iteration and concatenation for simple string transformations.

## 2024-10-10 - FFmpeg libx264 tune stillimage for static videos
**Learning:** For rendering mostly static videos (like karaoke videos which are just a black background with text and audio), using `-tune stillimage` alongside `-preset ultrafast` for libx264 in FFmpeg further reduces video generation time (over 30% speedup in basic local tests) by skipping motion search operations.
**Action:** When generating simple static or text-based videos, always use `-tune stillimage` to optimize encoding time.

## 2024-10-12 - Python string concatenation in loops vs Regex
**Learning:** Iterating over a string character-by-character and concatenating strings in a loop (like `s2 += "\\" + c` for FFmpeg escaping) is an O(n²) operation and very slow in Python.
**Action:** Use a precompiled regular expression and `re.sub` for string escaping/replacement, which is implemented in C and runs much faster than a manual loop in Python.

## 2025-02-18 - Demucs Multiprocessing
**Learning:** Demucs vocal separation is highly CPU-bound. When running via the CLI, using the `-j` flag to enable multiprocessing drastically reduces processing time compared to the default single-threaded behavior.
**Action:** Always pass `-j {cores}` (e.g. `-j str(os.cpu_count())`) to Demucs CLI invocations to fully utilize available CPU cores and minimize pipeline latency.

## 2026-10-10 - requests connection pooling for APIs
**Learning:** When making repeated requests to the same API (like lrclib in the watcher process), using `requests.get()` opens a new TCP/TLS connection every time which is slow.
**Action:** Use a module-level `requests.Session()` to pool and reuse connections for significant latency improvements on subsequent fetches.

## 2026-10-14 - Built-in divmod for simultaneous division and modulo
**Learning:** When calculating both the quotient and remainder of a division (e.g. seconds to minutes/seconds), using Python's built-in `divmod()` function is faster than sequential floor division (`//`) and modulo (`%`) operations.
**Action:** Use `divmod()` whenever both the quotient and remainder are needed from the same operation.
## 2023-11-20 - Concurrent I/O and CPU bound tasks
**Learning:** In the processing pipeline, the `fetch_lyrics` network call and `separate_vocals` CPU-bound operation were previously executed sequentially. Since these operations do not depend on each other, running them sequentially results in cumulative latency (Network Time + CPU Time).
**Action:** When a pipeline has independent network I/O and CPU-bound operations, execute them concurrently (e.g., using `concurrent.futures.ThreadPoolExecutor`) to overlap the execution and reduce total pipeline latency (to `max(Network Time, CPU Time)`).

## 2025-02-18 - Conditionally applying FFmpeg video filters
**Learning:** Applying an FFmpeg video filter like `ass` with an empty subtitle file still incurs significant processing overhead (e.g., evaluating the libass renderer) on every single video frame, slowing down render times by ~17% unnecessarily.
**Action:** Always verify that input data (like a lyrics file) is not empty before dynamically including its respective video filter in the FFmpeg command.

## 2024-10-18 - Dynamic framerate for static videos
**Learning:** Generating static videos (e.g., black backgrounds without subtitles) at high framerates (like 30fps) adds unnecessary encoding overhead, even when using `-tune stillimage`. Reducing the framerate to 1 fps for completely static videos results in a significant speedup (~1.75x) in FFmpeg processing time.
**Action:** Dynamically adjust the video framerate in FFmpeg based on whether motion or updates (like subtitles) are present. For completely static outputs, lower the framerate (`-r 1`) to improve performance.

## 2025-02-18 - String replacement chaining vs splitlines+regex
**Learning:** In Python, using `re.finditer` on an entire string avoids creating large intermediate lists and is more memory-efficient and faster than using `str.splitlines()` followed by line-by-line regex matching.
**Action:** Always prefer `re.finditer` over `str.splitlines()` + `re.match()` when extracting information from large multiline strings.

## 2025-02-18 - String join with unpacking vs concatenation
**Learning:** In Python, assembling large strings by unpacking elements into a single list and using `join()` (e.g., `"\n".join([header, *events])`) is faster than concatenating string literals with the result of another `join()` (e.g. `header + "\n".join(events)`).
**Action:** Use list unpacking within a single `join()` call for optimal string assembly performance instead of mixing `join()` with string concatenation.
