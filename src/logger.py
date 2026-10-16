"""Append alert events to a CSV log.

Each row: timestamp (ISO 8601, local time), class, confidence, zone.
The file and its header are created on first use. Rows are flushed
immediately so a crash or power loss keeps everything logged so far.
"""

import csv
import os
from datetime import datetime

DEFAULT_LOG_PATH = os.path.join("data", "logs", "detections.csv")
FIELDS = ["timestamp", "class", "confidence", "zone"]


class DetectionLogger:
    def __init__(self, path: str = DEFAULT_LOG_PATH):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        new_file = not os.path.exists(path) or os.path.getsize(path) == 0
        self._fh = open(path, "a", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._fh, fieldnames=FIELDS)
        if new_file:
            self._writer.writeheader()
            self._fh.flush()

    def log_alert(self, class_name: str, confidence: float, zone: str = "") -> None:
        """Record one alert. confidence is 0.0-1.0; it is written with 2 decimals."""
        self._writer.writerow({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "class": class_name,
            "confidence": f"{confidence:.2f}",
            "zone": zone,
        })
        self._fh.flush()
        os.fsync(self._fh.fileno())

    def close(self) -> None:
        self._fh.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
