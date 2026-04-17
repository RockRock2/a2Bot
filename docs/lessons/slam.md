# Lesson 4: SLAM Mapping

**Difficulty:** Intermediate  
**Time:** 1–2 hours  
**Prerequisites:** LiDAR working (Lesson 3), reliable odometry

---

## Overview

SLAM stands for **Simultaneous Localization and Mapping**. The robot builds a map of its environment *while* figuring out where it is within that map — both at the same time. It's one of the most important algorithms in mobile robotics.

EduBot uses **slam_toolbox**, which is the recommended SLAM package for ROS2.

---

## Background: How SLAM Works

Without a map, the robot only knows its relative position from odometry — which drifts over time. SLAM fixes this by matching LiDAR scans against each other:

```
Scan 1 (from start):   ██████ (wall shape)
Move forward 50 cm
Scan 2 (odometry):     ██████ (slightly different shape)

SLAM: align these scans → measure how much odometry drifted → correct position
```

Over many scans, the robot builds a 2D **occupancy grid map**: each cell is marked as free, occupied, or unknown.

---

## Step 1: Check Prerequisites

Before running SLAM, verify:

```bash
# LiDAR publishing
ros2 topic hz /scan   # should be ~10 Hz

# Odometry publishing  
ros2 topic hz /odom   # should be ~25 Hz

# TF tree is complete (no errors)
ros2 run tf2_tools view_frames
# Open frames.pdf — should show: odom → base_footprint → base_link → laser
```

If `/scan` or `/odom` are missing, fix those before continuing.

---

## Step 2: Launch SLAM

Open three terminals:

**Terminal 1 — Robot stack (Pi):**
```bash
ros2 launch my_robot robot.launch.py
```

**Terminal 2 — SLAM (Pi):**
```bash
ros2 launch my_robot slam.launch.py
```

**Terminal 3 — RViz2 (laptop):**
```bash
rviz2
```

In RViz2:
1. Fixed Frame: `map`
2. Add → **Map** → Topic: `/map`
3. Add → **RobotModel**
4. Add → **LaserScan** → Topic: `/scan`

---

## Step 3: Drive to Build the Map

Use keyboard teleop (in a 4th terminal) to drive around the room:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

**Mapping tips:**
- Drive **slowly** (reduce speed with `,` key in teleop)
- Cover all areas you want in the map
- Return to previously mapped areas — this helps SLAM close loops and reduce drift
- Avoid spinning in place rapidly — this confuses the scan matcher

Watch the map build in real-time in RViz2. Grey = unknown, white = free space, black = obstacles.

---

## Step 4: Save the Map

Once you're happy with the map:

```bash
ros2 run nav2_map_server map_saver_cli -f ~/maps/my_room

# This creates:
# ~/maps/my_room.pgm  — image of the map
# ~/maps/my_room.yaml — metadata (resolution, origin)
```

---

## Step 5: View the Saved Map

```bash
# The .yaml file looks like:
cat ~/maps/my_room.yaml
# image: my_room.pgm
# resolution: 0.05  ← each pixel = 5cm
# origin: [-X, -Y, 0]
# free_thresh: 0.25
# occupied_thresh: 0.65
```

Open `my_room.pgm` in any image viewer. White = free, black = walls, grey = unknown.

---

## Expected Outcome

- A 2D map that matches the room layout
- Walls appear as solid black lines
- Free space is white
- Map saved to `~/maps/`

---

## Checkpoint Questions

1. Why do you need both LiDAR and odometry for SLAM? What happens without each?
2. What does "loop closure" mean in SLAM?
3. If the map shows a wall that isn't there, what might have caused it?
4. What does the map resolution of 0.05 m/pixel mean practically?

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Map stays grey (no data) | Check `/scan` topic is publishing with correct `frame_id: laser` |
| Map grows but is clearly wrong | Check TF tree — `laser` frame must be connected to `base_link` |
| Robot jumps on the map | Odometry drift — calibrate wheel params before SLAM |
| SLAM crashes | Check Pi RAM: `free -h`. SLAM needs ~500 MB free |

---

## Next Step

With a saved map, you can run **[Autonomous Navigation](navigation.md)** — send the robot to any point on the map automatically.
