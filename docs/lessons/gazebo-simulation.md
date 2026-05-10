# Lesson 0: Gazebo Simulation

**Difficulty:** Beginner  
**Time:** 45 minutes  
**Prerequisites:** ROS2 Humble installed on laptop, Ubuntu 22.04

---

## Overview

Before working with the physical robot, you can test everything in a **simulator**. This lesson introduces two essential ROS2 tools — Gazebo and RViz2 — using the TurtleBot3 Burger as a stand-in for EduBot.

Once EduBot's motors are wired and working, everything you learn here transfers directly to the real robot.

---

## Gazebo vs RViz2 — What's the Difference?

Students often confuse these two tools. They serve completely different purposes:

| | **Gazebo** | **RViz2** |
|---|---|---|
| **What it is** | Physics simulator | Data visualizer |
| **Shows** | Simulated world with physics | Real or simulated sensor data |
| **Physics** | Yes (forces, collisions, dynamics) | No |
| **Use case** | Test algorithms without hardware | Debug sensor data, robot state |
| **When to use** | No physical robot available | Debugging robot during operation |

Think of it this way: **Gazebo replaces the hardware**. **RViz2 replaces your eyes**.

### What Gazebo Provides

- **Accurate physics** — gravity, wheel friction, motor inertia
- **Sensor simulation** — LiDAR, cameras, IMU all produce realistic data
- **3D environment** — walls, obstacles, entire rooms
- **Plugins** — custom behaviors for sensors and actuators

Gazebo is used for:
- Testing SLAM and Nav2 without a physical robot
- Developing control algorithms before deploying to hardware
- Prototyping robot designs
- Running tests in CI pipelines

---

## Part 1: Gazebo Simulation with TurtleBot3

### Step 1: Install TurtleBot3 Packages

On your laptop:

```bash
sudo apt install -y \
  ros-humble-turtlebot3-gazebo \
  ros-humble-turtlebot3-teleop \
  ros-humble-turtlebot3-cartographer \
  ros-humble-turtlebot3-navigation2
```

Set the robot model in your environment:

```bash
echo "export TURTLEBOT3_MODEL=burger" >> ~/.bashrc
source ~/.bashrc
```

---

### Step 2: Launch the Simulation

```bash
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

Gazebo will open showing a TurtleBot3 Burger in a small obstacle course. Give it 30–60 seconds to load — Gazebo is slow on first launch.

!!! tip "First launch is slow"
    Gazebo downloads model files on first use. Subsequent launches are much faster.

---

### Step 3: Drive the Simulated Robot

Open a **second terminal** and run the keyboard teleop:

```bash
ros2 run turtlebot3_teleop teleop_keyboard
```

Controls:
```
Moving around:
   u    i    o
   j    k    l
   m    ,    .

i/,  : forward/backward
j/l  : rotate left/right
k    : stop
```

Drive the robot around the obstacle course. Notice that collisions are physically simulated — the robot bumps into walls realistically.

---

### Step 4: Run SLAM in Simulation

While Gazebo is running, open a **third terminal** and launch SLAM:

```bash
ros2 launch turtlebot3_cartographer cartographer.launch.py use_sim_time:=True
```

This opens RViz2 automatically. Drive around to build the map.

!!! warning "use_sim_time:=True"
    In simulation, all nodes must use simulated time, not wall-clock time. Always pass `use_sim_time:=True` when running nodes alongside Gazebo.

Save the map when done:
```bash
ros2 run nav2_map_server map_saver_cli -f ~/sim_map
```

---

### Step 5: Run Autonomous Navigation in Simulation

Stop SLAM (Ctrl+C in terminal 3), then launch navigation with your saved map:

```bash
ros2 launch turtlebot3_navigation2 navigation2.launch.py \
  use_sim_time:=True \
  map:=$HOME/sim_map.yaml
```

In RViz2:
1. Click **2D Pose Estimate** → click where the robot is in the map → drag to set heading
2. Click **Nav2 Goal** → click anywhere in free space → robot navigates automatically

---

## Part 2: RViz2 Walkthrough

RViz2 works with both simulated and real robots. Here's what you can display:

### Key Display Types

| Display | Topic | Shows |
|---|---|---|
| **RobotModel** | `/robot_description` | 3D robot model from URDF |
| **LaserScan** | `/scan` | LiDAR point cloud |
| **Map** | `/map` | SLAM occupancy grid |
| **Odometry** | `/odom` | Robot pose and velocity arrow |
| **Path** | `/plan` | Nav2 planned path |
| **TF** | — | All coordinate frames |

### How to Add a Display

1. Click **Add** (bottom-left panel)
2. Choose display type
3. Set the **Topic** in the panel that appears
4. Adjust color/size as needed

### Setting the Fixed Frame

The **Fixed Frame** (top of Displays panel) determines the reference coordinate. Use:

- `odom` — for teleop and odometry visualization
- `map` — for SLAM and navigation (after SLAM has run)
- `base_link` — for sensor-relative views

!!! tip "Global Status: Error?"
    If RViz2 shows "Global Status: Error", the Fixed Frame doesn't exist yet. Switch it to a frame that does exist (check with `ros2 run tf2_tools view_frames`).

---

## Simulation vs Physical Robot

When you're ready to move from simulation to EduBot:

| | Simulation | EduBot physical |
|---|---|---|
| Launch command | `turtlebot3_gazebo turtlebot3_world.launch.py` | `my_robot robot.launch.py` |
| SLAM | `cartographer.launch.py use_sim_time:=True` | `my_robot slam.launch.py` |
| Navigation | `navigation2.launch.py use_sim_time:=True map:=...` | `my_robot navigation.launch.py map:=...` |
| RViz2 | Same — topics and displays are identical | Same |
| `use_sim_time` | Must be `True` | Must be `False` (or omit) |

The ROS2 topics (`/scan`, `/odom`, `/cmd_vel`, `/map`) are identical between simulation and real hardware. The skills you build here transfer directly.

---

## Expected Outcome

- Gazebo opens and robot is visible in the world
- Keyboard teleop moves the robot with physics-accurate collisions
- SLAM builds a 2D map as you drive
- Nav2 navigates to clicked goals autonomously
- RViz2 displays LiDAR scan, map, and robot model

---

## Checkpoint Questions

1. What is the key difference between Gazebo and RViz2?
2. Why must you pass `use_sim_time:=True` when running SLAM in Gazebo?
3. Which RViz2 Fixed Frame should you use during navigation, and why?
4. Name two advantages of testing in simulation before using the physical robot.

---

## Next Step

Ready to drive the real EduBot? Move on to **[Keyboard Teleop](keyboard-teleop.md)** — the commands are identical, just replace the launch files.
