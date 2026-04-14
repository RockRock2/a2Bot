# CLAUDE.md — EduBot Project Context

## Project Purpose

EduBot is an open-source educational differential drive robot targeting pre-university and high school students. The goal is a complete, buildable robot that teaches the full robotics stack — from hardware wiring to autonomous navigation — through progressive, hands-on lessons.

## Technology Stack

| Layer | Technology | Why |
|---|---|---|
| Robot OS | ROS2 Jazzy | Latest LTS ROS2; good community docs for students |
| SBC | Raspberry Pi 4 (4GB) | Widely available, strong community support |
| Motor control | ros2_control + Arduino Nano | Clean separation: ROS handles logic, Arduino handles real-time |
| Motor driver | Cytron MDD3A (dual PWM mode) | Simple PWM interface, suitable for classroom use |
| SLAM | slam_toolbox | ROS2 native, well-maintained |
| Navigation | Nav2 | Standard ROS2 navigation stack |
| Gesture vision | MediaPipe (runs on laptop) | No GPU required, easy pip install |
| Object detection | YOLOv8 | Planned — not yet implemented |
| Docs | MkDocs Material | Clean, searchable, free GitHub Pages hosting |

## Directory Structure

```
edubot-docs/
├── docs/                        # MkDocs source (Markdown)
│   ├── index.md                 # Home page / feature overview
│   ├── hardware/                # BOM, wiring, power (mostly empty)
│   ├── setup/                   # Pi setup, ROS2 install, camera (empty)
│   ├── software/                # URDF, Arduino, ros2_control, odometry (empty)
│   ├── lessons/
│   │   └── gesture-control.md   # Only completed lesson doc
│   └── api/                     # ROS2 topics, parameters (empty)
├── robot_firmware.ino/
│   └── robot_firmware.ino.ino   # Arduino firmware (production-ready)
├── ros_control_ws/              # ROS2 workspace
│   └── src/
│       ├── my_robot/            # Main package: launch, config, URDF, dashboard
│       ├── my_robot_hardware/   # Python hardware interface (serial bridge)
│       ├── my_robot_hardware_interface/  # C++ hardware interface
│       └── gesture_control/     # MediaPipe gesture node (laptop-side)
├── edubot-dashboard.service     # systemd service for auto-start
└── mkdocs.yml                   # Docs site config
```

## Serial Protocol (Arduino ↔ Pi)

- **Command (Pi → Arduino):** `V<left_rad_s>,<right_rad_s>\n` e.g. `V1.047,-1.047\n`
- **Feedback (Arduino → Pi):** `F<left_pos_rad>,<right_pos_rad>,<left_vel>,<right_vel>\n`
- **Rate:** 50Hz (20ms interval)
- **Baud:** 115200

## Key ROS2 Topics

- `/cmd_vel` — Twist velocity commands (subscribed by hardware interface)
- `/odom` — Odometry (published by ros2_control)
- `/scan` — LiDAR scan (RPLidar)

## Robot Hardware Parameters

- Wheel radius: 0.033m
- Encoder resolution: 360 ticks/rev
- Max PWM: 120 (software-limited from 200 to reduce speed)
- PWM deadband: 30
- Motor driver: Cytron MDD3A in dual PWM mode
- Left motor: pins 5 (AIN1), 6 (AIN2)
- Right motor: pins 9 (BIN1), 10 (BIN2)

## Gesture Mappings (MediaPipe)

| Gesture | Action |
|---|---|
| Thumb up | Forward |
| Peace sign | Rotate right |
| L sign | Rotate left |
| No gesture | Stop |

## Coding Conventions

- ROS2 Python nodes use `rclpy`, follow standard node/publisher/subscriber patterns
- Arduino firmware uses plain C++ (no libraries beyond Arduino core)
- Velocity units are always **rad/s** at the serial boundary
- All launch files are Python (`*.launch.py`)
- Config lives in `my_robot/config/`

## Documentation Rules

- All docs written for a high school student audience — assume no prior robotics knowledge
- Use admonitions (`!!! tip`, `!!! warning`) for important callouts
- Every lesson page must include: Overview, Prerequisites, Step-by-step instructions, Expected outcome
- Do not assume the student has a GPU — MediaPipe gesture control runs on laptop CPU

## Prohibited

- Do not introduce ROS1 concepts or packages
- Do not use `rospy` — this project is ROS2 only
- Do not hardcode IP addresses — use ROS_DOMAIN_ID for multi-machine comms
