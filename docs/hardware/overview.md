# Hardware Overview

EduBot is a two-wheeled differential drive robot built on a Raspberry Pi 4. This page describes the physical layout, dimensions, and component placement.

---

## Robot Layout

```
          ┌─────────────────────────────┐
          │   [RPLidar]  [Camera]       │  ← top plate
          │                             │
          │     [Raspberry Pi 4]        │
          │     [Arduino Nano]          │
          │     [Cytron MDD3A]          │
          └──────────────┬──────────────┘
  [Left Wheel]     [Caster]     [Right Wheel]
```

## Dimensions

| Measurement | Value |
|---|---|
| Body length | 250 mm |
| Body width | 200 mm |
| Body height | 80 mm |
| Wheel radius | 33 mm |
| Wheel width | 25 mm |
| Wheelbase (center-to-center) | 250 mm |
| Caster offset (rear) | 100 mm behind center |

## Component Placement (from URDF)

| Component | X offset | Y offset | Z offset |
|---|---|---|---|
| Left wheel | 0 mm | +112.5 mm | -7 mm |
| Right wheel | 0 mm | -112.5 mm | -7 mm |
| Caster wheel | -100 mm | 0 | -25 mm |
| LiDAR | +80 mm | 0 | +65 mm |
| IMU | 0 | 0 | +20 mm |

## System Architecture

```
┌─────────────────────────────────────────────┐
│             Raspberry Pi 4                  │
│                                             │
│  ROS2 Jazzy                                 │
│  ├── robot_state_publisher                  │
│  ├── controller_manager (ros2_control)      │
│  │   ├── diff_drive_controller             │
│  │   └── joint_state_broadcaster           │
│  ├── ekf_node (robot_localization)         │
│  ├── imu_node (MPU-9265 over I2C)          │
│  ├── rplidar (USB)                          │
│  └── robot_dashboard (FastAPI :8888)        │
└───────────────┬─────────────────────────────┘
                │ USB Serial (115200 baud)
┌───────────────▼─────────────────────────────┐
│             Arduino Nano                    │
│  ├── Reads V<l>,<r> velocity commands       │
│  ├── Controls Cytron MDD3A via PWM          │
│  └── Sends F<pos_l>,<pos_r>,<vel_l>,<vel_r> │
└───────────────┬─────────────────────────────┘
                │ PWM signals
┌───────────────▼─────────────────────────────┐
│         Cytron MDD3A Motor Driver            │
│   Left channel ←→ Right channel             │
└──────┬──────────────────────────┬────────────┘
       │                          │
  Left Motor                Right Motor
  (JGB37-520)                (JGB37-520)
  + encoder                  + encoder
```

## Key Components

### Raspberry Pi 4 (4 GB)
The brain of the robot. Runs ROS2 Jazzy and all high-level software. Connects to the Arduino over USB serial.

### Arduino Nano
Handles real-time motor control. The Pi sends velocity commands (rad/s) and the Arduino translates them to PWM signals and reports encoder feedback at 50 Hz.

### Cytron MDD3A
Dual-channel motor driver. Runs in **dual PWM mode** — each channel gets two PWM pins (speed + direction encoded in which pin is driven).

### JGB37-520 DC Motors with Encoders
Geared DC motors with built-in quadrature encoders. Encoder resolution: 360 ticks per revolution.

### RPLidar A1/A2
360° laser scanner connected via USB. Used for obstacle detection, SLAM mapping, and autonomous navigation.

### MPU-9265 IMU
6-axis inertial measurement unit (accelerometer + gyroscope) on I2C bus 1, address `0x68`. Used for sensor fusion in the EKF.

---

## Next Steps

- [Bill of Materials](bom.md) — parts list and where to buy
- [Wiring Guide](wiring.md) — how to connect everything
- [Power System](power.md) — battery and power distribution
