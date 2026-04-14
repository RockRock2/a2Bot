# PRD.md — EduBot Product Requirements

## Product Vision

A fully documented, open-source educational robot that a motivated high school student can build and program from scratch. Every hardware choice is justified, every software component is explained, and the learning progression moves from "turn the wheels" to "navigate autonomously."

---

## Feature Set

---

### F1 — Differential Drive Motion

**Description:** The robot moves using two independently controlled DC motors with encoder feedback, managed by ros2_control.

**Behavioral Specification:**
- Receives `/cmd_vel` (geometry_msgs/Twist) and converts to left/right wheel rad/s
- Arduino receives velocity commands over serial at 115200 baud (`V<l>,<r>\n` format)
- Arduino sends position and velocity feedback at 50Hz (`F<lp>,<rp>,<lv>,<rv>\n`)
- ros2_control hardware interface reads feedback and publishes `/odom`

**Acceptance Criteria:**
- [x] Robot moves forward, backward, left, right from keyboard teleop
- [x] Encoder feedback correctly reported back to ROS2
- [x] No motor stall at low speeds (deadband handled in firmware)
- [x] Max speed software-limited to safe classroom level (MAX_PWM 120)

**Edge Cases:**
- Zero velocity command must stop motors (both PWM pins = 0)
- PWM values below deadband (30) are clamped up to avoid stall

---

### F2 — Gesture Control

**Description:** A laptop-side ROS2 node uses a webcam and MediaPipe to detect hand gestures and publish velocity commands to the robot over WiFi.

**Behavioral Specification:**
- Gesture node runs on student's laptop (not the Pi)
- Uses MediaPipe Gesture Recognizer task model
- Publishes `/cmd_vel` when gesture detected, stops when no gesture
- Robot and laptop must share ROS_DOMAIN_ID on same WiFi network

**Gestures:**
- Thumb up → move forward
- Peace sign → rotate right
- L sign → rotate left
- No gesture / unknown → stop

**Acceptance Criteria:**
- [x] Robot responds to all four gesture states
- [x] Stop is immediate when hand leaves frame
- [x] Works on standard laptop CPU (no GPU requirement)
- [x] Installation documented (pip install mediapipe + model download)

**Edge Cases:**
- Multiple hands in frame: use first detected hand
- Poor lighting: documented as user responsibility in lesson page

---

### F3 — Robot Dashboard

**Description:** A terminal UI running on the Pi that displays live robot state (velocity, battery, mode).

**Behavioral Specification:**
- Runs as a systemd service (`edubot-dashboard.service`) for auto-start
- Sources ROS2 environment before launching
- Displays live data from ROS2 topics

**Acceptance Criteria:**
- [ ] Dashboard starts automatically on boot via systemd
- [ ] Shows current velocity, connection status
- [ ] Graceful restart on failure (Restart=on-failure, 5s delay)

---

### F4 — SLAM Mapping

**Description:** Student builds a map of their environment using RPLidar and slam_toolbox.

**Behavioral Specification:**
- Launch file brings up LiDAR, slam_toolbox in online async mode
- Student drives robot with keyboard to map the room
- Map saved to disk for use with Nav2

**Acceptance Criteria:**
- [ ] `slam.launch.py` brings up complete SLAM stack
- [ ] Map can be saved and reloaded
- [ ] Lesson page documents the full workflow with screenshots

---

### F5 — Autonomous Navigation

**Description:** Robot navigates to goal poses in a known map using Nav2.

**Behavioral Specification:**
- Uses saved map from SLAM
- Student sets goal in RViz2
- Robot plans and executes path, avoids obstacles

**Acceptance Criteria:**
- [ ] `navigation.launch.py` brings up Nav2 with loaded map
- [ ] Robot reaches goal pose reliably in open environment
- [ ] Lesson page explains costmaps and recovery behaviors at student level

---

### F6 — Documentation Site

**Description:** Full MkDocs Material site covering hardware build, software setup, and progressive lessons.

**Pages Required:**

| Page | Status |
|---|---|
| index.md | Done |
| hardware/overview.md | Not started |
| hardware/wiring.md | Not started |
| hardware/power.md | Not started |
| hardware/bom.md | Not started |
| setup/raspberry-pi.md | Not started |
| setup/ros2-jazzy.md | Not started |
| setup/camera.md | Not started |
| setup/display.md | Not started |
| software/urdf.md | Not started |
| software/arduino.md | Not started |
| software/ros2-control.md | Not started |
| software/odometry.md | Not started |
| lessons/keyboard-teleop.md | Not started |
| lessons/gesture-control.md | Done |
| lessons/lidar.md | Not started |
| lessons/slam.md | Not started |
| lessons/navigation.md | Not started |
| api/topics.md | Not started |
| api/parameters.md | Not started |

**Acceptance Criteria:**
- Each page uses student-friendly language (no assumed robotics background)
- Hardware pages include photos or diagrams
- Setup pages include exact commands, copy-pasteable
- Lessons include expected output so students know if it's working

---

### F7 — Object Detection (Planned)

**Description:** YOLOv8 person detection via USB webcam.

**Status:** Planned — not yet implemented.

---

## Non-Functional Requirements

- All software must run on Raspberry Pi 4 (4GB) with ROS2 Jazzy
- Gesture control must run on a standard laptop without GPU
- Total build cost should remain accessible for a school budget
- All dependencies must be installable via apt or pip (no custom kernel modules)
