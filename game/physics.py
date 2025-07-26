import numpy as np
import random
import config
from config import INITIAL_BALL_SPEED_SCALE, BALL_SPEED_SCALE, ROUND_END_DELAY
import time
import pygame

# 상수 정의
MAX_SCREEN = 1  # 화면 크기 기준 (정규화된 좌표)
BALL_TRAIL_LENGTH = 60  # 공 궤적 최대 길이
COLLISION_SOUND_PATH = 'assets/369515__lefty_studios__jumping-sfx.wav'  # 충돌 사운드 파일 경로
SCORE_SOUND_PATH = 'assets/33308__erlingx__time.wav'

class Physics:
    """게임의 물리 엔진을 관리하는 클래스"""
    def __init__(self):
        """물리 엔진 초기화"""
        self.score = [0, 0]  # 플레이어 점수 [왼쪽, 오른쪽]
        self.ignore_collisions = False  # 충돌 무시 플래그
        self.target_side = None  # 공이 향하는 목표 방향
        self.round_ended = False  # 라운드 종료 여부
        self.round_end_time = None  # 라운드 종료 시간
        self.ball_trail = []  # 공 궤적 저장
        self.goal_scored = False  # 골 이벤트 플래그
        self.collision_sound = None  # 충돌 사운드 객체
        self.speed_multiplier = 1.0  # 공 속도 배율
        self._init_audio()  # 오디오 초기화
        self.reset_ball()  # 공 초기화

    def _init_audio(self):
        """Pygame 믹서 및 충돌 사운드 초기화"""
        try:
            pygame.mixer.init()
            self.collision_sound = pygame.mixer.Sound(COLLISION_SOUND_PATH)
            self.score_sound = pygame.mixer.Sound(SCORE_SOUND_PATH)
        except FileNotFoundError:
            print(f"충돌 사운드 파일을 '{COLLISION_SOUND_PATH}'에서 찾을 수 없습니다. 나중에 추가해 주세요.")
        except Exception as e:
            print(f"오디오 초기화 중 오류: {e}")

    def check_collision(self, ball_pos: np.ndarray, hit_pos: np.ndarray, hit_radius: float) -> bool:
        """공과 히트박스 간 충돌 감지"""
        try:
            distance = np.linalg.norm(ball_pos - np.array(hit_pos))
            return distance < hit_radius
        except Exception as e:
            print(f"충돌 감지 중 오류: {e}")
            return False

    def update(self, player_positions: list, dt: float) -> None:
        """물리 상태 업데이트"""
        try:
            if self.round_ended:
                if time.time() - self.round_end_time >= ROUND_END_DELAY:
                    self.reset_ball()
                    self.round_ended = False
                    self.round_end_time = None
                    self.goal_scored = False
                return

            # 플레이어와 공 충돌 처리
            if not self.ignore_collisions:
                self._handle_player_ball_collision(player_positions)
            else:
                # 공이 목표 측에 도달했는지 확인
                ball_on_next_side = (
                    (self.target_side == 'left' and self.ball_pos[0] < MAX_SCREEN / 2) or
                    (self.target_side == 'right' and self.ball_pos[0] > MAX_SCREEN / 2)
                )
                if ball_on_next_side:
                    self.ignore_collisions = False
                    self.target_side = None

            # 공 위치 업데이트
            self.ball_pos += self.ball_vel * dt

            # 공 궤적 업데이트
            self._update_ball_trail()

            # 공과 벽 충돌 처리
            self._handle_wall_ball_collision()

        except Exception as e:
            print(f"물리 업데이트 중 오류: {e}")

    def _update_ball_trail(self):
        """공 궤적 업데이트"""
        self.ball_trail.append(self.ball_pos.copy())
        if len(self.ball_trail) > BALL_TRAIL_LENGTH:
            self.ball_trail.pop(0)

    def _handle_wall_ball_collision(self):
        """공과 벽 충돌 처리"""
        try:
            is_touch_left = self.ball_pos[0] < 0
            is_touch_right = self.ball_pos[0] > MAX_SCREEN
            is_touch_bottom = self.ball_pos[1] < config.BALL_RADIUS_RATIO
            is_touch_top = self.ball_pos[1] > MAX_SCREEN - config.BALL_RADIUS_RATIO

            if is_touch_left:
                self.score[1] += 1  # 오른쪽 플레이어 점수 증가
                self.round_ended = True
                self.round_end_time = time.time()
                self.goal_scored = True  # 화면 흔들림 효과 트리거
                if self.score_sound:
                    self.score_sound.play()
            elif is_touch_right:
                self.score[0] += 1  # 왼쪽 플레이어 점수 증가
                self.round_ended = True
                self.round_end_time = time.time()
                self.goal_scored = True  # 화면 흔들림 효과 트리거
                if self.score_sound:
                    self.score_sound.play()
            elif is_touch_bottom or is_touch_top:
                self.ball_vel[1] = -self.ball_vel[1]  # Y축 속도 반전
        except Exception as e:
            print(f"벽 충돌 처리 중 오류: {e}")

    def _handle_player_ball_collision(self, player_positions: list):
        """플레이어와 공 충돌 처리"""
        try:
            for pos in player_positions:
                if self.check_collision(self.ball_pos, pos, config.BALL_RADIUS_RATIO):
                    self.ignore_collisions = True
                    self.target_side = 'left' if self.ball_pos[0] > MAX_SCREEN / 2 else 'right'
                    # 공 속도 10% 증가
                    self.speed_multiplier *= 1.1
                    self.ball_vel = np.array([
                        -BALL_SPEED_SCALE * self.speed_multiplier if self.target_side == 'left' else BALL_SPEED_SCALE * self.speed_multiplier,
                        random.uniform(-0.5 * BALL_SPEED_SCALE * self.speed_multiplier, 0.5 * BALL_SPEED_SCALE * self.speed_multiplier)
                    ])
                    print('충돌', self.ball_vel)
                    if self.collision_sound:
                        self.collision_sound.play()
                    break
        except Exception as e:
            print(f"플레이어 충돌 처리 중 오류: {e}")

    def reset_ball(self):
        """공을 중앙으로 리셋"""
        try:
            self.ball_pos = np.array([MAX_SCREEN / 2, MAX_SCREEN / 2], dtype=float)
            self.ball_vel = np.array([
                random.choice([-1, 1]) * INITIAL_BALL_SPEED_SCALE * self.speed_multiplier,
                random.uniform(-0.5 * INITIAL_BALL_SPEED_SCALE * self.speed_multiplier, 0.5 * INITIAL_BALL_SPEED_SCALE * self.speed_multiplier)
            ], dtype=float)
            self.ignore_collisions = False
            self.target_side = None
            self.ball_trail = []
            self.goal_scored = False
        except Exception as e:
            print(f"공 리셋 중 오류: {e}")

    def reset_game(self):
        """게임 전체를 재시작"""
        try:
            self.score = [0, 0]
            self.speed_multiplier = 1.0  # 속도 배율 초기화
            self.reset_ball()
            self.round_ended = False
            self.round_end_time = None
            self.goal_scored = False
        except Exception as e:
            print(f"게임 재시작 중 오류: {e}")