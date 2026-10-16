"""Full-screen display: a red warning when ALERT, a dark screen when IDLE."""
import cv2
import numpy as np

WINDOW_NAME = "crossing-watch"
SCREEN_W, SCREEN_H = 1280, 720   # size of the screen we draw on


def make_window():
    """Open the window and make it fullscreen on the monitor."""
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)


def draw_state(state):
    """Build the image for the current state and show it."""
    if state == "ALERT":
        # Solid red background with large white text
        img = np.zeros((SCREEN_H, SCREEN_W, 3), dtype=np.uint8)
        img[:] = (0, 0, 200)  # BGR: this is red
        text_lines = ["ANIMAL NEAR ROAD", "SLOW DOWN"]
        y = 300
        for line in text_lines:
            size = cv2.getTextSize(line, cv2.FONT_HERSHEY_DUPLEX, 2.5, 4)[0]
            x = (SCREEN_W - size[0]) // 2   # center the text horizontally
            cv2.putText(img, line, (x, y), cv2.FONT_HERSHEY_DUPLEX, 2.5,
                        (255, 255, 255), 4)
            y += 150
    else:
        # Plain dark screen when nothing is happening
        img = np.full((SCREEN_H, SCREEN_W, 3), 20, dtype=np.uint8)

    cv2.imshow(WINDOW_NAME, img)
    cv2.waitKey(1)


def close_window():
    cv2.destroyAllWindows()
