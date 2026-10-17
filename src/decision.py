"""Decision logic: turn per-frame detections into a stable ALERT / IDLE state.

Rules:
  - A frame "hits" if at least one animal is inside the zone.
  - ALERT starts when 3 of the last 5 frames are hits.
  - Each hit frame while ALERT restarts the 5-second hold.
  - Miss frames never extend the hold. ALERT returns to IDLE 5 seconds
    after the last hit.
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

        # Enough hits in the window starts the alert.
        # (Adding a miss can only lower the count, so this happens on hit frames.)
        if sum(self.recent) >= NEEDED:
            self.state = "ALERT"

        if self.state == "ALERT":
            if frame_has_hit:
                # Only a real hit frame moves the hold timer forward
                self.last_hit_time = now
            elif now - self.last_hit_time >= HOLD_SECONDS:
                self.state = "IDLE"
        return self.state
