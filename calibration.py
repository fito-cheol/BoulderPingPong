import cv2
import numpy as np
import pygame
import time
from config import CHESSBOARD_SIZE, SQUARE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT, WALL_WIDTH, WALL_HEIGHT

def calibrate_projector(camera, screen):
    """체스보드 패턴으로 호모그래피 행렬 계산"""
    # 체스보드의 실제 좌표 (미터 단위)
    obj_points = np.zeros((CHESSBOARD_SIZE[0] * CHESSBOARD_SIZE[1], 2), np.float32)
    for i in range(CHESSBOARD_SIZE[1]):
        for j in range(CHESSBOARD_SIZE[0]):
            obj_points[i * CHESSBOARD_SIZE[0] + j] = [j * SQUARE_SIZE, i * SQUARE_SIZE]

    # 체스보드 패턴 투영
    screen.fill((0, 0, 0))  # 화면을 검은색으로 초기화

    # 체스보드 그리기
    for i in range(CHESSBOARD_SIZE[1]):
        for j in range(CHESSBOARD_SIZE[0]):
            if (i + j) % 2 == 0:
                x1 = int(j * SCREEN_WIDTH / CHESSBOARD_SIZE[0])
                y1 = int(i * SCREEN_HEIGHT / CHESSBOARD_SIZE[1])
                x2 = int((j + 1) * SCREEN_WIDTH / CHESSBOARD_SIZE[0])
                y2 = int((i + 1) * SCREEN_HEIGHT / CHESSBOARD_SIZE[1])
                pygame.draw.rect(screen, (255, 255, 255), (x1, y1, x2 - x1, y2 - y1))

    pygame.display.flip()

    print("=== 캘리브레이션 모드 ===")
    print("체스보드 패턴이 투영되었습니다.")
    print("카메라 창에서 다음 키를 눌러주세요:")
    print("'c' - 캘리브레이션 시도")
    print("'s' - 캘리브레이션 건너뛰기 (기본 호모그래피 사용)")
    print("'p' - 카메라 화면 표시/숨김 토글")
    print("'ESC' - 프로그램 종료")
    print("=====================================")

    # 캘리브레이션 루프
    captured = False
    skipped = False
    max_attempts = 10
    attempt_count = 0
    show_camera = False  # 카메라 화면 표시 여부

    while not captured and not skipped:
        # pygame 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                elif event.key == pygame.K_s:
                    print("캘리브레이션을 건너뛰고 기본 호모그래피를 사용합니다.")
                    skipped = True
                    break
                elif event.key == pygame.K_c:
                    print("캘리브레이션을 시도합니다...")
                    attempt_count += 1

                    frame = camera.get_frame()
                    if frame is None:
                        print("카메라에서 프레임을 가져올 수 없습니다.")
                        continue

                    # 체스보드 검출 시도
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    ret, corners = cv2.findChessboardCorners(gray, CHESSBOARD_SIZE, None)

                    if ret:
                        # 코너 정밀화
                        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
                        corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)

                        # 호모그래피 계산
                        src_points = corners.reshape(-1, 2)
                        dst_points = obj_points * np.array([SCREEN_WIDTH / WALL_WIDTH, SCREEN_HEIGHT / WALL_HEIGHT])

                        homography, mask = cv2.findHomography(src_points, dst_points, cv2.RANSAC, 5.0)

                        if homography is not None:
                            print("✓ 캘리브레이션 성공!")
                            captured = True
                            cv2.destroyAllWindows()
                            return homography
                        else:
                            print("× 호모그래피 계산 실패")
                    else:
                        print(f"× 체스보드 검출 실패 (시도: {attempt_count}/{max_attempts})")

                    if attempt_count >= max_attempts:
                        print(f"최대 시도 횟수({max_attempts})에 도달했습니다.")
                        print("'s' 키를 눌러 건너뛰거나 'c' 키로 계속 시도하세요.")
                elif event.key == pygame.K_p:
                    show_camera = not show_camera
                    print(f"카메라 화면 {'표시' if show_camera else '숨김'}")
                    if not show_camera:
                        cv2.destroyAllWindows()

        # 카메라 프레임 표시 (토글 상태에 따라)
        frame = camera.get_frame()
        if frame is not None and show_camera:
            # 체스보드 검출 상태 표시
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            ret, corners = cv2.findChessboardCorners(gray, CHESSBOARD_SIZE, None)

            if ret:
                cv2.drawChessboardCorners(frame, CHESSBOARD_SIZE, corners, ret)
                cv2.putText(frame, "Chessboard Detected! Press 'c' to calibrate",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "Position camera to see chessboard",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            cv2.putText(frame, "c: Calibrate, s: Skip, p: Toggle Camera, ESC: Exit",
                        (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            cv2.imshow("Calibration - Camera View", frame)

        # OpenCV 키 입력 처리
        key = cv2.waitKey(1) & 0xFF
        if key == ord('c'):
            print("캘리브레이션을 시도합니다...")
            attempt_count += 1

            frame = camera.get_frame()
            if frame is None:
                print("카메라에서 프레임을 가져올 수 없습니다.")
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            ret, corners = cv2.findChessboardCorners(gray, CHESSBOARD_SIZE, None)

            if ret:
                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
                corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)

                src_points = corners.reshape(-1, 2)
                dst_points = obj_points * np.array([SCREEN_WIDTH / WALL_WIDTH, SCREEN_HEIGHT / WALL_HEIGHT])

                homography, mask = cv2.findHomography(src_points, dst_points, cv2.RANSAC, 5.0)

                if homography is not None:
                    print("✓ 캘리브레이션 성공!")
                    captured = True
                    cv2.destroyAllWindows()
                    return homography
                else:
                    print("× 호모그래피 계산 실패")
            else:
                print(f"× 체스보드 검출 실패 (시도: {attempt_count}/{max_attempts})")

            if attempt_count >= max_attempts:
                print(f"최대 시도 횟수({max_attempts})에 도달했습니다.")
                print("'s' 키를 눌러 건너뛰거나 'c' 키로 계속 시도하세요.")

        elif key == ord('s'):
            print("캘리브레이션을 건너뛰고 기본 호모그래피를 사용합니다.")
            skipped = True
            break
        elif key == ord('p'):
            show_camera = not show_camera
            print(f"카메라 화면 {'표시' if show_camera else '숨김'}")
            if not show_camera:
                cv2.destroyAllWindows()
        elif key == 27:  # ESC 키
            print("캘리브레이션을 취소합니다.")
            cv2.destroyAllWindows()
            return None

        time.sleep(0.01)

    cv2.destroyAllWindows()

    if skipped:
        print("기본 호모그래피 매트릭스를 사용합니다.")
        return create_default_homography()

    return None

def create_default_homography():
    """기본 호모그래피 매트릭스 생성 (단위 행렬 기반)"""
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
        print("기본 호모그래피 매트릭스 생성 완료")
        return homography
    except Exception as e:
        print(f"기본 호모그래피 생성 실패: {e}")
        return np.eye(3, dtype=np.float32)