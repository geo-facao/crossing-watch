"""Detector test: find animals in a photo or the live webcam feed.

Usage:
  python scripts/detector_test.py              # live webcam, press 'q' to quit
  python scripts/detector_test.py photo.jpg    # one image, then exit
"""
import sys
import time

import cv2
from ultralytics import YOLO

# COCO dataset class IDs for animals (the model was trained on these)
ANIMAL_IDS = {14, 15, 16, 17, 18, 19, 20, 21, 22, 23}
CONF_THRESHOLD = 0.4   # ignore detections the model is less than 40% sure about

# Load the nano model (yolo11n = smallest, fastest version)
model = YOLO("yolo11n.pt")
names = model.names    # maps class IDs to names, such as 16 -> "dog"


def show_animals(frame):
    """Run the model on one frame and print any animals it finds."""
    # Run detection; imgsz=320 is smaller and faster on the Pi
    results = model(frame, imgsz=320, verbose=False)[0]
    for box in results.boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        if class_id in ANIMAL_IDS and confidence >= CONF_THRESHOLD:
            print(f"Animal: {names[class_id]}  confidence: {confidence:.2f}")
    return results


if len(sys.argv) > 1:
    # Photo mode: run once on the image file
    image = cv2.imread(sys.argv[1])
    if image is None:
        raise SystemExit(f"Could not read image: {sys.argv[1]}")
    results = show_animals(image)
    print("Done. Found", len(results.boxes), "objects total.")
else:
    # Live mode: run on the webcam and print the detection speed
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    frames, start = 0, time.time()
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        results = show_animals(frame)
        frames += 1
        if time.time() - start >= 5:
            print(f"Detection speed: {frames / (time.time() - start):.1f} frames/sec")
            frames, start = 0, time.time()
        # Draw the boxes on the frame so you can see what the model sees
        cv2.imshow("detector test", results.plot())
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()
