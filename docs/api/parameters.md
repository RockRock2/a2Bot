# ROS2 Parameters

All configurable parameters for EduBot nodes. Parameters can be set at launch time with `--ros-args -p name:=value`.

---

## gesture_node (laptop)

Node: `gesture_control/gesture_node`

| Parameter | Default | Description |
|---|---|---|
| `model_path` | `~/gesture_recognizer.task` | Path to MediaPipe gesture recognizer `.task` model file |
| `camera_index` | `4` | OpenCV camera index. Try `0`, `1`, `2` if the default doesn't open |

```bash
# Example: use camera 0 with a custom model path
ros2 run gesture_control gesture_node \
  --ros-args \
  -p camera_index:=0 \
  -p model_path:=/home/user/models/gesture_recognizer.task
```

---

## gesture_launcher (laptop)

Node: `gesture_control/gesture_launcher`

| Parameter | Default | Description |
|---|---|---|
| `pi_ip` | auto-detect (default gateway) | IP address of the Raspberry Pi. Auto-detection works on the Pi hotspot network |
| `camera_index` | `4` | Passed through to gesture_node when started |

```bash
# On non-hotspot networks, specify the Pi IP manually
ros2 run gesture_control gesture_launcher \
  --ros-args -p pi_ip:=192.168.1.42
```

---

## imu_node (Pi)

Node: `my_robot/imu_node`

Configured in `robot.launch.py`:

| Parameter | Default | Description |
|---|---|---|
| `i2c_bus` | `1` | I2C bus number (`/dev/i2c-1` on Pi) |
| `i2c_address` | `0x68` | MPU-9265 I2C address (0x68 when AD0=LOW, 0x69 when AD0=HIGH) |
| `publish_rate` | `10.0` | Hz — IMU data publish rate |
| `frame_id` | `imu_link` | TF frame for IMU data |

---

## diff_drive_controller (Pi)

Configured in `config/controllers.yaml`.

| Parameter | Default | Description |
|---|---|---|
| `wheel_separation` | `0.25` | Distance (m) between wheel centers — **measure your robot** |
| `wheel_radius` | `0.033` | Wheel radius in meters — **measure your robot** |
| `max_wheel_angular_velocity` | `3.0` | Maximum wheel speed in rad/s |
| `linear.x.max_velocity` | `0.10` | Maximum forward speed (m/s) |
| `angular.z.max_velocity` | `0.5` | Maximum rotation rate (rad/s) |
| `publish_rate` | `25.0` | Odometry publish rate (Hz) |
| `open_loop` | `false` | `true` = dead-reckoning only; `false` = use encoders |
| `enable_odom_tf` | `true` | Broadcast `odom → base_footprint` TF |

!!! warning "Critical parameters"
    `wheel_separation` and `wheel_radius` must match your physical robot exactly. Wrong values cause all odometry, SLAM, and navigation to fail silently.

---

## controller_manager (Pi)

Configured in `config/controllers.yaml`.

| Parameter | Default | Description |
|---|---|---|
| `update_rate` | `25` | Control loop rate in Hz |
| `use_sim_time` | `false` | Set `true` only when running in Gazebo simulation |

---

## Hardware Interface (URDF params, Pi)

Set in `urdf/robot.urdf.xml` under the `<ros2_control>` block:

| Parameter | Default | Description |
|---|---|---|
| `serial_port` | `/dev/arduino` | Serial device for Arduino connection |
| `baud_rate` | `115200` | Must match Arduino firmware baud rate |

---

## odometry_node (Pi, legacy)

!!! note
    `odometry_node` is a legacy Python node — it's been superseded by `diff_drive_controller` + `ekf_node`. Present in the codebase for reference.

| Parameter | Default | Description |
|---|---|---|
| `wheel_radius` | `0.033` | Meters |
| `wheel_separation` | `0.25` | Meters |
| `ticks_per_rev` | `3000` | Encoder ticks per revolution (legacy value — firmware uses 360) |

---

## Environment Variables

These must match across all machines on the same ROS2 network:

| Variable | Required Value | Where to set |
|---|---|---|
| `ROS_DOMAIN_ID` | `0` | `~/.bashrc` on Pi and laptop; `Environment=` in systemd units |

```bash
# Verify on Pi
echo $ROS_DOMAIN_ID

# Verify in systemd unit
systemctl show edubot-robot --property=Environment
systemctl show edubot-dashboard --property=Environment
```

Both should show `ROS_DOMAIN_ID=0`.
