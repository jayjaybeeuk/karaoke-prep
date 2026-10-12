import time
import re

raw_name = "The Beatles - Yesterday!@#$%"

print("--- Uncompiled Regex ---")
start = time.time()
for _ in range(1000000):
    safe_name = re.sub(r"[^a-zA-Z0-9_\- ]", "", raw_name).strip()
duration1 = time.time() - start
print(f"Uncompiled duration: {duration1:.3f} seconds")

print("--- Compiled Regex ---")
PATTERN = re.compile(r"[^a-zA-Z0-9_\- ]")
start = time.time()
for _ in range(1000000):
    safe_name = PATTERN.sub("", raw_name).strip()
duration2 = time.time() - start
print(f"Compiled duration: {duration2:.3f} seconds")

print(f"Improvement: {duration1 - duration2:.3f} seconds faster")
if duration2 < duration1:
    print(f"Speedup: {duration1 / (duration2 or 0.0001):.1f}x")
