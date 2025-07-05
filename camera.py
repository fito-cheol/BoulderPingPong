import cv2
import mediapipe as mp
import numpy as np
import time
import os
from config import WALL_WIDTH, WALL_HEIGHT, LANDMARKS_TO_TRACK, MAX_RECONNECT_ATTEMPTS, SCALE_FACTOR

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode


def get_camera_name_windows(index):
    """Windows에서 카메라 이름을 가져오는 함수"""
    try:
        import subprocess
        result = subprocess.run(['powershell', '-Command',
                               'Get-WmiObject -Class Win32_PnPEntity | Where-Object {$_.Name -like "*camera*" -or $_.Name -like "*webcam*"} | Select-Object Name'],
                               capture_output=True, text=True)
        cameras = result.stdout.strip().split('\n')[2:]  # 헤더 제거
        if index < len(cameras):
            return cameras[index].strip()
    except:
        pass
    return "알 수 없는 카메라"

def find_available_cameras():
    """사용 가능한 카메라 찾기"""
    available_cameras = []

    print("카메라 검색 중...")
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)

                # 카메라 이름 가져오기 (Windows용)
                camera_name = get_camera_name_windows(i)
                camera_type = "USB 카메라" if i > 0 else "내장 카메라"

                available_cameras.append({
                    'index': i,
                    'name': camera_name,
                    'type': camera_type,
                    'resolution': f"{width}x{height}",
                    'fps': fps
                })

                print(f"카메라 {i}: {camera_name} - {camera_type} ({width}x{height}, {fps:.1f}fps)")
            cap.release()
        else:
            # 카메라가 열리지 않으면 루프 종료
            if i > 2:  # 처음 몇 개 인덱스는 확인
                break

    return available_cameras


def select_camera():
    """사용자가 카메라 선택"""
    available_cameras = find_available_cameras()

    if not available_cameras:
        raise RuntimeError("사용 가능한 카메라가 없습니다.")

    if len(available_cameras) == 1:
        print(f"카메라 1개 발견: {available_cameras[0]['type']}")
        return available_cameras[0]['index']

    print("\n=== 카메라 선택 ===")
    for i, cam in enumerate(available_cameras):
        print(f"{i + 1}. {cam['type']} - {cam['resolution']}")

    while True:
        try:
            choice = input(f"\n사용할 카메라를 선택하세요 (1-{len(available_cameras)}): ")
            choice_idx = int(choice) - 1

            if 0 <= choice_idx < len(available_cameras):
                selected_camera = available_cameras[choice_idx]
                print(f"\n선택된 카메라: {selected_camera['type']} (인덱스: {selected_camera['index']})")
                return selected_camera['index']
            else:
                print("올바른 번호를 입력하세요.")
        except ValueError:
            print("숫자를 입력하세요.")
        except KeyboardInterrupt:
            print("\n프로그램을 종료합니다.")
            exit()


class Camera:
    def __init__(self, camera_index=None):
        # 카메라 인덱스가 지정되지 않으면 자동 선택
        if camera_index is None:
            camera_index = select_camera()

        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(camera_index)

        if not self.cap.isOpened():
            raise RuntimeError(f"Error: Cannot open camera {camera_index}")

        # 카메라 해상도 설정 시도
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        ret, frame = self.cap.read()
        if ret:
            self.camera_width = frame.shape[1]
            self.camera_height = frame.shape[0]
            print(f"카메라 해상도: {self.camera_width}x{self.camera_height}")
        else:
            self.camera_width, self.camera_height = 1280, 720
            print("Warning: Using default camera resolution (1280x720)")

        self.model_path = r"pose_landmarker_heavy.task"
        if not os.path.exists(self.model_path):
            raise RuntimeError(
                f"Error: Model file not found at {self.model_path}\n"
                "Please download the model from: https://developers.google.com/mediapipe/solutions/vision/pose_landmarker#models"
            )

        options = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=self.model_path),
            running_mode=VisionRunningMode.VIDEO,
            num_poses=2,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.landmarker = PoseLandmarker.create_from_options(options)
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = MAX_RECONNECT_ATTEMPTS

    def reconnect_camera(self):
        """카메라 재연결 시도"""
        print(f"카메라 {self.camera_index} 재연결 시도 중...")
        self.cap.release()
        time.sleep(1)  # 잠깐 대기
        self.cap = cv2.VideoCapture(self.camera_index)
        self.reconnect_attempts += 1

        if self.cap.isOpened():
            # 카메라 설정 재적용
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            print(f"카메라 {self.camera_index} 재연결 성공")
            self.reconnect_attempts = 0
            return True
        else:
            print(f"카메라 {self.camera_index} 재연결 실패")
            return False

    def get_player_positions(self):
        if not self.cap.isOpened():
            if not self.reconnect_camera():
                if self.reconnect_attempts > self.max_reconnect_attempts:
                    print("Error: Max reconnect attempts reached.")
                    return []
                return []

        ret, frame = self.cap.read()
        if not ret or frame is None:
            print("Error: Failed to capture frame")
            return []

        if frame.shape[0] == 0 or frame.shape[1] == 0:
            print("Error: Invalid frame dimensions")
            return []

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        try:
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        except Exception as e:
            print(f"Error creating mp.Image: {e}")
            return []

        timestamp_ms = int(time.time() * 1000)
        try:
            pose_landmarker_result = self.landmarker.detect_for_video(mp_image, timestamp_ms)
        except Exception as e:
            print(f"Error detecting landmarks: {e}")
            return []

        positions = []
        if pose_landmarker_result and pose_landmarker_result.pose_landmarks:
            for person_idx, pose_landmarks in enumerate(pose_landmarker_result.pose_landmarks):
                for idx, landmark in enumerate(pose_landmarks):
                    if idx in LANDMARKS_TO_TRACK:
                        try:
                            x = landmark.x * self.camera_width * (WALL_WIDTH / self.camera_width)
                            y = landmark.y * self.camera_height * (WALL_HEIGHT / self.camera_height)
                            positions.append([x, y])
                        except AttributeError as e:
                            print(f"Error processing landmark {idx} for person {person_idx + 1}: {e}")

        return positions

    def get_frame(self):
        if not self.cap.isOpened():
            if not self.reconnect_camera():
                if self.reconnect_attempts > self.max_reconnect_attempts:
                    print("Error: Max reconnect attempts reached.")
                    return None
                return None

        ret, frame = self.cap.read()
        return frame if ret else None

    def release(self):
        self.cap.release()
        self.landmarker.close()
        cv2.destroyAllWindows()