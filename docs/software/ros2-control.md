# ros2_control

ros2_control is the standard ROS2 hardware abstraction layer. It separates robot logic from hardware details — the controller doesn't know it's talking to an Arduino; it just sends velocity commands to a "joint."

---

## Architecture

```
Nav2 / Teleop / gesture_node
         │ /cmd_vel (Twist)
         ▼
diff_drive_controller       ← converts Twist → wheel velocities
         │ joint commands (rad/s)
         ▼
controller_manager          ← middleware: runs the control loop at 25 Hz
         │
         ▼
MyRobotHardware (C++ plugin)← hardware interface
         │ USB serial at 115200
         ▼
Arduino Nano                ← executes PWM, reads encoders
```

---

## Controller Configuration

File: `ros_control_ws/src/my_robot/config/controllers.yaml`

### Controller Manager

```yaml
controller_manager:
  ros__parameters:
    update_rate: 25        # Hz — control loop rate
    use_sim_time: false
```

The control loop runs at 25 Hz. Lower to 20 Hz if the Pi shows high CPU load.

### Differential Drive Controller

```yaml
diff_drive_controller:
  ros__parameters:
    left_wheel_names:  ["left_wheel_joint"]
    right_wheel_names: ["right_wheel_joint"]
    use_stamped_vel: false    # accept Twist (not TwistStamped)

    wheel_separation: 0.25    # meters, center-to-center
    wheel_radius:     0.033   # meters

    max_wheel_angular_velocity: 3.0   # rad/s

    linear:
      x:
        has_velocity_limits: true
        max_velocity:  0.10   # m/s forward
        min_velocity: -0.10   # m/s backward
    angular:
      z:
        has_velocity_limits: true
        max_velocity:  0.5    # rad/s
        min_velocity: -0.5
```

The `diff_drive_controller` subscribes to `/cmd_vel` and publishes wheel odometry. It also manages the `odom → base_footprint` TF transform when `enable_odom_tf: true`.

### Joint State Broadcaster

```yaml
joint_state_broadcaster:
  ros__parameters:
    joints:
      - left_wheel_joint
      - right_wheel_joint
```

Reads encoder positions and velocities from the hardware interface and publishes them on `/joint_states`.

---

## Hardware Interface (URDF block)

The `<ros2_control>` block in the URDF connects joints to the hardware plugin:

```xml
<ros2_control name="MyRobotHardware" type="system">
  <hardware>
    <plugin>my_robot_hardware_interface/MyRobotHardware</plugin>
    <param name="serial_port">/dev/arduino</param>
    <param name="baud_rate">115200</param>
  </hardware>

  <joint name="left_wheel_joint">
    <command_interface name="velocity"/>
    <state_interface name="position"/>
    <state_interface name="velocity"/>
  </joint>

  <joint name="right_wheel_joint">
    <command_interface name="velocity"/>
    <state_interface name="position"/>
    <state_interface name="velocity"/>
  </joint>
</ros2_control>
```

The hardware plugin (`my_robot_hardware_interface`) translates joint velocity commands into `V<left>,<right>\n` serial messages and parses `F<pos_l>,<pos_r>,<vel_l>,<vel_r>\n` feedback.

---

## Launch Sequence

The robot launches with `robot.launch.py`. Controllers must start in order:

```python
# 1. robot_state_publisher — loads URDF, sets up TF tree
# 2. ros2_control_node — starts hardware interface (connects to Arduino)
# 3. joint_state_broadcaster spawned after 8s — needs controller_manager ready
# 4. diff_drive_controller spawned after 4s
```

!!! tip "Why the delays?"
    The `TimerAction` delays give the `ros2_control_node` time to initialize the hardware interface (open serial port, wait for Arduino boot) before spawning controllers.

---

## Checking Controller Status

```bash
# List active controllers
ros2 control list_controllers

# Expected output:
# diff_drive_controller[diff_drive_controller/DiffDriveController] active
# joint_state_broadcaster[joint_state_broadcaster/JointStateBroadcaster] active

# List hardware interfaces
ros2 control list_hardware_interfaces
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Controller stuck in `inactive` | Hardware interface failed to open serial | Check `/dev/arduino` exists, baud=115200 |
| `/cmd_vel` published but no movement | Controller not `active` | `ros2 control switch_controllers --activate diff_drive_controller` |
| Odometry drifts immediately | `wheel_separation` or `wheel_radius` wrong | Measure your robot and update `controllers.yaml` |
| Control loop slow warnings | CPU overloaded | Lower `update_rate` to 20 in `controllers.yaml` |
