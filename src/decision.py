"""Decision logic: turn per-frame detections into a stable ALERT / IDLE state.

Rules:
  - A frame "hits" if at least one animal is inside the zone.
  - ALERT starts when 3 of the last 5 frames are hits.
  - ALERT stays on for 5 seconds after the last hit, then returns to IDLE.
"""
from collections import deque

WINDOW = 5          # how many recent frames we remember
NEEDED = 3          # how many hits in that window trigger an alert
HOLD_SECONDS = 5.0  # how long the alert stays on after the last hit


class Decider:
    def __init__(self):
        self.recent = deque(maxlen=WINDOW)  # True/False per recent frame
        self.state = "IDLE"
        self.last_hit_time = None

    def update(self, frame_has_hit, now):
        """Feed one frame's result and the current time in seconds.

        Returns the state: "IDLE" or "ALERT".
        """
        self.recent.append(bool(frame_has_hit))

        if sum(self.recent) >= NEEDED:
            self.state = "ALERT"
            self.last_hit_time = now
        elif self.state == "ALERT" and self.last_hit_time is not None:
            # Stay in ALERT until the hold time has passed with no new hits
            if now - self.last_hit_time >= HOLD_SECONDS:
                self.state = "IDLE"
        return self.state
