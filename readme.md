# Boulder Ping Pong
이 프로젝트는 웹캠과 프로젝터를 사용한 모션 기반 핑퐁 게임으로, Python과 MediaPipe를 사용하여 개발되었습니다.

## 요구 사항

- **Python**: 3.8 이상 (권장: Python 3.10.4)
- **의존성**: `requirements.txt`에 명시된 패키지


## 설치 방법

1. 저장소를 클론합니다:

   ```bash
   git clone <repository-url>
   cd BoulderPingPong
   ```

2. 가상 환경을 생성하고 활성화합니다:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. 의존성을 설치합니다:

   ```bash
   pip install -r requirements.txt
   ```

4. MediaPipe Pose Landmarker 모델(`pose_landmarker_full.task`)을 MediaPipe Pose Landmarker Models에서 다운로드하여 프로젝트 디렉토리에 배치합니다.

5. 게임을 실행합니다:

   ```bash
   python main.py
   ```

조작 방법

- **게임 재시작**: `r` 키를 눌러 공 위치와 점수를 초기화합니다.
- **상하폭 조절**:
  - `w`: 상하폭 증가
  - `s`: 상하폭 감소
- **좌우폭 조절**:
  - `d`: 좌우폭 증가
  - `a`: 좌우폭 감소
- **초점 이동**:
  - 상하좌우 화살표 키로 게임 화면의 초점을 이동합니다.
- **게임 종료**: `ESC` 키를 누릅니다.

참고 사항

- 웹캠과 프로젝터가 연결되어 있어야 합니다.
- 게임은 체스보드 패턴을 사용한 캘리브레이션이 필요합니다. 캘리브레이션 중 'c' 키를 눌러 캡처하세요.
