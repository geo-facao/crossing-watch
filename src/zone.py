"""Zone check: is a detection's center point inside the roadside zone?"""
import numpy as np
import cv2


def make_zone(points):
    """Turn the saved corner list into a polygon OpenCV can test against."""
    return np.array(points, dtype=np.int32)


def box_center(box):
    """Return the center (x, y) of a box given as (x1, y1, x2, y2)."""
    x1, y1, x2, y2 = box
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def in_zone(box, zone_polygon):
    """True if the center of the box is inside the zone polygon."""
    # pointPolygonTest returns > 0 inside, 0 on the edge, < 0 outside
    center = box_center(box)
    return cv2.pointPolygonTest(zone_polygon, center, False) >= 0
