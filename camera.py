import cv2
import mediapipe as mp
from config import WALL_WIDTH, WALL_HEIGHT

class Camera:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.cap = cv2.VideoCapture(0)  # 노트북 웹캠
        if not self.cap.isOpened():
            raise RuntimeError("Error: Cannot open webcam")
        ret, frame = self.cap.read()
        if ret:
            self.camera_width = frame.shape[1]
            self.camera_height = frame.shape[0]
        else:
            self.camera_width, self.camera_height = 1280, 720

    def get_player_positions(self):
        """손/발 위치 추출"""
        ret, frame = self.cap.read()
        if not ret:
            return []
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(frame_rgb)
        positions = []
        if results.pose_landmarks:
            for idx, landmark in enumerate(results.pose_landmarks.landmark):
                if idx in [15, 16, 27, 28]:  # 왼손, 오른손, 왼발, 오른발
                    x = landmark.x * self.camera_width * (WALL_WIDTH / self.camera_width)
                    y = landmark.y * self.camera_height * (WALL_HEIGHT / self.camera_height)
                    positions.append([x, y])
        return positions

    def get_frame(self):
        """카메라 프레임 반환 (캘리브레이션용)"""
        ret, frame = self.cap.read()
        return frame if ret else None

    def release(self):
        self.cap.release()
        self.pose.close()