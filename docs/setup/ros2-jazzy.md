# ROS2 Jazzy Install

ROS2 Jazzy is the 2024 LTS release of ROS2. Install it on both the Raspberry Pi and your laptop.

---

## Prerequisites

- Ubuntu 24.04 LTS (Noble) — required for Jazzy
- Internet connection
- ~2 GB disk space

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
sudo apt install -y ros-jazzy-ros-base
```

**On your laptop (full desktop, includes RViz2):**
```bash
sudo apt install -y ros-jazzy-desktop
```

---

## Step 3: Install Build Tools and Dependencies

```bash
sudo apt install -y \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-vcstool \
  ros-jazzy-ros2-control \
  ros-jazzy-ros2-controllers \
  ros-jazzy-controller-manager \
  ros-jazzy-robot-localization \
  ros-jazzy-slam-toolbox \
  ros-jazzy-nav2-bringup \
  ros-jazzy-rplidar-ros \
  ros-jazzy-teleop-twist-keyboard \
  ros-jazzy-tf2-tools
```

---

## Step 4: Source ROS2 Automatically

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
echo "export ROS_DOMAIN_ID=0" >> ~/.bashrc
source ~/.bashrc
```

Verify:
```bash
ros2 --version
# ros2 2.x.x (jazzy)
```

---

## Step 5: Initialize rosdep

```bash
sudo rosdep init
rosdep update
```

---

## Step 6: Build the EduBot Workspace

```bash
cd ~/edubot-docs/ros_control_ws

# Install ROS dependencies from package.xml files
rosdep install --from-paths src --ignore-src -r -y

# Build
colcon build

# Source the workspace
echo "source ~/edubot-docs/ros_control_ws/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

The build takes 3–8 minutes on a Pi 4. Warnings are normal; errors are not.

---

## Step 7: Verify the Build

```bash
# Check packages are found
ros2 pkg list | grep my_robot
# Should show: my_robot, my_robot_hardware, my_robot_hardware_interface, gesture_control

# Test launch
ros2 launch my_robot robot.launch.py
# Wait 10 seconds then Ctrl+C — no ERROR lines is good
```

---

## Rebuilding After Code Changes

```bash
cd ~/edubot-docs/ros_control_ws
colcon build --packages-select my_robot gesture_control   # faster: only changed packages
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
| `ros2: command not found` | Run `source /opt/ros/jazzy/setup.bash` or add to `.bashrc` |
| `colcon build` fails with missing headers | Run `rosdep install` first |
| Package not found after build | Run `source install/setup.bash` after build |
| `ROS_DOMAIN_ID` not set | Add `export ROS_DOMAIN_ID=0` to `.bashrc` |
