# Boulder Ping Pong
이 프로젝트는 웹캠과 프로젝터를 사용한 모션 기반 핑퐁 게임으로, Python과 MediaPipe를 사용하여 개발되었습니다.

### 요구 사항

Python: 3.8 이상 (권장: Python 3.10.4)
의존성: requirements.txt에 명시된 패키지

### 설치 방법

저장소를 클론합니다:git clone <repository-url>
cd BoulderPingPong


가상 환경을 생성하고 활성화합니다:python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows


의존성을 설치합니다:pip install -r requirements.txt


MediaPipe Pose Landmarker 모델(pose_landmarker_full.task)을 MediaPipe Pose Landmarker Models에서 다운로드하여 프로젝트 디렉토리에 배치합니다.
게임을 실행합니다:python main.py



### 참고 사항

웹캠과 프로젝터가 연결되어 있어야 합니다.
게임은 체스보드 패턴을 사용한 캘리브레이션이 필요합니다. 캘리브레이션 중 'c' 키를 눌러 캡처하세요.
게임을 종료하려면 ESC 키를 누르세요.
