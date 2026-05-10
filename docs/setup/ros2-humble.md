# ROS2 Humble Install

ROS2 Humble Hawksbill is the LTS release we use for EduBot. It runs on **Ubuntu 22.04 LTS (Jammy)** and is supported until May 2027. Install it on both the Raspberry Pi and your laptop.

---

## Prerequisites

- Ubuntu 22.04 LTS (Jammy) — required for Humble
- Internet connection
- ~2 GB disk space

!!! warning "Ubuntu version matters"
    ROS2 Humble requires Ubuntu **22.04 Jammy**, not 24.04 Noble. If your Pi is running a different version, flash a fresh Ubuntu Server 22.04 image before continuing.

---

## Step 1: Add ROS2 Repository

```bash
# Install prerequisites
sudo apt install -y software-properties-common curl

# Add ROS2 GPG key
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg

# Add the repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update
```

---

## Step 2: Install ROS2

**On the Raspberry Pi (server, no GUI):**
```bash
sudo apt install -y ros-humble-ros-base
```

**On your laptop (full desktop, includes RViz2):**
```bash
sudo apt install -y ros-humble-desktop
```

---

## Step 3: Install EduBot Dependencies

```bash
sudo apt install -y \
  python3-colcon-common-extensions \
  python3-rosdep \
  ros-humble-ros2-control \
  ros-humble-ros2-controllers \
  ros-humble-hardware-interface \
  ros-humble-pluginlib \
  ros-humble-rclcpp-lifecycle \
  ros-humble-controller-manager \
  ros-humble-robot-localization \
  ros-humble-slam-toolbox \
  ros-humble-nav2-bringup \
  ros-humble-rplidar-ros \
  ros-humble-teleop-twist-keyboard \
  ros-humble-tf2-tools
```

---

## Step 4: Source ROS2 Automatically

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
echo "export ROS_DOMAIN_ID=0" >> ~/.bashrc
source ~/.bashrc
```

Verify:
```bash
ros2 --version
# ros2 2.x.x (humble)
```

!!! tip "ROS_DOMAIN_ID"
    `ROS_DOMAIN_ID=0` must be set identically on the Pi **and** your laptop. Without this, topics from the robot won't appear on your laptop even when you're on the same network.

---

## Step 5: Initialize rosdep

```bash
sudo rosdep init
rosdep update
```

---

## Step 6: Build the EduBot Workspace

```bash
cd ~/ros_control_ws

# Install ROS dependencies from package.xml files
rosdep install --from-paths src --ignore-src -r -y

# Build all packages
colcon build

# Source the workspace
echo "source ~/ros_control_ws/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

The build takes 3–8 minutes on a Pi 4. Warnings are normal; errors are not.

Expected output:
```
Summary: 4 packages finished [Xs]
  0 packages had stderr output
```

---

## Step 7: Verify the Build

```bash
# Check packages are found
ros2 pkg list | grep my_robot
# Should show: my_robot  my_robot_hardware  my_robot_hardware_interface  gesture_control

# Test launch (hardware interface will fail without Arduino connected — that's OK)
ros2 launch my_robot robot.launch.py
# Wait 10 seconds then Ctrl+C
# Look for: [rplidar]: RPLidar health status : OK
```

---

## Step 8: Deploy Systemd Services (Pi only)

EduBot includes two systemd services that auto-start on Pi boot:

```bash
sudo cp ~/ros_control_ws/src/my_robot/edubot-robot.service /etc/systemd/system/
sudo cp ~/ros_control_ws/src/my_robot/edubot-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now edubot-robot edubot-dashboard
```

Check status:
```bash
systemctl status edubot-robot
systemctl status edubot-dashboard
```

!!! warning "ROS_DOMAIN_ID in systemd"
    Systemd does NOT read `~/.bashrc`. Both service files already set `Environment=ROS_DOMAIN_ID=0`. If you change the domain ID, update both service files and run `sudo systemctl daemon-reload`.

---

## Rebuilding After Code Changes

```bash
cd ~/ros_control_ws
colcon build --packages-select my_robot gesture_control   # only rebuild changed packages
source install/setup.bash
```

---

## Laptop-Only: Install MediaPipe (for gesture control)

```bash
pip3 install mediapipe opencv-python flask requests
```

Download the gesture recognizer model:
```bash
cd ~
wget https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ros2: command not found` | Run `source /opt/ros/humble/setup.bash` or add to `.bashrc` |
| `ament_cmake` not found during `colcon build` | Source ROS2 before building: `source /opt/ros/humble/setup.bash` |
| `colcon build` fails with missing headers | Run `rosdep install --from-paths src --ignore-src -r -y` first |
| Package not found after build | Run `source install/setup.bash` after build |
| `ROS_DOMAIN_ID` not set | Add `export ROS_DOMAIN_ID=0` to `.bashrc` on both Pi and laptop |
| Topics visible on Pi but not laptop | Verify `ROS_DOMAIN_ID=0` on laptop; must be on the same network |
