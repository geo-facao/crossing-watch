"""Monitor window: live camera on the left, status panel on the right.

The window is a normal window (title bar and close button) unless
START_FULLSCREEN is True. The panel has a clickable QUIT button.
Each draw function returns the key pressed, or 255 if none. It returns
27 (Esc) when the user clicks QUIT, so main.py can quit with one check.

Text sizes match the original version: bold DUPLEX headlines and
0.6-size plain status lines.
"""
import cv2
import numpy as np

WINDOW_NAME = "crossing-watch"
START_FULLSCREEN = False           # True = fill the monitor, no title bar
SCREEN_W, SCREEN_H = 1280, 720     # size of the canvas we draw on
CAM_W = 960                        # camera area on the left
PANEL_W = SCREEN_W - CAM_W         # 320 px status panel on the right
PAD = 20                           # inner margin inside the panel
FONT = cv2.FONT_HERSHEY_DUPLEX     # bold font for headlines
FONT_PLAIN = cv2.FONT_HERSHEY_SIMPLEX
ESC = 27

# Colors are BGR (blue, green, red), not RGB
PANEL_BG = (38, 34, 30)
CARD_BG = (58, 52, 46)
RED = (40, 40, 205)
RED_DARK = (30, 25, 150)
GREEN = (110, 210, 110)
WHITE = (255, 255, 255)
TEXT = (235, 235, 235)
MUTED = (165, 160, 155)

# QUIT button in panel coordinates: (x1, y1, x2, y2)
QUIT_PANEL = (PAD, SCREEN_H - 70, PANEL_W - PAD, SCREEN_H - 20)

_quit_clicked = False              # set by the mouse callback
_win_size = (SCREEN_W, SCREEN_H)   # current window size, updated each frame


def _text(img, text, x, y, scale=0.6, color=TEXT, thickness=2, font=FONT_PLAIN):
    """Draw text with its left edge at x and baseline at y."""
    cv2.putText(img, text, (x, y), font, scale, color, thickness)


def _fit_scale(text, max_width, scale, thickness, font):
    """Shrink the font scale if the text would be wider than max_width."""
    width = cv2.getTextSize(text, font, scale, thickness)[0][0]
    if width <= max_width:
        return scale
    return scale * max_width / width


def _centered(img, text, y, scale, color, thickness=2, font=FONT_PLAIN):
    """Draw text centered horizontally in img, with baseline at y."""
    width = cv2.getTextSize(text, font, scale, thickness)[0][0]
    x = (img.shape[1] - width) // 2
    _text(img, text, x, y, scale, color, thickness, font)


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
        img[:] = RED
        for i, line in enumerate(["ANIMAL NEAR ROAD", "SLOW DOWN"]):
            _centered(img, line, 300 + i * 150, 2.5, WHITE, 4, FONT)
    else:
        img = np.full((SCREEN_H, SCREEN_W, 3), 20, dtype=np.uint8)
    cv2.imshow(WINDOW_NAME, img)
    return cv2.waitKey(1) & 0xFF


def _draw_panel(panel, state, status_lines):
    """Paint the status panel. panel is its own PANEL_W x SCREEN_H image."""
    alert = state == "ALERT"
    panel[:] = RED if alert else PANEL_BG

    # Header
    _text(panel, "CROSSING WATCH", PAD, 45, 0.7, TEXT, 2, FONT)
    _text(panel, "Roadside zone monitor", PAD, 72, 0.45, MUTED, 1)

    if alert:
        # Bold warning headline, same size as the original version
        for i, line in enumerate(["ANIMAL", "NEAR ROAD", "SLOW DOWN"]):
            _centered(panel, line, 170 + i * 90, 1.4, WHITE, 3, FONT)
        card_top = 400
    else:
        _text(panel, "All clear", PAD, 140, 0.9, GREEN, 2, FONT)
        card_top = 170

    # Status card: one line per status message
    line_h = 36
    card_h = len(status_lines) * line_h + 24
    card_color = RED_DARK if alert else CARD_BG
    cv2.rectangle(panel, (PAD, card_top), (PANEL_W - PAD, card_top + card_h),
                  card_color, -1)
    max_text_w = PANEL_W - 2 * PAD - 24     # space inside the card
    y = card_top + 32
    for text in status_lines:
        scale = _fit_scale(text, max_text_w, 0.6, 2, FONT_PLAIN)
        _text(panel, text, PAD + 12, y, scale, TEXT, 2)
        y += line_h

    # QUIT button at the bottom
    qx1, qy1, qx2, qy2 = QUIT_PANEL
    cv2.rectangle(panel, (qx1, qy1), (qx2, qy2), CARD_BG, -1)
    cv2.rectangle(panel, (qx1, qy1), (qx2, qy2), MUTED, 2)
    _centered(panel, "QUIT  (or press Q)", qy1 + 32, 0.6, TEXT, 2)


def draw_screen(frame, state, status_lines):
    """Show the camera frame on the left and the status panel on the right.

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

    canvas = np.full((SCREEN_H, SCREEN_W, 3), PANEL_BG, dtype=np.uint8)
    canvas[:, :CAM_W] = cv2.resize(frame, (CAM_W, SCREEN_H))

    panel = np.zeros((SCREEN_H, PANEL_W, 3), dtype=np.uint8)
    _draw_panel(panel, state, status_lines)
    canvas[:, CAM_W:] = panel

    cv2.imshow(WINDOW_NAME, canvas)
    key = cv2.waitKey(1) & 0xFF

    if _quit_clicked:
        _quit_clicked = False
        return ESC
    return key


def close_window():
    cv2.destroyAllWindows()
