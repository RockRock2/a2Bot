# Odometry

Odometry is how the robot estimates its own position and orientation by counting wheel rotations. EduBot uses encoder-based odometry fused with IMU data through an Extended Kalman Filter (EKF).

---

## Differential Drive Basics

EduBot uses **differential drive** — the simplest and most common locomotion system for ground robots. There are two independently driven wheels. Movement is achieved by varying their speeds:

```
         Left Wheel
              │
Reference ────●──── Forward direction →
  Point       │
         Right Wheel
```

| Command | Left wheel | Right wheel | Result |
|---|---|---|---|
| Forward | +v | +v | Straight ahead |
| Backward | −v | −v | Straight back |
| Turn right | +v | −v | Rotate clockwise |
| Turn left | −v | +v | Rotate counter-clockwise |
| Gentle curve right | +v_fast | +v_slow | Arc to the right |

The `diff_drive_controller` converts a single **Twist** message (`linear.x`, `angular.z`) into individual left/right wheel velocities:

```
v_left  = linear.x − (angular.z × wheel_separation / 2)
v_right = linear.x + (angular.z × wheel_separation / 2)
```

EduBot's wheel separation is **0.25 m** and wheel radius is **0.033 m**.

---

## Rotary Encoders

Each motor on EduBot has a **quadrature encoder** — two output signals (A and B) 90° out of phase. This lets the Arduino count ticks and determine direction.

```
Counter-clockwise:       Clockwise:
A: ─┐ ┌─┐ ┌─           A: ─┐ ┌─┐ ┌─
B: ──┐ ┌─┐ ┌            B:  └─┘ └─┘
     A leads B               B leads A
```

When ENC_A rises:
- ENC_B is HIGH → wheel moving forward → `ticks++`
- ENC_B is LOW  → wheel moving backward → `ticks--`

EduBot's encoders have **360 ticks per revolution**. At 0.033 m wheel radius, each tick = **0.576 mm** of wheel travel.

---

## IMU (Inertial Measurement Unit)

EduBot's 9-DOF IMU provides three types of measurement:

| Sensor | Measures | Unit | Use in EduBot |
|---|---|---|---|
| **Accelerometer** | Linear acceleration (X, Y, Z) | m/s² | Detect if robot is tilted or bumped |
| **Gyroscope** | Angular velocity (roll, pitch, yaw) | rad/s | Measure how fast robot is turning |
| **Magnetometer** | Earth's magnetic field (X, Y, Z) | µT | Compass heading (absolute orientation) |

The gyroscope is the most important for navigation — it measures the robot's yaw rate and is fused with wheel odometry to reduce drift.

!!! tip "Filters"
    Raw IMU data is noisy. EduBot uses a **Kalman Filter** (via `robot_localization`) to optimally blend gyroscope and encoder data. This produces a smoother `/odom` estimate than either sensor alone.

---

## How Wheel Odometry Works

Each encoder tick = a tiny rotation of the wheel. By counting ticks on both wheels and comparing them, the robot can calculate:

- **Distance traveled** — average of left and right wheel distances
- **Heading change** — difference between left and right wheel distances divided by wheelbase

```
dist_per_tick = (2π × wheel_radius) / ticks_per_rev
             = (2π × 0.033) / 360
             = 0.000576 m per tick  (0.576 mm)

d_left  = Δleft_ticks  × dist_per_tick
d_right = Δright_ticks × dist_per_tick

d_center = (d_left + d_right) / 2        ← forward distance
d_theta  = (d_right - d_left) / wheel_separation  ← heading change

x += d_center × cos(θ + d_θ/2)
y += d_center × sin(θ + d_θ/2)
θ += d_θ
```

---

## Data Flow

```
Arduino Nano
  └─ F<pos_l>,<pos_r>,<vel_l>,<vel_r>\n  (50 Hz serial)
        │
  Hardware Interface (C++ plugin)
        │ /joint_states (JointState, 25 Hz)
        │
  diff_drive_controller
        │ /wheel_odom (Odometry)
        │ odom→base_footprint TF
        │
  ekf_node (robot_localization)
        │ /imu/data_raw (Imu)  ← also from imu_node
        │
        └─ /odom (Odometry, filtered)  ← what everything else uses
```

---

## EKF Sensor Fusion

The `ekf_node` fuses wheel odometry with IMU gyroscope data. This reduces drift from wheel slip and encoder noise.

Config file: `ros_control_ws/src/my_robot/config/ekf.yaml`

The EKF output is remapped to `/odom` in the launch file:
```python
remappings=[('odometry/filtered', '/odom')]
```

---

## Checking Odometry

```bash
# Watch live odometry
ros2 topic echo /odom

# Check publish rate (should be ~25 Hz)
ros2 topic hz /odom

# Visualize path in RViz2
# Add: Odometry display, Topic: /odom
```

---

## Odometry Parameters

These are set in `controllers.yaml` for the `diff_drive_controller`:

| Parameter | Value | Description |
|---|---|---|
| `wheel_separation` | 0.25 m | Distance between wheel centers |
| `wheel_radius` | 0.033 m | Wheel radius |
| `open_loop` | false | Use encoder feedback (not dead-reckoning only) |
| `enable_odom_tf` | true | Publish `odom → base_footprint` TF |
| `publish_rate` | 25.0 Hz | Odometry publish rate |

---

## Calibration

Wheel odometry accumulates error over time. Before running SLAM or navigation, verify:

**Straight-line test:**
```bash
# Drive forward 1 meter
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{ linear: { x: 0.1 }, angular: { z: 0.0 } }" --rate 10
# After ~10 seconds (should travel ~1m), stop:
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{}" --once
# Check reported distance:
ros2 topic echo /odom --once
```

**Rotation test:**
```bash
# Rotate 360° (2π rad at 0.5 rad/s ≈ 12.6 seconds)
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{ linear: { x: 0.0 }, angular: { z: 0.5 } }" --rate 10
# Check final heading in /odom — should return near 0
```

If the robot travels less/more than expected, adjust `wheel_radius`. If rotation is off, adjust `wheel_separation`.

---

## Common Issues

| Issue | Cause | Fix |
|---|---|---|
| Robot drifts sideways immediately | `wheel_separation` wrong | Measure center-to-center and update `controllers.yaml` |
| 1 m command = ~0.8 m actual | `wheel_radius` too small | Measure actual wheel radius |
| Odometry jumps at startup | Stale encoder values from last run | Normal — resets each time ros2_control starts |
| `/odom` not publishing | EKF node not running | Check `ros2 node list` for `ekf_filter_node` |
