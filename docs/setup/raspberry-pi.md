# Raspberry Pi Setup

This page walks through setting up a fresh Raspberry Pi 4 for EduBot. By the end you'll have Ubuntu 24.04, all dependencies installed, and the robot workspace ready to build.

---

## Prerequisites

- Raspberry Pi 4 (4 GB recommended)
- microSD card, 32 GB or larger (fast card: A2 rated)
- Laptop with SD card reader
- Monitor, keyboard, and mouse (for initial setup) or HDMI cable + USB hub

---

## Step 1: Flash Ubuntu 24.04

Ubuntu 24.04 LTS (Noble) is required for ROS2 Jazzy.

1. Download **Raspberry Pi Imager**: https://www.raspberrypi.com/software/
2. Open Imager → Choose OS → Other general-purpose OS → Ubuntu → **Ubuntu Server 24.04 LTS (64-bit)**
3. Choose your SD card
4. Click the gear icon ⚙ to set:
   - Hostname: `edubot`
   - Username: `rock`, password of your choice
   - Wi-Fi SSID and password (your home network)
   - Enable SSH
5. Write and eject

---

## Step 2: First Boot

Insert the SD card and power on. Wait 2 minutes for first-boot setup.

SSH in from your laptop:
```bash
ssh rock@edubot.local
# If that doesn't work, find the IP on your router and use:
# ssh rock@<pi-ip>
```

Update the system:
```bash
sudo apt update && sudo apt upgrade -y
sudo reboot
```

---

## Step 3: Set Hostname and Timezone

```bash
sudo hostnamectl set-hostname edubot
sudo timedatectl set-timezone America/New_York   # change to your timezone
timedatectl status
```

---

## Step 4: Configure Static IP (optional but recommended)

A static IP makes SSH and the dashboard URL predictable.

```bash
# Find your network interface name
ip link show

# Edit netplan config
sudo nano /etc/netplan/50-cloud-init.yaml
```

Add a static IP:
```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: false
      addresses: [192.168.1.100/24]
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
  wifis:
    wlan0:
      dhcp4: true
      access-points:
        "YourWiFiName":
          password: "YourPassword"
```

```bash
sudo netplan apply
```

---

## Step 5: Enable I2C (for IMU)

```bash
sudo apt install -y i2c-tools
sudo raspi-config   # or edit /boot/firmware/config.txt
# Interface Options → I2C → Enable

# Verify IMU is detected after wiring
sudo i2cdetect -y 1
# Should show 68 at address 0x68
```

---

## Step 6: Serial Port Access (for Arduino)

```bash
sudo usermod -aG dialout rock
# Log out and back in for this to take effect
```

---

## Step 7: Install Python Dependencies

```bash
sudo apt install -y python3-pip python3-smbus2

# Dashboard dependencies
pip3 install fastapi uvicorn requests
```

---

## Step 8: Clone the EduBot Repository

```bash
cd ~
git clone https://github.com/RockRock2/a2Bot.git edubot-docs
```

---

## Step 9: Set ROS_DOMAIN_ID

This must match on all machines:

```bash
echo "export ROS_DOMAIN_ID=0" >> ~/.bashrc
source ~/.bashrc
```

---

## Next Steps

- [ROS2 Jazzy Install](ros2-jazzy.md)
- [Camera Setup](camera.md)
