import cv2
import numpy as np
import pygame
from config import CHESSBOARD_SIZE, SQUARE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT, WALL_WIDTH, WALL_HEIGHT

def calibrate_projector(camera, screen):
    """체스보드 패턴으로 호모그래피 행렬 계산"""
    # 체스보드의 실제 좌표 (미터 단위)
    obj_points = np.zeros((CHESSBOARD_SIZE[0] * CHESSBOARD_SIZE[1], 2), np.float32)
    for i in range(CHESSBOARD_SIZE[1]):
        for j in range(CHESSBOARD_SIZE[0]):
            obj_points[i * CHESSBOARD_SIZE[0] + j] = [j * SQUARE_SIZE, i * SQUARE_SIZE]

    # 체스보드 패턴 투영
    chessboard = np.zeros((SCREEN_HEIGHT, SCREEN_WIDTH, 3), dtype=np.uint8)
    for i in range(CHESSBOARD_SIZE[1]):
        for j in range(CHESSBOARD_SIZE[0]):
            if (i + j) % 2 == 0:
                x1 = int(j * SCREEN_WIDTH / CHESSBOARD_SIZE[0])
                y1 = int(i * SCREEN_HEIGHT / CHESSBOARD_SIZE[1])
                x2 = int((j + 1) * SCREEN_WIDTH / CHESSBOARD_SIZE[0])
                y2 = int((i + 1) * SCREEN_HEIGHT / CHESSBOARD_SIZE[1])
                pygame.draw.rect(screen, (255, 255, 255), (x1, y1, x2 - x1, y2 - y1))
    pygame.display.flip()

    print("Please point the camera at the projected chessboard and press 'c' to capture.")
    captured = False
    while not captured:
        frame = camera.get_frame()
        if frame is None:
            continue
        cv2.imshow("Calibration", frame)
        if cv2.waitKey(1) & 0xFF == ord('c'):
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            ret, corners = cv2.findChessboardCorners(gray, CHESSBOARD_SIZE, None)
            if ret:
                corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1),
                                          criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
                src_points = corners.reshape(-1, 2)
                dst_points = obj_points * np.array([SCREEN_WIDTH / WALL_WIDTH, SCREEN_HEIGHT / WALL_HEIGHT])
                homography, _ = cv2.findHomography(src_points, dst_points)
                captured = True
            else:
                print("Chessboard not detected. Try again.")
    cv2.destroyAllWindows()
    return homography