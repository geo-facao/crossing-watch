"""Monitor window: live camera on the left, status panel on the right.

The window is a normal window (title bar and close button) unless
START_FULLSCREEN is True. The panel has a clickable QUIT button.
Each draw function returns the key pressed, or 255 if none. It returns
27 (Esc) when the user clicks QUIT, so main.py can quit with one check.

The panel text is the same as the first version of this file.
"""
import cv2
import numpy as np

WINDOW_NAME = "crossing-watch"
START_FULLSCREEN = False           # True = fill the monitor, no title bar
SCREEN_W, SCREEN_H = 1280, 720     # size of the canvas we draw on
CAM_W = 960                        # camera area on the left
PANEL_W = SCREEN_W - CAM_W         # 320 px status panel on the right
FONT = cv2.FONT_HERSHEY_DUPLEX     # bold font for the warning
ESC = 27

# QUIT button in panel coordinates: (x1, y1, x2, y2)
QUIT_PANEL = (20, SCREEN_H - 70, PANEL_W - 20, SCREEN_H - 20)

_quit_clicked = False              # set by the mouse callback
_win_size = (SCREEN_W, SCREEN_H)   # current window size, updated each frame


def _on_mouse(event, x, y, flags, param):
    """OpenCV calls this on every mouse event. A left click on QUIT sets the flag."""
    global _quit_clicked
    if event != cv2.EVENT_LBUTTONDOWN:
        return
    # The window may be resized, so scale the click to canvas coordinates
    win_w, win_h = _win_size
    cx = x * SCREEN_W / win_w
    cy = y * SCREEN_H / win_h
    px = cx - CAM_W                    # position inside the panel
    qx1, qy1, qx2, qy2 = QUIT_PANEL
    if qx1 <= px <= qx2 and qy1 <= cy <= qy2:
        _quit_clicked = True


def make_window():
    """Open the window and set up mouse clicks. Fullscreen only if START_FULLSCREEN."""
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, SCREEN_W, SCREEN_H)
    cv2.setMouseCallback(WINDOW_NAME, _on_mouse)
    if START_FULLSCREEN:
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
    Returns the key pressed (255 if none), or 27 if the user clicked QUIT.
    """
    global _quit_clicked, _win_size

    # Remember the current window size so clicks map to the right spot.
    # If OpenCV can't report the size, keep the last known size.
    try:
        _, _, win_w, win_h = cv2.getWindowImageRect(WINDOW_NAME)
        if win_w > 0 and win_h > 0:
            _win_size = (win_w, win_h)
    except cv2.error:
        pass

    canvas = np.full((SCREEN_H, SCREEN_W, 3), 20, dtype=np.uint8)
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

    # QUIT button at the bottom of the panel
    qx1, qy1, qx2, qy2 = QUIT_PANEL
    cv2.rectangle(panel, (qx1, qy1), (qx2, qy2), (70, 70, 70), -1)
    cv2.rectangle(panel, (qx1, qy1), (qx2, qy2), (200, 200, 200), 2)
    cv2.putText(panel, "QUIT (or press Q)", (qx1 + 30, qy1 + 33),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.imshow(WINDOW_NAME, canvas)
    key = cv2.waitKey(1) & 0xFF

    if _quit_clicked:
        _quit_clicked = False
        return ESC
    return key


def close_window():
    cv2.destroyAllWindows()
