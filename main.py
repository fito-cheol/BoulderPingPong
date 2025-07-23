import pygame
import tkinter as tk
from camera.camera import Camera
from game.game import Game
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FULLSCREEN
from godot_server_gui import GodotServerGUI


def show_mode_selection():
    """모드 선택 다이얼로그 표시"""
    root = tk.Tk()
    root.title("Boulder Ping Pong")
    root.geometry("500x300")
    root.resizable(False, False)
    
    # 중앙 정렬
    root.geometry("+%d+%d" % (
        root.winfo_screenwidth()//2 - 250,
        root.winfo_screenheight()//2 - 150
    ))
    
    # 선택 결과
    selected_mode = None
    
    def select_pygame_mode():
        nonlocal selected_mode
        selected_mode = "pygame"
        root.destroy()
    
    def select_gui_mode():
        nonlocal selected_mode
        selected_mode = "gui"
        root.destroy()
    
    def cancel_selection():
        nonlocal selected_mode
        selected_mode = None
        root.destroy()
    
    # UI 구성
    main_frame = tk.Frame(root, padx=30, pady=30)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 제목
    title_label = tk.Label(main_frame, text="Boulder Ping Pong", font=("Arial", 18, "bold"))
    title_label.pack(pady=(0, 10))
    
    subtitle_label = tk.Label(main_frame, text="실행 모드를 선택하세요", font=("Arial", 12))
    subtitle_label.pack(pady=(0, 30))
    
    # 설명
    desc_label = tk.Label(main_frame, text="어떤 모드로 실행하시겠습니까?", font=("Arial", 10))
    desc_label.pack(pady=(0, 20))
    
    # 버튼 프레임
    button_frame = tk.Frame(main_frame)
    button_frame.pack(pady=20)
    
    # Pygame 모드 버튼
    pygame_button = tk.Button(button_frame, text="Pygame 모드\n(직접 게임)", 
                             command=select_pygame_mode, width=18, height=4,
                             font=("Arial", 10, "bold"))
    pygame_button.pack(side=tk.LEFT, padx=(0, 15))
    
    # GUI 서버 모드 버튼
    gui_button = tk.Button(button_frame, text="GUI 서버 모드\n(Godot 연동)", 
                           command=select_gui_mode, width=18, height=4,
                           font=("Arial", 10, "bold"))
    gui_button.pack(side=tk.LEFT)
    
    # 취소 버튼
    cancel_button = tk.Button(main_frame, text="취소", command=cancel_selection,
                             width=10, height=2)
    cancel_button.pack(pady=(20, 0))
    
    # 창을 최상위로 가져오기
    root.lift()
    root.attributes('-topmost', True)
    root.attributes('-topmost', False)
    root.focus_force()
    
    # 다이얼로그가 닫힐 때까지 대기
    root.mainloop()
    
    return selected_mode


def run_pygame_mode():
    """Pygame 모드 실행"""
    print("Pygame 모드를 시작합니다.")
    print("시작하기 전에 카메라를 선택하세요.\n")

    try:
        # 카메라 초기화 (자동으로 선택 메뉴 표시)
        camera = Camera()

        # Pygame 초기화
        pygame.init()
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN if FULLSCREEN else 0)
        pygame.display.set_caption("Interactive Soccer Game")

        # 호모그래피 사용 X
        homography = None
        # print("\n=== 캘리브레이션 시작 ===")
        # homography = calibrate_projector(camera, screen)
        # if homography is None:
        #     print("캘리브레이션이 취소되었습니다. 프로그램을 종료합니다.")
        #     return

        print("\n=== 게임 시작 ===")
        print("게임 조작법:")
        print("- R: 게임 재시작")
        print("- W/S: 상하 영역 크기 조절")
        print("- A/D: 좌우 영역 크기 조절")
        print("- 방향키: 화면 중심 이동")
        print("- ESC: 게임 종료")
        print("================")

        # 수정된 부분: camera와 homography 모두 전달
        game = Game(camera, homography)
        game.main()

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


def run_gui_mode():
    """GUI 서버 모드 실행"""
    print("GUI 서버 모드를 시작합니다.")
    app = GodotServerGUI()
    app.run()


def main():
    """메인 함수"""
    print("=== Boulder Ping Pong ===")
    print("실행 모드를 선택하세요.")
    
    # 모드 선택
    selected_mode = show_mode_selection()
    
    if selected_mode == "pygame":
        run_pygame_mode()
    elif selected_mode == "gui":
        run_gui_mode()
    else:
        print("모드 선택이 취소되었습니다.")


if __name__ == "__main__":
    # main()
    run_pygame_mode()