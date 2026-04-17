# Lesson 5: Autonomous Navigation

**Difficulty:** Intermediate–Advanced  
**Time:** 1–2 hours  
**Prerequisites:** Saved map from Lesson 4

---

## Overview

Autonomous navigation means the robot can move to a goal position on its own — planning a path around obstacles without any human input. EduBot uses **Nav2**, the standard navigation stack for ROS2.

---

## Background: How Nav2 Works

```
You click a goal in RViz2
         │
         ▼
Nav2 BT Navigator — runs a behaviour tree (plan → execute → monitor)
         │
         ├── Global Planner — finds a path from current position to goal
         │       (searches the static map for a clear route)
         │
         ├── Local Planner — follows the path while avoiding dynamic obstacles
         │       (uses live /scan data to dodge things not on the map)
         │
         └── /cmd_vel → diff_drive_controller → Arduino → Motors
```

---

## Step 1: Launch Navigation

You need three things running simultaneously:

**Terminal 1 — Robot stack (Pi):**
```bash
ros2 launch my_robot robot.launch.py
```

**Terminal 2 — Navigation stack (Pi):**
```bash
ros2 launch my_robot navigation.launch.py map:=~/maps/my_room.yaml
```

Wait for Nav2 to report `Nav2 is ready`:
```
[INFO] [lifecycle_manager]: Managed nodes are active
```

**Terminal 3 — RViz2 (laptop):**
```bash
rviz2
```

---

## Step 2: Set Up RViz2

In RViz2:
1. Fixed Frame: `map`
2. Add → **Map** → Topic: `/map`
3. Add → **RobotModel**
4. Add → **LaserScan** → Topic: `/scan`
5. Add → **Path** → Topic: `/plan`

You should see your saved map loaded, with the robot model roughly in the right position.

---

## Step 3: Set the Initial Pose

Nav2 needs to know where the robot currently is on the map. Use **2D Pose Estimate** in RViz2 (top toolbar):

1. Click the **2D Pose Estimate** button
2. Click on the map at the robot's actual current position
3. Drag to set the orientation (which direction it faces)

The robot should localize — the LiDAR scan should line up with the map walls.

---

## Step 4: Send a Goal

1. Click the **Nav2 Goal** button in RViz2 (or **2D Nav Goal**)
2. Click anywhere on the free (white) space of the map
3. Drag to set the goal orientation

The robot will:
1. Plan a path (shown as a green line)
2. Drive along the path
3. Stop at the goal

---

## Understanding the Nav2 Config

Config file: `ros_control_ws/src/my_robot/config/nav2_params.yaml`

Key parameters:

```yaml
# Robot footprint — must match your robot dimensions
robot_radius: 0.15  # meters (safe stopping distance)

# Velocity limits (should match controllers.yaml)
max_vel_x: 0.10
min_vel_x: -0.10
max_vel_theta: 0.5
```

---

## Expected Outcome

- Robot drives to the clicked goal without hitting obstacles
- Path shown in RViz2 goes around walls
- Robot stops and rotates to the goal orientation

---

## Checkpoint Questions

1. What is the difference between the global planner and the local planner?
2. What happens if you place a new obstacle (like a chair) that wasn't in the map?
3. Why does Nav2 need a 2D Pose Estimate at startup?
4. What does `robot_radius` control in Nav2?

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "Could not find valid path" | Goal is in occupied space — click in white (free) area |
| Robot localizes poorly | Re-do the 2D Pose Estimate more carefully |
| Robot drives into walls | Check LiDAR frame_id matches URDF; check robot_radius |
| Nav2 nodes not starting | Check RAM: `free -h`. Nav2 needs ~700 MB free |

---

## Next Steps

Congratulations — you've completed the full EduBot lesson sequence! From here you could:

- Add **object detection** with YOLOv8 (planned)
- Create custom navigation behaviours using Nav2 BT (Behaviour Trees)
- Add more sensors (depth camera, additional IMU)
- Contribute improvements back to the EduBot project
