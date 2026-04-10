# EduBot — Educational ROS2 Differential Drive Robot

![EduBot](assets/robot.jpg)

EduBot is an open-source educational mobile robot built with ROS2 Jazzy,
designed to teach robotics concepts from hardware to autonomous navigation.

## Features

- **Differential drive** — two-wheel independent motor control
- **ROS2 Jazzy** — full ROS2 stack on Raspberry Pi 4
- **SLAM** — build maps with RPLidar and slam_toolbox
- **Autonomous Navigation** — Nav2 goal-based navigation
- **Gesture Control** — control robot with hand gestures via MediaPipe
- **Object Detection** — YOLOv8 person detection with webcam

## Hardware

| Component | Specification |
|---|---|
| Computer | Raspberry Pi 4 (4GB) |
| Motors | JGB37-520 DC with encoders |
| Motor Driver | Cytron MDD3A |
| Microcontroller | Arduino Nano |
| LiDAR | RPLidar A1/A2 |
| Camera | USB Webcam |
| Display | lcdwiki 4" HDMI (MPI4008) |
| Battery | 3S LiPo 11.1V |

## Quick Start

```bash
# Launch robot
ros2 launch my_robot robot.launch.py

# Keyboard teleop
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# Gesture control
ros2 run gesture_control gesture_node
```

## Getting Started

New to EduBot? Start here:

1. [Hardware Overview](hardware/overview.md)
2. [Raspberry Pi Setup](setup/raspberry-pi.md)
3. [ROS2 Jazzy Install](setup/ros2-jazzy.md)
4. [First Drive](lessons/keyboard-teleop.md)