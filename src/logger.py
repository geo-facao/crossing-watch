"""Append alert events to a CSV log.

Each row: timestamp (ISO 8601, local time), class, confidence, zone, raw_label.
  class      - always "animal" (what the system claims)
  raw_label  - the species the model guessed, e.g. "cow" for a deer (for review)

The file and its header are created on first use. Rows are flushed
immediately so a crash or power loss keeps everything logged so far.
If an older log with a different header is found, it is moved aside
(not deleted) so the new columns line up.
"""

import csv
import os
from datetime import datetime

DEFAULT_LOG_PATH = os.path.join("data", "logs", "detections.csv")
FIELDS = ["timestamp", "class", "confidence", "zone", "raw_label"]


class DetectionLogger:
    def __init__(self, path: str = DEFAULT_LOG_PATH):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

        # If the file has an old header, move it aside so columns line up
        if os.path.exists(path) and os.path.getsize(path) > 0:
            with open(path, newline="", encoding="utf-8") as f:
                old_header = next(csv.reader(f), [])
            if old_header != FIELDS:
                root, ext = os.path.splitext(path)
                backup = f"{root}_old{ext}"
                os.replace(path, backup)
                print(f"Log format changed; old log moved to {backup}")

        new_file = not os.path.exists(path) or os.path.getsize(path) == 0
        self._fh = open(path, "a", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._fh, fieldnames=FIELDS)
        if new_file:
            self._writer.writeheader()
            self._fh.flush()

    def log_alert(self, class_name: str, confidence: float, zone: str = "",
                  raw_label: str = "") -> None:
        """Record one alert. confidence is 0.0-1.0; it is written with 2 decimals."""
        self._writer.writerow({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "class": class_name,
            "confidence": f"{confidence:.2f}",
            "zone": zone,
            "raw_label": raw_label,
        })
        self._fh.flush()
        os.fsync(self._fh.fileno())

    def close(self) -> None:
        self._fh.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
