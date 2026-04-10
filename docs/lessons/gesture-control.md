# Gesture Control

Control EduBot with hand gestures using MediaPipe and ROS2.

## Overview

The gesture control node runs on your laptop, detects hand gestures
via webcam, and publishes velocity commands to the robot over WiFi.

Webcam → MediaPipe → ROS2 /cmd_vel → Robot

## Gestures

| Gesture | Action |
|---|---|
| 👍 Thumb up | Move forward |
| ✌️ Peace sign | Rotate right |
| 🤙 L sign | Rotate left |
| No gesture | Stop |

## Installation

```bash
pip3 install mediapipe
wget -O ~/gesture_recognizer.task \
  https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task
```

## Running

```bash
# Terminal 1 — launch robot on Pi
ros2 launch my_robot robot.launch.py

# Terminal 2 — gesture node on laptop
ros2 run gesture_control gesture_node
```

!!! tip
    Make sure `ROS_DOMAIN_ID` matches on both laptop and Pi.

!!! warning
    Both devices must be on the same WiFi network.