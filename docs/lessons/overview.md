# Lessons Overview

EduBot lessons are designed to be completed in order. Each lesson builds on the previous one — you won't need SLAM until you can drive reliably, and you won't navigate autonomously until you have a map.

---

## Learning Pathway

```
1. Keyboard Teleop ──────────► Drive with keyboard, understand /cmd_vel
        │
        ▼
2. Gesture Control ──────────► Control robot with hand gestures, learn MediaPipe
        │
        ▼
3. Adding LiDAR ─────────────► Mount RPLidar, see obstacle data in RViz2
        │
        ▼
4. SLAM Mapping ─────────────► Build a map of a room, save it
        │
        ▼
5. Autonomous Navigation ────► Give the robot a goal, watch it plan a path
```

---

## Lesson Summary

### 1. [Keyboard Teleop](keyboard-teleop.md)
**Prerequisite:** Robot assembled, ROS2 running  
**Outcome:** Drive the robot with arrow keys, understand velocity commands and the `/cmd_vel` topic

**What you'll learn:**
- How ROS2 nodes send messages
- What a `Twist` message is
- How differential drive steering works

---

### 2. [Gesture Control](gesture-control.md)
**Prerequisite:** Keyboard teleop working, laptop with webcam  
**Outcome:** Control the robot using hand gestures detected by MediaPipe on your laptop

**What you'll learn:**
- How computer vision can generate robot commands
- MediaPipe hand landmark detection
- Running ROS2 nodes across two machines (`ROS_DOMAIN_ID`)

---

### 3. [Adding LiDAR](lidar.md)
**Prerequisite:** Basic driving working  
**Outcome:** Mount and configure the RPLidar, visualize scan data in RViz2

**What you'll learn:**
- How a spinning laser scanner works
- ROS2 sensor topics (`/scan`)
- Visualizing data in RViz2

---

### 4. [SLAM Mapping](slam.md)
**Prerequisite:** LiDAR working  
**Outcome:** Drive the robot around a room and generate a 2D occupancy grid map

**What you'll learn:**
- What SLAM means (Simultaneous Localization and Mapping)
- How slam_toolbox builds a map from LiDAR scans + odometry
- How to save a map for later use

---

### 5. [Autonomous Navigation](navigation.md)
**Prerequisite:** A saved map  
**Outcome:** Click a goal in RViz2 and watch the robot navigate to it while avoiding obstacles

**What you'll learn:**
- Path planning (how does the robot choose a route?)
- Obstacle avoidance
- Nav2 stack overview

---

## Tips for All Lessons

!!! tip "Always check ROS_DOMAIN_ID first"
    If topics from another machine aren't visible, run `echo $ROS_DOMAIN_ID`. Both the Pi and your laptop must show `0` (or the same number). See [Parameters](../api/parameters.md#environment-variables).

!!! tip "Check node health with the dashboard"
    Open `http://<pi-ip>:8888` to see which nodes are running before starting a lesson.

!!! tip "Save your work"
    After each lesson, commit your changes: `git add -A && git commit -m "lesson X complete"`. This gives you a restore point if something breaks later.
