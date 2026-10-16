"""Click four corners on the live camera view to define the roadside zone.

Controls:
  left click  - add a corner (click 4 times, clockwise)
  r           - reset the points
  s           - save the zone to config.yaml and quit
  q           - quit without saving
"""
import cv2
import yaml

CONFIG_PATH = "config.yaml"

# Load the current config so we only change the zone
with open(CONFIG_PATH) as f:
    config = yaml.safe_load(f)

cap = cv2.VideoCapture(config["camera"]["index"], cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, config["camera"]["width"])
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config["camera"]["height"])

# Grab a few frames so the camera has time to adjust exposure
for _ in range(10):
    ok, frame = cap.read()
if not ok:
    raise SystemExit("Could not read from the webcam.")

points = []  # the four (x, y) corners the user clicks


def on_click(event, x, y, flags, param):
    """Record a corner each time the left mouse button is clicked."""
    if event == cv2.EVENT_LBUTTONDOWN and len(points) < 4:
        points.append((x, y))


cv2.namedWindow("calibrate zone")
cv2.setMouseCallback("calibrate zone", on_click)

while True:
    view = frame.copy()
    # Draw each clicked corner as a red dot
    for px, py in points:
        cv2.circle(view, (px, py), 5, (0, 0, 255), -1)
    # Draw the outline once we have 2 or more corners
    if len(points) >= 2:
        cv2.polylines(view, [np_points := __import__("numpy").array(points)],
                      isClosed=(len(points) == 4), color=(0, 255, 255), thickness=2)
    cv2.putText(view, f"Corners: {len(points)}/4  (s=save, r=reset, q=quit)",
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.imshow("calibrate zone", view)

    key = cv2.waitKey(20) & 0xFF
    if key == ord("r"):
        points.clear()
    elif key == ord("s") and len(points) == 4:
        # Save the four corners as plain integer pairs
        config["zone"]["points"] = [[int(x), int(y)] for x, y in points]
        with open(CONFIG_PATH, "w") as f:
            yaml.safe_dump(config, f, sort_keys=False)
        print("Saved zone to config.yaml:", config["zone"]["points"])
        break
    elif key == ord("q"):
        print("Quit without saving.")
        break

cap.release()
cv2.destroyAllWindows()
