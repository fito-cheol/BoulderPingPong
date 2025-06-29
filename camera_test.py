import cv2
import mediapipe as mp
import numpy as np
import time
import os

# 설정값 (킬터보드 크기)
WALL_WIDTH = 3.66  # 킬터보드 너비 (미터)
WALL_HEIGHT = 3.66  # 킬터보드 높이 (미터)

# MediaPipe 초기화
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# POSE_CONNECTIONS 정의 (PoseLandmarker와 호환되도록)
POSE_CONNECTIONS = mp.solutions.pose.POSE_CONNECTIONS

def initialize_camera():
    """카메라 초기화 및 해상도 설정"""
    cap = cv2.VideoCapture(0)  # 노트북 웹캠
    if not cap.isOpened():
        print("Error: Cannot open webcam")
        return None, None, None
    ret, frame = cap.read()
    if ret:
        camera_width = frame.shape[1]
        camera_height = frame.shape[0]
    else:
        camera_width, camera_height = 1280, 720  # 기본값
        print("Warning: Using default camera resolution (1280x720)")
    return cap, camera_width, camera_height

def draw_landmark_info(frame, person_idx, landmark_idx, x_m, y_m, pos_y):
    """랜드마크 정보(인덱스, 좌표)를 프레임에 그리기"""
    label = f"Person {person_idx} Landmark {landmark_idx}: ({x_m:.2f}m, {y_m:.2f}m)"
    cv2.putText(frame, label, (10, pos_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

def main():
    # 초기 카메라 설정
    cap, CAMERA_WIDTH, CAMERA_HEIGHT = initialize_camera()
    if cap is None:
        print("Failed to initialize camera. Exiting...")
        return

    # PoseLandmarker 모델 경로 설정
    model_path = r"C:\Users\USER\PycharmProjects\BoulderPingPong\pose_landmarker_full.task"

    # 모델 파일 존재 여부 확인
    if not os.path.exists(model_path):
        print(f"Error: Model file not found at {model_path}")
        print("Please download the model from: https://developers.google.com/mediapipe/solutions/vision/pose_landmarker#models")
        return

    # PoseLandmarker 옵션 설정
    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=VisionRunningMode.VIDEO,
        num_poses=2,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5
    )

    # PoseLandmarker 초기화
    try:
        with PoseLandmarker.create_from_options(options) as landmarker:
            running = True
            reconnect_attempts = 0
            max_reconnect_attempts = 5

            while running:
                # 카메라 연결 확인 및 재연결 시도
                if not cap.isOpened():
                    print("Error: Camera disconnected, attempting to reconnect...")
                    cap.release()
                    cap, CAMERA_WIDTH, CAMERA_HEIGHT = initialize_camera()
                    reconnect_attempts += 1
                    if reconnect_attempts > max_reconnect_attempts:
                        print("Error: Max reconnect attempts reached. Exiting...")
                        break
                    if cap is None:
                        print("Error: Reconnection failed. Retrying in 2 seconds...")
                        time.sleep(2)
                        continue
                    reconnect_attempts = 0

                ret, frame = cap.read()
                if not ret or frame is None:
                    print("Error: Failed to capture frame")
                    cap.release()
                    cap, CAMERA_WIDTH, CAMERA_HEIGHT = initialize_camera()
                    reconnect_attempts += 1
                    if reconnect_attempts > max_reconnect_attempts:
                        print("Error: Max reconnect attempts reached. Exiting...")
                        break
                    if cap is None:
                        print("Error: Reconnection failed. Retrying in 2 seconds...")
                        time.sleep(2)
                        continue
                    continue

                # 프레임 크기 확인
                if frame.shape[0] == 0 or frame.shape[1] == 0:
                    print("Error: Invalid frame dimensions")
                    continue

                # 프레임을 RGB로 변환 및 MediaPipe 이미지 객체로 변환
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                try:
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
                except Exception as e:
                    print(f"Error creating mp.Image: {e}")
                    continue

                timestamp_ms = int(time.time() * 1000)  # 안정적인 타임스탬프

                # 포즈 랜드마크 감지
                try:
                    pose_landmarker_result = landmarker.detect_for_video(mp_image, timestamp_ms)
                except Exception as e:
                    print(f"Error detecting landmarks: {e}")
                    continue

                # 프레임에 랜드마크 그리기
                frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                text_y = 30

                # 랜드마크 처리
                if pose_landmarker_result and pose_landmarker_result.pose_landmarks:
                    print(f"Detected {len(pose_landmarker_result.pose_landmarks)} person(s)")
                    for person_idx, pose_landmarks in enumerate(pose_landmarker_result.pose_landmarks):
                        # 랜드마크 데이터 구조 디버깅
                        print(f"Person {person_idx + 1} landmarks: {pose_landmarks}")
                        try:
                            # 랜드마크 그리기
                            mp_drawing.draw_landmarks(
                                frame_bgr,
                                pose_landmarks,
                                POSE_CONNECTIONS,
                                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
                            )
                        except Exception as e:
                            print(f"Error drawing landmarks for person {person_idx + 1}: {e}")
                            # 대체 렌더링: 수동으로 랜드마크 점 그리기
                            for idx, landmark in enumerate(pose_landmarks):
                                if idx in [15, 16, 27, 28]:  # 손/발 랜드마크
                                    try:
                                        x_pixel = int(landmark.x * CAMERA_WIDTH)
                                        y_pixel = int(landmark.y * CAMERA_HEIGHT)
                                        color = (0, 0, 255) if idx in [15, 16] else (255, 0, 0)
                                        cv2.circle(frame_bgr, (x_pixel, y_pixel), 10, color, -1)
                                    except AttributeError as ae:
                                        print(f"Invalid landmark {idx} for person {person_idx + 1}: {ae}")
                                        continue

                        # 손/발 위치 추출
                        for idx, landmark in enumerate(pose_landmarks):
                            if idx in [15, 16, 27, 28]:
                                try:
                                    x_m = landmark.x * CAMERA_WIDTH * (WALL_WIDTH / CAMERA_WIDTH)
                                    y_m = landmark.y * CAMERA_HEIGHT * (WALL_HEIGHT / CAMERA_HEIGHT)
                                    x_pixel = int(landmark.x * CAMERA_WIDTH)
                                    y_pixel = int(landmark.y * CAMERA_HEIGHT)
                                    color = (0, 0, 255) if idx in [15, 16] else (255, 0, 0)
                                    cv2.circle(frame_bgr, (x_pixel, y_pixel), 10, color, -1)
                                    draw_landmark_info(frame_bgr, person_idx + 1, idx, x_m, y_m, text_y)
                                    text_y += 30
                                except AttributeError as e:
                                    print(f"Error processing landmark {idx} for person {person_idx + 1}: {e}")
                                    continue
                else:
                    print("No landmarks detected in this frame")

                # 결과 프레임 표시
                cv2.imshow("Camera Test - Multi-Person Hand/Foot Tracking", frame_bgr)

                # ESC 키로 종료
                if cv2.waitKey(1) & 0xFF == 27:
                    running = False

    except Exception as e:
        print(f"Error initializing PoseLandmarker: {e}")
        return

    # 종료
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()