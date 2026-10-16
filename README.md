# crossing-watch

A prototype that detects animals near a roadside zone with a webcam and warns drivers with a full-screen alert.

**This is a prototype. It does not prove that collisions go down.** It detects animals and warns. Measuring a real reduction would require a real-road study.

## How it works
1. A webcam watches the road.
2. A YOLO model (yolo11n) finds animals in each frame.
3. If an animal's center is inside the zone for 3 of the last 5 frames, the system raises an ALERT.
4. The monitor shows a full-screen warning. It returns to idle 5 seconds after the last detection.
5. Each alert is logged to `data/logs/detections.csv`.

## Hardware
- Raspberry Pi 5 with Raspberry Pi OS
- USB webcam
- External monitor (micro-HDMI)
- Arduino LEDs are planned but not built

## Setup
```bash
cd ~/crossing-watch
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
python src/main.py          # full-screen warning only
python src/main.py --debug  # also shows detection boxes
```

Press `q` in a window, or `Ctrl+C` in the terminal, to quit.

## Calibrate the zone
```bash
python scripts/calibrate_zone.py
```
Click four corners around the area to watch, press `s` to save.

## Test
```bash
python -m pytest tests/ -v          # decision logic unit tests
python scripts/evaluate.py          # runs labeled clips in data/test_clips/
```

## Results so far
- Labeled test set: 4 clips, 4 of 4 passed, 0 false alarms.
- Detector speed: about 10.6 frames per second on the Pi 5 at 320-pixel input.
- Tested indoors with a cat and a dog. Not tested on a road.

## Limits
- Species is not reliable. The alert says "animal detected."
- Screen glare and poor lighting reduce detection.
- An animal that stops and starts can trigger repeat alerts.

See `docs/demo_script.md` for the demo steps and fallback plan.

## Context
Monterey Road in Coyote Valley (San Jose) has documented wildlife road deaths. The VTA US 101/Monterey Road Wildlife Crossings Project is planned but not yet built. This prototype is an interim idea, not a replacement for crmm









