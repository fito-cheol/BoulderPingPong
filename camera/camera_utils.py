import subprocess
from typing import List, Dict


def get_camera_name_windows(index: int) -> str | None:
    """Retrieve camera name on Windows."""
    try:
        result = subprocess.run(
            ['powershell', '-Command',
             'Get-WmiObject -Class Win32_PnPEntity | Where-Object {$_.Name -like "*camera*" -or $_.Name -like "*webcam*"} | Select-Object Name'],
            capture_output=True, text=True
        )
        cameras = result.stdout.strip().split('\n')[2:]  # Skip header
        return cameras[index].strip() if index < len(cameras) else None
    except Exception:
        return None


def is_virtual_camera(camera_name: str | None) -> bool:
    """Check if the camera is virtual."""
    if not camera_name:
        return False
    virtual_keywords = [
        'virtual', 'vcam', 'nvidia', 'broadcast', 'obs', 'xsplit',
        'webcamoid', 'manycam', 'splitcam', 'wirecast', 'v4l2loopback',
        'droidcam', 'ivcam', 'epoccam', 'kinect', 'leap motion'
    ]
    return any(keyword in camera_name.lower() for keyword in virtual_keywords)


def find_available_cameras(max_index: int = 4) -> List[Dict[str, str | int]]:
    """Find available cameras."""
    available_cameras = []
    print("Searching for cameras...")
    for i in range(max_index):
        try:
            camera_name = get_camera_name_windows(i)
            if camera_name is None:
                break
            available_cameras.append({'index': i, 'name': camera_name})
        except Exception as e:
            print(f"Error searching for camera {i}: {e}")
            continue
    return available_cameras


def select_camera() -> int:
    """Prompt user to select a camera."""
    available_cameras = find_available_cameras()
    if not available_cameras:
        raise RuntimeError("No cameras available.")
    if len(available_cameras) == 1:
        return available_cameras[0]['index']

    print("\n=== Camera Selection ===")
    for i, cam in enumerate(available_cameras):
        print(f"{i + 1}. {cam['name']}")

    while True:
        try:
            choice = input(f"\nSelect a camera (1-{len(available_cameras)}): ")
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(available_cameras):
                selected_camera = available_cameras[choice_idx]
                print(f"\nSelected camera: {selected_camera['name']} (index: {selected_camera['index']})")
                return selected_camera['index']
            else:
                print("Invalid number.")
        except ValueError:
            print("Please enter a number.")
        except KeyboardInterrupt:
            print("\nExiting program.")
            exit()
