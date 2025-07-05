import pygame
from camera import Camera
from calibration import calibrate_projector
from game import Game
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FULLSCREEN


def main():
    print("=== 멀티카메라 지원 축구 게임 ===")
    print("시작하기 전에 카메라를 선택하세요.\n")

    try:
        # 카메라 초기화 (자동으로 선택 메뉴 표시)
        camera = Camera()

        # Pygame 초기화
        pygame.init()
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN if FULLSCREEN else 0)
        pygame.display.set_caption("Interactive Soccer Game")

        print("\n=== 캘리브레이션 시작 ===")
        homography = calibrate_projector(camera, screen)

        if homography is None:
            print("캘리브레이션이 취소되었습니다. 프로그램을 종료합니다.")
            return

        print("\n=== 게임 시작 ===")
        print("게임 조작법:")
        print("- R: 게임 재시작")
        print("- W/S: 상하 영역 크기 조절")
        print("- A/D: 좌우 영역 크기 조절")
        print("- 방향키: 화면 중심 이동")
        print("- ESC: 게임 종료")
        print("================")

        game = Game(homography)
        game.run()

    except RuntimeError as e:
        print(f"오류 발생: {e}")
        print("프로그램을 종료합니다.")
    except KeyboardInterrupt:
        print("\n사용자가 프로그램을 종료했습니다.")
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        print("프로그램을 종료합니다.")
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()