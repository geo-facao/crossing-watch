# crossing-watch demo script

## What we are claiming
crossing-watch detects animals in a defined roadside zone and warns drivers with a red warning panel on a monitor. It is a prototype.

**We do NOT claim** that it reduces collisions. We have not measured that, and we could not test on a real road.

## Measured results (say these, and only these)
- **Labeled clips:** 4 clips (animal in zone, animal outside zone, empty road, person on road). **4 of 4 passed. 0 false alarms.** The clips are short and indoors, so call this a smoke test, not accuracy.
- **Speed:** about **10.6 frames per second** for the detector alone on the Raspberry Pi 5 at the 320-pixel input. The full loop was not timed separately.
- **Unit tests:** 8 of 8 pass for the decision logic.
- **Time to red:** not yet timed. Do not quote a number unless the timed run below is done.

Do not quote alerts per minute or "alerts in 1 minute" from the clips. They were recorded at 15 FPS but labeled 10 FPS, so their timing is stretched 1.5 times. Pass/fail and false alarms count frames, so they still hold.

## Limits to state up front
- Tested indoors, with a cat and a dog. Not tested on a road, at night, or in rain.
- Species labels are unreliable. The model guessed "cow" and "horse" for a cat in one test. The screen and the boxes only say "animal".
- Screen glare hurt detection of a photo. Use a matte printout and even lighting.

## Before judges arrive
1. Connect the webcam and the monitor to the Pi. Confirm the monitor shows the desktop.
2. Open a terminal in `~/crossing-watch` and run `source venv/bin/activate`.
3. Run `date`. The time must be right, because the log timestamps are shown.
4. Run `ls yolo11n.pt` to confirm the model file is there.
5. Run `python src/main.py`. Check that the terminal prints `Frame size: 640x480` with no WARNING, that the yellow zone is where you want it, and that the panel says `Source: live webcam` and `State: IDLE`.
6. Bring the prop into the zone once to confirm it alerts in this room's lighting.
7. Optional, once: film the monitor and the prop together on a phone. From the video, note the time from entering the zone to red, and from leaving to dark. Only then may you quote "red within about X seconds."

## Live demo steps
1. Say what the system is for, using the claim above.
2. Show the dark panel. Say it is idle and point at the yellow zone.
3. Bring the animal prop into the zone. The panel should turn red with **ANIMAL / NEAR ROAD / SLOW DOWN**, and the box should say `animal` with a confidence.
4. Take the prop out of the zone. The panel should return to dark about 5 seconds after the last detection.
5. Open a second terminal and run `tail -n 3 data/logs/detections.csv`. Show the new row: timestamp, `animal`, confidence, `roadside`, and the model's raw guess in the last column. Explain why the guess is logged but never shown.
6. Show the measured results above. Say they come from four short recorded clips in a room.
7. State the limits.

## Fallback plan
- **Webcam fails:** the program tries to reconnect 5 times, then prints the fallback command. Quit and run:
  ```bash
  python src/main.py --source data/test_clips/animal_in_zone.mp4
  ```
  The panel will say `Source: recorded clip`. Say it is a recorded clip from the same camera, going through the same pipeline.
- **Monitor fails:** show the terminal output (`ALERT: animal detected ...` lines) and the CSV log instead. Say the warning panel is not displayed.
- **Detection misses the prop:** say the model is limited and that lighting matters. Switch to the recorded clip.
- **Arduino:** not part of this build. Do not mention it as working.

## Questions judges may ask
- **"Does this reduce collisions?"** No, and we have not measured that. It detects animals in a zone and warns. A next step would be a field pilot: compare detections with a trail camera, and check whether driver speed drops during alerts. Showing fewer collisions would need a long study.
- **"What species is it?"** It only says "animal". COCO, the dataset the model was trained on, has no deer or coyote class, so it guesses the nearest one, like "cow". We log that guess for review and never show it. Training on deer and coyote images is the obvious next step.
- **"How accurate is it?"** Four short indoor clips, all passed, no false alarms. That is a smoke test, not an accuracy number.
- **"Does it work at night?"** Not tested. A normal webcam cannot see in the dark. It would need an infrared or thermal camera.
- **"Why not just a static sign?"** Static signs are always on, and drivers tune them out. This one only lights up when an animal is detected. We have not measured whether drivers respond better.
- **"Why does it sometimes alert more than once?"** An animal that stops and starts in the zone can leave the zone long enough for the 5-second hold to end. A cooldown would reduce repeats.
- **"Why Monterey Road?"** VTA plans wildlife crossings there, with construction scheduled for 2028-2030 and full funding still to be identified. This is an idea for the years before then, not a replacement.
