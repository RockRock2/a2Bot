# URDF Robot Model

The URDF (Unified Robot Description Format) is an XML file that describes EduBot's physical structure. ROS2 uses it to build a transform tree (TF), visualize the robot in RViz2, and configure the ros2_control hardware interface.

File location: `ros_control_ws/src/my_robot/urdf/robot.urdf.xml`

---

## Link and Joint Structure

```
base_footprint (virtual ground plane)
    │ base_footprint_joint (fixed, z=40mm)
    └── base_link (robot body, 250×200×80mm)
            ├── left_wheel_joint (continuous, y=+112.5mm)
            │       └── left_wheel (cylinder r=33mm)
            ├── right_wheel_joint (continuous, y=−112.5mm)
            │       └── right_wheel (cylinder r=33mm)
            ├── caster_joint (fixed, x=−100mm, z=−25mm)
            │       └── caster_wheel (sphere r=15mm)
            ├── laser_joint (fixed, x=+80mm, z=+65mm)
            │       └── laser (RPLidar)
            └── imu_joint (fixed, z=+20mm)
                    └── imu_link (MPU-9265)
```

---

## Physical Dimensions

| Link | Geometry | Size |
|---|---|---|
| base_link | Box | 250 × 200 × 80 mm |
| left_wheel | Cylinder | radius 33 mm, length 25 mm |
| right_wheel | Cylinder | radius 33 mm, length 25 mm |
| caster_wheel | Sphere | radius 15 mm |
| laser | Cylinder | radius 40 mm, length 50 mm |
| imu_link | Box | 30 × 30 × 10 mm |

## Joint Positions (relative to base_link)

| Joint | X (mm) | Y (mm) | Z (mm) | Type |
|---|---|---|---|---|
| left_wheel | 0 | +112.5 | −7 | continuous |
| right_wheel | 0 | −112.5 | −7 | continuous |
| caster | −100 | 0 | −25 | fixed |
| laser | +80 | 0 | +65 | fixed |
| imu | 0 | 0 | +20 | fixed |

Wheel joints are rotated `−90°` around X (`rpy="-1.5708 0 0"`) so their cylinder axis aligns with the Y axis (left-right).

---

## Inertial Properties

Inertia values are simplified but sufficient for visualization and basic simulation:

| Link | Mass |
|---|---|
| base_link | 2.0 kg |
| left_wheel | 0.15 kg |
| right_wheel | 0.15 kg |
| caster_wheel | 0.05 kg |

---

## ros2_control Block

The URDF also contains a `<ros2_control>` section that wires the wheel joints to the hardware plugin:

```xml
<ros2_control name="MyRobotHardware" type="system">
  <hardware>
    <plugin>my_robot_hardware_interface/MyRobotHardware</plugin>
    <param name="serial_port">/dev/arduino</param>
    <param name="baud_rate">115200</param>
  </hardware>

  <joint name="left_wheel_joint">
    <command_interface name="velocity"/>  <!-- Pi sends velocity commands -->
    <state_interface name="position"/>   <!-- Arduino reports position -->
    <state_interface name="velocity"/>   <!-- Arduino reports velocity -->
  </joint>
  <!-- same for right_wheel_joint -->
</ros2_control>
```

This means the `diff_drive_controller` can command wheel velocities and read back position/velocity from the same joint object — without knowing anything about serial ports or PWM.

---

## Viewing in RViz2

```bash
# Launch the robot stack first
ros2 launch my_robot robot.launch.py

# In another terminal, open RViz2
rviz2

# Add displays:
#   - RobotModel (Fixed Frame: odom)
#   - TF
#   - LaserScan (Topic: /scan)
```

You should see the 3D model with spinning wheels and the LiDAR rays around it.

---

## Modifying the URDF

If you physically change the robot (move the LiDAR, change wheel size), update the URDF:

1. Edit `robot.urdf.xml`
2. Rebuild: `colcon build --packages-select my_robot`
3. Restart the robot stack: `sudo systemctl restart edubot-robot`

!!! warning "Keep wheel parameters in sync"
    The `wheel_radius` and `wheel_separation` appear in **two places**: the URDF joint positions and `controllers.yaml`. Both must match your physical robot, or odometry will be wrong.
