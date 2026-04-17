# Camera Setup

EduBot uses a USB webcam on the **laptop** for gesture control (MediaPipe). No camera is needed on the Raspberry Pi — the gesture detection runs entirely on the laptop.

---

## Camera Requirements

| Requirement | Minimum | Recommended |
|---|---|---|
| Resolution | 640×480 | 1280×720 (720p) |
| Frame rate | 15 fps | 30 fps |
| Connection | USB 2.0 | USB 3.0 |
| Driver | UVC (most USB cams) | — |

Most USB webcams sold today are UVC-compatible and work out of the box on Linux.

---

## Step 1: Plug In and Detect

```bash
# List video devices
ls /dev/video*
# Typical output: /dev/video0  /dev/video1  /dev/video2 ...

# Get device details
v4l2-ctl --list-devices
```

Each physical camera usually appears as two or more device files. Try `/dev/video0` first.

---

## Step 2: Find Your Camera Index

OpenCV uses integer indices (0, 1, 2, …) instead of `/dev/videoN`. The index doesn't always match the device number.

```python
# Run this Python snippet to find working camera indices
import cv2
for i in range(6):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Camera index {i}: OK")
        cap.release()
    else:
        print(f"Camera index {i}: not available")
```

```bash
python3 find_cameras.py
```

Note the working index — you'll pass it to `gesture_node` as `camera_index`.

---

## Step 3: Test the Camera

```bash
# Quick test with v4l2-ctl
sudo apt install -y v4l-utils
v4l2-ctl --device=/dev/video0 --stream-mmap --stream-count=3
# If no error: camera works

# Or open a preview with ffplay
ffplay /dev/video0
```

---

## Step 4: Run gesture_node with Your Camera Index

```bash
# Replace 0 with your actual camera index
ros2 run gesture_control gesture_node --ros-args -p camera_index:=0
```

A fullscreen window titled **EduBot Gesture Control** should open. Press **Q** to quit.

---

## Using the Dashboard to Start the Gesture Demo

The dashboard start button passes `camera_index` through `gesture_launcher`:

```bash
ros2 run gesture_control gesture_launcher \
  --ros-args -p camera_index:=0 -p pi_ip:=<pi-ip>
```

Then open `http://<pi-ip>:8888` and click **Start Demo**.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| No `/dev/video*` files | Camera not recognized — try a different USB port |
| `Cannot open camera at index 4` | Wrong index — run the Python snippet to find yours |
| Black window, no image | Camera opened but no frames — try `v4l2-ctl` to diagnose |
| Gesture window too small | It should be fullscreen; check display server (X11/Wayland) |
| Gesture not recognized | Model file missing at `~/gesture_recognizer.task` |

---

## Downloading the Gesture Model

The gesture recognizer requires MediaPipe's `.task` model file:

```bash
cd ~
wget https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task
ls -lh ~/gesture_recognizer.task
# Should be ~4-5 MB
```

The default model path is `~/gesture_recognizer.task`. Override with:
```bash
--ros-args -p model_path:=/path/to/your/gesture_recognizer.task
```
