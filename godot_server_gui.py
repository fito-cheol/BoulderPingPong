import json
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import socket
import struct
import base64
import hashlib
from camera.camera import Camera
from camera.calibration import calibrate_projector
import pygame
import cv2
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FULLSCREEN

from util.debug import timer_decorator

class WebSocketServer:
    def __init__(self, camera, host='localhost', port=8080):
        self.camera = camera
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []
        self.running = False
        self.connected = False
        self.latest_pose = []
        self.last_request_time = 0
        self.last_response_time_ms = 0
        self.pose_loop_thread = threading.Thread(target=self.pose_loop, daemon=True)
        self.pose_loop_thread.start()

    @timer_decorator
    def pose_loop(self):
        while True:
            if self.camera:
                try:
                    self.latest_pose = self.camera.get_full_pose_data()
                    # 연결된 클라이언트들에게 데이터 전송
                    if self.clients:
                        self.broadcast_pose_data()
                except Exception as e:
                    print("[Pose Loop Error]", e)
            time.sleep(0.03)  # ~30 FPS

    @timer_decorator
    def broadcast_pose_data(self):
        """연결된 모든 클라이언트에게 포즈 데이터 전송"""
        if not self.clients:
            return
        
        try:
            # side 키 추가 (MediaPipe 랜드마크 인덱스 기반)
            processed_players = []
            for player in self.latest_pose or []:
                processed_player = player.copy()
                
                # 손 데이터에 side 키 추가 (랜드마크 인덱스 기반)
                if 'hands' in processed_player:
                    for hand in processed_player['hands']:
                        # MediaPipe 랜드마크 인덱스로 구분
                        # 15: LEFT_WRIST, 16: RIGHT_WRIST
                        if 'landmark_index' in hand:
                            if hand['landmark_index'] == 15:
                                hand['side'] = 'left'
                            elif hand['landmark_index'] == 16:
                                hand['side'] = 'right'
                        else:
                            # landmark_index가 없으면 첫 번째는 왼쪽, 두 번째는 오른쪽으로 가정
                            print("Warning: landmark_index not found in hand data")
                
                # 발 데이터에 side 키 추가 (랜드마크 인덱스 기반)
                if 'feet' in processed_player:
                    for foot in processed_player['feet']:
                        # MediaPipe 랜드마크 인덱스로 구분
                        # 27: LEFT_ANKLE, 28: RIGHT_ANKLE
                        if 'landmark_index' in foot:
                            if foot['landmark_index'] == 27:
                                foot['side'] = 'left'
                            elif foot['landmark_index'] == 28:
                                foot['side'] = 'right'
                        else:
                            # landmark_index가 없으면 첫 번째는 왼쪽, 두 번째는 오른쪽으로 가정
                            print("Warning: landmark_index not found in foot data")
                
                processed_players.append(processed_player)
            
            data = {
                'timestamp': time.time(),
                'players': processed_players
            }
            message = json.dumps(data)
            frame = self.create_websocket_frame(message)
            
            # 연결이 끊어진 클라이언트 제거
            disconnected_clients = []
            for client in self.clients:
                try:
                    client.send(frame)
                except:
                    disconnected_clients.append(client)
            
            # 끊어진 클라이언트 제거
            for client in disconnected_clients:
                self.clients.remove(client)
                client.close()
            
            self.connected = len(self.clients) > 0
            if self.connected:
                self.last_request_time = time.time()
                
        except Exception as e:
            print(f"브로드캐스트 오류: {e}")

    @timer_decorator
    def create_websocket_frame(self, message):
        """WebSocket 프레임 생성"""
        message_bytes = message.encode('utf-8')
        length = len(message_bytes)
        
        # WebSocket 헤더 구성
        frame = bytearray()
        frame.append(0x81)  # FIN + text frame
        
        if length <= 125:
            frame.append(length)
        elif length <= 65535:
            frame.append(126)
            frame.extend(struct.pack('>H', length))
        else:
            frame.append(127)
            frame.extend(struct.pack('>Q', length))
        
        frame.extend(message_bytes)
        return frame

    @timer_decorator
    def handle_websocket_handshake(self, client_socket, request):
        """WebSocket 핸드셰이크 처리"""
        try:
            print(f"WebSocket 핸드셰이크 시작")
            print(f"요청 데이터: {request[:200]}...")  # 처음 200바이트만 출력
            
            # HTTP 요청에서 WebSocket 키 추출
            lines = request.decode('utf-8').split('\n')
            ws_key = None
            upgrade_header = None
            connection_header = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('Sec-WebSocket-Key:'):
                    ws_key = line.split(':', 1)[1].strip()
                    print(f"WebSocket 키 발견: {ws_key}")
                elif line.startswith('Upgrade:'):
                    upgrade_header = line.split(':', 1)[1].strip()
                    print(f"Upgrade 헤더: {upgrade_header}")
                elif line.startswith('Connection:'):
                    connection_header = line.split(':', 1)[1].strip()
                    print(f"Connection 헤더: {connection_header}")
            
            if not ws_key:
                print("WebSocket 키를 찾을 수 없음")
                return False
            
            if upgrade_header != 'websocket':
                print(f"잘못된 Upgrade 헤더: {upgrade_header}")
                return False
            
            # WebSocket 응답 생성
            ws_accept = base64.b64encode(
                hashlib.sha1((ws_key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()
            ).decode()
            
            response = (
                'HTTP/1.1 101 Switching Protocols\r\n'
                'Upgrade: websocket\r\n'
                'Connection: Upgrade\r\n'
                f'Sec-WebSocket-Accept: {ws_accept}\r\n'
                '\r\n'
            )
            
            print(f"WebSocket 응답 전송: {response}")
            client_socket.send(response.encode())
            print("WebSocket 핸드셰이크 완료")
            return True
            
        except Exception as e:
            print(f"WebSocket 핸드셰이크 오류: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def start_server(self):
        """WebSocket 서버 시작"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1)  # 1초 타임아웃
            
            self.running = True
            print(f"WebSocket 서버가 시작되었습니다: ws://{self.host}:{self.port}")
            
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    print(f"클라이언트 연결: {address}")
                    
                    # 클라이언트 소켓 설정
                    client_socket.settimeout(5)  # 5초 타임아웃
                    
                    # WebSocket 핸드셰이크
                    try:
                        request = client_socket.recv(1024)
                        print(f"클라이언트로부터 {len(request)} 바이트 수신")
                        
                        if self.handle_websocket_handshake(client_socket, request):
                            self.clients.append(client_socket)
                            self.connected = True
                            print(f"WebSocket 연결 성공: {address}")
                        else:
                            print(f"WebSocket 핸드셰이크 실패: {address}")
                            client_socket.close()
                    except Exception as e:
                        print(f"핸드셰이크 처리 중 오류: {e}")
                        client_socket.close()
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"서버 오류: {e}")
                    break
                    
        except Exception as e:
            print(f"서버 시작 실패: {e}")
        finally:
            self.stop_server()
    
    def start_server_thread(self):
        """별도 스레드에서 서버 시작"""
        server_thread = threading.Thread(target=self.start_server, daemon=True)
        server_thread.start()
    
    def stop_server(self):
        """서버 종료"""
        self.running = False
        
        # 모든 클라이언트 연결 종료
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        self.clients.clear()
        
        # 서버 소켓 종료
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        self.connected = False

    def is_connected(self):
        """연결 상태 확인"""
        return self.connected and len(self.clients) > 0

class CameraSelectionDialog:
    def __init__(self, parent):
        self.parent = parent
        self.selected_camera_index = None
        self.dialog = None
        
    def show(self):
        """카메라 선택 다이얼로그 표시"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("카메라 선택")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 중앙 정렬
        self.dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + self.parent.winfo_width()//2 - 250,
            self.parent.winfo_rooty() + self.parent.winfo_height()//2 - 200
        ))
        
        self.setup_ui()
        
        # 다이얼로그가 닫힐 때까지 대기
        self.parent.wait_window(self.dialog)
        return self.selected_camera_index
    
    def setup_ui(self):
        """UI 구성"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_label = ttk.Label(main_frame, text="카메라 선택", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 검색 중 표시
        self.search_label = ttk.Label(main_frame, text="카메라 검색 중...", font=("Arial", 10))
        self.search_label.pack(pady=(0, 10))
        
        # 진행률 표시
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(0, 20))
        self.progress.start()
        
        # 카메라 목록 프레임
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # 트리뷰 생성
        columns = ('index', 'name', 'type', 'resolution', 'fps')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        
        # 컬럼 설정
        self.tree.heading('index', text='인덱스')
        self.tree.heading('name', text='카메라 이름')
        self.tree.heading('type', text='타입')
        self.tree.heading('resolution', text='해상도')
        self.tree.heading('fps', text='FPS')
        
        self.tree.column('index', width=60)
        self.tree.column('name', width=150)
        self.tree.column('type', width=80)
        self.tree.column('resolution', width=100)
        self.tree.column('fps', width=60)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.select_button = ttk.Button(button_frame, text="선택", command=self.select_camera, state="disabled")
        self.select_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        self.cancel_button = ttk.Button(button_frame, text="취소", command=self.cancel)
        self.cancel_button.pack(side=tk.RIGHT)
        
        # 더블클릭 이벤트
        self.tree.bind('<Double-1>', self.on_double_click)
        
        # 카메라 검색 시작
        self.search_cameras()
    
    def search_cameras(self):
        """카메라 검색 (별도 스레드에서 실행)"""
        def search_thread():
            try:
                # 빠른 카메라 검색 (타임아웃 적용)
                available_cameras = self.find_cameras_fast()
                
                # UI 업데이트는 메인 스레드에서
                self.dialog.after(0, self.update_camera_list, available_cameras)
                
            except Exception as e:
                self.dialog.after(0, self.show_error, str(e))
        
        threading.Thread(target=search_thread, daemon=True).start()
    
    def find_cameras_fast(self):
        """빠른 카메라 검색 (타임아웃 적용)"""
        available_cameras = []
        
        # 더 안전한 검색 범위 설정
        max_camera_index = 5  # 일반적으로 5개 정도면 충분
        
        for i in range(max_camera_index):
            try:
                # OpenCV 경고 메시지 억제
                import warnings
                warnings.filterwarnings("ignore", category=UserWarning)
                
                cap = cv2.VideoCapture(i, cv2.CAP_ANY)
                if cap.isOpened():
                    # 빠른 프레임 읽기 시도 (타임아웃 적용)
                    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 500)  # 0.5초로 단축
                    cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 500)  # 0.5초로 단축
                    
                    # 프레임 읽기 시도 (더 안전한 방법)
                    try:
                        ret, frame = cap.read()
                        if ret and frame is not None and frame.size > 0:
                            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                            fps = cap.get(cv2.CAP_PROP_FPS)
                            
                            # 카메라 이름 가져오기
                            camera_name = self.get_camera_name_windows(i)
                            
                            # 가상 카메라 필터링
                            if self.is_virtual_camera(camera_name):
                                print(f"가상 카메라 제외: {camera_name}")
                                cap.release()
                                continue
                            
                            camera_type = "USB 카메라" if i > 0 else "내장 카메라"
                            
                            available_cameras.append({
                                'index': i,
                                'name': camera_name,
                                'type': camera_type,
                                'resolution': f"{width}x{height}",
                                'fps': fps
                            })
                    except Exception as frame_error:
                        print(f"카메라 {i} 프레임 읽기 실패: {frame_error}")
                        pass
                    
                    cap.release()
                else:
                    # 연속으로 2개 이상 실패하면 중단 (더 빠른 종료)
                    if i > 1 and len(available_cameras) == 0:
                        break
                        
            except Exception as e:
                print(f"카메라 {i} 검색 중 오류: {e}")
                continue
        
        return available_cameras
    
    def is_virtual_camera(self, camera_name):
        """가상 카메라인지 확인"""
        if not camera_name:
            return False
        
        virtual_keywords = [
            'virtual', 'vcam', 'nvidia', 'broadcast', 'obs', 'xsplit',
            'webcamoid', 'manycam', 'splitcam', 'wirecast', 'v4l2loopback',
            'droidcam', 'ivcam', 'epoccam', 'kinect', 'leap motion'
        ]
        
        camera_name_lower = camera_name.lower()
        for keyword in virtual_keywords:
            if keyword in camera_name_lower:
                return True
        
        return False
    
    def get_camera_name_windows(self, index):
        """Windows에서 카메라 이름을 가져오는 함수"""
        try:
            import subprocess
            result = subprocess.run(['powershell', '-Command',
                                   'Get-WmiObject -Class Win32_PnPEntity | Where-Object {$_.Name -like "*camera*" -or $_.Name -like "*webcam*"} | Select-Object Name'],
                                   capture_output=True, text=True, timeout=2)
            cameras = result.stdout.strip().split('\n')[2:]  # 헤더 제거
            if index < len(cameras):
                return cameras[index].strip()
        except:
            pass
        return f"카메라 {index}"
    
    def update_camera_list(self, cameras):
        """카메라 목록 업데이트"""
        self.progress.stop()
        self.progress.pack_forget()
        
        if not cameras:
            self.search_label.config(text="사용 가능한 카메라가 없습니다.")
            return
        
        self.search_label.config(text=f"{len(cameras)}개의 카메라를 찾았습니다.")
        
        # 트리뷰에 카메라 추가
        for camera in cameras:
            self.tree.insert('', 'end', values=(
                camera['index'],
                camera['name'],
                camera['type'],
                camera['resolution'],
                f"{camera['fps']:.1f}"
            ))
        
        # 첫 번째 카메라 선택
        if cameras:
            first_item = self.tree.get_children()[0]
            self.tree.selection_set(first_item)
            self.select_button.config(state="normal")
    
    def show_error(self, error_msg):
        """오류 표시"""
        self.progress.stop()
        self.progress.pack_forget()
        self.search_label.config(text=f"카메라 검색 중 오류: {error_msg}")
    
    def select_camera(self):
        """카메라 선택"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            camera_index = int(item['values'][0])
            self.selected_camera_index = camera_index
            self.dialog.destroy()
    
    def on_double_click(self, event):
        """더블클릭으로 카메라 선택"""
        self.select_camera()
    
    def cancel(self):
        """취소"""
        self.selected_camera_index = None
        self.dialog.destroy()

class GodotServerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Godot 연동 서버")
        self.root.geometry("800x500")
        self.root.resizable(True, True)
        self.root.minsize(600, 400)
        
        # 서버 관련 변수
        self.camera = None
        self.pose_server = None
        self.server_running = False
        
        self.setup_ui()

    @timer_decorator
    def setup_ui(self):
        """UI 구성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(4, weight=1)  # 로그 프레임이 늘어나도록
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
        # 제목
        title_label = ttk.Label(main_frame, text="Godot 연동 서버", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 서버 설정 프레임
        settings_frame = ttk.LabelFrame(main_frame, text="서버 설정", padding="10")
        settings_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 호스트 설정
        ttk.Label(settings_frame, text="호스트:").grid(row=0, column=0, sticky=tk.W)
        self.host_var = tk.StringVar(value="localhost")
        host_entry = ttk.Entry(settings_frame, textvariable=self.host_var, width=15)
        host_entry.grid(row=0, column=1, padx=(10, 0))
        
        # 포트 설정
        ttk.Label(settings_frame, text="포트:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.port_var = tk.StringVar(value="8080")
        port_entry = ttk.Entry(settings_frame, textvariable=self.port_var, width=15)
        port_entry.grid(row=1, column=1, padx=(10, 0), pady=(10, 0))
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        # 카메라 선택 버튼
        self.camera_select_button = ttk.Button(button_frame, text="카메라 선택", command=self.select_camera)
        self.camera_select_button.grid(row=0, column=0, padx=(0, 10))
        
        # 시작/중지 버튼
        self.start_button = ttk.Button(button_frame, text="서버 시작", command=self.start_server)
        self.start_button.grid(row=0, column=1, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="서버 중지", command=self.stop_server, state="disabled")
        self.stop_button.grid(row=0, column=2, padx=(0, 10))
        
        # 캘리브레이션 버튼
        self.calib_button = ttk.Button(button_frame, text="캘리브레이션", command=self.run_calibration)
        self.calib_button.grid(row=0, column=3, padx=(0, 10))
        
        # 카메라 화면 버튼
        self.camera_button = ttk.Button(button_frame, text="카메라 화면", command=self.show_camera_view)
        self.camera_button.grid(row=0, column=4, padx=(0, 10))
        
        # 웹소켓 테스트 버튼
        self.websocket_test_button = ttk.Button(button_frame, text="웹소켓 테스트", command=self.open_websocket_test)
        self.websocket_test_button.grid(row=0, column=5)
        
        # 상태 프레임
        status_frame = ttk.LabelFrame(main_frame, text="서버 상태", padding="10")
        status_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 카메라 정보 표시
        self.camera_info_var = tk.StringVar(value="카메라가 선택되지 않음")
        camera_info_label = ttk.Label(status_frame, textvariable=self.camera_info_var, font=("Arial", 10))
        camera_info_label.grid(row=0, column=0, sticky=tk.W)
        
        # 상태 표시
        self.status_var = tk.StringVar(value="대기 중")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, font=("Arial", 10))
        status_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # 연결 상태
        self.connection_var = tk.StringVar(value="연결 없음")
        connection_label = ttk.Label(status_frame, textvariable=self.connection_var, font=("Arial", 10))
        connection_label.grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        
        # URL 표시
        self.url_var = tk.StringVar(value="")
        url_label = ttk.Label(status_frame, textvariable=self.url_var, font=("Arial", 9), foreground="blue")
        url_label.grid(row=3, column=0, sticky=tk.W, pady=(5, 0))
        
        # 로그 프레임
        log_frame = ttk.LabelFrame(main_frame, text="로그", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.N, tk.S, tk.E, tk.W), pady=(0, 10))
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        # 로그 텍스트
        self.log_text = tk.Text(log_frame)
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # 상태 업데이트 타이머
        self.update_status()
    
    def select_camera(self):
        """카메라 선택"""
        dialog = CameraSelectionDialog(self.root)
        camera_index = dialog.show()
        
        if camera_index is not None:
            # 카메라 초기화를 별도 스레드에서 실행
            self.camera_select_button.config(state="disabled")
            self.log_message(f"카메라 {camera_index} 초기화 중... (잠시만 기다려주세요)")
            
            # 진행률 표시
            self.camera_info_var.set("카메라 초기화 중...")
            
            def progress_callback(message):
                """진행률 콜백"""
                self.root.after(0, lambda: self.camera_info_var.set(message))
            
            def init_camera_thread():
                try:
                    camera = Camera(camera_index=camera_index, progress_callback=progress_callback)
                    # UI 업데이트는 메인 스레드에서
                    self.root.after(0, self.on_camera_initialized, camera, camera_index)
                except Exception as e:
                    self.root.after(0, self.on_camera_init_failed, str(e))
            
            # 별도 스레드에서 카메라 초기화
            threading.Thread(target=init_camera_thread, daemon=True).start()
    
    def on_camera_initialized(self, camera, camera_index):
        """카메라 초기화 완료"""
        self.camera = camera
        self.camera_info_var.set(f"카메라 {camera_index} - {camera.camera_width}x{camera.camera_height}")
        self.camera_select_button.config(state="normal")
        self.log_message(f"카메라 {camera_index} 초기화 완료")
    
    def on_camera_init_failed(self, error_msg):
        """카메라 초기화 실패"""
        self.camera = None
        self.camera_info_var.set("카메라 초기화 실패")
        self.camera_select_button.config(state="normal")
        self.log_message(f"카메라 초기화 실패: {error_msg}")
        messagebox.showerror("오류", f"카메라 초기화 실패:\n{error_msg}")
    
    def log_message(self, message):
        """로그 메시지 추가"""
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)

    @timer_decorator
    def start_server(self):
        """서버 시작"""
        if not self.camera:
            messagebox.showwarning("경고", "먼저 카메라를 선택하세요.")
            return
            
        try:
            # 서버 시작
            host = self.host_var.get()
            port = int(self.port_var.get())
            
            self.pose_server = WebSocketServer(self.camera, host, port)
            self.pose_server.start_server_thread()
            
            self.server_running = True
            self.status_var.set("실행 중")
            self.url_var.set(f"ws://{host}:{port}")
            
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            
            self.log_message(f"서버가 시작되었습니다: ws://{host}:{port}")
            
        except Exception as e:
            self.log_message(f"서버 시작 실패: {e}")
            messagebox.showerror("오류", f"서버 시작 실패:\n{e}")
    
    def stop_server(self):
        """서버 중지"""
        if self.pose_server:
            self.pose_server.stop_server()
            self.server_running = False
            self.status_var.set("중지됨")
            self.connection_var.set("연결 없음")
            self.url_var.set("")
            
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            
            self.log_message("서버가 중지되었습니다.")
    
    def run_calibration(self):
        """캘리브레이션 실행"""
        if not self.camera:
            messagebox.showwarning("경고", "먼저 카메라를 초기화하세요.")
            return
        
        try:
            self.log_message("캘리브레이션 시작...")
            
            # Pygame 초기화
            pygame.init()
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN if FULLSCREEN else 0)
            pygame.display.set_caption("캘리브레이션")
            
            # 캘리브레이션 실행
            homography = calibrate_projector(self.camera, screen)
            
            if homography is not None:
                self.log_message("캘리브레이션 완료")
                messagebox.showinfo("완료", "캘리브레이션이 완료되었습니다.")
            else:
                self.log_message("캘리브레이션 취소됨")
                messagebox.showinfo("취소", "캘리브레이션이 취소되었습니다.")
                
        except Exception as e:
            self.log_message(f"캘리브레이션 실패: {e}")
            messagebox.showerror("오류", f"캘리브레이션 실패:\n{e}")
        finally:
            pygame.quit()
    
    def show_camera_view(self):
        """카메라 화면 표시 (디버깅용)"""
        if not self.camera:
            messagebox.showwarning("경고", "먼저 카메라를 초기화하세요.")
            return
        
        try:
            self.log_message("카메라 화면 시작...")
            
            # Pygame 초기화
            pygame.init()
            
            # 카메라 해상도에 맞춰 윈도우 크기 설정
            camera_width = self.camera.camera_width
            camera_height = self.camera.camera_height
            
            # 화면 크기 제한 (최대 1920x1080)
            max_width = 1920
            max_height = 1080
            
            # 비율 유지하면서 크기 조정
            scale = min(max_width / camera_width, max_height / camera_height, 1.0)
            window_width = int(camera_width * scale)
            window_height = int(camera_height * scale)
            
            screen = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
            pygame.display.set_caption(f"카메라 화면 ({camera_width}x{camera_height}) - ESC: 종료, F: 전체화면")
            
            clock = pygame.time.Clock()
            running = True
            fullscreen = False
            
            # 인식 범위 설정 변수
            detection_confidence = 0.5
            presence_confidence = 0.5
            tracking_confidence = 0.5
            
            # 설정 UI - 한글 폰트 사용
            try:
                # Windows 기본 한글 폰트 사용
                font = pygame.font.Font("C:/Windows/Fonts/malgun.ttf", 20)  # 맑은 고딕
            except:
                try:
                    font = pygame.font.Font("C:/Windows/Fonts/gulim.ttc", 20)  # 굴림
                except:
                    try:
                        font = pygame.font.Font("C:/Windows/Fonts/batang.ttc", 20)  # 바탕
                    except:
                        # 폰트를 찾을 수 없으면 기본 폰트 사용
                        font = pygame.font.Font(None, 24)
                        print("한글 폰트를 찾을 수 없어 기본 폰트를 사용합니다.")
            
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                        elif event.key == pygame.K_f:
                            # 전체화면 토글
                            fullscreen = not fullscreen
                            if fullscreen:
                                screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                            else:
                                screen = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
                        elif event.key == pygame.K_UP:
                            # 인식 범위 증가
                            detection_confidence = min(1.0, detection_confidence + 0.1)
                            self.update_detection_settings(detection_confidence, presence_confidence, tracking_confidence)
                        elif event.key == pygame.K_DOWN:
                            # 인식 범위 감소
                            detection_confidence = max(0.1, detection_confidence - 0.1)
                            self.update_detection_settings(detection_confidence, presence_confidence, tracking_confidence)
                        elif event.key == pygame.K_LEFT:
                            # presence confidence 감소
                            presence_confidence = max(0.1, presence_confidence - 0.1)
                            self.update_detection_settings(detection_confidence, presence_confidence, tracking_confidence)
                        elif event.key == pygame.K_RIGHT:
                            # presence confidence 증가
                            presence_confidence = min(1.0, presence_confidence + 0.1)
                            self.update_detection_settings(detection_confidence, presence_confidence, tracking_confidence)
                        elif event.key == ord('d'):
                            # detection confidence 증가
                            detection_confidence = min(1.0, detection_confidence + 0.1)
                            self.update_detection_settings(detection_confidence, presence_confidence, tracking_confidence)
                        elif event.key == ord('f'):
                            # detection confidence 감소
                            detection_confidence = max(0.1, detection_confidence - 0.1)
                            self.update_detection_settings(detection_confidence, presence_confidence, tracking_confidence)
                        elif event.key == ord('p'):
                            # presence confidence 증가
                            presence_confidence = min(1.0, presence_confidence + 0.1)
                            self.update_detection_settings(detection_confidence, presence_confidence, tracking_confidence)
                        elif event.key == ord('o'):
                            # presence confidence 감소
                            presence_confidence = max(0.1, presence_confidence - 0.1)
                            self.update_detection_settings(detection_confidence, presence_confidence, tracking_confidence)
                    elif event.type == pygame.VIDEORESIZE:
                        if not fullscreen:
                            window_width, window_height = event.size
                            screen = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
                
                # 카메라에서 프레임 가져오기
                frame = self.camera.get_frame()
                if frame is not None:
                    # OpenCV BGR을 RGB로 변환
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # 프레임 크기 조정
                    frame_resized = cv2.resize(frame_rgb, (window_width, window_height))
                    
                    # numpy 배열을 pygame surface로 변환
                    frame_surface = pygame.surfarray.make_surface(frame_resized.swapaxes(0, 1))
                    
                    # 화면에 표시
                    screen.blit(frame_surface, (0, 0))
                    
                    # 설정 정보 표시
                    info_text = [
                        f"Detection: {detection_confidence:.1f} (Up/Down)",
                        f"Presence: {presence_confidence:.1f} (Left/Right)",
                        f"Tracking: {tracking_confidence:.1f}",
                        f"F: 전체화면, ESC: 종료"
                    ]
                    
                    for i, text in enumerate(info_text):
                        text_surface = font.render(text, True, (255, 255, 255), (0, 0, 0))
                        screen.blit(text_surface, (10, 10 + i * 25))
                    
                    pygame.display.flip()
                
                clock.tick(30)  # 30 FPS
            
            self.log_message("카메라 화면 종료")
            
        except Exception as e:
            self.log_message(f"카메라 화면 실패: {e}")
            messagebox.showerror("오류", f"카메라 화면 실패:\n{e}")
        finally:
            pygame.quit()
    
    def update_detection_settings(self, detection_confidence, presence_confidence, tracking_confidence):
        """인식 설정 업데이트"""
        try:
            if hasattr(self.camera, 'landmarker'):
                # 새로운 설정으로 landmarker 재생성
                from camera.camera import PoseLandmarkerOptions, BaseOptions, VisionRunningMode
                
                options = PoseLandmarkerOptions(
                    base_options=BaseOptions(model_asset_path=self.camera.model_path),
                    running_mode=VisionRunningMode.VIDEO,
                    num_poses=2,
                    min_pose_detection_confidence=detection_confidence,
                    min_pose_presence_confidence=presence_confidence,
                    min_tracking_confidence=tracking_confidence
                )
                
                # 기존 landmarker 종료
                self.camera.landmarker.close()
                
                # 새로운 landmarker 생성
                from camera.camera import PoseLandmarker
                self.camera.landmarker = PoseLandmarker.create_from_options(options)
                
                self.log_message(f"인식 설정 업데이트: Detection={detection_confidence:.1f}, Presence={presence_confidence:.1f}, Tracking={tracking_confidence:.1f}")
                
        except Exception as e:
            self.log_message(f"인식 설정 업데이트 실패: {e}")
    
    def open_websocket_test(self):
        """웹소켓 테스트 HTML 파일 열기"""
        try:
            import os
            import subprocess
            import webbrowser
            
            # 현재 디렉토리의 websocket_test.html 파일 경로
            html_file_path = os.path.abspath("websocket_test.html")
            
            if os.path.exists(html_file_path):
                # 기본 웹 브라우저로 HTML 파일 열기
                webbrowser.open(f"file://{html_file_path}")
                self.log_message(f"웹소켓 테스트 페이지를 열었습니다: {html_file_path}")
            else:
                self.log_message(f"웹소켓 테스트 파일을 찾을 수 없습니다: {html_file_path}")
                messagebox.showerror("오류", f"웹소켓 테스트 파일을 찾을 수 없습니다:\n{html_file_path}")
                
        except Exception as e:
            self.log_message(f"웹소켓 테스트 파일 열기 실패: {e}")
            messagebox.showerror("오류", f"웹소켓 테스트 파일 열기 실패:\n{e}")

    @timer_decorator
    def update_status(self):
        """상태 업데이트"""
        if self.pose_server and self.server_running:
            if self.pose_server.is_connected():
                self.connection_var.set("연결됨")
            else:
                self.connection_var.set("연결 대기 중...")
            # 최근 응답 시간 표시
            resp_ms = self.pose_server.last_response_time_ms
            self.status_var.set(f"실행 중 (최근 응답: {resp_ms} ms)")
        
        # 1초마다 업데이트
        self.root.after(1000, self.update_status)
    
    def run(self):
        """GUI 실행"""
        self.root.mainloop()
        
        # 종료 시 정리
        if self.pose_server:
            self.pose_server.stop_server()
        if self.camera:
            self.camera.release()

def main():
    """메인 함수"""
    app = GodotServerGUI()
    app.run()

if __name__ == "__main__":
    main() 