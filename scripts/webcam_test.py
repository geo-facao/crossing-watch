"""Webcam test: show a live window and print the frame rate.

Press 'q' in the window to quit.
"""
import time

import cv2

CAMERA_INDEX = 0          # 0 = /dev/video0, the 1080P Pro Stream
WIDTH, HEIGHT = 640, 480  # a smaller frame keeps the Pi fast

# Open the camera using the Video4Linux2 backend (the Linux camera system)
cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

if not cap.isOpened():
    raise SystemExit("Could not open the webcam. Check /dev/video0.")

frames = 0
start = time.time()

while True:
    ok, frame = cap.read()          # grab one frame
    if not ok:
        print("Lost the camera feed.")
        break

    frames += 1
    elapsed = time.time() - start
    if elapsed >= 1.0:              # print FPS once per second
        print(f"FPS: {frames / elapsed:.1f}")
        frames = 0
        start = time.time()

    cv2.imshow("crossing-watch camera test", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):   # quit on 'q'
        break

cap.release()
cv2.destroyAllWindows()
