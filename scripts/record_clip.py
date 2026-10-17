"""Record a labeled test clip from the webcam.

Usage (from the project root):
  python scripts/record_clip.py NAME SECONDS

Example:
  python scripts/record_clip.py animal_in_zone 20

Shows a 3-second "get ready" countdown, then records SECONDS of video to
data/test_clips/NAME.mp4. Press 'q' to stop early.

The file is always written at exactly FPS frames per real second, whatever
speed the camera runs at: frames are skipped when the camera is faster than
FPS and repeated when it is slower. So a 20-second recording plays for 20
seconds, and evaluate.py's video time matches real time. (Before, every
camera frame was written but the file was labeled 10 FPS, so a camera
running at 30 FPS made clips play 3 times too slowly.)
"""
import os
import sys
import time

import cv2
import yaml

FPS = 10  # frames per second written to the file (about the live loop's speed)

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

# Countdown: show the live view so you can get into position
frame = None
end = time.time() + 3
while time.time() < end:
    ok, frame = cap.read()
    if ok:
        view = frame.copy()
        cv2.putText(view, "get ready", (20, 50), cv2.FONT_HERSHEY_SIMPLEX,
                    1.2, (0, 255, 255), 2)
        cv2.imshow("record", view)
    cv2.waitKey(1)
if frame is None:
    raise SystemExit("Could not read from the webcam.")

# Use the real frame size. VideoWriter silently writes nothing if the frames
# are a different size than it was opened with.
height, width = frame.shape[:2]
if (width, height) != (cam["width"], cam["height"]):
    print(f"WARNING: camera gives {width}x{height}, config.yaml expects "
          f"{cam['width']}x{cam['height']}. The zone will not line up.")
writer = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), FPS,
                         (width, height))

print(f"Recording {seconds} seconds to {out_path} ...")
start = time.time()
captured = 0   # frames the camera gave us
written = 0    # frames written to the file
while time.time() - start < seconds:
    ok, frame = cap.read()
    if not ok:
        print("Lost the camera feed.")
        break
    captured += 1

    # How many frames the file should hold by now to stay at FPS per real second
    target = int((time.time() - start) * FPS) + 1
    while written < target:
        writer.write(frame)
        written += 1

    cv2.imshow("record", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

elapsed = time.time() - start
writer.release()
cap.release()
cv2.destroyAllWindows()
print(f"Camera delivered {captured / elapsed:.1f} frames/sec.")
print(f"Saved {written} frames at {FPS} FPS = {written / FPS:.1f} s of video "
      f"(recorded for {elapsed:.1f} s) to {out_path}")
