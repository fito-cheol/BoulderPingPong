import cv2
import numpy as np
import pygame
from typing import Optional, Tuple
from config import CHESSBOARD_SIZE, SQUARE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT, WALL_WIDTH, WALL_HEIGHT
from PIL import Image, ImageDraw, ImageFont
import os

# 상수 정의
MAX_ATTEMPTS = 10  # 최대 캘리브레이션 시도 횟수
DELAY_MS = 33  # 프레임 지연 시간 (밀리초) - 약 30 FPS
FONT_SCALE = 0.7  # 텍스트 폰트 크기
FONT_THICKNESS = 2  # 텍스트 두께
SMALL_FONT_SCALE = 0.5  # 작은 텍스트 폰트 크기
TEXT_COLOR_GREEN = (0, 255, 0)  # 초록색 텍스트 색상
TEXT_COLOR_RED = (0, 0, 255)  # 빨간색 텍스트 색상
TEXT_COLOR_WHITE = (255, 255, 255)  # 흰색 텍스트 색상
CORNER_SUBPIX_WINDOW = (11, 11)  # 코너 정밀화 윈도우 크기
CORNER_SUBPIX_ZERO_ZONE = (-1, -1)  # 코너 정밀화 제로 존
CORNER_SUBPIX_CRITERIA = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)  # 코너 정밀화 기준


def create_chessboard_points() -> np.ndarray:
    """체스보드의 실제 좌표를 생성 (미터 단위)"""
    obj_points = np.zeros((CHESSBOARD_SIZE[0] * CHESSBOARD_SIZE[1], 2), np.float32)
    for i in range(CHESSBOARD_SIZE[1]):
        for j in range(CHESSBOARD_SIZE[0]):
            obj_points[i * CHESSBOARD_SIZE[0] + j] = [j * SQUARE_SIZE, i * SQUARE_SIZE]
    return obj_points


def draw_chessboard_pattern(screen: pygame.Surface) -> None:
    """프로젝터 화면에 체스보드 패턴을 그림"""
    screen.fill((0, 0, 0))  # 화면을 검은색으로 초기화
    cell_width = SCREEN_WIDTH // CHESSBOARD_SIZE[0]  # 셀 너비 계산
    cell_height = SCREEN_HEIGHT // CHESSBOARD_SIZE[1]  # 셀 높이 계산

    for i in range(CHESSBOARD_SIZE[1]):
        for j in range(CHESSBOARD_SIZE[0]):
            if (i + j) % 2 == 0:
                x1, y1 = j * cell_width, i * cell_height
                x2, y2 = (j + 1) * cell_width, (i + 1) * cell_height
                pygame.draw.rect(screen, (255, 255, 255), (x1, y1, x2 - x1, y2 - y1))

    pygame.display.flip()  # 화면 업데이트


def display_instructions() -> None:
    """콘솔에 캘리브레이션 지침 출력"""
    print("=== 캘리브레이션 모드 ===")
    print("체스보드 패턴이 투영되었습니다.")
    print("카메라 창에서 다음 키를 눌러주세요:")
    print("'c' - 캘리브레이션 시도")
    print("'s' - 캘리브레이션 건너뛰기 (기본 호모그래피 사용)")
    print("'ESC' - 프로그램 종료")
    print("")
    print("=== 검색 범위 설정 ===")
    print("방향키: 검색 범위 조정 (외곽 부분 제외)")
    print("D/F: Detection 신뢰도 조정")
    print("P/O: Presence 신뢰도 조정")
    print("=====================================")


def process_camera_frame(camera, frame: np.ndarray) -> Tuple[bool, Optional[np.ndarray]]:
    """카메라 프레임에서 체스보드 코너를 검출"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(gray, CHESSBOARD_SIZE, None)

    if ret:
        corners = cv2.cornerSubPix(gray, corners, CORNER_SUBPIX_WINDOW,
                                   CORNER_SUBPIX_ZERO_ZONE, CORNER_SUBPIX_CRITERIA)
    return ret, corners


def create_default_homography() -> np.ndarray:
    """화면과 벽 치수를 기반으로 기본 호모그래피 행렬 생성"""
    src_points = np.float32([
        [0, 0],
        [WALL_WIDTH, 0],
        [WALL_WIDTH, WALL_HEIGHT],
        [0, WALL_HEIGHT]
    ])
    dst_points = np.float32([
        [0, 0],
        [SCREEN_WIDTH, 0],
        [SCREEN_WIDTH, SCREEN_HEIGHT],
        [0, SCREEN_HEIGHT]
    ])

    try:
        homography = cv2.getPerspectiveTransform(src_points, dst_points)
        print("기본 호모그래피 행렬 생성 완료")
        return homography
    except Exception as e:
        print(f"기본 호모그래피 생성 실패: {e}")
        return np.eye(3, dtype=np.float32)


def calculate_homography(corners: np.ndarray, obj_points: np.ndarray) -> Optional[np.ndarray]:
    """검출된 코너에서 호모그래피 행렬 계산"""
    src_points = corners.reshape(-1, 2)
    dst_points = obj_points * np.array([SCREEN_WIDTH / WALL_WIDTH, SCREEN_HEIGHT / WALL_HEIGHT])
    homography, _ = cv2.findHomography(src_points, dst_points, cv2.RANSAC, 5.0)
    return homography


def put_korean_text(img: np.ndarray, text: str, position: Tuple[int, int], 
                   font_size: int = 24, color: Tuple[int, int, int] = (255, 255, 255)) -> np.ndarray:
    """한글 텍스트를 이미지에 그리는 함수"""
    try:
        # PIL Image로 변환
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_img)
        
        # 한글 폰트 로드
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("C:/Windows/Fonts/gulim.ttc", font_size)
            except:
                try:
                    font = ImageFont.truetype("C:/Windows/Fonts/batang.ttc", font_size)
                except:
                    # 폰트를 찾을 수 없으면 기본 폰트 사용
                    font = ImageFont.load_default()
        
        # 텍스트 그리기
        draw.text(position, text, font=font, fill=color)
        
        # OpenCV 형식으로 변환
        result = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        return result
        
    except Exception as e:
        print(f"한글 텍스트 그리기 실패: {e}")
        # 실패하면 기본 OpenCV 텍스트 사용
        cv2.putText(img, text, position, cv2.FONT_HERSHEY_SIMPLEX, 
                    font_size/24, color, 2)
        return img


def update_search_settings(camera, search_margin_x: float, search_margin_y: float,
                         detection_confidence: float, presence_confidence: float, tracking_confidence: float) -> None:
    """검색 범위 설정 업데이트"""
    try:
        if hasattr(camera, 'landmarker'):
            # 새로운 설정으로 landmarker 재생성
            from camera import PoseLandmarkerOptions, BaseOptions, VisionRunningMode
            
            options = PoseLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=camera.model_path),
                running_mode=VisionRunningMode.VIDEO,
                num_poses=2,
                min_pose_detection_confidence=detection_confidence,
                min_pose_presence_confidence=presence_confidence,
                min_tracking_confidence=tracking_confidence
            )
            
            # 기존 landmarker 종료
            camera.landmarker.close()
            
            # 새로운 landmarker 생성
            from camera import PoseLandmarker
            camera.landmarker = PoseLandmarker.create_from_options(options)
            
            # 검색 범위 설정을 camera 객체에 저장
            camera.search_margin_x = search_margin_x
            camera.search_margin_y = search_margin_y
            
            print(f"검색 범위 업데이트: X여백={search_margin_x:.2f}, Y여백={search_margin_y:.2f}")
            print(f"Detection={detection_confidence:.1f}, Presence={presence_confidence:.1f}, Tracking={tracking_confidence:.1f}")
            
    except Exception as e:
        print(f"검색 범위 설정 업데이트 실패: {e}")


def display_camera_feed(frame: np.ndarray, corners_detected: bool) -> None:
    """카메라 피드에 오버레이 텍스트와 검출된 코너를 표시"""
    if corners_detected:
        cv2.drawChessboardCorners(frame, CHESSBOARD_SIZE, corners, True)
        frame = put_korean_text(frame, "체스보드 검출됨! 'c'를 눌러 캘리브레이션",
                               (10, 30), 24, (0, 255, 0))
    else:
        frame = put_korean_text(frame, "카메라를 체스보드가 보이도록 조정",
                               (10, 30), 24, (0, 0, 255))

    frame = put_korean_text(frame, "c: 캘리브레이션, s: 건너뛰기, ESC: 종료",
                           (10, frame.shape[0] - 30), 18, (255, 255, 255))
    cv2.imshow("캘리브레이션 - 카메라 뷰", frame)


def display_camera_feed_with_settings(frame: np.ndarray, corners_detected: bool,
                                    search_margin_x: float, search_margin_y: float,
                                    detection_confidence: float, presence_confidence: float, tracking_confidence: float,
                                    camera=None) -> None:
    """설정 정보와 함께 카메라 피드 표시 (포즈 인식 마크 포함)"""
    # 검색 범위 표시 (사각형 그리기)
    height, width = frame.shape[:2]
    margin_x = int(width * search_margin_x)
    margin_y = int(height * search_margin_y)
    
    # 검색 범위 사각형 그리기
    cv2.rectangle(frame, (margin_x, margin_y), (width - margin_x, height - margin_y), (0, 255, 255), 2)
    
    # 포즈 인식 마크 추가
    if camera and hasattr(camera, 'landmarker'):
        try:
            pose_data = camera.get_full_pose_data()
            if pose_data:
                for player in pose_data:
                    # 손 마크 (파란색 - 왼쪽, 빨간색 - 오른쪽)
                    if 'hands' in player:
                        for hand in player['hands']:
                            if 'x' in hand and 'y' in hand:
                                x = int(hand['x'] * width)
                                y = int(hand['y'] * height)
                                if 'side' in hand:
                                    if hand['side'] == 'left':
                                        # 왼쪽 손 - 파란색 원
                                        cv2.circle(frame, (x, y), 15, (255, 0, 0), -1)  # 파란색
                                        cv2.circle(frame, (x, y), 15, (255, 255, 255), 2)  # 흰색 테두리
                                        cv2.putText(frame, "L", (x-5, y+5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                                    elif hand['side'] == 'right':
                                        # 오른쪽 손 - 빨간색 원
                                        cv2.circle(frame, (x, y), 15, (0, 0, 255), -1)  # 빨간색
                                        cv2.circle(frame, (x, y), 15, (255, 255, 255), 2)  # 흰색 테두리
                                        cv2.putText(frame, "R", (x-5, y+5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    
                    # 발 마크 (초록색 - 왼쪽, 노란색 - 오른쪽)
                    if 'feet' in player:
                        for foot in player['feet']:
                            if 'x' in foot and 'y' in foot:
                                x = int(foot['x'] * width)
                                y = int(foot['y'] * height)
                                if 'side' in foot:
                                    if foot['side'] == 'left':
                                        # 왼쪽 발 - 초록색 사각형
                                        cv2.rectangle(frame, (x-10, y-10), (x+10, y+10), (0, 255, 0), -1)  # 초록색
                                        cv2.rectangle(frame, (x-10, y-10), (x+10, y+10), (255, 255, 255), 2)  # 흰색 테두리
                                        cv2.putText(frame, "L", (x-5, y+5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                                    elif foot['side'] == 'right':
                                        # 오른쪽 발 - 노란색 사각형
                                        cv2.rectangle(frame, (x-10, y-10), (x+10, y+10), (0, 255, 255), -1)  # 노란색
                                        cv2.rectangle(frame, (x-10, y-10), (x+10, y+10), (255, 255, 255), 2)  # 흰색 테두리
                                        cv2.putText(frame, "R", (x-5, y+5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        except Exception as e:
            print(f"포즈 마크 그리기 실패: {e}")
    
    if corners_detected:
        cv2.drawChessboardCorners(frame, CHESSBOARD_SIZE, corners, True)
        frame = put_korean_text(frame, "체스보드 검출됨! 'c'를 눌러 캘리브레이션",
                               (10, 30), 24, (0, 255, 0))
    else:
        frame = put_korean_text(frame, "카메라를 체스보드가 보이도록 조정",
                               (10, 30), 24, (0, 0, 255))

    # 설정 정보 표시
    settings_text = [
        f"검색 범위: X여백={search_margin_x:.2f}, Y여백={search_margin_y:.2f}",
        f"Detection: {detection_confidence:.1f} (D/F)",
        f"Presence: {presence_confidence:.1f} (P/O)",
        f"조작법: 방향키(검색범위), D/F(Detection), P/O(Presence)",
        f"c: 캘리브레이션, s: 건너뛰기, ESC: 종료"
    ]
    
    for i, text in enumerate(settings_text):
        frame = put_korean_text(frame, text, (10, frame.shape[0] - 150 + i * 25), 16, (255, 255, 255))
    
    cv2.imshow("캘리브레이션 - 카메라 뷰", frame)


def calibrate_projector(camera, screen: pygame.Surface) -> Optional[np.ndarray]:
    """체스보드 패턴을 사용해 프로젝터를 캘리브레이션하여 호모그래피 행렬 계산"""
    obj_points = create_chessboard_points()
    draw_chessboard_pattern(screen)
    display_instructions()

    attempt_count = 0
    captured = False
    skipped = False
    
    # 검색 범위 설정 변수
    search_margin_x = 0.1  # 좌우 여백 (0.1 = 10%)
    search_margin_y = 0.1  # 상하 여백 (0.1 = 10%)
    detection_confidence = 0.5
    presence_confidence = 0.5
    tracking_confidence = 0.5
    
    # 초기 검색 범위 설정 적용
    update_search_settings(camera, search_margin_x, search_margin_y, 
                          detection_confidence, presence_confidence, tracking_confidence)

    while not captured and not skipped:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                cv2.destroyAllWindows()
                print("캘리브레이션 취소")
                return None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    print("캘리브레이션 건너뛰고 기본 호모그래피 사용")
                    skipped = True
                    break
                elif event.key == pygame.K_c:
                    attempt_count = process_calibration_attempt(camera, obj_points, attempt_count)
                    if attempt_count >= MAX_ATTEMPTS:
                        print(f"최대 시도 횟수({MAX_ATTEMPTS}) 도달")
                        print("'s' 키로 건너뛰기 또는 'c' 키로 계속 시도")
                # 검색 범위 조정 키
                elif event.key == pygame.K_UP:
                    search_margin_y = max(0.0, search_margin_y - 0.05)
                    update_search_settings(camera, search_margin_x, search_margin_y, 
                                       detection_confidence, presence_confidence, tracking_confidence)
                elif event.key == pygame.K_DOWN:
                    search_margin_y = min(0.4, search_margin_y + 0.05)
                    update_search_settings(camera, search_margin_x, search_margin_y, 
                                       detection_confidence, presence_confidence, tracking_confidence)
                elif event.key == pygame.K_LEFT:
                    search_margin_x = max(0.0, search_margin_x - 0.05)
                    update_search_settings(camera, search_margin_x, search_margin_y, 
                                       detection_confidence, presence_confidence, tracking_confidence)
                elif event.key == pygame.K_RIGHT:
                    search_margin_x = min(0.4, search_margin_x + 0.05)
                    update_search_settings(camera, search_margin_x, search_margin_y, 
                                       detection_confidence, presence_confidence, tracking_confidence)
                elif event.key == ord('d'):
                    detection_confidence = min(1.0, detection_confidence + 0.1)
                    update_search_settings(camera, search_margin_x, search_margin_y, 
                                       detection_confidence, presence_confidence, tracking_confidence)
                elif event.key == ord('f'):
                    detection_confidence = max(0.1, detection_confidence - 0.1)
                    update_search_settings(camera, search_margin_x, search_margin_y, 
                                       detection_confidence, presence_confidence, tracking_confidence)
                elif event.key == ord('p'):
                    presence_confidence = min(1.0, presence_confidence + 0.1)
                    update_search_settings(camera, search_margin_x, search_margin_y, 
                                       detection_confidence, presence_confidence, tracking_confidence)
                elif event.key == ord('o'):
                    presence_confidence = max(0.1, presence_confidence - 0.1)
                    update_search_settings(camera, search_margin_x, search_margin_y, 
                                       detection_confidence, presence_confidence, tracking_confidence)

        frame = camera.get_frame()
        if frame is None:
            print("카메라에서 프레임 캡처 실패")
            pygame.time.wait(DELAY_MS)
            continue

        corners_detected, corners = process_camera_frame(camera, frame)
        display_camera_feed_with_settings(frame, corners_detected, search_margin_x, search_margin_y,
                                        detection_confidence, presence_confidence, tracking_confidence, camera)

        # OpenCV 키 이벤트 처리 (Pygame 이벤트와 중복 방지)
        key = cv2.waitKey(DELAY_MS) & 0xFF
        if key == ord('s'):
            print("캘리브레이션 건너뛰고 기본 호모그래피 사용")
            skipped = True
        elif key == ord('c'):
            attempt_count = process_calibration_attempt(camera, obj_points, attempt_count)
            if attempt_count >= MAX_ATTEMPTS:
                print(f"최대 시도 횟수({MAX_ATTEMPTS}) 도달")
                print("'s' 키로 건너뛰기 또는 'c' 키로 계속 시도")
        elif key == 27:  # ESC
            print("캘리브레이션 취소")
            cv2.destroyAllWindows()
            return None
        elif key == ord('d'):
            detection_confidence = min(1.0, detection_confidence + 0.1)
            update_search_settings(camera, search_margin_x, search_margin_y, 
                               detection_confidence, presence_confidence, tracking_confidence)
        elif key == ord('f'):
            detection_confidence = max(0.1, detection_confidence - 0.1)
            update_search_settings(camera, search_margin_x, search_margin_y, 
                               detection_confidence, presence_confidence, tracking_confidence)
        elif key == ord('p'):
            presence_confidence = min(1.0, presence_confidence + 0.1)
            update_search_settings(camera, search_margin_x, search_margin_y, 
                               detection_confidence, presence_confidence, tracking_confidence)
        elif key == ord('o'):
            presence_confidence = max(0.1, presence_confidence - 0.1)
            update_search_settings(camera, search_margin_x, search_margin_y, 
                               detection_confidence, presence_confidence, tracking_confidence)

    cv2.destroyAllWindows()
    
    # 최종 검색 범위 설정을 camera 객체에 저장
    if hasattr(camera, 'landmarker'):
        camera.search_margin_x = search_margin_x
        camera.search_margin_y = search_margin_y
        print(f"최종 검색 범위 설정 저장: X여백={search_margin_x:.2f}, Y여백={search_margin_y:.2f}")
    
    return create_default_homography() if skipped else None


def process_calibration_attempt(camera, obj_points: np.ndarray, attempt_count: int) -> int:
    """단일 캘리브레이션 시도 처리"""
    print("캘리브레이션 시도 중...")
    frame = camera.get_frame()
    if frame is None:
        print("카메라에서 프레임 캡처 실패")
        return attempt_count + 1

    corners_detected, corners = process_camera_frame(camera, frame)
    if corners_detected:
        homography = calculate_homography(corners, obj_points)
        if homography is not None:
            print("✓ 캘리브레이션 성공!")
            cv2.destroyAllWindows()
            return attempt_count + 1
        else:
            print("× 호모그래피 계산 실패")
    else:
        print(f"× 체스보드 검출 실패 (시도: {attempt_count + 1}/{MAX_ATTEMPTS})")

    return attempt_count + 1