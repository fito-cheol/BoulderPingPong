import cv2
import numpy as np
import pygame
from typing import Optional, Tuple
from config import CHESSBOARD_SIZE, SQUARE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT, WALL_WIDTH, WALL_HEIGHT

# 상수 정의
MAX_ATTEMPTS = 10  # 최대 캘리브레이션 시도 횟수
DELAY_MS = 10  # 프레임 지연 시간 (밀리초)
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


def display_camera_feed(frame: np.ndarray, corners_detected: bool) -> None:
    """카메라 피드에 오버레이 텍스트와 검출된 코너를 표시"""
    if corners_detected:
        cv2.drawChessboardCorners(frame, CHESSBOARD_SIZE, corners, True)
        cv2.putText(frame, "체스보드 검출됨! 'c'를 눌러 캘리브레이션",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, FONT_SCALE, TEXT_COLOR_GREEN, FONT_THICKNESS)
    else:
        cv2.putText(frame, "카메라를 체스보드가 보이도록 조정",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, FONT_SCALE, TEXT_COLOR_RED, FONT_THICKNESS)

    cv2.putText(frame, "c: 캘리브레이션, s: 건너뛰기, ESC: 종료",
                (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
                SMALL_FONT_SCALE, TEXT_COLOR_WHITE, 1)
    cv2.imshow("캘리브레이션 - 카메라 뷰", frame)


def calibrate_projector(camera, screen: pygame.Surface) -> Optional[np.ndarray]:
    """체스보드 패턴을 사용해 프로젝터를 캘리브레이션하여 호모그래피 행렬 계산"""
    obj_points = create_chessboard_points()
    draw_chessboard_pattern(screen)
    display_instructions()

    attempt_count = 0
    captured = False
    skipped = False

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

        frame = camera.get_frame()
        if frame is None:
            print("카메라에서 프레임 캡처 실패")
            pygame.time.wait(DELAY_MS)
            continue

        corners_detected, corners = process_camera_frame(camera, frame)
        display_camera_feed(frame, corners_detected)

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

    cv2.destroyAllWindows()
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