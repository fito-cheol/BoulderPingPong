import cv2
import numpy as np

# Global variables
new_hsv_color = None
frame = None  # Declare frame as global

def pick_color(event, x, y, flags, param):
    """Callback function for mouse click events"""
    global new_hsv_color, frame
    if event == cv2.EVENT_LBUTTONDOWN:
        if frame is None:
            print("Frame not available")
            return
        # Get BGR color value at clicked position
        pixel_bgr = frame[y, x]
        # Convert BGR to HSV
        pixel_hsv = cv2.cvtColor(np.uint8([[pixel_bgr]]), cv2.COLOR_BGR2HSV)[0][0]
        # Store selected HSV color in global variable
        new_hsv_color = pixel_hsv
        print(f"Color picked -> BGR: {pixel_bgr}, HSV: {new_hsv_color}")

def nothing(x):
    """Empty callback function for trackbars"""
    pass

def main():
    global new_hsv_color, frame  # Declare global variables
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera.")
        return

    # Create window for original frame and set mouse callback
    cv2.namedWindow('Original')
    cv2.setMouseCallback('Original', pick_color)

    # Create window for trackbars
    cv2.namedWindow('Trackbars')
    cv2.resizeWindow('Trackbars', 640, 240)

    # Initialize trackbars for HSV range
    cv2.createTrackbar("H Min", "Trackbars", 35, 179, nothing)
    cv2.createTrackbar("S Min", "Trackbars", 80, 255, nothing)
    cv2.createTrackbar("V Min", "Trackbars", 80, 255, nothing)
    cv2.createTrackbar("H Max", "Trackbars", 85, 179, nothing)
    cv2.createTrackbar("S Max", "Trackbars", 255, 255, nothing)
    cv2.createTrackbar("V Max", "Trackbars", 255, 255, nothing)

    while True:
        ret, frame = cap.read()  # Update global frame
        if not ret:
            break

        # Update trackbar values if a new color is picked
        if new_hsv_color is not None:
            h, s, v = new_hsv_color
            # Set approximate range around selected color
            h_min_new = max(0, h - 10)
            h_max_new = min(179, h + 10)
            s_min_new = max(0, s - 50)
            s_max_new = min(255, s + 50)
            v_min_new = max(0, v - 50)
            v_max_new = min(255, v + 50)

            cv2.setTrackbarPos("H Min", "Trackbars", h_min_new)
            cv2.setTrackbarPos("S Min", "Trackbars", s_min_new)
            cv2.setTrackbarPos("V Min", "Trackbars", v_min_new)
            cv2.setTrackbarPos("H Max", "Trackbars", h_max_new)
            cv2.setTrackbarPos("S Max", "Trackbars", s_max_new)
            cv2.setTrackbarPos("V Max", "Trackbars", v_max_new)

            new_hsv_color = None  # Reset after applying

        # Convert frame to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Get current trackbar positions
        h_min = cv2.getTrackbarPos("H Min", "Trackbars")
        s_min = cv2.getTrackbarPos("S Min", "Trackbars")
        v_min = cv2.getTrackbarPos("V Min", "Trackbars")
        h_max = cv2.getTrackbarPos("H Max", "Trackbars")
        s_max = cv2.getTrackbarPos("S Max", "Trackbars")
        v_max = cv2.getTrackbarPos("V Max", "Trackbars")

        # Create mask and result image
        lower = np.array([h_min, s_min, v_min])
        upper = np.array([h_max, s_max, v_max])
        mask = cv2.inRange(hsv, lower, upper)
        result = cv2.bitwise_and(frame, frame, mask=mask)

        # Display windows
        cv2.imshow("Original", frame)
        cv2.imshow("Mask", mask)
        cv2.imshow("Result", result)

        # Print current trackbar values
        print(f"Lower: [{h_min}, {s_min}, {v_min}], Upper: [{h_max}, {s_max}, {v_max}]", end='\r')

        # Exit on ESC key
        if cv2.waitKey(1) & 0xFF == 27:
            break

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()