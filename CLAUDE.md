# CLAUDE.md — EduBot Project Context

## Project Purpose

EduBot is an open-source educational differential drive robot targeting pre-university and high school students. The goal is a complete, buildable robot that teaches the full robotics stack — from hardware wiring to autonomous navigation — through progressive, hands-on lessons.

## Current State

| Area | Status |
|---|---|
| Differential drive + encoder feedback | Working on physical robot |
| Gesture control (laptop → Pi) | Working |
| Robot dashboard (Pi, port 8888) | Working |
| Humble code migration | Complete — 4/4 packages build 0 errors |
| Pi hardware setup (Ubuntu 22.04 + Humble install) | Pending |
| SLAM | Pending |
| Autonomous navigation (Nav2) | Pending |
| Documentation site | In progress — gesture-control lesson done |
| YOLOv8 object detection | Planned |

## Technology Stack

| Layer | Technology | Why |
|---|---|---|
| Host OS | Ubuntu 22.04 LTS (Jammy) | Required base for Humble; use on Pi and dev machine |
| Robot OS | ROS2 Humble | LTS (EOL May 2027); required by course |
| SBC | Raspberry Pi 4 (4GB) | Widely available, strong community support |
| Motor control | ros2_control + Arduino Nano | Clean separation: ROS handles logic, Arduino handles real-time |
| Motor driver | Cytron MDD3A (dual PWM mode) | Simple PWM interface, suitable for classroom use |
| SLAM | slam_toolbox | ROS2 native, well-maintained |
| Navigation | Nav2 (1.1.x) | Standard ROS2 navigation stack |
| Gesture vision | MediaPipe (runs on laptop) | No GPU required, easy pip install |
| Object detection | YOLOv8 | Planned — not yet implemented |
| Docs | MkDocs Material | Clean, searchable, free GitHub Pages hosting |

## Directory Structure

```
a2Bot/
├── docs/                        # MkDocs source (Markdown)
│   ├── index.md                 # Home page / feature overview
│   ├── hardware/                # BOM, wiring, power (mostly empty)
│   ├── setup/                   # Pi setup, ROS2 install, camera
│   │   └── ros2-jazzy.md        # To be renamed ros2-humble.md
│   ├── software/                # URDF, Arduino, ros2_control, odometry (empty)
│   ├── lessons/
│   │   └── gesture-control.md   # Only completed lesson doc
│   └── api/                     # ROS2 topics, parameters (empty)
├── robot_firmware.ino/
│   └── robot_firmware.ino.ino   # Arduino firmware (production-ready)
├── ros_control_ws/              # ROS2 workspace (built against Humble)
│   └── src/
│       ├── my_robot/            # Main package: launch, config, URDF, dashboard
│       ├── my_robot_hardware/   # Python hardware interface (serial bridge)
│       ├── my_robot_hardware_interface/  # C++ hardware interface (ros2_control plugin)
│       └── gesture_control/     # MediaPipe gesture node (laptop-side)
├── edubot-robot.service         # systemd: auto-starts robot.launch.py on Pi boot
├── edubot-dashboard.service     # systemd: auto-starts robot_dashboard on Pi boot
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
- Wheel separation: 0.25m
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

Uses the MediaPipe **Tasks API** (`mediapipe.tasks.python.vision.GestureRecognizer`). Model file must exist at `~/gesture_recognizer.task` on the laptop. Old `mp.solutions.hands` API is removed in MediaPipe 0.10+.

## Dashboard / Gesture Demo Architecture

Browser MJPEG streaming was abandoned. Gesture demo shows a fullscreen OpenCV window on the laptop instead. Dashboard only handles status/control, no video.

- `gesture_launcher` (laptop, port 5001) — starts/stops `gesture_node`. On startup POSTs to `http://<pi>:8888/api/gesture/register` so the Pi learns its IP.
- `gesture_node` (laptop) — runs MediaPipe, opens a **fullscreen OpenCV window** (`cv2.WND_PROP_FULLSCREEN`). No Flask, no MJPEG. Press **Q** in window to quit (calls `rclpy.shutdown()`).
- `robot_dashboard` (Pi, port 8888) — UI, WebSocket state, manual drive pad, relays `/api/demo/{start,stop}` to launcher. No camera feed, no `/video_feed` route.

Launcher auto-detects Pi IP from default gateway; on non-hotspot networks pass `--ros-args -p pi_ip:=<pi-ip>`.

### Auto-start on Pi boot

Two systemd units both set `Environment=ROS_DOMAIN_ID=0` so they match SSH shells:

- `edubot-robot.service` — runs `ros2 launch my_robot robot.launch.py`
- `edubot-dashboard.service` — runs `ros2 run my_robot robot_dashboard`

Both source `/opt/ros/humble/setup.bash`. Deploy to Pi:
```bash
sudo cp /path/to/a2Bot/edubot-{robot,dashboard}.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now edubot-robot edubot-dashboard
```

> **Systemd does NOT source `~/.bashrc`.** If `ROS_DOMAIN_ID` lives only in bashrc, the systemd service and your SSH terminal sit on different domains → `ros2 topic echo` appears empty even while the robot moves. Fix: set `Environment=ROS_DOMAIN_ID=0` in `[Service]` **and** export it in `~/.bashrc` on both Pi and laptop.

### Drive pad continuous publish

Drive buttons use `setInterval(fn, 100)` on `mousedown`/`touchstart` and `clearInterval` + zero-twist on `mouseup`/`touchend`. Without this, one click publishes a single `/cmd_vel` message and the robot jerks once then stops.

### Key Implementation Notes

- `_gesture_host` is in-memory only — if dashboard restarts, gesture_launcher must be restarted too
- `gesture_launcher /start` calls `pkill -f gesture_control.gesture_node` before spawning — clears stale processes
- `camera_index` is a ROS parameter (default 4); pass via `--ros-args -p camera_index:=N`
- Gesture window is a native OpenCV window — requires a display (X11/Wayland) on the laptop, not headless-safe
- `robot_dashboard._build_ros_env()` hardcodes Humble paths (`/opt/ros/humble`, `python3.10`)

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
- Do not write Jazzy-specific code — target is Humble (ros2_control 2.x, Nav2 1.1.x)

---

## Pending Work

### Pi hardware setup (do once on the physical Pi)
1. Confirm Ubuntu 22.04 Jammy (not 24.04 Noble)
2. `sudo apt install ros-humble-ros-base ros-humble-ros2-control ros-humble-ros2-controllers ros-humble-hardware-interface ros-humble-pluginlib ros-humble-rclcpp-lifecycle ros-humble-robot-localization ros-humble-slam-toolbox ros-humble-nav2-bringup ros-humble-rplidar-ros`
3. Add `source /opt/ros/humble/setup.bash` and `export ROS_DOMAIN_ID=0` to `~/.bashrc`
4. Build workspace: `cd ~/ros_control_ws && colcon build`
5. Deploy and enable systemd services
6. Smoke-test: `ros2 launch my_robot robot.launch.py` → controller manager must report active

### Testing (after Pi is set up)
- Drive test: send `/cmd_vel`, confirm motor response and `/odom` publishing
- Gesture pipeline: run `gesture_launcher` on laptop → verify gesture→motion
- Nav2: `ros2 launch my_robot navigation.launch.py` → AMCL and DWB must load without errors

### Documentation (after physical robot verified)
- Rename `docs/setup/ros2-jazzy.md` → `docs/setup/ros2-humble.md` and rewrite install instructions
- Update `mkdocs.yml` nav entry
- Write remaining lesson pages: keyboard-teleop, SLAM, Nav2
- Fill empty doc sections: hardware BOM/wiring, Pi setup, URDF, Arduino, ros2_control, odometry
