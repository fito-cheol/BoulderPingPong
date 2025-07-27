import cv2
import time
import numpy as np
from typing import List, Dict, Optional, Callable, Any
from .config_manager import CameraConfig
from .camera_manager import CameraManager
from .pose_processor import PoseProcessor
import threading
from queue import Queue

class Camera:
    """Integrates camera capture and pose detection with multithreading."""
    def __init__(self, config: CameraConfig = CameraConfig(), camera_index: Optional[int] = None,
                 progress_callback: Optional[Callable] = None):
        """Initialize camera and pose landmarker.

        Args:
            config: Configuration for camera and pose detection.
            camera_index: Camera index, auto-select if None.
            progress_callback: Optional callback for progress updates.
        """
        self.config = config
        self.camera_manager = CameraManager(config, camera_index, progress_callback)
        self.pose_processor = PoseProcessor(config, progress_callback)
        self.progress_callback = progress_callback
        self.running = False
        self.processed_data = None
        self.processed_data_lock = threading.Lock()
        self.frame_queue = Queue(maxsize=1)  # Limit queue size to avoid memory issues
        self.result_queue = Queue(maxsize=1)
        self.thread = None
        if self.progress_callback:
            self.progress_callback("Initialization complete")

    def start_processing(self):
        """Start the pose processing thread."""
        self.running = True
        self.thread = threading.Thread(target=self._process_frames, daemon=True)
        self.thread.start()

    def _process_frames(self):
        """카메라 프레임을 별도의 스레드에서 처리하는 메서드"""
        while self.running:  # 카메라 처리 루프가 실행 중일 때 반복
            # 카메라 연결 상태 확인
            if not self.camera_manager.camera.isOpened():
                # 카메라가 연결되어 있지 않으면 재연결 시도
                if not self.camera_manager.reconnect_camera():
                    # 재연결 실패 시 최대 재연결 시도 횟수 확인
                    if self.camera_manager.reconnect_attempts > self.config.max_reconnect_attempts:
                        print("오류: 최대 재연결 시도 횟수 초과")
                        time.sleep(0.1)  # 과도한 CPU 사용 방지를 위해 0.1초 대기
                        continue
                continue

            # 카메라에서 프레임 가져오기
            frame = self.camera_manager.get_frame()
            if frame is None:
                print("오류: 프레임 캡처 실패")
                time.sleep(0.01)  # 짧은 대기 후 다음 프레임 처리
                continue

            # 프레임 크기 유효성 검사
            if frame.shape[0] == 0 or frame.shape[1] == 0:
                print("오류: 잘못된 프레임 크기")
                time.sleep(0.01)  # 짧은 대기 후 다음 프레임 처리
                continue

            # 검색 마진 적용
            if self.config.search_margin_x > 0 or self.config.search_margin_y > 0:
                # 프레임의 높이와 너비 가져오기
                height, width = frame.shape[:2]
                # x축 마진 크기 계산 (프레임 너비에 마진 비율 곱하기)
                margin_x = int(width * self.config.search_margin_x)
                # y축 마진 크기 계산 (프레임 높이에 마진 비율 곱하기)
                margin_y = int(height * self.config.search_margin_y)
                # 프레임의 상하좌우에서 마진만큼 잘라내기
                frame = frame[margin_y:height - margin_y, margin_x:width - margin_x]
                # 자른 프레임이 유효한지 확인
                if frame.size == 0:
                    print("오류: 마진 적용 후 잘못된 프레임")
                    time.sleep(0.01)  # 짧은 대기 후 다음 프레임 처리
                    continue

            timestamp_ms = int(time.time() * 1000)
            result = self.pose_processor.process_frame(frame, timestamp_ms)

            # Store result in queue
            try:
                if not self.result_queue.empty():
                    self.result_queue.get_nowait()  # Clear old result
                self.result_queue.put((frame, result))
            except Exception as e:
                print(f"Error queuing result: {e}")
                continue

    def _capture_and_process_frame(self) -> tuple[Optional[np.ndarray], Optional[Any]]:
        """Retrieve the latest processed frame and result."""
        try:
            if not self.result_queue.empty():
                frame, result = self.result_queue.get_nowait()
                with self.processed_data_lock:
                    self.processed_data = (frame, result)
            return self.processed_data
        except Exception as e:
            print(f"Error retrieving processed data: {e}")
            return None, None

    def get_player_positions(self) -> List[List[float]]:
        """Get normalized [x, y] coordinates of tracked landmarks.

        Returns:
            List of [x, y] coordinates for tracked landmarks.
        """
        frame, result = self._capture_and_process_frame()
        if not result or not result.pose_landmarks:
            return []

        positions = []
        for pose_landmarks in result.pose_landmarks:
            for idx, landmark in enumerate(pose_landmarks):
                if idx in self.config.landmarks_to_track:
                    positions.append([landmark.x, landmark.y])
        return positions

    def get_full_pose_data(self) -> List[Dict[str, Any]]:
        """Get full pose data for all detected persons.

        Returns:
            List of dictionaries containing pose data (head, hands, feet, body).
        """
        frame, result = self._capture_and_process_frame()
        if not result or not result.pose_landmarks:
            return []

        original_width = self.camera_manager.camera_width
        original_height = self.camera_manager.camera_height
        margin_x = self.config.search_margin_x * original_width
        margin_y = self.config.search_margin_y * original_height
        width = original_width - 2 * margin_x
        height = original_height - 2 * margin_y

        players_data = []
        for pose_landmarks in result.pose_landmarks:
            player_data = self.pose_processor.process_pose_landmarks(pose_landmarks)
            if margin_x > 0 or margin_y > 0:
                for section in ['head', 'hands', 'feet', 'body']:
                    if section == 'hands' or section == 'feet':
                        for item in player_data[section]:
                            item['x'] = (item['x'] * width + margin_x) / original_width
                            item['y'] = (item['y'] * height + margin_y) / original_height
                    else:
                        for idx, data in player_data[section].items():
                            data['x'] = (data['x'] * width + margin_x) / original_width
                            data['y'] = (data['y'] * height + margin_y) / original_height
            players_data.append(player_data)
        return players_data

    def get_frame(self) -> Optional[np.ndarray]:
        """Get the raw camera frame."""
        return self.camera_manager.get_frame()

    def release(self) -> None:
        """Release all resources."""
        self.running = False
        if self.thread is not None:
            self.thread.join(timeout=1.0)
        self.camera_manager.release()
        self.pose_processor.close()
        cv2.destroyAllWindows()