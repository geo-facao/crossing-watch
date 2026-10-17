"""Monitor screen: live camera on the left, status panel on the right.

The panel turns red with the warning during ALERT and stays dark when IDLE.
Every draw function returns the key pressed in the window (or -1 if none),
so the main loop can quit on 'q' or Esc.
"""
import cv2
import numpy as np

WINDOW_NAME = "crossing-watch"
SCREEN_W, SCREEN_H = 1280, 720     # size of the screen we draw on
CAM_W = 960                        # camera area on the left
PANEL_W = SCREEN_W - CAM_W         # 320 px status panel on the right
FONT = cv2.FONT_HERSHEY_DUPLEX


def make_window():
    """Open the window and make it fullscreen on the monitor."""
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)


def draw_state(state):
    """Full-screen red or dark image only. Used by scripts/display_test.py."""
    if state == "ALERT":
        img = np.zeros((SCREEN_H, SCREEN_W, 3), dtype=np.uint8)
        img[:] = (0, 0, 200)           # BGR: this is red
        y = 300
        for line in ["ANIMAL NEAR ROAD", "SLOW DOWN"]:
            size = cv2.getTextSize(line, FONT, 2.5, 4)[0]
            x = (SCREEN_W - size[0]) // 2
            cv2.putText(img, line, (x, y), FONT, 2.5, (255, 255, 255), 4)
            y += 150
    else:
        img = np.full((SCREEN_H, SCREEN_W, 3), 20, dtype=np.uint8)
    cv2.imshow(WINDOW_NAME, img)
    return cv2.waitKey(1) & 0xFF


def draw_screen(frame, state, status_lines):
    """Show the camera frame on the left and a status panel on the right.

    frame: the camera image (BGR), with zone and boxes already drawn on it.
    status_lines: short text lines shown in the panel.
    Returns the key pressed this frame (-1 if none).
    """
    canvas = np.full((SCREEN_H, SCREEN_W, 3), 20, dtype=np.uint8)

    # Stretch the camera frame to fill the left side of the screen
    canvas[:, :CAM_W] = cv2.resize(frame, (CAM_W, SCREEN_H))

    # panel is a view into canvas, so drawing on it changes the screen
    panel = canvas[:, CAM_W:]
    if state == "ALERT":
        panel[:] = (0, 0, 200)         # red background
        y = 200
        for line in ["ANIMAL", "NEAR ROAD", "SLOW DOWN"]:
            size = cv2.getTextSize(line, FONT, 1.4, 3)[0]
            x = (PANEL_W - size[0]) // 2
            cv2.putText(panel, line, (x, y), FONT, 1.4, (255, 255, 255), 3)
            y += 90
        y = 420                        # status text goes below the warning
    else:
        panel[:] = (30, 30, 30)        # dark background
        y = 60

    for text in status_lines:
        cv2.putText(panel, text, (15, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (255, 255, 255), 2)
        y += 40

    cv2.imshow(WINDOW_NAME, canvas)
    return cv2.waitKey(1) & 0xFF


def close_window():
    cv2.destroyAllWindows()
