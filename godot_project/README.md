# Boulder Ping Pong - Godot 연동 버전

이 프로젝트는 Python으로 구현된 증강현실 핑퐁 게임을 Godot 엔진과 연동한 버전입니다.

## 구조

```
BoulderPingPong/
├── godot_server.py          # Python HTTP 서버 (포즈 데이터 전송)
├── godot_project/           # Godot 프로젝트
│   ├── project.godot        # Godot 프로젝트 설정
│   ├── scenes/Main.tscn     # 메인 게임 씬
│   └── scripts/
│       ├── PoseDataReceiver.gd  # 포즈 데이터 수신
│       └── GameManager.gd        # 게임 로직 처리
└── (기존 Python 파일들)
```

## 실행 방법

### 1. Python 서버 실행 (3가지 옵션)

#### 옵션 1: 기본 서버 (Pygame 윈도우)
```bash
python godot_server.py
```
- Pygame 윈도우로 상태 표시
- ESC 키로 종료
- 실시간 연결 상태 확인

#### 옵션 2: 비동기 서버 (권장)
```bash
python godot_server_async.py
```
- asyncio 기반 비동기 처리
- 더 나은 성능과 응답성
- ESC 키로 종료

#### 옵션 3: GUI 서버
```bash
python godot_server_gui.py
```
- tkinter 기반 GUI 인터페이스
- 서버 시작/중지 버튼
- 실시간 로그 및 상태 표시
- 캘리브레이션 버튼

모든 서버는:
- 카메라를 초기화하고 캘리브레이션을 수행
- MediaPipe를 사용하여 사람의 포즈를 인식
- `http://localhost:8080/pose_data`에서 JSON 형태로 포즈 데이터 제공

### 2. Godot 프로젝트 실행

Godot 에디터에서 `godot_project` 폴더를 열고 실행하거나, 명령줄에서:

```bash
godot --path godot_project
```

## 게임 조작법

- **Enter**: 게임 재시작
- **ESC**: 게임 종료
- **손 움직임**: 플레이어 패들 제어 (카메라로 인식)

## 포즈 데이터 형식

서버에서 전송하는 JSON 데이터 형식:

```json
{
  "timestamp": 1234567890.123,
  "players": [
    {
      "hands": [
        {
          "x": 1.5,
          "y": 2.0,
          "z": 0.0,
          "visibility": 0.8,
          "presence": 0.9
        }
      ],
      "feet": [
        {
          "x": 1.5,
          "y": 3.0,
          "z": 0.0,
          "visibility": 0.7,
          "presence": 0.8
        }
      ],
      "head": {
        "0": {"x": 1.5, "y": 1.0, "z": 0.0, "visibility": 0.9, "presence": 0.9}
      },
      "body": {
        "11": {"x": 1.4, "y": 1.5, "z": 0.0, "visibility": 0.8, "presence": 0.8}
      }
    }
  ]
}
```

## 주요 기능

### Python 서버 (godot_server.py)
- 카메라 자동 선택 및 초기화
- MediaPipe 포즈 인식
- 캘리브레이션 지원
- HTTP API로 포즈 데이터 제공
- CORS 지원으로 웹/게임 엔진 연동 가능

### Godot 게임 (GameManager.gd)
- 실시간 포즈 데이터 수신
- 핑퐁 게임 로직 구현
- 손 위치 기반 패들 제어
- AI 상대와의 대전
- 점수 시스템

### 포즈 데이터 수신기 (PoseDataReceiver.gd)
- HTTP 요청으로 포즈 데이터 수신
- JSON 파싱 및 데이터 구조화
- 연결 상태 관리
- 30 FPS 업데이트

## 시스템 요구사항

- Python 3.8+
- Godot 4.2+
- 웹캠 또는 카메라
- MediaPipe 라이브러리

## 설치 및 설정

1. Python 의존성 설치:
```bash
pip install -r requirements.txt
```

2. MediaPipe 모델 파일 다운로드:
   - `pose_landmarker_heavy.task` 파일을 프로젝트 루트에 배치
   - [MediaPipe 모델 다운로드](https://developers.google.com/mediapipe/solutions/vision/pose_landmarker#models)

3. Godot 4.2+ 설치

## 문제 해결

### 서버 연결 실패
- Python 서버가 실행 중인지 확인
- 방화벽 설정 확인
- `http://localhost:8080/pose_data` 접속 테스트

### 카메라 인식 문제
- 카메라가 제대로 연결되어 있는지 확인
- 다른 프로그램에서 카메라를 사용 중인지 확인
- MediaPipe 모델 파일이 올바른 위치에 있는지 확인

### 게임 성능 문제
- Godot 프로젝트 설정에서 렌더링 방법 확인
- 포즈 데이터 업데이트 빈도 조정 (PoseDataReceiver.gd의 update_timer.wait_time) 