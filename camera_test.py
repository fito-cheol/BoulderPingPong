import cv2
import mediapipe as mp
import numpy as np

# 설정값 (킬터보드 크기)
WALL_WIDTH = 3.66  # 킬터보드 너비 (미터)
WALL_HEIGHT = 3.66  # 킬터보드 높이 (미터)

# MediaPipe 초기화
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# 카메라 초기화
cap = cv2.VideoCapture(0)  # 노트북 웹캠
if not cap.isOpened():
    print("Error: Cannot open webcam")
    exit()

# 카메라 해상도 동적 설정
ret, frame = cap.read()
if ret:
    CAMERA_WIDTH = frame.shape[1]
    CAMERA_HEIGHT = frame.shape[0]
else:
    CAMERA_WIDTH, CAMERA_HEIGHT = 1280, 720  # 기본값
    print("Warning: Using default camera resolution (1280x720)")

def draw_landmark_info(frame, landmark_idx, x_m, y_m, pos_y):
    """랜드마크 정보(인덱스, 좌표)를 프레임에 그리기"""
    label = f"Landmark {landmark_idx}: ({x_m:.2f}m, {y_m:.2f}m)"
    cv2.putText(frame, label, (10, pos_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

# 메인 루프
running = True
while running:
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture frame")
        continue

    # 프레임을 RGB로 변환
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(frame_rgb)

    # 프레임에 랜드마크 그리기
    frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
    positions = []
    text_y = 30  # 텍스트 표시 y 위치

    if results.pose_landmarks:
        # 전체 랜드마크 그리기 (참고용)
        mp_drawing.draw_landmarks(
            frame_bgr,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
        )

        # 손/발 위치 추출 (랜드마크 15, 16, 27, 28)
        for idx, landmark in enumerate(results.pose_landmarks.landmark):
            if idx in [15, 16, 27, 28]:
                # 카메라 좌표를 킬터보드 좌표(미터)로 변환
                x_m = landmark.x * CAMERA_WIDTH * (WALL_WIDTH / CAMERA_WIDTH)
                y_m = landmark.y * CAMERA_HEIGHT * (WALL_HEIGHT / CAMERA_HEIGHT)
                positions.append([x_m, y_m])

                # 프레임에 원 그리기 (픽셀 단위)
                x_pixel = int(landmark.x * CAMERA_WIDTH)
                y_pixel = int(landmark.y * CAMERA_HEIGHT)
                color = (0, 0, 255) if idx in [15, 16] else (255, 0, 0)  # 손: 빨강, 발: 파랑
                cv2.circle(frame_bgr, (x_pixel, y_pixel), 10, color, -1)

                # 좌표 정보 표시
                draw_landmark_info(frame_bgr, idx, x_m, y_m, text_y)
                text_y += 30

    # 결과 프레임 표시
    cv2.imshow("Camera Test - Hand/Foot Tracking", frame_bgr)

    # ESC 키로 종료
    if cv2.waitKey(1) & 0xFF == 27:
        running = False

# 종료
cap.release()
pose.close()
cv2.destroyAllWindows()