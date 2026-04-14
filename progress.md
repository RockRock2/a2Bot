# progress.md — EduBot Development Journal

## Current State (April 2026)

The physical robot is working. It can drive and respond to hand gestures via MediaPipe on a laptop over WiFi. The ROS2 control stack is operational. Focus now shifts to writing the documentation site and implementing the remaining software features (SLAM, Nav2).

---

## Decisions & Reasoning

### Serial protocol: rad/s not PWM
Chose to pass rad/s across the serial boundary (not raw PWM) so that the ROS2 side stays unit-consistent and the hardware interface doesn't need to know motor specifics. The Arduino handles the rad/s → PWM conversion using `MAX_MOTOR_RAD_S` and `MAX_PWM` constants that are easy to tune per-robot.

### MAX_PWM set to 120 (not 255)
Robot was too fast for classroom use at higher PWM. Soft-limited in firmware. Students are told to measure their motor's actual rad/s at full PWM and update `MAX_MOTOR_RAD_S` accordingly.

### PWM deadband = 30
Motors don't move below ~30 PWM due to friction. Deadband implemented in firmware to snap low commands up rather than sending useless near-zero PWM.

### Gesture control runs on laptop, not Pi
Pi 4 CPU is busy with ROS2. MediaPipe runs acceptably on a laptop CPU. Avoids needing a GPU or offloading vision to the Pi. Communicated via ROS_DOMAIN_ID over WiFi.

### Two hardware interface packages
`my_robot_hardware` (Python) and `my_robot_hardware_interface` (C++) both exist. Likely the C++ version is the active one used by ros2_control. This should be verified — it's possible the Python version is legacy or experimental.

### Dashboard as systemd service
`edubot-dashboard.service` auto-starts the terminal dashboard on boot. Sources both `/opt/ros/jazzy/setup.bash` and the workspace `install/setup.bash` in the ExecStart command.

---

## Open Questions

- Which hardware interface is active — Python (`my_robot_hardware`) or C++ (`my_robot_hardware_interface`)? Need to check `controllers.yaml` and the robot launch file.
- Is the EKF (`ekf.yaml`) currently active in the launch? robot_localization fusing IMU data, or just wheel odometry?
- Does the dashboard (`ros2 run my_robot robot_dashboard`) currently work, or is it a stub?
- YOLOv8 object detection — is there any existing code started, or is it fully planned?

---

## Completed Milestones

- **Robot drives** — differential drive, encoder feedback, ros2_control stack all working
- **Gesture control works** — MediaPipe detects thumb up / peace / L sign, publishes cmd_vel
- **Serial protocol stable** — V/F message format, 50Hz, 115200 baud
- **Dashboard service configured** — systemd unit written and placed at project root

---

## Next Priorities

1. Write hardware documentation pages (BOM, wiring, power) — most critical for new builders
2. Write setup pages (Pi setup, ROS2 Jazzy install) — required before any lesson
3. Write keyboard teleop lesson — simplest lesson, natural first step after setup
4. Implement and document SLAM lesson
5. Implement and document Nav2 lesson
6. Investigate and implement YOLOv8 object detection
