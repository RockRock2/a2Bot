# EduBot Codebase Walkthrough — Presenter Script

This is a spoken-style script for presenting the EduBot software stack as a lesson.
It's written so you can read it almost verbatim, with file references you can pull
up live on screen. Audience: students with some Python/C++ basics but new to ROS2 —
explain ROS2 concepts (node, topic, publisher) the first time each appears.

**Suggested live demo setup:** SSH into the Pi in one terminal, have VS Code open
on the repo in another, and have the dashboard (`http://<pi-ip>:8888`) open in a browser.

---

## 1. The Big Picture (5 min)

> "EduBot is a small two-wheeled robot. It has a Raspberry Pi as its brain, an
> Arduino as its 'hands' that talk directly to the motors, a lidar sensor that
> sees the room, and a web dashboard you can control it from on your phone or
> laptop. Today we're going to open up the code and trace exactly what happens
> from the moment you press a button to the moment the wheels turn."

**Draw this on the board (or show as a diagram):**

```
[Your laptop browser]  --WiFi-->  [Raspberry Pi running ROS2]  --USB serial-->  [Arduino]  --PWM-->  [Motors]
                                          ↑                                         ↓
                                     [RPLidar]                              [Wheel encoders]
```

Key idea to land here: **the Pi runs the "thinking" software (ROS2), the Arduino
runs simple, fast, real-time motor control.** They never run the same code — they
talk to each other over a USB cable using plain text messages, like two people
passing notes.

---

## 2. Repository Tour (5 min)

Open the repo root and show:

```
a2Bot/
├── robot_firmware.ino/         ← code that runs ON the Arduino (not the Pi)
├── ros_control_ws/             ← everything that runs ON the Pi
│   └── src/
│       ├── my_robot/                       ← launch files, configs, dashboard, URDF
│       ├── my_robot_hardware_interface/    ← C++ bridge between ROS2 and the Arduino
│       ├── my_robot_hardware/              ← (legacy Python version, not currently used)
│       └── gesture_control/                ← optional webcam gesture demo (laptop-side)
├── docs/                        ← the student-facing lesson website
└── CLAUDE.md                    ← project notes or AI assistant context (skip in class)
```

> "Notice there are two folders that sound like they do the same thing —
> `my_robot_hardware` and `my_robot_hardware_interface`. Only the second one,
> written in C++, is actually used. The Python one was an earlier attempt and
> is kept around but not loaded. This happens in real projects all the time —
> codebases have leftover pieces. Part of being a good engineer is knowing
> which code is actually 'live'."

---

## 3. The Story of One Button Press (the spine of the talk, 15 min)

This is the core of the lesson — trace a single `/cmd_vel` (drive) command all
the way from a web click to a spinning wheel, then all the way back as odometry.

### Step 1 — The dashboard button (laptop/phone browser)

Open `ros_control_ws/src/my_robot/my_robot/robot_dashboard.py`, scroll to the
`drive-pad` HTML/JS near the bottom (search for `sendDrive`).

> "When you press and hold the forward arrow, this JavaScript fires every
> 100 milliseconds, sending a tiny JSON message — `{linear: 0.3, angular: 0}` —
> to the Pi. It keeps sending it the whole time you're holding the button, and
> the moment you let go, it sends one more message saying 'stop'. Why do you
> think it needs to keep sending it repeatedly, instead of sending it once?"

*(Discussion prompt — answer: if it only sent once, and the connection dropped
or you walked away, the robot would drive forever. Sending continuously means
if anything goes wrong, the robot stops within 100ms.)*

### Step 2 — FastAPI receives it (still on the Pi, but in Python/ROS2 land)

Show the `/api/drive` endpoint:
```python
@app.post("/api/drive")
async def drive(body: dict):
    ...
    _ros_node.cmd_vel_pub.publish(twist)
```

> "This is a regular web server (FastAPI) running on the Pi. It receives the
> JSON, builds a ROS2 message called a `Twist` — which is just two numbers,
> 'how fast forward' and 'how fast turning' — and **publishes** it onto a ROS2
> topic called `/cmd_vel`. A topic is like a radio channel: anyone can publish
> to it, and anyone can tune in and listen (subscribe), without the publisher
> needing to know who's listening."

### Step 3 — diff_drive_controller turns Twist into wheel speeds

> "Something else on the Pi is subscribed to `/cmd_vel` — a piece of standard
> ROS2 software called `diff_drive_controller`. It does the math: if the robot
> has two wheels 25cm apart and you want to drive forward at 0.3 m/s with no
> turning, both wheels need to spin at the same speed. If you want to turn,
> the inside wheel needs to spin slower than the outside wheel. This controller
> does exactly that conversion."

Show `ros_control_ws/src/my_robot/config/controllers.yaml`, point at:
```yaml
wheel_separation: 0.25
wheel_radius:     0.033
```
> "These two numbers are why the controller can do that math — it knows the
> robot's actual physical dimensions."

### Step 4 — The Hardware Interface talks to the Arduino over USB

Open `ros_control_ws/src/my_robot_hardware_interface/src/my_robot_hardware.cpp`,
scroll to `write()`:
```cpp
cmd << "V" << left_wheel_cmd_ << "," << right_wheel_cmd_ << "\n";
writeSerial(cmd.str());
```

> "This is C++, not Python — it runs in a tight, fast loop (25 times a second)
> because motor control needs to be quick and reliable. It takes the wheel
> speeds the controller calculated and writes a plain text line out the USB
> serial cable: something like `V1.047,-1.047`. That's it — a string of text,
> the same as if you typed it into a terminal."

### Step 5 — The Arduino reads it and drives the motors

Open `robot_firmware.ino/robot_firmware.ino.ino`, show `parseVelocityCommand()`
and `setMotorRadS()`.

> "The Arduino is constantly listening on serial. When it sees a line starting
> with 'V', it splits it on the comma, gets two numbers, and converts each one
> into a PWM value — basically 'how hard to push the motor', a number from 0
> to 120. Why 120 and not 255 (the normal Arduino max)?"

*(Point at `MAX_PWM = 120` — answer: it was measured that anything faster made
the robot too fast/hard to control safely for a classroom demo.)*

### Step 6 — The wheels turn, encoders count, and the story reverses

> "Now here's the part most people forget: the Arduino isn't just receiving
> commands, it's also counting. Every tiny rotation of each wheel triggers an
> interrupt — a 'tap on the shoulder' to the Arduino's processor — that
> increments a tick counter. 50 times a second, the Arduino converts those
> ticks into a position and a speed, and sends them back up the same serial
> cable as a different kind of message: `F<left_pos>,<right_pos>,<left_vel>,<right_vel>`."

Show the ISR functions and `Serial.print("F")` block in the firmware.

Back in `my_robot_hardware.cpp`, show `read()`:
```cpp
left_wheel_pos_  = -vals[0];
right_wheel_pos_ = -vals[1];
```

> "Notice the minus signs. This is a great real bug-fix story: the two wheels'
> encoders were wired with opposite electrical conventions, so without this
> negation, the robot's calculated position went **backward** every time it
> physically drove forward. Hardware bugs like this — where the code is
> 'correct' but the wiring doesn't match what the code assumes — are extremely
> common in robotics. This is also a good moment to ask the class: how would
> you even notice this bug? (Answer: drive forward, watch the on-screen map or
> odometry value go the wrong direction.)"

### Step 7 — Odometry, sensor fusion, and the dashboard update

> "Those position/velocity numbers become a ROS2 topic called `/odom` —
> the robot's belief about where it is. We also have an IMU... well, we
> *would*, but it's not currently working (point at `ekf.yaml`'s `odom0_config`)
> — so right now we trust wheel encoders alone, fused through something called
> an EKF (Extended Kalman Filter) that smooths out noise."

Show `ekf.yaml`'s comment about `process_noise_covariance` briefly — don't go
deep into the math, just say:

> "This filter is doing statistics under the hood to combine noisy sensor
> readings into a best estimate — you don't need to understand Kalman filters
> today, just know that 'fusing sensors' is a real, named technique you'll see
> again if you study robotics further."

Finally, back in `robot_dashboard.py`, show `_odom_cb`:
```python
self.create_subscription(Odometry, "/odom", self._odom_cb, 10)
```
> "And we've come full circle — the dashboard is *also* subscribed to `/odom`,
> which is how the position numbers you see on the webpage update live."

---

## 4. The Sensors That Don't Drive Anything (10 min)

### LiDAR

> "The RPLidar spins 360 degrees, about 7 times a second, firing a laser and
> timing how long it takes to bounce back — that tells it distance. It
> publishes a `/scan` topic: basically a list of ~290 distances, one for each
> angle around the robot."

Mention briefly (don't need code): the lidar plugs in over USB just like the
Arduino, but it speaks its own binary protocol, handled by a pre-built ROS2
package (`rplidar_ros`) — "we didn't write this part ourselves, and that's
normal: most robotics code is built from existing, trusted libraries, not
written from scratch."

### SLAM

> "SLAM stands for Simultaneous Localization And Mapping — building a map of
> the room *while* figuring out where you are in it, at the same time, which
> is the chicken-and-egg problem that makes this hard. We use a library called
> `slam_toolbox`. It takes `/scan` and the robot's odometry, and produces a
> `/map` topic — a grid where each cell is 'empty', 'wall', or 'unknown'."

Show `slam_toolbox_params.yaml`, point at two specific numbers:
```yaml
minimum_travel_distance: 0.1
minimum_travel_heading: 0.2
```
> "These say: only bother adding a new piece to the map if the robot has moved
> at least 10cm or turned about 11 degrees since the last update. Why do you
> think we'd want that limit instead of updating constantly?"

*(Discussion — answer: efficiency. Updating the map every single scan, even
when the robot hasn't moved, wastes CPU for no benefit.)*

---

## 5. How It All Gets Started: Launch Files (5 min)

Open `ros_control_ws/src/my_robot/launch/robot.launch.py`.

> "ROS2 systems are made of many small programs (called *nodes*) that all need
> to start up in roughly the right order and with the right settings. A launch
> file is a Python script whose only job is to start all of them at once. Look
> at this list:"

Walk through the `Node(...)` blocks quickly: `robot_state_publisher`,
`ros2_control_node`, `ekf_node`, `rplidar`, `robot_dashboard`.

> "One thing worth noticing — at the very top, before anything starts, there's
> cleanup code:"
```python
subprocess.run('rm -rf /dev/shm/fastrtps_*', shell=True, check=False)
subprocess.run('pkill -f robot_dashboard', shell=True, check=False)
_stop_rplidar()
```
> "This is defensive programming — making sure that if the robot was shut down
> messily last time (crashed, lost power, you hit Ctrl+C at a bad moment), this
> launch doesn't just fail with a confusing error. It cleans up known-messy
> leftover state first. This is the kind of code you only write *after* you've
> been burned by the problem it fixes."

---

## 6. The Web Dashboard, Briefly (5 min)

> "The dashboard you've been clicking buttons on is a single Python file
> (`robot_dashboard.py`) doing three jobs at once: it's a ROS2 node (talking to
> the robot), a web server (FastAPI, serving the HTML/CSS/JS you see), and a
> WiFi manager (so the robot can set itself up on a new network without a
> keyboard ever touching it — useful for a classroom of many robots)."

Show the WebSocket loop:
```python
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    while True:
        await ws.send_json(data)
        await asyncio.sleep(1.0)
```
> "This is how the page updates live without you refreshing — the browser
> keeps an open connection, and the Pi pushes new data down it once a second."

---

## 7. Wrap-Up Summary Slide

Put this diagram up as the closing image and narrate it once, start to finish,
without stopping:

```
 Browser (dashboard)                Pi (ROS2)                          Arduino
 ──────────────────                 ─────────                          ───────
 [Drive button held] --HTTP-->  /api/drive  --publishes-->  /cmd_vel
                                                                 │
                                                    diff_drive_controller
                                                       (Twist → wheel speeds)
                                                                 │
                                              my_robot_hardware.cpp write()
                                                                 │
                                                          "V1.0,-1.0\n"  --USB-->  parseVelocityCommand()
                                                                                          │
                                                                                    setMotorRadS()
                                                                                          │
                                                                                    [Motors spin]
                                                                                          │
                                                                                    [Encoders tick]
                                                                 ↑
                                              my_robot_hardware.cpp read()  <--USB--  "F0.1,0.1,1.0,1.0\n"
                                                                 │
                                                            /odom topic
                                                                 │
                                              EKF  +  slam_toolbox (uses /scan too)
                                                                 │
 [Dashboard updates] <--WebSocket--   robot_dashboard.py subscribes to /odom
```

> "Every single feature this robot has — driving, mapping, the web UI — is
> just topics being published and subscribed to, chained together. If you
> remember nothing else from today, remember this: **ROS2's whole job is
> letting many small, separate programs talk to each other through named
> channels, without any of them needing to know who else is listening.**"

---

## Appendix: Anticipated Questions

- **"Why C++ for the hardware interface but Python for the dashboard?"**
  Speed where it matters (the 25Hz control loop), convenience where it doesn't
  (a web server has plenty of time between requests).

- **"What happens if the Arduino is unplugged while running?"**
  `read()`/`writeSerial()` check `serial_fd_ < 0` and fail gracefully rather
  than crashing — show this in the code if there's time.

- **"Why does the robot need both an EKF *and* SLAM — isn't that double
  tracking position?"**
  EKF answers "where am I relative to where I started" using only wheel
  motion (fast, but drifts over time). SLAM answers "where am I on a map of
  the room" using the lidar to correct that drift (slower, but doesn't drift).
  Nav2 (not covered today) uses both together.

- **"Is any of this code AI-generated?"**
  Be honest if asked — focus the answer on the fact that the *debugging
  process* (reading logs, isolating root causes, testing hypotheses) is the
  actual transferable skill, regardless of who typed the first draft.
