# ROS2 Topics

All topics published and subscribed to by EduBot nodes. `ROS_DOMAIN_ID=0` must be set on all machines.

---

## Control Topics

| Topic | Type | Direction | Publisher | Subscribers |
|---|---|---|---|---|
| `/cmd_vel` | `geometry_msgs/Twist` | Commands | teleop / gesture_node / Nav2 | diff_drive_controller |

`/cmd_vel` is the main velocity command topic. Send a Twist message to drive the robot:

```bash
# Drive forward at 0.1 m/s
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{ linear: { x: 0.1, y: 0.0, z: 0.0 }, angular: { x: 0.0, y: 0.0, z: 0.0 } }" \
  --rate 10

# Stop
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{}" --once
```

---

## Odometry and State Topics

| Topic | Type | Publisher | Rate |
|---|---|---|---|
| `/odom` | `nav_msgs/Odometry` | ekf_node (filtered) | ~25 Hz |
| `/wheel_odom` | `nav_msgs/Odometry` | diff_drive_controller (raw) | 25 Hz |
| `/joint_states` | `sensor_msgs/JointState` | joint_state_broadcaster | 25 Hz |
| `/tf` | `tf2_msgs/TFMessage` | robot_state_publisher, ekf_node | — |
| `/tf_static` | `tf2_msgs/TFMessage` | robot_state_publisher | latched |

### `/odom` message fields

```
header.frame_id: "odom"
child_frame_id:  "base_footprint"

pose.pose.position.x  — forward distance from start (meters)
pose.pose.position.y  — lateral distance from start (meters)
pose.pose.orientation — quaternion, yaw = heading angle

twist.twist.linear.x  — forward velocity (m/s)
twist.twist.angular.z — rotation rate (rad/s)
```

### `/joint_states` message fields

```
name:     ["left_wheel_joint", "right_wheel_joint"]
position: [left_pos_rad, right_pos_rad]   — cumulative angle
velocity: [left_vel_rad_s, right_vel_rad_s]
```

---

## Sensor Topics

| Topic | Type | Publisher | Rate | Notes |
|---|---|---|---|---|
| `/scan` | `sensor_msgs/LaserScan` | rplidar | ~10 Hz | 360° LiDAR, frame `laser` |
| `/imu/data_raw` | `sensor_msgs/Imu` | imu_node | 50 Hz | MPU-9265, uncalibrated |

### `/scan` message fields

```
header.frame_id: "laser"
angle_min:       -π  (−180°)
angle_max:       +π  (+180°)
range_min:       0.15 m
range_max:       6.0 m (A1) / 12.0 m (A2)
ranges:          array of distances (m) — 360 values at 1°/step
```

---

## Dashboard API Topics (HTTP, not ROS)

The dashboard at `http://<pi-ip>:8888` also exposes these HTTP endpoints:

| Endpoint | Method | Description |
|---|---|---|
| `/api/status` | GET | Full robot state JSON |
| `/ws` | WebSocket | Live state at 1 Hz |
| `/api/wifi/networks` | GET | Scan for Wi-Fi networks |
| `/api/wifi/connect` | POST | Connect to a Wi-Fi network |
| `/api/gesture/register` | POST | Laptop registers its IP for gesture demo |
| `/api/demo/start` | POST | Start gesture demo (relays to gesture_launcher:5001) |
| `/api/demo/stop` | POST | Stop gesture demo |

---

## TF Transform Tree

```
odom
 └── base_footprint  (from ekf_node / diff_drive_controller)
      └── base_link  (from robot_state_publisher)
           ├── left_wheel   (joint state)
           ├── right_wheel  (joint state)
           ├── caster_wheel (static)
           ├── laser        (static: x=+80mm, z=+65mm)
           └── imu_link     (static: z=+20mm)
```

---

## Useful Monitoring Commands

```bash
# List all active topics
ros2 topic list

# Watch odometry
ros2 topic echo /odom

# Check LiDAR
ros2 topic hz /scan

# Check encoder velocities
ros2 topic echo /joint_states

# Watch IMU
ros2 topic echo /imu/data_raw

# Monitor all topics bandwidth
ros2 topic bw /scan
```
