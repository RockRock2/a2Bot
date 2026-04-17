# Lesson 1: Keyboard Teleop

**Difficulty:** Beginner  
**Time:** 30 minutes  
**Prerequisites:** Robot assembled and powered, ROS2 Jazzy installed on Pi

---

## Overview

In this lesson you will drive EduBot using a keyboard. Along the way you'll learn how ROS2 nodes communicate, what a velocity command looks like, and how differential drive steering works.

---

## Background: How Does the Robot Move?

EduBot receives velocity commands on a topic called `/cmd_vel`. A **topic** is like a radio channel — any node can publish to it, and any node can subscribe to it.

The velocity command is a **Twist** message with two fields:
- `linear.x` — how fast to go forward/backward (meters per second)
- `angular.z` — how fast to rotate left/right (radians per second)

```
Twist message:
  linear.x  =  0.1   →  go forward at 0.1 m/s
  angular.z =  0.5   →  rotate left at 0.5 rad/s
```

The `diff_drive_controller` receives this Twist and calculates:
```
left_wheel_speed  = (linear.x - angular.z × wheelbase/2) / wheel_radius
right_wheel_speed = (linear.x + angular.z × wheelbase/2) / wheel_radius
```

These wheel speeds go to the Arduino, which converts them to PWM.

---

## Step 1: Start the Robot Stack

On the Raspberry Pi (SSH in, or use a keyboard/display):

```bash
ros2 launch my_robot robot.launch.py
```

Wait about 10 seconds for all nodes to start. You should see:
```
[INFO] [robot_dashboard]: Robot dashboard node started
```

Check that controllers are active:
```bash
ros2 control list_controllers
# Expected:
# diff_drive_controller[...] active
# joint_state_broadcaster[...] active
```

---

## Step 2: Install teleop_twist_keyboard

On your laptop (or on the Pi directly):

```bash
sudo apt install ros-jazzy-teleop-twist-keyboard
```

---

## Step 3: Drive!

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

You should see:
```
Reading from the keyboard  and Publishing to Twist!
---------------------------
Moving around:
   u    i    o
   j    k    l
   m    ,    .

i/,  : increase/decrease linear velocity
j/l  : increase/decrease angular velocity
```

**Key mapping:**
| Key | Action |
|---|---|
| `i` | Forward |
| `,` | Backward |
| `j` | Rotate left |
| `l` | Rotate right |
| `u` | Forward + left |
| `o` | Forward + right |
| `k` | Stop |

!!! warning "Start slow!"
    The first time, start with a low speed. The robot's default max is 0.1 m/s forward and 0.5 rad/s rotation. Press `i` to decrease speed if the robot moves too fast.

---

## Step 4: Watch the Topics

Open a second terminal (keep teleop running):

```bash
# Watch velocity commands being sent
ros2 topic echo /cmd_vel

# Watch odometry (robot's estimated position)
ros2 topic echo /odom

# See all active topics
ros2 topic list
```

As you drive, you'll see `/cmd_vel` messages update in real time. `/odom` shows the robot's X/Y position and heading.

---

## Step 5: Visualize in RViz2

```bash
rviz2
```

In RViz2:
1. Set **Fixed Frame** to `odom`
2. Add → **RobotModel** → Topic: `/robot_description`
3. Add → **Odometry** → Topic: `/odom`

Drive the robot and watch the position marker move on screen.

---

## Expected Outcome

- Robot drives smoothly in all directions
- `/cmd_vel` shows Twist messages while driving
- `/odom` updates with position changes
- Robot stops when you release the key (teleop sends a zero Twist on key release)

---

## Checkpoint Questions

1. What is the maximum forward speed (m/s) configured in `controllers.yaml`?
2. If `linear.x = 0` and `angular.z = 0.5`, which direction does the robot turn?
3. Why does the robot stop when you lift your finger from the key?
4. What happens to `/odom` if you drive in a square and return to the start?

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "No movement" | Check `ros2 control list_controllers` — both must be `active` |
| Robot jerks then stops | teleop lost focus — click the terminal window, try again |
| Very slow response | Check CPU load on Pi: `htop`. Try lowering `update_rate` in controllers.yaml |
| Can't see Pi from laptop | Check `ROS_DOMAIN_ID=0` on both machines |
