"""Shows IDLE for 3 seconds, then ALERT for 3 seconds. Press q to quit early."""
import sys
import time
sys.path.insert(0, "src")

import display

display.make_window()
for state in ["IDLE", "ALERT"]:
    display.draw_state(state)
    print("Showing", state)
    end = time.time() + 3
    while time.time() < end:
        display.cv2.waitKey(30)
display.close_window()
