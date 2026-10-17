"""Main loop: camera -> detector -> zone check -> decision -> display -> log.

Run from the project root:
  python src/main.py                                         # live webcam
  python src/main.py --source data/test_clips/animal_in_zone.mp4  # recorded clip

With --source, the clip plays through the same pipeline and loops at the
end, and the status panel says "Source: recorded clip" so nobody mistakes
it for live video. Use it if the webcam fails during the demo.

If the webcam stops sending frames, the program tries to reopen it
(up to MAX_CAMERA_RETRIES times, 1 second apart) before it stops.

Quit with 'q' or Esc in the window, close the window with its X, or press
Ctrl+C in the terminal.

The screen and log say "animal". The model's guessed species is only
written to the log's raw_label column, since it is often wrong for wildlife.
"""
import argparse
import os
import sys
import time
from datetime import datetime

import cv2
import yaml
from ultralytics import YOLO

sys.path.insert(0, os.path.dirname(__file__))
from decision import Decider                                # noqa: E402
from display import make_window, draw_screen, close_window  # noqa: E402
from logger import DetectionLogger                          # noqa: E402
from zone import make_zone, in_zone                         # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "config.yaml")
MODEL_PATH = os.path.join(ROOT, "yolo11n.pt")
ZONE_LABEL = "roadside"
QUIT_KEYS = (ord("q"), 27)          # 'q' or Esc (27)
MAX_CAMERA_RETRIES = 5              # reopen tries before giving up
# COCO classes the model may guess for an animal. Deer and coyote are not
# COCO classes, so the model often guesses a similar one (e.g. "cow").
ANIMAL_CLASSES = {"bird", "cat", "dog", "horse", "sheep", "cow",
                  "elephant", "bear", "zebra", "giraffe"}


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def parse_args():
    parser = argparse.ArgumentParser(description="crossing-watch main loop")
    parser.add_argument("--source",
                        help="video file to play instead of the webcam "
                             "(fallback if the webcam fails)")
    return parser.parse_args()


def open_camera(cfg):
    """Open the webcam with the same V4L2 backend the calibration script uses."""
    cam = cfg["camera"]
    cap = cv2.VideoCapture(cam["index"], cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam["width"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam["height"])
    if not cap.isOpened():
        raise RuntimeError(f"Could not open webcam {cam['index']} (/dev/video{cam['index']})")
    return cap


def open_clip(path):
    """Open a recorded video file instead of the webcam."""
    if not os.path.exists(path):
        raise RuntimeError(f"Clip not found: {path}")
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open clip: {path}")
    return cap


def check_frame_size(cap, cfg):
    """Print the real frame size and warn if it differs from config.yaml.

    The zone corners are pixel positions, so they only line up when the
    frame is the same size it was when the zone was calibrated.
    """
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    want_w, want_h = cfg["camera"]["width"], cfg["camera"]["height"]
    print(f"Frame size: {w}x{h}")
    if (w, h) != (want_w, want_h):
        print(f"WARNING: config.yaml expects {want_w}x{want_h}. "
              f"The zone will be in the wrong place.")


def reopen_camera(cap, cfg):
    """Try to reopen the webcam after a failed read.

    Returns a working capture, or None after MAX_CAMERA_RETRIES failed tries.
    waitKey (not time.sleep) is used for the 1-second pause so the window
    keeps responding while we wait.
    """
    cap.release()
    for attempt in range(1, MAX_CAMERA_RETRIES + 1):
        print(f"Camera read failed; reconnect try {attempt}/{MAX_CAMERA_RETRIES}...")
        cv2.waitKey(1000)
        try:
            new_cap = open_camera(cfg)
        except RuntimeError:
            continue
        ok, _ = new_cap.read()
        if ok:
            print("Camera reconnected.")
            return new_cap
        new_cap.release()
    return None


def detect(model, frame, conf_min, image_size=640):
    """Return a list of (box_xyxy, confidence, class_name) for this frame.

    image_size is the square size the frame is resized to before the model
    runs. Smaller is faster but may miss small animals.
    """
    result = model(frame, imgsz=image_size, verbose=False)[0]
    out = []
    for b in result.boxes:
        conf = float(b.conf[0])
        if conf < conf_min:
            continue
        box = tuple(float(v) for v in b.xyxy[0])
        cls_name = result.names[int(b.cls[0])]
        if cls_name not in ANIMAL_CLASSES:
            continue
        out.append((box, conf, cls_name))
    return out


def draw(frame, zone_poly, state, hits):
    """Draw the zone outline, detection boxes, and state label on the frame.

    Boxes say "animal", not the model's species guess (which is often
    wrong, e.g. "cow" for a deer). The guess is kept in the log's raw_label.
    """
    cv2.polylines(frame, [zone_poly], True, (0, 255, 255), 2)
    for box, conf, _name, in_z in hits:
        x1, y1, x2, y2 = map(int, box)
        color = (0, 0, 255) if in_z else (0, 255, 0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f"animal {conf:.2f}", (x1, y1 - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    color = (0, 0, 255) if state == "ALERT" else (0, 200, 0)
    cv2.putText(frame, state, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.4, color, 3)
    return frame


def status_lines(state, animal_in_zone, alert_count, last_alert, source_text):
    """Text shown in the status panel on the monitor."""
    lines = [
        f"Source: {source_text}",
        "Watching: roadside zone",
        f"State: {state}",
        f"Animal in zone: {'yes' if animal_in_zone else 'no'}",
        f"Alerts this run: {alert_count}",
    ]
    if last_alert:
        lines.append(f"Last alert: {last_alert}")
    lines.append(f"Time: {datetime.now():%H:%M:%S}")
    return lines


def main():
    args = parse_args()
    cfg = load_config()
    conf_min = cfg["detector"]["confidence"]
    image_size = cfg["detector"]["image_size"]   # 320 in config.yaml
    zone_poly = make_zone(cfg["zone"]["points"])

    if not os.path.exists(MODEL_PATH):
        print(f"WARNING: {MODEL_PATH} not found. Ultralytics will try to "
              f"download it, which needs internet.")
    model = YOLO(MODEL_PATH)

    using_clip = args.source is not None
    source_text = "recorded clip" if using_clip else "live webcam"
    try:
        cap = open_clip(args.source) if using_clip else open_camera(cfg)
    except RuntimeError as err:
        print(f"ERROR: {err}")
        if not using_clip:
            print("Fallback: python src/main.py --source data/test_clips/animal_in_zone.mp4")
        sys.exit(1)
    print(f"Source: {args.source if using_clip else 'webcam'}")
    check_frame_size(cap, cfg)

    decider = Decider()
    log = DetectionLogger(os.path.join(ROOT, "data", "logs", "detections.csv"))

    alert_count = 0
    last_alert = None        # text like "17:23:21 animal 0.83"

    make_window()
    prev_state = "IDLE"
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                if using_clip:
                    # End of the clip: start it again from the first frame
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ok, frame = cap.read()
                    if not ok:
                        print("Could not read the clip; stopping.")
                        break
                else:
                    new_cap = reopen_camera(cap, cfg)
                    if new_cap is None:
                        print("Camera did not come back; stopping.")
                        print("Fallback: python src/main.py --source "
                              "data/test_clips/animal_in_zone.mp4")
                        break
                    cap = new_cap
                    continue

            detections = detect(model, frame, conf_min, image_size)
            hits = []
            best_hit = None
            for box, conf, name in detections:
                in_z = in_zone(box, zone_poly)
                hits.append((box, conf, name, in_z))
                if in_z and (best_hit is None or conf > best_hit[1]):
                    best_hit = (box, conf, name)

            animal_in_zone = best_hit is not None
            state = decider.update(animal_in_zone, time.monotonic())

            if state == "ALERT" and prev_state == "IDLE" and best_hit is not None:
                _, conf, name = best_hit
                # Log "animal" for the claim, and the model's guess for review
                log.log_alert("animal", conf, zone=ZONE_LABEL, raw_label=name)
                alert_count += 1
                last_alert = f"{datetime.now():%H:%M:%S} animal {conf:.2f}"
                print(f"ALERT: animal detected ({conf:.2f})")
            prev_state = state

            view = draw(frame.copy(), zone_poly, state, hits)
            lines = status_lines(state, animal_in_zone, alert_count, last_alert,
                                 source_text)
            key = draw_screen(view, state, lines)
            if key in QUIT_KEYS:
                print("Quit from the window.")
                break
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        log.close()
        close_window()


if __name__ == "__main__":
    main()
