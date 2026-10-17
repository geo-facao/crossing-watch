# crossing-watch

A prototype that watches a roadside zone with a webcam, detects animals in it, and warns drivers with a red warning panel on a monitor.

**This is a prototype. It does not prove that collisions go down.** It detects animals and shows a warning. Measuring a real reduction would need a study on a real road.

## How it works
1. A USB webcam on a Raspberry Pi 5 watches the scene.
2. A YOLO model (`yolo11n`, trained on the COCO dataset) finds animals in each frame.
3. A frame counts as a "hit" if the center of an animal's box is inside the zone (a polygon set in `config.yaml`).
4. If 3 of the last 5 frames are hits, the system goes to ALERT. The status panel turns red and reads **ANIMAL / NEAR ROAD / SLOW DOWN**.
5. Each new hit restarts a 5-second hold. The panel returns to dark 5 seconds after the last hit.
6. Each new alert adds one row to `data/logs/detections.csv`.

The monitor shows the camera view (operator view, with the zone and detection boxes) on the left and the warning panel (what a driver would see) on the right.

### "Animal", not a species
COCO has no deer or coyote class, so the model guesses the nearest class it knows (for example "cow" for a deer). The screen, the boxes, and the log's `class` column always say **animal**. The model's guess is kept only in the log's `raw_label` column, for review.

Log columns: `timestamp, class, confidence, zone, raw_label`

## Hardware
- Raspberry Pi 5 with Raspberry Pi OS
- USB webcam (runs at about 15 FPS at 640x480)
- External monitor (micro-HDMI)
- Arduino LED warning: idea only, not implemented

## Setup
```bash
cd ~/crossing-watch
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
The model file `yolo11n.pt` must be in the project root. It is not in the repo (`*.pt` is gitignored). If it is missing, Ultralytics tries to download it on first run, which needs internet.

## Run
```bash
python src/main.py                                               # live webcam
python src/main.py --source data/test_clips/animal_in_zone.mp4  # recorded clip
```
With `--source`, a recorded clip goes through the same pipeline and loops, and the panel says `Source: recorded clip`. This is the fallback if the webcam fails.

On startup the terminal prints the frame size. It must match `config.yaml` (640x480), or the zone will be in the wrong place. If the webcam stops sending frames, the program tries to reopen it 5 times, 1 second apart, before stopping.

Quit with `q` or `Esc` in the window, the window's X button, or `Ctrl+C` in the terminal.

## Calibrate the zone
```bash
python scripts/calibrate_zone.py
```
Click four corners around the area to watch (clockwise), then press `s` to save to `config.yaml`. `r` resets the points, `q` quits without saving.

## Record and check test clips
```bash
python scripts/record_clip.py animal_in_zone 30   # records 30 s to data/test_clips/animal_in_zone.mp4
python scripts/clip_info.py                       # size, fps, frames, and length of each clip
```
Clips are saved at exactly 10 frames per real second, close to the live loop's speed.

## Test
```bash
python -m pytest tests/ -v          # decision logic unit tests (8)
python scripts/evaluate.py          # runs the clips listed in data/test_clips/labels.csv
```
`evaluate.py` uses the same detect, zone, and decision code as `src/main.py` and does not write to the log.

## Results so far
- **Labeled clips:** 4 clips (animal in zone, animal outside zone, empty road, person on road). **4 of 4 passed, 0 false alarms.** The clips are short (under a minute each), so this is a smoke test, not an accuracy measurement.
- **Detector speed:** about 10.6 frames per second on the Pi 5 at 320-pixel input, for the detector alone. The full loop was not timed separately.
- **Unit tests:** 8 of 8 pass.
- **Where:** indoors, with a cat and a dog. Not tested on a road, at night, or in rain.

Note on the clips: they were recorded before a fix to `record_clip.py`. The webcam ran at 15 FPS, but the files were labeled 10 FPS, so they play 1.5 times slower than real time. Pass/fail and false-alarm counts depend only on frames (3 hits in 5 frames), so they are not affected. Time-based numbers from those clips (alerts per minute) are not reliable and are not reported.

## Limits
- Species is not reliable. The system only claims "animal".
- The zone check uses the center of the box. With a camera at an angle, an animal standing on the edge of the road can have its box center outside the zone.
- Glare and poor lighting reduce detection. A normal webcam cannot see at night.
- An animal that stops and starts in the zone can trigger repeat alerts.
- The zone is in pixels for a 640x480 frame. It must be recalibrated if the camera moves or the frame size changes.

## Context
Monterey Road and US 101 cross Coyote Valley in south San Jose. VTA's US 101/Monterey Road Wildlife Crossings Project lists reducing wildlife-vehicle collisions as a goal. VTA schedules construction for 2028-2030, at an estimated $80-90 million, with full funding still to be identified. This prototype is an interim idea for the years before the crossings exist, not a replacement for them.

Sources: [VTA project page](https://www.vta.org/projects/us-101monterey-road-wildlife-crossings-project), [VTA fact sheet (July 2025)](https://www.vta.org/sites/default/files/2025-08/US101-MontereyRoad-WildlifeCrossingsProject-ENG-073125_FactSheet.pdf)

See `docs/demo_script.md` for the demo steps and fallback plan.
