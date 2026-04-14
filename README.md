# EduBot — Educational ROS2 Differential Drive Robot

An open-source educational mobile robot built with ROS2 Jazzy, designed to teach robotics concepts to pre-university and high school students — from hardware wiring to autonomous navigation.

## Hardware

| Component | Specification |
|---|---|
| Computer | Raspberry Pi 4 (4GB) |
| Motors | JGB37-520 DC with encoders |
| Motor Driver | Cytron MDD3A (dual PWM mode) |
| Microcontroller | Arduino Nano |
| LiDAR | RPLidar A1/A2 |
| Camera | USB Webcam |
| Display | lcdwiki 4" HDMI (MPI4008) |
| Battery | 3S LiPo 11.1V |

## Quick Start

```bash
# Launch robot (on Pi)
ros2 launch my_robot robot.launch.py

# Keyboard teleop (on Pi or laptop)
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# Gesture control (on laptop)
ros2 run gesture_control gesture_node
```

## Repository Structure

```
edubot-docs/
├── docs/                    # MkDocs documentation source
├── robot_firmware.ino/      # Arduino firmware (ros2_control serial bridge)
├── ros_control_ws/          # ROS2 workspace
│   └── src/
│       ├── my_robot/                    # Main package
│       ├── my_robot_hardware/           # Python hardware interface
│       ├── my_robot_hardware_interface/ # C++ hardware interface
│       └── gesture_control/             # MediaPipe gesture node (laptop)
├── edubot-dashboard.service # systemd auto-start service
└── mkdocs.yml               # Documentation site config
```

## Documentation Site

Built with MkDocs Material. To serve locally:

```bash
pip install mkdocs-material
mkdocs serve
```

---

## Implementation Status

### Completed

- [x] Differential drive motion — ros2_control + Arduino serial bridge
- [x] Encoder feedback — 50Hz position and velocity reporting
- [x] Keyboard teleoperation — standard `teleop_twist_keyboard`
- [x] Gesture control — MediaPipe hand gesture → `/cmd_vel` over WiFi
- [x] Robot dashboard — terminal UI, runs as systemd service
- [x] Gesture control lesson page — full install and run instructions

### In Progress

- [ ] Documentation site pages — most pages exist in nav but content not yet written

### Remaining — Software Features

- [ ] SLAM mapping — slam_toolbox launch + lesson
- [ ] Autonomous navigation — Nav2 launch + lesson
- [ ] Object detection — YOLOv8 person detection (planned)

### Remaining — Documentation Pages

- [ ] hardware/ — overview, wiring, power, BOM
- [ ] setup/ — Raspberry Pi, ROS2 Jazzy, camera, display
- [ ] software/ — URDF, Arduino firmware, ros2_control, odometry
- [ ] lessons/ — keyboard teleop, LiDAR, SLAM, navigation
- [ ] api/ — topics reference, parameters reference
