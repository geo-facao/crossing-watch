"""Main loop: camera -> detector -> zone check -> decision -> display -> log.

Run from the project root:
  python src/main.py            # full-screen warning only
  python src/main.py --debug    # also show a window with detection boxes
Press 'q' in a window, or Ctrl+C in the terminal, to quit.
"""
import argparse
import os
import sys
import time

import cv2
import yaml
from ultralytics import YOLO

sys.path.insert(0, os.path.dirname(__file__))
import display                        # noqa: E402
from decision import Decider          # noqa: E402
from logger import DetectionLogger    # noqa: E402
from zone import make_zone, in_zone   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "config.yaml")
MODEL_PATH = os.path.join(ROOT, "yolo11n.pt")
ZONE_LABEL = "roadside"
DEBUG_WINDOW = "detections (debug)"
# COCO classes that count as wildlife
ANIMAL_CLASSES = {"bird", "cat", "dog", "horse", "sheep", "cow",
                  "elephant", "bear", "zebra", "giraffe"}


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def open_camera(cfg):
    cam = cfg["camera"]
    cap = cv2.VideoCapture(cam["index"])
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam["width"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam["height"])
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam")
    return cap


def detect(model, frame, conf_min, image_size):
    """Return a list of (box_xyxy, confidence, class_name) for this frame.

    image_size is the square size the model resizes each frame to.
    Smaller is faster but can miss small animals.
    """
    result = model(frame, imgsz=image_size, verbose=False)[0]
    out = []
    for b in result.boxes:
        conf = float(b.conf[0])
        if conf < conf_min:
            continue
        cls_name = result.names[int(b.cls[0])]
        if cls_name not in ANIMAL_CLASSES:
            continue
        box = tuple(float(v) for v in b.xyxy[0])
        out.append((box, conf, cls_name))
    return out


def draw(frame, zone_poly, state, hits):
    """Draw the zone, boxes, and state label onto the frame (debug window only)."""
    cv2.polylines(frame, [zone_poly], True, (0, 255, 255), 2)
    for box, conf, name, in_z in hits:
        x1, y1, x2, y2 = map(int, box)
        color = (0, 0, 255) if in_z else (0, 255, 0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f"{name} {conf:.2f}", (x1, y1 - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    color = (0, 0, 255) if state == "ALERT" else (0, 200, 0)
    cv2.putText(frame, state, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.4, color, 3)
    return frame


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true",
                        help="also show a window with detection boxes")
    args = parser.parse_args()

    cfg = load_config()
    conf_min = cfg["detector"]["confidence"]
    image_size = cfg["detector"]["image_size"]
    zone_poly = make_zone(cfg["zone"]["points"])

    model = YOLO(MODEL_PATH)
    cap = open_camera(cfg)
    decider = Decider()
    log = DetectionLogger(os.path.join(ROOT, "data", "logs", "detections.csv"))

    # The full-screen warning window is always on
    display.make_window()
    display.draw_state("IDLE")
    if args.debug:
        cv2.namedWindow(DEBUG_WINDOW, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(DEBUG_WINDOW, 960, 720)

    prev_state = "IDLE"
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Camera read failed; stopping.")
                break

            detections = detect(model, frame, conf_min, image_size)
            hits = []
            best_hit = None
            for box, conf, name in detections:
                in_z = in_zone(box, zone_poly)
                hits.append((box, conf, name, in_z))
                if in_z and (best_hit is None or conf > best_hit[1]):
                    best_hit = (box, conf, name)

            state = decider.update(best_hit is not None, time.monotonic())

            # Log once when an alert starts
            if state == "ALERT" and prev_state == "IDLE" and best_hit is not None:
                _, conf, name = best_hit
                log.log_alert(name, conf, zone=ZONE_LABEL)
                print(f"ALERT: {name} ({conf:.2f})")

            # Redraw the warning screen only when the state changes
            if state != prev_state:
                display.draw_state(state)
            prev_state = state

            if args.debug:
                cv2.imshow(DEBUG_WINDOW, draw(frame, zone_poly, state, hits))

            # waitKey keeps the windows responsive; 'q' quits
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        log.close()
        display.close_window()


if __name__ == "__main__":
    main()
