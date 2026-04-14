#!/usr/bin/env python3
"""
EduBot Robot Dashboard
FastAPI web server + ROS 2 node for robot monitoring and control.
Served at http://<robot-ip>:8888
"""
import asyncio
import copy
import os
import subprocess
import threading

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
import uvicorn

from my_robot import wifi_manager


# ── Shared state (written by ROS thread, read by FastAPI) ───────────────────
_state = {
    "wifi": {"mode": "unknown", "ssid": "", "ip": "", "signal": 0},
    "nodes": {
        "controller_manager": False,
        "diff_drive_controller": False,
        "joint_state_broadcaster": False,
        "odometry_node": False,
        "robot_state_publisher": False,
        "imu_node": False,
        "gesture_node": False,
    },
    "odometry": {"x": 0.0, "y": 0.0, "vx": 0.0, "omega": 0.0},
    "encoders": {"left_vel": 0.0, "right_vel": 0.0},
    "demo_running": False,
}
_lock = threading.Lock()
_demo_proc = None
_ros_node = None


# ── ROS 2 Node ──────────────────────────────────────────────────────────────
class DashboardNode(Node):
    def __init__(self):
        super().__init__("robot_dashboard")
        self.create_subscription(Odometry, "/odom", self._odom_cb, 10)
        self.create_subscription(JointState, "/joint_states", self._joint_cb, 10)
        self._cmd_pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.create_timer(2.0, self._update_nodes)
        self.create_timer(5.0, self._update_wifi)
        self._ros_env = self._build_ros_env()
        self.get_logger().info("Robot dashboard node started")

    def _build_ros_env(self):
        env = os.environ.copy()
        env["PATH"] = "/opt/ros/jazzy/bin:" + env.get("PATH", "")
        env["ROS_DISTRO"] = "jazzy"
        env["AMENT_PREFIX_PATH"] = "/opt/ros/jazzy"
        env["PYTHONPATH"] = (
            "/opt/ros/jazzy/lib/python3.12/site-packages:"
            + env.get("PYTHONPATH", "")
        )
        env["LD_LIBRARY_PATH"] = (
            "/opt/ros/jazzy/lib:" + env.get("LD_LIBRARY_PATH", "")
        )
        return env

    def _odom_cb(self, msg: Odometry):
        with _lock:
            _state["odometry"] = {
                "x": round(msg.pose.pose.position.x, 3),
                "y": round(msg.pose.pose.position.y, 3),
                "vx": round(msg.twist.twist.linear.x, 3),
                "omega": round(msg.twist.twist.angular.z, 3),
            }

    def _joint_cb(self, msg: JointState):
        vels = dict(zip(msg.name, msg.velocity))
        with _lock:
            _state["encoders"] = {
                "left_vel": round(vels.get("left_wheel_joint", 0.0), 3),
                "right_vel": round(vels.get("right_wheel_joint", 0.0), 3),
            }

    def _update_nodes(self):
        try:
            r = subprocess.run(
                ["ros2", "node", "list"],
                capture_output=True, text=True,
                timeout=5, env=self._ros_env,
            )
            active = set(r.stdout.strip().splitlines())
            with _lock:
                for key in list(_state["nodes"].keys()):
                    if key == "gesture_node":
                        continue  # tracked by demo_proc, not ros2 node list
                    _state["nodes"][key] = ("/" + key) in active
        except Exception as e:
            self.get_logger().warn(f"Node list update failed: {e}")

    def _update_wifi(self):
        info = wifi_manager.get_status()
        with _lock:
            _state["wifi"] = info

    def publish_cmd_vel(self, linear_x: float, angular_z: float):
        msg = Twist()
        msg.linear.x = float(linear_x)
        msg.angular.z = float(angular_z)
        self._cmd_pub.publish(msg)


# ── FastAPI application ─────────────────────────────────────────────────────
app = FastAPI(title="EduBot Dashboard")


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=_HTML)


@app.get("/api/status")
async def api_status():
    with _lock:
        return copy.deepcopy(_state)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            with _lock:
                data = copy.deepcopy(_state)
            await ws.send_json(data)
            await asyncio.sleep(1.0)
    except (WebSocketDisconnect, Exception):
        pass


@app.get("/api/wifi/networks")
async def wifi_networks():
    networks = await asyncio.get_event_loop().run_in_executor(
        None, wifi_manager.scan_networks
    )
    return {"networks": networks}


@app.post("/api/wifi/connect")
async def wifi_connect(body: dict):
    ssid = body.get("ssid", "")
    password = body.get("password", "")
    if not ssid:
        return JSONResponse({"ok": False, "error": "ssid required"}, status_code=400)
    result = await asyncio.get_event_loop().run_in_executor(
        None, wifi_manager.connect, ssid, password
    )
    return result


@app.post("/api/demo/start")
async def demo_start():
    global _demo_proc
    with _lock:
        if _state["demo_running"]:
            return {"ok": True, "message": "already running"}
    try:
        env = os.environ.copy()
        env["PATH"] = "/opt/ros/jazzy/bin:" + env.get("PATH", "")
        _demo_proc = subprocess.Popen(
            ["ros2", "run", "gesture_control", "gesture_node"],
            env=env,
        )
        with _lock:
            _state["demo_running"] = True
            _state["nodes"]["gesture_node"] = True
        return {"ok": True}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@app.post("/api/demo/stop")
async def demo_stop():
    global _demo_proc
    if _demo_proc and _demo_proc.poll() is None:
        _demo_proc.terminate()
        _demo_proc = None
    with _lock:
        _state["demo_running"] = False
        _state["nodes"]["gesture_node"] = False
    return {"ok": True}


@app.post("/api/drive")
async def drive(body: dict):
    linear_x = float(body.get("linear_x", 0.0))
    angular_z = float(body.get("angular_z", 0.0))
    if _ros_node:
        _ros_node.publish_cmd_vel(linear_x, angular_z)
    return {"ok": True}


@app.get("/video_feed")
async def video_feed():
    """Proxy the MJPEG stream from gesture_node running on port 5000."""
    import requests

    def _stream():
        try:
            with requests.get(
                "http://localhost:5000/video_feed", stream=True, timeout=5
            ) as r:
                for chunk in r.iter_content(chunk_size=4096):
                    if chunk:
                        yield chunk
        except Exception:
            return

    return StreamingResponse(
        _stream(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


# ── HTML frontend ───────────────────────────────────────────────────────────
_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>EduBot</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: system-ui, -apple-system, sans-serif;
       background: #f0f2f5; color: #111; min-height: 100vh; }

header { background: #1a1a2e; color: #fff; padding: 16px 24px;
         display: flex; align-items: center; gap: 12px; }
header h1 { font-size: 20px; font-weight: 600; }
#conn-status { font-size: 12px; color: #aaa; margin-left: auto; }

/* ── WiFi Setup Screen ── */
#setup-screen { display: none; max-width: 420px; margin: 60px auto; padding: 24px; }
.setup-card { background: #fff; border-radius: 16px; padding: 32px;
              box-shadow: 0 4px 20px rgba(0,0,0,.08); }
.setup-card h2 { font-size: 22px; margin-bottom: 8px; }
.setup-card p  { color: #666; font-size: 14px; margin-bottom: 24px; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 13px; font-weight: 500;
                    margin-bottom: 6px; color: #444; }
.form-group select, .form-group input {
  width: 100%; padding: 10px 14px; border: 1px solid #ddd;
  border-radius: 8px; font-size: 15px; outline: none;
  transition: border-color .2s; }
.form-group select:focus, .form-group input:focus { border-color: #4f6ef7; }
.btn-primary { width: 100%; padding: 14px; background: #4f6ef7; color: #fff;
               border: none; border-radius: 10px; font-size: 16px;
               font-weight: 600; cursor: pointer; transition: background .2s; }
.btn-primary:hover { background: #3a55d4; }
.btn-primary:disabled { background: #aaa; cursor: not-allowed; }
.setup-msg { margin-top: 14px; font-size: 13px; text-align: center; color: #666; }

/* ── Dashboard Screen ── */
#dashboard-screen { display: none; padding: 20px 24px;
                    max-width: 1000px; margin: 0 auto; }
.grid-2 { display: grid; grid-template-columns: 300px 1fr;
          gap: 20px; align-items: start; }
@media (max-width: 700px) { .grid-2 { grid-template-columns: 1fr; } }
.section-label { font-size: 11px; font-weight: 700; letter-spacing: .06em;
                 text-transform: uppercase; color: #888; margin-bottom: 10px; }
.card { background: #fff; border-radius: 14px; padding: 18px 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,.06); }

.status-row { display: flex; align-items: center; gap: 10px;
              padding: 9px 0; border-bottom: 1px solid #f0f0f0; }
.status-row:last-child { border: none; }
.dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.dot.ok  { background: #22c55e; }
.dot.err { background: #ef4444; animation: pulse 1.5s infinite; }
.dot.unk { background: #d1d5db; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
.status-label { flex: 1; font-size: 14px; font-weight: 500; }
.status-val   { font-size: 13px; color: #666; }

.node-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px; }
.node-tag { font-size: 11px; font-family: monospace; padding: 4px 8px;
            border-radius: 6px; display: flex; align-items: center; gap: 5px; }
.node-tag.ok  { background: #dcfce7; color: #166534; }
.node-tag.err { background: #fee2e2; color: #991b1b; }
.node-tag span { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.node-tag.ok  span { background: #22c55e; }
.node-tag.err span { background: #ef4444; }

.camera-box { background: #111; border-radius: 12px; overflow: hidden;
              aspect-ratio: 4/3; display: flex; align-items: center;
              justify-content: center; }
.camera-box img { width: 100%; height: 100%; object-fit: cover; }
.camera-off { color: #555; font-size: 13px; text-align: center; padding: 20px; }

.controls-row { display: flex; gap: 12px; flex-wrap: wrap; }
.btn-demo { flex: 1; min-width: 160px; padding: 14px 20px; border: none;
            border-radius: 10px; font-size: 15px; font-weight: 600;
            cursor: pointer; transition: background .2s; }
.btn-demo.start { background: #22c55e; color: #fff; }
.btn-demo.start:hover { background: #16a34a; }
.btn-demo.stop  { background: #ef4444; color: #fff; }
.btn-demo.stop:hover  { background: #dc2626; }

.drive-pad { display: grid;
             grid-template-columns: repeat(3, 64px);
             grid-template-rows: repeat(3, 64px);
             gap: 6px; margin-top: 16px; }
.d-btn { border: none; border-radius: 10px; background: #e5e7eb;
         font-size: 24px; cursor: pointer; user-select: none;
         display: flex; align-items: center; justify-content: center;
         transition: background .1s; touch-action: none; }
.d-btn:active { background: #4f6ef7; color: #fff; }
.d-btn.stop-btn { background: #fef3c7; font-size: 13px;
                  font-weight: 700; color: #92400e; }
.d-btn.stop-btn:active { background: #f59e0b; color: #fff; }
</style>
</head>
<body>

<header>
  <h1>EduBot</h1>
  <span id="conn-status">Connecting...</span>
</header>

<!-- Screen A: WiFi Setup (hotspot mode) -->
<div id="setup-screen">
  <div class="setup-card">
    <h2>Connect to WiFi</h2>
    <p>The robot is in setup mode. Select a network and enter the
       password to get started.</p>
    <div class="form-group">
      <label>Available Networks</label>
      <select id="ssid-select">
        <option value="">Loading networks...</option>
      </select>
    </div>
    <div class="form-group">
      <label>Password</label>
      <input type="password" id="wifi-password" placeholder="WiFi password">
    </div>
    <button class="btn-primary" id="connect-btn" onclick="connectWifi()">
      Connect
    </button>
    <p class="setup-msg" id="setup-msg"></p>
  </div>
</div>

<!-- Screen B: Main Dashboard -->
<div id="dashboard-screen">
  <div class="grid-2">

    <!-- Left column: status panels -->
    <div>
      <div class="section-label">Robot Status</div>
      <div class="card">
        <div class="status-row">
          <div class="dot unk" id="dot-wifi"></div>
          <div class="status-label">WiFi</div>
          <div class="status-val" id="val-wifi">—</div>
        </div>
        <div class="status-row">
          <div class="dot unk" id="dot-motors"></div>
          <div class="status-label">Motor Controller</div>
          <div class="status-val" id="val-motors">—</div>
        </div>
        <div class="status-row">
          <div class="dot unk" id="dot-odom"></div>
          <div class="status-label">Odometry</div>
          <div class="status-val" id="val-odom">—</div>
        </div>
        <div class="status-row">
          <div class="dot unk" id="dot-demo"></div>
          <div class="status-label">Gesture Demo</div>
          <div class="status-val" id="val-demo">Stopped</div>
        </div>
      </div>

      <div class="section-label" style="margin-top:18px;">Motion Data</div>
      <div class="card">
        <div class="status-row">
          <div class="status-label">Left wheel</div>
          <div class="status-val" id="val-left">0.000 rad/s</div>
        </div>
        <div class="status-row">
          <div class="status-label">Right wheel</div>
          <div class="status-val" id="val-right">0.000 rad/s</div>
        </div>
        <div class="status-row">
          <div class="status-label">Position X</div>
          <div class="status-val" id="val-x">0.000 m</div>
        </div>
        <div class="status-row">
          <div class="status-label">Position Y</div>
          <div class="status-val" id="val-y">0.000 m</div>
        </div>
      </div>

      <div class="section-label" style="margin-top:18px;">ROS Nodes</div>
      <div class="card">
        <div class="node-grid" id="node-grid">
          <div class="node-tag err"><span></span>loading...</div>
        </div>
      </div>
    </div>

    <!-- Right column: camera + controls -->
    <div>
      <div class="section-label">Camera Feed</div>
      <div class="camera-box" id="camera-box">
        <span class="camera-off">Camera offline<br>Start gesture demo to activate</span>
      </div>

      <div class="section-label" style="margin-top:18px;">Controls</div>
      <div class="card">
        <div class="controls-row">
          <button class="btn-demo start" id="demo-btn" onclick="toggleDemo()">
            Start Gesture Demo
          </button>
        </div>

        <div class="section-label" style="margin-top:20px;">Manual Drive</div>
        <div class="drive-pad">
          <div></div>
          <button class="d-btn"
            onmousedown="drive(0.08,0)"  onmouseup="drive(0,0)"
            ontouchstart="drive(0.08,0)" ontouchend="drive(0,0)">▲</button>
          <div></div>

          <button class="d-btn"
            onmousedown="drive(0,0.5)"  onmouseup="drive(0,0)"
            ontouchstart="drive(0,0.5)" ontouchend="drive(0,0)">◄</button>
          <button class="d-btn stop-btn"
            onmousedown="drive(0,0)"
            ontouchstart="drive(0,0)">STOP</button>
          <button class="d-btn"
            onmousedown="drive(0,-0.5)"  onmouseup="drive(0,0)"
            ontouchstart="drive(0,-0.5)" ontouchend="drive(0,0)">►</button>

          <div></div>
          <button class="d-btn"
            onmousedown="drive(-0.08,0)"  onmouseup="drive(0,0)"
            ontouchstart="drive(-0.08,0)" ontouchend="drive(0,0)">▼</button>
          <div></div>
        </div>
      </div>
    </div>

  </div>
</div>

<script>
const NODES = [
  'controller_manager', 'diff_drive_controller',
  'joint_state_broadcaster', 'odometry_node',
  'robot_state_publisher', 'imu_node', 'gesture_node'
];

let demoRunning = false;
let ws, wsRetries = 0;

function dot(id, state) {
  const el = document.getElementById(id);
  if (el) el.className = 'dot ' + state;
}

function connectWS() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${proto}://${location.host}/ws`);
  ws.onopen = () => {
    wsRetries = 0;
    document.getElementById('conn-status').textContent = 'Connected';
  };
  ws.onclose = () => {
    document.getElementById('conn-status').textContent = 'Reconnecting...';
    setTimeout(connectWS, Math.min(5000, 1000 * (++wsRetries)));
  };
  ws.onmessage = e => update(JSON.parse(e.data));
}

function update(s) {
  const hotspot = s.wifi.mode === 'hotspot';
  document.getElementById('setup-screen').style.display     = hotspot ? 'block' : 'none';
  document.getElementById('dashboard-screen').style.display = hotspot ? 'none'  : 'block';
  if (hotspot) return;

  // WiFi row
  const wifiOk = s.wifi.mode === 'connected';
  dot('dot-wifi', wifiOk ? 'ok' : 'err');
  document.getElementById('val-wifi').textContent =
    wifiOk ? (s.wifi.ssid || 'Connected') : 'Disconnected';

  // Motor controller row
  const motorsOk = s.nodes.controller_manager && s.nodes.diff_drive_controller;
  dot('dot-motors', motorsOk ? 'ok' : 'err');
  document.getElementById('val-motors').textContent = motorsOk ? 'Ready' : 'Not ready';

  // Odometry row
  const odomOk = s.nodes.odometry_node;
  dot('dot-odom', odomOk ? 'ok' : 'err');
  document.getElementById('val-odom').textContent = odomOk ? 'Active' : 'Inactive';

  // Demo row
  demoRunning = s.demo_running;
  dot('dot-demo', s.demo_running ? 'ok' : 'unk');
  document.getElementById('val-demo').textContent = s.demo_running ? 'Running' : 'Stopped';
  const btn = document.getElementById('demo-btn');
  btn.textContent = s.demo_running ? 'Stop Gesture Demo' : 'Start Gesture Demo';
  btn.className   = 'btn-demo ' + (s.demo_running ? 'stop' : 'start');

  // Camera
  const box = document.getElementById('camera-box');
  if (s.demo_running) {
    if (!box.querySelector('img')) {
      box.innerHTML = '<img src="/video_feed" alt="Camera feed">';
    }
  } else {
    box.innerHTML = '<span class="camera-off">Camera offline<br>Start gesture demo to activate</span>';
  }

  // Motion data
  document.getElementById('val-left').textContent  = s.encoders.left_vel.toFixed(3)  + ' rad/s';
  document.getElementById('val-right').textContent = s.encoders.right_vel.toFixed(3) + ' rad/s';
  document.getElementById('val-x').textContent = s.odometry.x.toFixed(3) + ' m';
  document.getElementById('val-y').textContent = s.odometry.y.toFixed(3) + ' m';

  // Node grid
  document.getElementById('node-grid').innerHTML = NODES.map(n => {
    const ok = s.nodes[n] || false;
    return `<div class="node-tag ${ok ? 'ok' : 'err'}">
      <span></span>${n.replace(/_/g, ' ')}
    </div>`;
  }).join('');
}

function drive(lx, az) {
  fetch('/api/drive', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({linear_x: lx, angular_z: az})
  });
}

function toggleDemo() {
  fetch(demoRunning ? '/api/demo/stop' : '/api/demo/start', {method: 'POST'});
}

// WiFi setup screen
async function loadNetworks() {
  const sel = document.getElementById('ssid-select');
  try {
    const r = await fetch('/api/wifi/networks');
    const data = await r.json();
    if (data.networks.length === 0) {
      sel.innerHTML = '<option value="">No networks found</option>';
    } else {
      sel.innerHTML = data.networks.map(n =>
        `<option value="${n.ssid}">${n.ssid} (${n.signal} dBm)</option>`
      ).join('');
    }
  } catch(e) {
    sel.innerHTML = '<option value="">Failed to scan</option>';
  }
}

async function connectWifi() {
  const ssid = document.getElementById('ssid-select').value;
  const password = document.getElementById('wifi-password').value;
  const msg = document.getElementById('setup-msg');
  const btn = document.getElementById('connect-btn');
  if (!ssid) { msg.textContent = 'Please select a network.'; return; }
  btn.disabled = true;
  msg.textContent = 'Connecting to ' + ssid + '...';
  try {
    const r = await fetch('/api/wifi/connect', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ssid, password})
    });
    const data = await r.json();
    if (data.ok && data.ip) {
      msg.textContent = 'Connected! Opening dashboard at ' + data.ip + '...';
      setTimeout(() => { window.location.href = 'http://' + data.ip + ':8888'; }, 2500);
    } else {
      msg.textContent = 'Failed: ' + (data.error || 'unknown error');
      btn.disabled = false;
    }
  } catch(e) {
    msg.textContent = 'Error: ' + e.message;
    btn.disabled = false;
  }
}

connectWS();
loadNetworks();
</script>
</body>
</html>"""


# ── Entry point ─────────────────────────────────────────────────────────────
def main(args=None):
    global _ros_node

    rclpy.init(args=args)
    _ros_node = DashboardNode()

    # Check WiFi on startup; start hotspot if not connected
    wifi_manager.ensure_connectivity()

    # Run rclpy.spin in background thread so FastAPI can use the main thread
    spin_thread = threading.Thread(
        target=rclpy.spin, args=(_ros_node,), daemon=True
    )
    spin_thread.start()

    _ros_node.get_logger().info("Dashboard available at http://<robot-ip>:8888")
    uvicorn.run(app, host="0.0.0.0", port=8888, log_level="warning")

    _ros_node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
