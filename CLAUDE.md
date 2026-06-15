# CLAUDE.md — EduBot Project Context

## Project Purpose

EduBot is an open-source educational differential drive robot targeting pre-university and high school students. The goal is a complete, buildable robot that teaches the full robotics stack — from hardware wiring to autonomous navigation — through progressive, hands-on lessons.

## Current State

| Area | Status |
|---|---|
| Humble code migration | ✅ Complete — 4/4 packages build 0 errors |
| Pi colcon build | ✅ Working (must `source /opt/ros/humble/setup.bash` first) |
| RPLidar A1/A2 | ✅ Working — `/dev/rplidar` udev rule, 115200 baud, ~7 Hz |
| RViz2 scan visualization (laptop) | ✅ Working via `ROS_DOMAIN_ID=0` over WiFi |
| Differential drive + encoder feedback | ✅ Working — `/odom` position.x increases steadily on forward drive |
| Teleop / turning | ✅ Working — left wheel reverse wiring fixed (pin 10 wire reseated) |
| WiFi SSH | ✅ Pi at 192.168.0.11, avahi `a2bot.local` enabled |
| IMU (MPU-9250) | ⚠️ I2C wired but not detected — EKF running wheel-only for now |
| Gesture control (laptop → Pi) | Working (untested this session) |
| Robot dashboard (Pi, port 8888) | Working (untested this session) |
| Pi hardware setup (Ubuntu 22.04 + Humble) | ✅ Complete — build + LiDAR verified |
| SLAM | ✅ Map saved at `/home/a2bot/maps/room.yaml` (55×75 cells @ 0.05 m/cell) |
| Autonomous navigation (Nav2) | ⚠️ Launch working — nav goal test pending |
| Documentation site | ✅ All lessons written, Humble throughout, GitHub Actions auto-deploy |
| Course slides (Day 3 + Day 4) | ✅ ROS2 pptx versions created |
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
│   ├── setup/
│   │   ├── raspberry-pi.md      # Pi flashing + first-boot steps
│   │   └── ros2-humble.md       # Full Humble install guide (Ubuntu 22.04)
│   ├── software/
│   │   ├── arduino.md           # Serial protocol, pin map, firmware guide ✅
│   │   ├── odometry.md          # Diff-drive, encoders, IMU, EKF theory ✅
│   │   ├── urdf.md              # (stub)
│   │   └── ros2-control.md      # (stub)
│   ├── lessons/
│   │   ├── gazebo-simulation.md # Lesson 0: Gazebo + RViz2 + TurtleBot3 ✅
│   │   ├── keyboard-teleop.md   # Lesson 1 ✅
│   │   ├── gesture-control.md   # Lesson 2 ✅
│   │   ├── lidar.md             # Lesson 3 ✅
│   │   ├── slam.md              # Lesson 4 ✅
│   │   └── navigation.md        # Lesson 5 ✅
│   └── api/                     # ROS2 topics, parameters (empty)
├── .github/workflows/docs.yml   # Auto-deploys MkDocs to gh-pages on push
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
├── 4th Day caftra intermediate A2BOT - ROS2.pptx  # Course slides Day 4 (ROS2 updated)
├── 3rd Day caftra intermediate - ROS2.pptx         # Course slides Day 3 (new, ROS2)
└── mkdocs.yml                   # Docs site config
```

## Serial Protocol (Arduino ↔ Pi)

- **Command (Pi → Arduino):** `V<left_rad_s>,<right_rad_s>\n` e.g. `V1.047,-1.047\n`
- **Feedback (Arduino → Pi):** `F<left_pos_rad>,<right_pos_rad>,<left_vel>,<right_vel>\n`
- **Rate:** 50Hz (20ms interval)
- **Baud:** 115200

## LiDAR Hardware

- **Model:** RPLidar A1 or A2 (confirmed: firmware 1.29, hardware rev 7)
- **Baud rate:** 115200 (verified on physical hardware — set explicitly in `robot.launch.py`)
- **Scan rate:** ~7 Hz on Pi (10 Hz native; USB overhead reduces it slightly)
- **Max range:** 12 m (scan mode: Sensitivity)
- **udev rule:** `/etc/udev/rules.d/99-rplidar.rules` → `ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60"` → symlink `/dev/rplidar`
- **Standalone test:** `ros2 run rplidar_ros rplidar_node --ros-args -p serial_port:=/dev/rplidar -p serial_baudrate:=115200`

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

## Known Issues / Gotchas

- **`colcon build` fails with `ament_cmake` not found** — you forgot to `source /opt/ros/humble/setup.bash` before building. Always source first.
- **Gazebo TurtleBot3 spawn timeout** — on first launch, Gazebo downloads models and the `/spawn_entity` service times out. Fix: `git clone https://github.com/osrf/gazebo_models.git ~/.gazebo/models/` then retry.
- **`odometry_node.py` had wrong TPR** — was `3000` (placeholder), corrected to `360` (matches Arduino firmware). Commit `05d4094`.
- **WS_ziad reference workspace** at `/home/rock-ubuntu/Desktop/A2_bot/WS_ziad` — ROS1-based reference from the course. Useful for Nav2 config parameters and modular launch file structure. Do NOT use its serial bridge or hector_slam.
- **rplidar_ros buffer overflow** — apt-installed `rplidar_ros` on Humble crashes with "buffer overflow detected". Fix: build from source (`git clone -b ros2 https://github.com/Slamtec/rplidar_ros.git` into workspace) or pass `-p channel_type:=serial`. The `rplidar_composition` node in `robot.launch.py` is unaffected.
- **Pi workspace path** — Pi workspace root is `~/a2Bot/` (install at `~/a2Bot/install/`, source at `~/a2Bot/src/`). Not `~/a2Bot/ros_control_ws/` as previously noted. Always edit source under `~/a2Bot/src/` and rebuild from `~/a2Bot/`.
- **nav2_params.yaml `critics` → `plugins`** — DWBLocalPlanner in Humble uses `plugins:` not `critics:` for trajectory critics list. Fixed in `config/nav2_params.yaml` FollowPath section.
- **controllers.yaml invalid params** — `cmd_vel_topic` and `max_wheel_angular_velocity` are not valid diff_drive_controller parameters in Humble — they cause controller configure to fail. Removed.
- **Port 8888 in use** — if robot.launch.py is killed and relaunched quickly, the dashboard port may still be held. Run `pkill -f robot_dashboard` before relaunching.
- **map_saver tilde path** — `map_saver_cli -f ~/maps/room` fails if `~/maps/` doesn't exist. Run `mkdir -p ~/maps` first. Also use absolute paths (not `~`) when passing `map:=` to navigation.launch.py.
- **Left wheel reverse wiring** — Arduino pin 10 (LEFT_AIN2) → Cytron signal wire was broken/disconnected. Fixed by replacing/reseating wire. ✅ Resolved.

---

## Pending Work

### Motors + Drive Stack (2026-06-15)
- Arduino wired, udev rule `/dev/arduino` (CH340: `idVendor=="1a86"`, symlink → ttyUSB1)
- Firmware: right encoder ISR sign fixed, MAX_MOTOR_RAD_S=14.8 measured, left encoder ISR flipped after M+/M− swap
- Left motor M+/M− swapped at Cytron to correct forward direction
- Left/right motor+encoder pins swapped in firmware (software fix — physical wiring was L/R reversed)
- `use_stamped_vel: true` in controllers.yaml (twist_to_twist_stamped publishes TwistStamped)
- EKF: odom topic corrected to `/diff_drive_controller/odom`; IMU removed (wheel-only for now)
- Hardware interface serial buffer drain fix: read all pending lines per cycle, use latest
- `/odom` confirmed publishing; forward drive confirmed working
- Motor self-test added to firmware (`#define MOTOR_TEST 1` in robot_firmware.ino.ino) — runs 4-step FWD/REV sequence on boot for diagnosis; set back to 0 for normal use
- Left wheel reverse fixed — pin 10 (LEFT_AIN2) wire from Arduino to Cytron reseated ✅; teleop turns ('j'/'l') verified

### WiFi ✅ (2026-05-15)
- Pi connected to home WiFi via netplan (`/etc/netplan/60-wifi.yaml`)
- IP: `192.168.0.11` (DHCP — reserve in router for stability)
- `avahi-daemon` installed → `ssh a2bot@a2bot.local` works on LAN
- Pi `~/.bashrc` sources `/opt/ros/humble/setup.bash` and workspace `install/setup.bash`

### IMU (MPU-9250) — blocked
- Wired: VCC→Pin1(3.3V), GND→Pin6, SDA→Pin3, SCL→Pin5
- I2C enabled in `/boot/firmware/config.txt` (`dtparam=i2c_arm=on`)
- `i2cdetect -y 1` shows no devices — module not responding
- `imu_node` disabled in `robot.launch.py` (commented out) until I2C resolved
- EKF runs wheel-odometry-only in the meantime

### SLAM ✅ (2026-06-15)
- Map saved at `/home/a2bot/maps/room.yaml` + `room.pgm` (55×75 cells @ 0.05 m/cell)
- `mkdir -p ~/maps` required before first save

### Nav2 ⚠️ (2026-06-15 — launch working, nav goal pending)
- Launch: `ros2 launch my_robot navigation.launch.py map:=/home/a2bot/maps/room.yaml`
- Fixed: `critics:` → `plugins:` in `nav2_params.yaml` FollowPath section (Humble DWB API)
- Fixed: removed `cmd_vel_topic` and `max_wheel_angular_velocity` from `controllers.yaml`
- All Nav2 nodes now launch without crash
- **Next:** Set 2D Pose Estimate in RViz2, send Nav2 goal, confirm autonomous navigation works

### Documentation (remaining stubs)
- `docs/hardware/` — BOM, wiring diagram, power system
- `docs/software/urdf.md` — robot model explanation
- `docs/software/ros2-control.md` — controller manager, diff_drive_controller
- `docs/api/` — topics and parameters reference

### Course slides (manual edits still needed)
- Day 4 pptx: slides 13-15 / 29-31 ("ROS master & slave") need concept rewrite for ROS2 DDS
- Day 4 pptx: slides 11/27 (Windows IP config) — simplify to "same WiFi + ROS_DOMAIN_ID=0"
- Day 3 pptx: visual formatting (font sizes, code box styling) needs review in PowerPoint
