# FAQ

Common questions about setting up and running EduBot.

---

## General

**Q: What is ROS_DOMAIN_ID and why do I keep needing to set it?**

ROS2 uses DDS (Data Distribution Service) for communication. The domain ID is like a channel number — only nodes with the same ID can see each other. Default is 0. The tricky part: `systemd` services don't source `~/.bashrc`, so the environment variable must be set explicitly in each `.service` file with `Environment=ROS_DOMAIN_ID=0`. If your Pi's systemd service runs on domain 0 but your SSH terminal is on domain 5 (because `.bashrc` sets it differently), topics will appear empty.

**Q: The robot moved when I ran the command but `/cmd_vel` shows nothing in `ros2 topic echo`. Why?**

Almost certainly a `ROS_DOMAIN_ID` mismatch. The robot is receiving commands within its own domain; your laptop is watching a different domain. Run `echo $ROS_DOMAIN_ID` on both machines — they must match.

**Q: Can I run EduBot on a Raspberry Pi 3?**

Technically yes for basic driving, but SLAM and Nav2 need more RAM than the Pi 3's 1 GB provides. Pi 4 (4 GB) is strongly recommended.

---

## Hardware

**Q: The motors spin but the robot doesn't move straight. How do I fix it?**

Possible causes:
1. One encoder is counting in the wrong direction — check the ISR direction logic in `robot_firmware.ino`
2. `wheel_separation` or `wheel_radius` in `controllers.yaml` is wrong — measure your robot
3. One motor is physically more powerful — adjust `MAX_PWM` per-motor if needed

**Q: The Arduino connects but the hardware interface keeps failing to open `/dev/arduino`.**

1. Verify the udev rule created the symlink: `ls -la /dev/arduino`
2. Check your user is in the `dialout` group: `groups rock` — must show `dialout`
3. Check another process isn't holding the port: `fuser /dev/arduino`
4. Try `screen /dev/arduino 115200` — if you see `F...` lines, the firmware is running

**Q: The IMU calibration message says "keep robot still" but it never finishes.**

The IMU node waits 200 samples at startup. If `smbus2` can't open the I2C bus, it will error immediately. Check:
```bash
sudo i2cdetect -y 1   # should show 68 at 0x68
ls /dev/i2c-1         # should exist
groups rock           # should include i2c (or run with sudo to test)
```

---

## Software

**Q: `colcon build` says a package can't be found.**

Run `rosdep install --from-paths src --ignore-src -r -y` from inside `ros_control_ws/`. This installs all declared dependencies. Then rebuild.

**Q: The gesture window doesn't open when I run `gesture_node`.**

`gesture_node` opens a native OpenCV window — it needs a display. It will fail on headless systems (no `$DISPLAY`). Run it on your laptop, not the Pi. If you're SSHed in without X11 forwarding, the window can't appear.

**Q: The gesture launcher's `/start` button does nothing.**

Check the launcher is running on the laptop: `curl http://localhost:5001/status`. If the Pi can't reach the laptop, the relay will fail silently. The launcher registers its IP with the Pi on startup — if the dashboard was restarted after the launcher, re-restart the launcher too.

**Q: Nav2 starts but immediately says "Planner failed".**

1. Check the initial pose is set (2D Pose Estimate in RViz2)
2. Check the goal is in free (white) space on the map — not in an occupied cell
3. Check `robot_radius` in `nav2_params.yaml` isn't larger than the corridor you're navigating

---

## Systemd Services

**Q: How do I check if the robot services are running?**

```bash
systemctl status edubot-robot
systemctl status edubot-dashboard

# Watch live logs
journalctl -u edubot-robot -f
journalctl -u edubot-dashboard -f
```

**Q: I updated the code but the robot is still running the old version.**

Rebuild and restart:
```bash
cd ~/edubot-docs/ros_control_ws
colcon build --packages-select my_robot
source install/setup.bash
sudo systemctl restart edubot-robot edubot-dashboard
```

**Q: The service fails with "exec format error".**

The `ExecStart` in the `.service` file must source ROS setup scripts via bash:
```ini
ExecStart=/bin/bash -c "source /opt/ros/jazzy/setup.bash && source install/setup.bash && ros2 launch ..."
```
A bare `ros2 launch ...` without sourcing will fail because `ros2` isn't in the default PATH for systemd.
