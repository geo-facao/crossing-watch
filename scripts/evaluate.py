"""Evaluate the detector and decision logic on labeled test clips.

Usage (from the project root):
  python scripts/evaluate.py

Reads data/test_clips/labels.csv and runs each clip through the same
detect -> zone -> Decider logic that src/main.py uses. Reports, per clip:
  - expected vs actual result (PASS or FAIL)
  - number of alerts
  - alerts per minute of video

Summary: pass count, false alarms (alerts on clips labeled IDLE), and
alerts per minute on the clips labeled ALERT.

It does NOT write to data/logs/detections.csv.
"""
import csv
import os
import sys

import cv2
import yaml
from ultralytics import YOLO

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from decision import Decider                  # noqa: E402
from main import detect                       # noqa: E402  same detector as live
from zone import make_zone, in_zone           # noqa: E402

CLIPS_DIR = os.path.join(ROOT, "data", "test_clips")
LABELS_PATH = os.path.join(CLIPS_DIR, "labels.csv")


def run_clip(model, path, zone_poly, conf_min, image_size):
    """Run one clip through the pipeline. Returns alert count and video length."""
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise SystemExit(f"Could not open clip: {path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 10.0

    decider = Decider()
    prev_state = "IDLE"
    alerts = 0
    frames = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        now = frames / fps          # video time in seconds, not wall-clock
        frames += 1

        # Does any animal's center sit inside the zone on this frame?
        hit = False
        for box, conf, name in detect(model, frame, conf_min, image_size):
            if in_zone(box, zone_poly):
                hit = True

        state = decider.update(hit, now)
        if state == "ALERT" and prev_state == "IDLE":
            alerts += 1             # count each new alert once
        prev_state = state

    cap.release()
    minutes = frames / fps / 60
    return alerts, minutes


def main():
    with open(os.path.join(ROOT, "config.yaml")) as f:
        cfg = yaml.safe_load(f)
    conf_min = cfg["detector"]["confidence"]
    image_size = cfg["detector"]["image_size"]
    zone_poly = make_zone(cfg["zone"]["points"])

    model = YOLO(os.path.join(ROOT, "yolo11n.pt"))
    with open(LABELS_PATH) as f:
        rows = list(csv.DictReader(f))

    passed = 0
    false_alarms = 0
    alert_minutes = 0.0
    alerts_on_alert_clips = 0

    print(f"{'clip':<26} {'expected':<8} {'alerts':>6} {'min':>6} {'alerts/min':>10}  result")
    for row in rows:
        name = row["filename"]
        expected = row["expected"]
        path = os.path.join(CLIPS_DIR, name)
        alerts, minutes = run_clip(model, path, zone_poly, conf_min, image_size)

        if expected == "ALERT":
            ok = alerts >= 1
            alerts_on_alert_clips += alerts
            alert_minutes += minutes
        else:
            ok = alerts == 0
            if alerts > 0:
                false_alarms += alerts

        passed += ok
        per_min = alerts / minutes if minutes else 0.0
        print(f"{name:<26} {expected:<8} {alerts:>6} {minutes:>6.2f} {per_min:>10.2f}  "
              f"{'PASS' if ok else 'FAIL'}")

    print()
    print(f"Passed: {passed}/{len(rows)} clips")
    print(f"False alarms (alerts on IDLE clips): {false_alarms}")
    if alert_minutes:
        print(f"Alerts per minute on ALERT clips: {alerts_on_alert_clips / alert_minutes:.2f}")


if __name__ == "__main__":
    main()
