"""Record a labeled test clip from the webcam.

Usage (from the project root):
  python scripts/record_clip.py NAME SECONDS

Example:
  python scripts/record_clip.py animal_in_zone 20

Shows a 3-second "get ready" countdown, then records SECONDS of video to
data/test_clips/NAME.mp4. Press 'q' to stop early.
"""
import os
import sys
import time

import cv2
import yaml

FPS = 10  # frames per second written to the file

if len(sys.argv) != 3:
    raise SystemExit("Usage: python scripts/record_clip.py NAME SECONDS")
name = sys.argv[1]
seconds = float(sys.argv[2])

with open("config.yaml") as f:
    cfg = yaml.safe_load(f)
cam = cfg["camera"]

out_dir = os.path.join("data", "test_clips")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, name + ".mp4")

cap = cv2.VideoCapture(cam["index"], cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam["width"])
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam["height"])
if not cap.isOpened():
    raise SystemExit("Could not open the webcam.")

writer = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), FPS,
                         (cam["width"], cam["height"]))

# Countdown: show the live view so you can get into position
end = time.time() + 3
while time.time() < end:
    ok, frame = cap.read()
    if ok:
        cv2.putText(frame, "get ready", (20, 50), cv2.FONT_HERSHEY_SIMPLEX,
                    1.2, (0, 255, 255), 2)
        cv2.imshow("record", frame)
    cv2.waitKey(1)

print(f"Recording {seconds} seconds to {out_path} ...")
start = time.time()
frames = 0
while time.time() - start < seconds:
    ok, frame = cap.read()
    if not ok:
        print("Lost the camera feed.")
        break
    writer.write(frame)
    frames += 1
    cv2.imshow("record", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

writer.release()
cap.release()
cv2.destroyAllWindows()
print(f"Saved {frames} frames to {out_path}")
