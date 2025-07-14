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
    return None

def find_available_cameras():
    """사용 가능한 카메라 찾기 (개선된 버전)"""
    available_cameras = []

    print("카메라 검색 중...")
    
    # 더 안전한 검색 범위 설정
    max_camera_index = 4  # 일반적으로 4개 정도면 충분
    
    for i in range(max_camera_index):
        try:
            # 카메라 이름 가져오기 (Windows용)
            camera_name = get_camera_name_windows(i)
            if camera_name is None:
                break;

            available_cameras.append({
                'index': i,
                'name': camera_name,
            })
        except Exception as e:
            print(f"카메라 {i} 검색 중 오류: {e}")
            continue

    return available_cameras

def is_virtual_camera(camera_name):
    """가상 카메라인지 확인"""
    if not camera_name:
        return False
    
    virtual_keywords = [
        'virtual', 'vcam', 'nvidia', 'broadcast', 'obs', 'xsplit',
        'webcamoid', 'manycam', 'splitcam', 'wirecast', 'v4l2loopback',
        'droidcam', 'ivcam', 'epoccam', 'kinect', 'leap motion'
    ]
    
    camera_name_lower = camera_name.lower()
    for keyword in virtual_keywords:
        if keyword in camera_name_lower:
            return True
    
    return False


def select_camera():
    """사용자가 카메라 선택"""
    available_cameras = find_available_cameras()

    if not available_cameras:
        raise RuntimeError("사용 가능한 카메라가 없습니다.")

    if len(available_cameras) == 1:
        return available_cameras[0]['index']

    print("\n=== 카메라 선택 ===")
    for i, cam in enumerate(available_cameras):
        print(f"{cam['index'] + 1}. {cam['name']} ")

    while True:
        try:
            choice = input(f"\n사용할 카메라를 선택하세요 (1-{len(available_cameras)}): ")
            choice_idx = int(choice) - 1

            if 0 <= choice_idx < len(available_cameras):
                selected_camera = available_cameras[choice_idx]
                print(f"\n선택된 카메라: (인덱스: {selected_camera['index']})")
                return selected_camera['index']
            else:
                print("올바른 번호를 입력하세요.")
        except ValueError:
            print("숫자를 입력하세요.")
        except KeyboardInterrupt:
            print("\n프로그램을 종료합니다.")
            exit()


class Camera:
    def __init__(self, camera_index=None, progress_callback=None):
        # 카메라 인덱스가 지정되지 않으면 자동 선택
        if camera_index is None:
            camera_index = select_camera()

        self.camera_index = camera_index
        self.progress_callback = progress_callback
        
        # OpenCV 경고 메시지 억제
        import warnings
        warnings.filterwarnings("ignore", category=UserWarning)
        
        # 더 안전한 카메라 열기
        if self.progress_callback:
            self.progress_callback("카메라 연결 중...")
        
        # 여러 백엔드 시도
        backends = [cv2.CAP_ANY, cv2.CAP_DSHOW, cv2.CAP_MSMF]
        self.cap = None
        
        for backend in backends:
            try:
                self.cap = cv2.VideoCapture(camera_index, backend)
                if self.cap.isOpened():
                    print(f"카메라 {camera_index} 백엔드 {backend}로 연결 성공")
                    break
            except Exception as e:
                print(f"백엔드 {backend} 실패: {e}")
                if self.cap:
                    self.cap.release()
                continue
        
        if not self.cap or not self.cap.isOpened():
            raise RuntimeError(f"Error: Cannot open camera {camera_index} with any backend")
        
        # 타임아웃 설정
        self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 2000)  # 2초 타임아웃
        self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 2000)  # 2초 타임아웃

        # 카메라 해상도 설정 시도
        if self.progress_callback:
            self.progress_callback("카메라 설정 중...")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        # 프레임 읽기 시도 (더 안전한 방법)
        try:
            ret, frame = self.cap.read()
            if ret and frame is not None and frame.size > 0:
                self.camera_width = frame.shape[1]
                self.camera_height = frame.shape[0]
                print(f"카메라 해상도: {self.camera_width}x{self.camera_height}")
            else:
                self.camera_width, self.camera_height = 1280, 720
                print("Warning: Using default camera resolution (1280x720)")
        except Exception as e:
            print(f"Warning: Frame read failed, using default resolution: {e}")
            self.camera_width, self.camera_height = 1280, 720

        # MediaPipe 모델 로딩 최적화
        if self.progress_callback:
            self.progress_callback("AI 모델 로딩 중...")
        model_paths = [
            r"pose_landmarker_lite.task",      # 가장 가벼운 모델
            r"pose_landmarker_full.task",      # 중간 모델
            r"pose_landmarker_heavy.task"      # 가장 무거운 모델
        ]
        
        self.model_path = None
        for model_path in model_paths:
            if os.path.exists(model_path):
                self.model_path = model_path
                print(f"사용할 모델: {model_path}")
                break
        
        if not self.model_path:
            raise RuntimeError(
                f"Error: No model file found. Please download one of the models:\n"
                f"  - pose_landmarker_lite.task (recommended)\n"
                f"  - pose_landmarker_full.task\n"
                f"  - pose_landmarker_heavy.task\n"
                f"From: https://developers.google.com/mediapipe/solutions/vision/pose_landmarker#models"
            )

        # 모델 크기에 따른 설정 조정
        if "lite" in self.model_path:
            confidence_threshold = 0.3  # 가벼운 모델은 더 낮은 임계값
        elif "full" in self.model_path:
            confidence_threshold = 0.4
        else:  # heavy
            confidence_threshold = 0.5

        options = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=self.model_path),
            running_mode=VisionRunningMode.VIDEO,
            num_poses=2,
            min_pose_detection_confidence=confidence_threshold,
            min_pose_presence_confidence=confidence_threshold,
            min_tracking_confidence=confidence_threshold
        )
        
        print("MediaPipe 모델 로딩 중...")
        self.landmarker = PoseLandmarker.create_from_options(options)
        print("MediaPipe 모델 로딩 완료")
        
        if self.progress_callback:
            self.progress_callback("초기화 완료")
        
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = MAX_RECONNECT_ATTEMPTS

    def reconnect_camera(self):
        """카메라 재연결 시도"""
        print(f"카메라 {self.camera_index} 재연결 시도 중...")
        self.cap.release()
        time.sleep(1)  # 잠깐 대기
        
        # 여러 백엔드로 재연결 시도
        backends = [cv2.CAP_ANY, cv2.CAP_DSHOW, cv2.CAP_MSMF]
        
        for backend in backends:
            try:
                self.cap = cv2.VideoCapture(self.camera_index, backend)
                if self.cap.isOpened():
                    # 카메라 설정 재적용
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                    self.cap.set(cv2.CAP_PROP_FPS, 30)
                    print(f"카메라 {self.camera_index} 백엔드 {backend}로 재연결 성공")
                    self.reconnect_attempts = 0
                    return True
            except Exception as e:
                print(f"백엔드 {backend} 재연결 실패: {e}")
                if self.cap:
                    self.cap.release()
                continue
        
        print(f"카메라 {self.camera_index} 재연결 실패")
        self.reconnect_attempts += 1
        return False

    def get_player_positions(self):
        if not self.cap.isOpened():
            if not self.reconnect_camera():
                if self.reconnect_attempts > self.max_reconnect_attempts:
                    print("Error: Max reconnect attempts reached.")
                    return []
                return []

        try:
            ret, frame = self.cap.read()
            if not ret or frame is None or frame.size == 0:
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
            
        except Exception as e:
            print(f"Error in get_player_positions: {e}")
            return []

    def get_full_pose_data(self):
        """전체 포즈 데이터를 반환하는 메서드 (Godot 연동용)"""
        if not self.cap.isOpened():
            if not self.reconnect_camera():
                if self.reconnect_attempts > self.max_reconnect_attempts:
                    return []
                return []

        try:
            ret, frame = self.cap.read()
            if not ret or frame is None or frame.size == 0:
                return []

            if frame.shape[0] == 0 or frame.shape[1] == 0:
                return []

            # 검색 범위 적용 (외곽 부분 제외)
            if hasattr(self, 'search_margin_x') and hasattr(self, 'search_margin_y'):
                height, width = frame.shape[:2]
                margin_x = int(width * self.search_margin_x)
                margin_y = int(height * self.search_margin_y)
                
                # 검색 범위 내의 프레임만 사용
                frame = frame[margin_y:height-margin_y, margin_x:width-margin_x]
                
                if frame.size == 0:
                    return []

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            try:
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            except Exception as e:
                return []

            timestamp_ms = int(time.time() * 1000)
            try:
                pose_landmarker_result = self.landmarker.detect_for_video(mp_image, timestamp_ms)
            except Exception as e:
                return []

            players_data = []
            if pose_landmarker_result and pose_landmarker_result.pose_landmarks:
                for person_idx, pose_landmarks in enumerate(pose_landmarker_result.pose_landmarks):
                    player_data = {
                        'landmarks': {},
                        'hands': [],
                        'feet': [],
                        'head': {},
                        'body': {}
                    }
                    
                    # 모든 랜드마크 처리
                    for idx, landmark in enumerate(pose_landmarks):
                        try:
                            # 원본 카메라 좌표 (0-1 범위)
                            x = landmark.x
                            y = landmark.y
                            z = getattr(landmark, 'z', 0.0)
                            visibility = getattr(landmark, 'visibility', 0.0)
                            presence = getattr(landmark, 'presence', 0.0)
                            
                            # 검색 범위가 적용된 경우 좌표를 원본 크기에 맞게 조정
                            if hasattr(self, 'search_margin_x') and hasattr(self, 'search_margin_y'):
                                original_height, original_width = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT), self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                                margin_x = original_width * self.search_margin_x
                                margin_y = original_height * self.search_margin_y
                                
                                # 좌표를 원본 프레임 크기에 맞게 조정
                                x = (x * (original_width - 2 * margin_x) + margin_x) / original_width
                                y = (y * (original_height - 2 * margin_y) + margin_y) / original_height
                            
                            # 좌표를 0-1 범위로 클램핑
                            x = max(0.0, min(1.0, x))
                            y = max(0.0, min(1.0, y))
                            
                            landmark_data = {
                                'x': x,
                                'y': y,
                                'z': z,
                                'visibility': visibility,
                                'presence': presence,
                                'landmark_index': idx
                            }
                            
                            # 랜드마크 타입별로 분류
                            if idx in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:  # 머리
                                player_data['head'][idx] = landmark_data
                            elif idx in [11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]:  # 팔
                                if idx == 15:  # 왼쪽 손목
                                    # visibility가 0.1 이상인 경우만 추가
                                    if visibility > 0.1:
                                        landmark_data['side'] = 'left'
                                        player_data['hands'].append(landmark_data)
                                elif idx == 16:  # 오른쪽 손목
                                    # visibility가 0.1 이상인 경우만 추가
                                    if visibility > 0.1:
                                        landmark_data['side'] = 'right'
                                        player_data['hands'].append(landmark_data)
                            elif idx in [23, 24, 25, 26, 27, 28, 29, 30, 31, 32]:  # 다리
                                if idx == 27:  # 왼쪽 발목
                                    # visibility가 0.05 이상인 경우만 추가
                                    if visibility > 0.05:
                                        landmark_data['side'] = 'left'
                                        player_data['feet'].append(landmark_data)
                                elif idx == 28:  # 오른쪽 발목
                                    # visibility가 0.05 이상인 경우만 추가
                                    if visibility > 0.05:
                                        landmark_data['side'] = 'right'
                                        player_data['feet'].append(landmark_data)
                                else:
                                    player_data['body'][idx] = landmark_data
                            else:
                                player_data['body'][idx] = landmark_data
                                
                        except AttributeError as e:
                            continue
                    
                    players_data.append(player_data)

            return players_data
            
        except Exception as e:
            print(f"Error in get_full_pose_data: {e}")
            return []

    def get_frame(self):
        if not self.cap.isOpened():
            if not self.reconnect_camera():
                if self.reconnect_attempts > self.max_reconnect_attempts:
                    print("Error: Max reconnect attempts reached.")
                    return None
                return None

        try:
            ret, frame = self.cap.read()
            if ret and frame is not None and frame.size > 0:
                return frame
            else:
                return None
        except Exception as e:
            print(f"Error in get_frame: {e}")
            return None

    def release(self):
        self.cap.release()
        self.landmarker.close()
        cv2.destroyAllWindows()