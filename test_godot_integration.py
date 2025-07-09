#!/usr/bin/env python3
"""
Godot 연동 테스트 스크립트
Python 서버가 제대로 작동하는지 테스트합니다.
"""

import requests
import json
import time
import sys
from godot_server import GodotPoseServer, Camera

def test_server_connection():
    """서버 연결 테스트"""
    print("=== Godot 연동 테스트 시작 ===")
    
    try:
        # 카메라 초기화 (테스트용)
        print("1. 카메라 초기화 중...")
        camera = Camera()
        print("✓ 카메라 초기화 성공")
        
        # 서버 시작
        print("2. HTTP 서버 시작 중...")
        pose_server = GodotPoseServer(camera, host='localhost', port=8080)
        pose_server.start_server_thread()
        
        # 서버 시작 대기
        time.sleep(2)
        
        # HTTP 요청 테스트
        print("3. HTTP API 테스트 중...")
        response = requests.get('http://localhost:8080/pose_data', timeout=5)
        
        if response.status_code == 200:
            print("✓ HTTP API 응답 성공")
            
            # JSON 파싱 테스트
            try:
                pose_data = response.json()
                print("✓ JSON 파싱 성공")
                
                # 데이터 구조 확인
                if 'timestamp' in pose_data and 'players' in pose_data:
                    print("✓ 데이터 구조 올바름")
                    print(f"  - 타임스탬프: {pose_data['timestamp']}")
                    print(f"  - 플레이어 수: {len(pose_data['players'])}")
                    
                    if pose_data['players']:
                        player = pose_data['players'][0]
                        print(f"  - 손 개수: {len(player.get('hands', []))}")
                        print(f"  - 발 개수: {len(player.get('feet', []))}")
                        print(f"  - 머리 랜드마크: {len(player.get('head', {}))}")
                        print(f"  - 몸 랜드마크: {len(player.get('body', {}))}")
                else:
                    print("✗ 데이터 구조가 올바르지 않음")
                    return False
                    
            except json.JSONDecodeError as e:
                print(f"✗ JSON 파싱 실패: {e}")
                return False
        else:
            print(f"✗ HTTP 응답 오류: {response.status_code}")
            return False
        
        print("\n=== 테스트 성공! ===")
        print("Godot에서 다음 URL로 연결할 수 있습니다:")
        print("http://localhost:8080/pose_data")
        print("\n서버를 계속 실행하려면 Ctrl+C를 누르세요.")
        
        # 서버 계속 실행
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n서버를 종료합니다...")
        
        return True
        
    except Exception as e:
        print(f"✗ 테스트 실패: {e}")
        return False
    finally:
        if 'pose_server' in locals():
            pose_server.stop_server()
        if 'camera' in locals():
            camera.release()

def test_pose_data_format():
    """포즈 데이터 형식 테스트"""
    print("\n=== 포즈 데이터 형식 테스트 ===")
    
    # 예상 데이터 형식
    expected_format = {
        "timestamp": float,
        "players": [
            {
                "hands": [
                    {
                        "x": float,
                        "y": float,
                        "z": float,
                        "visibility": float,
                        "presence": float
                    }
                ],
                "feet": [
                    {
                        "x": float,
                        "y": float,
                        "z": float,
                        "visibility": float,
                        "presence": float
                    }
                ],
                "head": dict,
                "body": dict
            }
        ]
    }
    
    print("예상 데이터 형식:")
    print(json.dumps(expected_format, indent=2))
    print("\n실제 데이터를 확인하려면 서버를 실행하고 브라우저에서")
    print("http://localhost:8080/pose_data 를 방문하세요.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--format":
        test_pose_data_format()
    else:
        test_server_connection() 