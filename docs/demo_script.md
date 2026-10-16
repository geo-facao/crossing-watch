# crossing-watch demo script

## What we are claiming
crossing-watch detects animals in a defined roadside zone and warns drivers with a full-screen alert. It is a prototype.

**We do NOT claim** that it reduces collisions. We have not measured that, and we could not test on a real road.

## Measured results (say these, and only these)
- Labeled test set: 4 clips (animal in zone, animal outside zone, empty road, person on road). **4 of 4 passed. 0 false alarms.**
- The cat clip produced 3 alerts in about 1 minute. Each alert came after the state returned to idle. The 5-second hold works, but a cat that stops and starts can trigger repeat alerts.
- Speed: about **10.6 frames per second** for the detector alone on the Raspberry Pi 5 at the 320-pixel input setting. The full main loop was not separately timed.
- Unit tests: 5 of 5 pass for the decision logic.

## Limits to state up front
- Tested indoors, with a cat and a dog, on a screen or a live animal in a room. Not tested on a road, at night, or in rain.
- Species labels are unreliable. The model guessed "cow" and "horse" for a cat in one test. Say "animal detected," never a species.
- Screen glare hurt detection of a photo. Use a matte screen and even lighting.

## Setup before judges arrive
1. Connect the webcam and the monitor to the Pi. Confirm the monitor shows the desktop.
2. Confirm the zone in `config.yaml` covers the area you want to demonstrate.
3. Open a terminal in `~/crossing-watch`.
4. Run `python src/main.py`. The screen should show a dark IDLE window.

## Live demo steps
1. Say what the system is for, using the claim above.
2. Show the dark screen. Say it is idle.
3. Bring an animal (the cat or the dog photo) into the zone. The screen should turn red with "ANIMAL NEAR ROAD / SLOW DOWN" within about a second.
4. Take the animal out of the zone. The screen should return to dark about 5 seconds later.
5. Open a second terminal and run `tail -n 3 data/logs/detections.csv`. Show the new `roadside` row with its timestamp and confidence.
6. Show the measured results above. Say they come from four recorded clips in a room.
7. State the limits.

## Fallback plan
- **Webcam fails:** play a recorded clip, such as `data/test_clips/animal_in_zone.mp4`, through the same pipeline. Say the clip is recorded, not live. Note that the pipeline is the same.
- **Monitor fails:** show the terminal output and the CSV log instead. Say the warning screen is not displayed.
- **Arduino:** not part of this build. Skip it. Do not debug it on stage.
- **Detection misses the animal:** explain that the model is limited and that lighting matters. Show the measured clips instead.

## Questions judges may ask
- "Does this reduce collisions?" No. It detects animals and warns drivers. Reduction would need a real-road study.
- "What species is it?" It only says "animal" in the alert. The model cannot reliably tell deer or coyote from other animals.
- "Why does it sometimes alert more than once?" Repeat alerts happen when an animal stops and starts in the zone. A cooldown could fix this, and it is a planned next step.
