# Lesson 3: Adding LiDAR

**Difficulty:** Beginner–Intermediate  
**Time:** 45 minutes  
**Prerequisites:** Keyboard teleop working (Lesson 1)

---

## Overview

A LiDAR (Light Detection and Ranging) sensor spins a laser beam 360° and measures the distance to objects at each angle. EduBot uses an RPLidar A1 or A2. In this lesson you'll mount the sensor, install the driver, and visualize the scan data in RViz2.

---

## Background: How LiDAR Works

```
        obstacle
           │
    ╔══════╪══════╗
    ║  →→→→│      ║   laser beam hits obstacle
    ║      │←←←←  ║   reflected pulse returns
    ╚══════╪══════╝
           │
         sensor
```

The sensor measures the **time of flight** of each laser pulse. Since light travels at a known speed, distance = (time × speed of light) / 2.

It does this ~8000 times per second while spinning, producing a complete 360° scan every ~100 ms.

---

## Step 1: Mount the LiDAR

Mount the RPLidar on top of the robot, centered front-to-back, with the USB cable accessible. The URDF already places it at `x=80mm, z=65mm` from `base_link` center.

!!! warning "Cable routing"
    Route the USB cable so it doesn't catch on rotating parts. Use cable ties.

---

## Step 2: Install the ROS2 Driver

```bash
sudo apt install ros-jazzy-rplidar-ros
```

---

## Step 3: Create the udev Rule

```bash
# Find vendor/product IDs
lsusb | grep -i slamtec

# Create udev rule
sudo bash -c 'cat > /etc/udev/rules.d/99-rplidar.rules << EOF
KERNEL=="ttyUSB*", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="rplidar", MODE="0666"
EOF'

sudo udevadm control --reload-rules
sudo udevadm trigger

# Verify
ls -la /dev/rplidar
```

---

## Step 4: Test the LiDAR

```bash
# Test standalone (without full robot stack)
ros2 run rplidar_ros rplidar_composition \
  --ros-args \
  -p serial_port:=/dev/rplidar \
  -p frame_id:=laser
```

In another terminal:
```bash
# Check it's publishing
ros2 topic hz /scan
# Should show ~10 Hz

# Look at a few scan values
ros2 topic echo /scan --field ranges | head -20
```

---

## Step 5: Visualize in RViz2

The RPLidar is already included in `robot.launch.py` — it starts automatically.

```bash
# Start full stack
ros2 launch my_robot robot.launch.py

# On your laptop
rviz2
```

In RViz2:
1. Fixed Frame: `odom`
2. Add → **RobotModel**
3. Add → **LaserScan** → Topic: `/scan` → Style: `Points` → Size: `0.03`

Point EduBot at a wall and slowly approach it. The red point cloud should densify as you get closer.

---

## Expected Outcome

- `/scan` publishes at ~10 Hz
- RViz2 shows 360° ring of points around the robot
- Points correctly match obstacles in the room
- Points disappear in open space (returns `inf` for no obstacle)

---

## Checkpoint Questions

1. What does `range_min` in the `/scan` message mean?
2. Why does the LiDAR return `inf` for some angles?
3. The URDF places the LiDAR 80mm forward from center. Why does this matter for SLAM?
4. What would happen if the `frame_id` in the LiDAR driver didn't match the URDF joint name?

---

## Next Step

Once LiDAR is working, move on to **[SLAM Mapping](slam.md)** — you'll use these scans to build a map.
