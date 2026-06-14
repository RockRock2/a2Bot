# Session Log: 15-05-2026 — Motor Bring-up & Full Drive Stack

## Quick Reference (for AI scanning)
**Confidence keywords:** Arduino, Cytron MDD3A, encoder ISR, MAX_MOTOR_RAD_S, use_stamped_vel, serial buffer overflow, EKF, /diff_drive_controller/odom, brltty, dialout, netplan, avahi, I2C, MPU-9250, left/right swap
**Packages modified:** robot_firmware.ino, my_robot_hardware_interface, my_robot (controllers.yaml, ekf.yaml, robot.launch.py)
**Outcome:** Motors + encoders working, /odom publishing, forward drive confirmed, WiFi SSH set up. Left/right pin swap fix applied (pending test). SLAM is next.

---

## Solutions & Fixes

### 1. Serial test — firmware confirmed working
Used Python serial script to send V commands and read F feedback directly. Confirmed:
- Arduino firmware running at 115200 baud
- F lines at 50Hz

### 2. Motor power — Cytron VIN not connected
Initial V1.0,1.0 test showed no movement. Root cause: motor battery not connected to Cytron VIN/GND. After connecting battery, V4.0,4.0 moved motors.

### 3. Encoder not counting during motor run — EMI noise / startup delay
First 0.5s of motor test showed zero encoder counts, then counting began normally. Confirmed to be motor spin-up time, not noise. Long-term buffer issue addressed separately (see fix 8).

### 4. Right encoder ISR sign fix
Right encoder counted negative while left counted positive for V>0 (forward). Fixed in firmware:
```cpp
// was: rightTicks += (digitalRead(RIGHT_ENC_B) == HIGH) ? -1 : 1;
rightTicks += (digitalRead(RIGHT_ENC_B) == HIGH) ? 1 : -1;
```

### 5. MAX_MOTOR_RAD_S calibration
Was 5.0 (placeholder). Measured ~14.8 rad/s at full PWM 120. Updated in firmware.

### 6. Left motor direction — M+/M− swap at Cytron
Left motor spun backward for positive command. Fixed by physically swapping M+ and M− wires at the Cytron AOUT1/AOUT2 terminals. No firmware change needed.

### 7. Left encoder ISR sign — after M+/M− swap
Swapping motor wires reverses shaft rotation direction, which reverses encoder count direction. After the swap, left encoder counted negative for forward motion. Fixed:
```cpp
// was: leftTicks += (digitalRead(LEFT_ENC_B) == HIGH) ? 1 : -1;
leftTicks += (digitalRead(LEFT_ENC_B) == HIGH) ? -1 : 1;
```

### 8. use_stamped_vel mismatch — robot not moving via ROS2
`twist_to_twist_stamped` node publishes TwistStamped to `/diff_drive_controller/cmd_vel`.
`controllers.yaml` had `use_stamped_vel: false` → type mismatch, messages dropped silently.
Fix: `use_stamped_vel: true` in controllers.yaml.

### 9. Joint states freezing after ~5s — serial buffer overflow
Arduino sends at 50Hz, hardware interface reads one line per 25Hz cycle. Buffer grows by one line per cycle, overflows at ~5s, corrupts incoming data. Fix in `my_robot_hardware.cpp`:
```cpp
// Drain all buffered lines, use only the latest valid F line
std::string latest;
std::string line;
while (!(line = readLine()).empty()) {
    if (line[0] == 'F') latest = line;
}
```

### 10. /odom not publishing — EKF config issues
Two problems:
- `odom0: /wheel_odom` wrong topic → changed to `/diff_drive_controller/odom`
- IMU configured as input but `imu_node` crashed (smbus2 missing) → removed IMU from EKF, disabled imu_node in launch

### 11. brltty blocking Arduino USB (laptop)
`ch341-uart` attached then immediately disconnected on laptop. Cause: brltty (Braille daemon) claimed the CH340 device.
Fix: `sudo apt remove brltty`

### 12. Arduino IDE permission denied
CH340 port at `/dev/ttyUSB0` required dialout group.
Fix: `sudo usermod -aG dialout $USER` + `newgrp dialout`

### 13. Arduino upload "not in sync: resp=0x46"
0x46 = 'F' = Arduino running firmware, not in bootloader. Fix: select "ATmega328P (Old Bootloader)" in Arduino IDE Tools > Processor.

### 14. WiFi setup
```bash
sudo nano /etc/netplan/60-wifi.yaml
# add wlan0 config with SSID + password
sudo chmod 600 /etc/netplan/60-wifi.yaml
sudo netplan apply
```
Pi WiFi IP: `192.168.0.11`. Installed `avahi-daemon` for `a2bot.local` mDNS resolution.

### 15. IMU (MPU-9250) I2C not detected
- Enabled I2C in `/boot/firmware/config.txt`: `dtparam=i2c_arm=on`
- `/dev/i2c-1` present but `i2cdetect -y 1` shows nothing
- Tried: ADD pin to GND, 5V on VCC, verify pin positions — still undetected
- Left for later; EKF uses wheel odometry only

### 16. Left/right motor+encoder pins swapped — software fix
Joint states showed left and right velocities flipped. Root cause: physical wiring has L/R reversed relative to firmware assumptions. Software fix — swapped pin defines in firmware:
```cpp
// After fix:
#define LEFT_AIN1   9   // was 5
#define LEFT_AIN2   10  // was 6
#define RIGHT_BIN1  5   // was 9
#define RIGHT_BIN2  6   // was 10
#define LEFT_ENC_A  3   // was 2 (interrupt)
#define LEFT_ENC_B  11  // was 8
#define RIGHT_ENC_A 2   // was 3 (interrupt)
#define RIGHT_ENC_B 8   // was 11
```
Pending: reflash and verify teleop turns ('j'/'l') work correctly.

---

## Key Parameters Confirmed
- MAX_MOTOR_RAD_S: 14.8 rad/s (measured at full PWM 120)
- PWM_DEADBAND: 30
- MAX_PWM: 120
- TICKS_PER_REV: 360
- Wheel radius: 0.033m, separation: 0.25m
- Arduino udev: CH340, idVendor 1a86, symlink `/dev/arduino` → ttyUSB1
- Pi workspace: `~/a2Bot/ros_control_ws`
- Pi user: `a2bot`

## Files Modified
- `robot_firmware.ino/robot_firmware.ino.ino`: encoder ISR signs, MAX_MOTOR_RAD_S, L/R pin swap
- `ros_control_ws/src/my_robot/config/controllers.yaml`: use_stamped_vel true
- `ros_control_ws/src/my_robot/config/ekf.yaml`: correct odom topic, remove IMU
- `ros_control_ws/src/my_robot/launch/robot.launch.py`: disable imu_node
- `ros_control_ws/src/my_robot_hardware_interface/src/my_robot_hardware.cpp`: serial buffer drain fix

## Pending Tasks
1. Reflash Arduino with L/R pin swap, verify teleop turns work
2. Reserve 192.168.0.11 in router (DHCP lease may change)
3. Debug MPU-9250 I2C (optional — not blocking SLAM)
4. SLAM mapping session
5. Save map → Nav2

## Quick Resume
Full ROS2 drive stack working: Arduino → serial → hardware interface → diff_drive_controller → /odom (EKF wheel-only). Forward drive confirmed. Left/right firmware pin swap applied (reflash pending). WiFi SSH via `a2bot.local`. IMU detected but not responding on I2C — EKF running wheel-only. Next: reflash firmware, test turns, then SLAM.
