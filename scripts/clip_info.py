"""Print the size, frame rate, and length of test clips.

Usage (from the project root):
  python scripts/clip_info.py                  # every .mp4 in data/test_clips/
  python scripts/clip_info.py some_clip.mp4    # one or more given files

Use it to check that a clip is 640x480 (so the zone lines up) and that its
length matches how long you actually recorded.
"""
import glob
import os
import sys

import cv2

paths = sys.argv[1:] or sorted(glob.glob(os.path.join("data", "test_clips", "*.mp4")))
if not paths:
    raise SystemExit("No clips found in data/test_clips/")

print(f"{'clip':<34} {'size':>9} {'fps':>5} {'frames':>7} {'length':>8}")
for path in paths:
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print(f"{path:<34} could not open")
        continue
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    length = frames / fps if fps else 0.0
    cap.release()
    print(f"{os.path.basename(path):<34} {w:>4}x{h:<4} {fps:>5.1f} {frames:>7} {length:>7.1f}s")
