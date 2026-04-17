# Display Setup

EduBot optionally mounts a 4" HDMI touchscreen (lcdwiki MPI4008) directly on the robot for a local view of the dashboard.

!!! note "Display is optional"
    You can use EduBot without any attached display — the dashboard is accessible from any browser on the same network at `http://<pi-ip>:8888`.

---

## Supported Display

| Model | lcdwiki MPI4008 |
|---|---|
| Size | 4 inches |
| Resolution | 800 × 480 |
| Interface | HDMI + USB (for touch) |
| Driver | Built into Ubuntu 24.04 (DRM/KMS) |

Other small HDMI displays should also work.

---

## Step 1: Physical Connection

1. Connect the display's HDMI cable to the **Pi's HDMI0 port** (the one closer to the USB-C power port)
2. Connect the USB-A cable for touch input (optional)
3. Power on — the Pi should detect the display automatically

---

## Step 2: Configure Screen Resolution

If the display shows the wrong resolution or no picture:

```bash
# Check current resolution
xrandr   # or: wlr-randr (Wayland)

# Edit boot config
sudo nano /boot/firmware/config.txt
```

Add or modify:
```ini
# Force HDMI even if no display detected at boot
hdmi_force_hotplug=1

# Set resolution for MPI4008
hdmi_group=2
hdmi_mode=87
hdmi_cvt=800 480 60 6 0 0 0
```

```bash
sudo reboot
```

---

## Step 3: Auto-Launch Browser on Boot (optional)

To show the dashboard automatically on boot, install a minimal desktop:

```bash
sudo apt install -y xorg openbox chromium-browser unclutter

# Create autostart file
mkdir -p ~/.config/openbox
cat > ~/.config/openbox/autostart << 'EOF'
unclutter -idle 0 &
chromium-browser --kiosk --no-sandbox http://localhost:8888 &
EOF

# Auto-start X on login
echo "startx" >> ~/.bash_profile
```

Now when the Pi boots and `rock` logs in, it opens the dashboard full-screen on the display.

---

## Step 4: Rotate Display (if needed)

If the display is mounted in portrait orientation:

```bash
# In /boot/firmware/config.txt, add:
display_rotate=1    # 1 = 90°, 2 = 180°, 3 = 270°
```

Or at runtime:
```bash
xrandr --output HDMI-1 --rotate left
```

---

## Without a Physical Display

You can access the dashboard from any device on the same network:

1. Find the Pi's IP address:
   ```bash
   hostname -I
   ```
2. Open a browser on your laptop/phone: `http://<pi-ip>:8888`

The dashboard shows:
- Wi-Fi status and IP address
- Running ROS2 nodes
- Live odometry (position, velocity)
- Encoder velocities
- Drive pad (tap/click to drive)
- Gesture demo start/stop
