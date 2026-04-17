#!/usr/bin/env python3
"""
Gesture Launcher — runs on the laptop.
Tiny HTTP service (port 5001) that starts and stops gesture_node on demand.
The Pi dashboard relays start/stop commands here (browser never calls localhost
directly, which is blocked by the browser's Private Network Access policy).

Usage:
    ros2 run gesture_control gesture_launcher --ros-args -p pi_ip:=192.168.88.167
    # pi_ip defaults to the default-route gateway (works on Pi hotspot)
"""
import os
import signal
import subprocess
import threading
import time

import requests
from flask import Flask, jsonify

app = Flask(__name__)

_proc: subprocess.Popen | None = None
_lock = threading.Lock()
_camera_index: int = 4


def _is_running() -> bool:
    return _proc is not None and _proc.poll() is None


@app.get("/status")
def status():
    return jsonify({"running": _is_running()})


def _kill_stale_gesture_node():
    """Kill any leftover gesture_node process by name, not by port."""
    try:
        subprocess.run(
            ["pkill", "-f", "gesture_control.gesture_node"],
            capture_output=True,
        )
        time.sleep(0.5)
    except FileNotFoundError:
        pass


@app.post("/start")
def start():
    global _proc
    with _lock:
        if _is_running():
            return jsonify({"ok": True, "message": "already running"})
        _kill_stale_gesture_node()
        env = os.environ.copy()
        ros_setup = "/opt/ros/jazzy/setup.bash"
        ws_setup = os.path.expanduser("~/edubot-docs/ros_control_ws/install/setup.bash")
        cmd = (f"source {ros_setup} && source {ws_setup} && "
               f"ros2 run gesture_control gesture_node "
               f"--ros-args -p camera_index:={_camera_index}")
        _proc = subprocess.Popen(
            ["bash", "-c", cmd],
            env=env,
            preexec_fn=os.setsid,
        )
    return jsonify({"ok": True})


@app.post("/stop")
def stop():
    global _proc
    with _lock:
        if _proc and _proc.poll() is None:
            os.killpg(os.getpgid(_proc.pid), signal.SIGTERM)
            _proc = None
    return jsonify({"ok": True})


def _detect_gateway() -> str | None:
    """Return the default-route gateway IP (the Pi when on its hotspot)."""
    try:
        r = subprocess.run(
            ["ip", "route", "show", "default"],
            capture_output=True, text=True,
        )
        for line in r.stdout.splitlines():
            parts = line.split()
            if "via" in parts:
                return parts[parts.index("via") + 1]
    except Exception:
        pass
    return None


def _register_with_pi(pi_ip: str, retries: int = 5):
    """POST to the Pi dashboard so it knows our IP. Retries on failure."""
    url = f"http://{pi_ip}:8888/api/gesture/register"
    for attempt in range(1, retries + 1):
        try:
            r = requests.post(url, timeout=5)
            if r.ok:
                print(f"Registered with Pi dashboard at {pi_ip}")
                return
        except Exception as e:
            print(f"Register attempt {attempt}/{retries} failed: {e}")
        time.sleep(3)
    print(f"Warning: could not register with Pi at {pi_ip}. Start/Stop from dashboard will not work.")


def main(args=None):
    global _camera_index
    import rclpy
    from rclpy.node import Node

    rclpy.init(args=args)
    node = Node("gesture_launcher")
    pi_ip = node.declare_parameter("pi_ip", "").value
    _camera_index = node.declare_parameter("camera_index", 4).value
    node.destroy_node()
    rclpy.shutdown()

    if not pi_ip:
        pi_ip = _detect_gateway()

    if pi_ip:
        print(f"Pi IP: {pi_ip}")
        t = threading.Thread(target=_register_with_pi, args=(pi_ip,), daemon=True)
        t.start()
    else:
        print("Warning: could not determine Pi IP. Pass with --ros-args -p pi_ip:=<ip>")

    print("Gesture launcher running at http://0.0.0.0:5001")
    print("  POST /start  — launch gesture_node")
    print("  POST /stop   — kill gesture_node")
    print("  GET  /status — check if running")
    app.run(host="0.0.0.0", port=5001, threaded=True)


if __name__ == "__main__":
    main()
