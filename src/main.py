"""Main loop: camera -> detector -> zone check -> decision -> display -> log.

Run from the project root:  python src/main.py
Press 'q' in the window (or Ctrl+C) to quit.
"""
import os
import sys
import time

import cv2
import yaml
from ultralytics import YOLO

sys.path.insert(0, os.path.dirname(__file__))
from decision import Decider          # noqa: E402
from logger import DetectionLogger    # noqa: E402
from zone import make_zone, in_zone   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "config.yaml")
MODEL_PATH = os.path.join(ROOT, "yolo11n.pt")  # ASSUMED location; adjust if different
ZONE_LABEL = "roadside"
WINDOW_NAME = "wildlife-crossing"


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def open_camera(cfg):
    # ASSUMED config keys: camera.index, camera.width, camera.height
    cam = cfg.get("camera", {})
    cap = cv2.VideoCapture(cam.get("index", 0))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam.get("width", 640))
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam.get("height", 480))
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam")
    return cap


def detect(model, frame, conf_min):
    """Return a list of (box_xyxy, confidence, class_name) for this frame."""
    result = model(frame, verbose=False)[0]
    out = []
    for b in result.boxes:
        conf = float(b.conf[0])
        if conf < conf_min:
            continue
        box = tuple(float(v) for v in b.xyxy[0])
        cls_name = result.names[int(b.cls[0])]
        out.append((box, conf, cls_name))
    return out


def draw(frame, zone_poly, state, hits):
    """Draw the zone, boxes, and state label onto the frame."""
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
    cfg = load_config()
    conf_min = cfg.get("detector", {}).get("confidence", 0.25)  # ASSUMED key
    zone_points = cfg["zone"]["points"]                          # ASSUMED key
    zone_poly = make_zone(zone_points)

    model = YOLO(MODEL_PATH)
    cap = open_camera(cfg)
    decider = Decider()
    log = DetectionLogger(os.path.join(ROOT, "data", "logs", "detections.csv"))

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    prev_state = "IDLE"
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Camera read failed; stopping.")
                break

            detections = detect(model, frame, conf_min)
            hits = []
            best_hit = None
            for box, conf, name in detections:
                in_z = in_zone(box, zone_poly)
                hits.append((box, conf, name, in_z))
                if in_z and (best_hit is None or conf > best_hit[1]):
                    best_hit = (box, conf, name)

            state = decider.update(best_hit is not None, time.monotonic())

            if state == "ALERT" and prev_state == "IDLE" and best_hit is not None:
                _, conf, name = best_hit
                log.log_alert(name, conf, zone=ZONE_LABEL)
                print(f"ALERT: {name} ({conf:.2f})")
            prev_state = state

            shown = draw(frame, zone_poly, state, hits)
            cv2.imshow(WINDOW_NAME, shown)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        log.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
