# ~/robot_ws/src/my_robot/my_robot/node_monitor_server.py

import rclpy
from rclpy.node import Node
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import subprocess
import json
import os

HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Robot Node Monitor</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: #f5f5f5;
         color: #111; padding: 1.5rem; }
  h1 { font-size: 18px; font-weight: 500; margin-bottom: 4px; }
  .sub { font-size: 13px; color: #666; margin-bottom: 1.5rem; }
  .metrics { display: grid; grid-template-columns: repeat(4,1fr);
             gap: 10px; margin-bottom: 1.5rem; }
  .metric { background: #fff; border: 1px solid #e0e0e0;
            border-radius: 10px; padding: 12px 14px; }
  .metric-label { font-size: 11px; color: #888; margin-bottom: 4px; }
  .metric-val { font-size: 22px; font-weight: 500; }
  .ok  { color: #3a7d0a; } .warn { color: #a06000; }
  .error { color: #c0392b; } .unknown { color: #888; }
  .section { font-size: 11px; font-weight: 600; color: #888;
             text-transform: uppercase; letter-spacing: .05em;
             margin: 1.25rem 0 .5rem; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill,minmax(200px,1fr));
          gap: 8px; }
  .card { background: #fff; border: 1px solid #e0e0e0;
          border-radius: 10px; padding: 10px 12px; }
  .card-header { display: flex; justify-content: space-between;
                 align-items: center; margin-bottom: 5px; }
  .card-name { font-size: 12px; font-weight: 500;
               font-family: monospace; color: #111;
               white-space: nowrap; overflow: hidden;
               text-overflow: ellipsis; max-width: 85%; }
  .dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
  .dot.ok { background: #3a7d0a; }
  .dot.warn { background: #a06000; animation: pulse 1.5s infinite; }
  .dot.error { background: #c0392b; animation: pulse 1.5s infinite; }
  .dot.unknown { background: #bbb; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
  .card-meta { font-size: 11px; color: #888; }
  .topics-grid { display: grid;
    grid-template-columns: repeat(auto-fill,minmax(220px,1fr)); gap: 8px; }
  .topic-card { background: #fff; border: 1px solid #e0e0e0;
                border-radius: 10px; padding: 10px 12px; }
  .topic-name { font-size: 12px; font-family: monospace; font-weight: 500;
                margin-bottom: 4px; white-space: nowrap; overflow: hidden;
                text-overflow: ellipsis; }
  .topic-row { display: flex; justify-content: space-between;
               font-size: 11px; color: #888; margin-top: 3px; }
  .hz-bar { height: 3px; background: #eee; border-radius: 2px;
            margin-top: 6px; }
  .hz-fill { height: 100%; border-radius: 2px;
             background: #3a7d0a; transition: width .4s; }
  .log-box { background: #fff; border: 1px solid #e0e0e0;
             border-radius: 10px; padding: 10px 14px;
             max-height: 200px; overflow-y: auto; margin-top: .5rem; }
  .log-row { font-size: 11px; font-family: monospace; padding: 3px 0;
             border-bottom: 1px solid #f0f0f0;
             display: flex; gap: 10px; }
  .log-row:last-child { border: none; }
  .log-time { color: #aaa; flex-shrink: 0; }
  .log-ok { color: #3a7d0a; }
  .log-warn { color: #a06000; }
  .log-error { color: #c0392b; }
  .log-info { color: #888; }
  .refresh-bar { display: flex; align-items: center; gap: 10px;
                 margin-bottom: 1rem; font-size: 12px; color: #888; }
  select, button { font-size: 12px; padding: 5px 10px;
                   border: 1px solid #ddd; border-radius: 6px;
                   background: #fff; cursor: pointer; }
  button:hover { background: #f0f0f0; }
  #last-update { font-size: 11px; color: #aaa; margin-left: auto; }
</style>
</head>
<body>
<h1>Robot node monitor</h1>
<p class="sub">Rock Pi 4 · ROS2 Jazzy · ros2_control</p>

<div class="refresh-bar">
  <label>Refresh every</label>
  <select id="interval" onchange="setInterval_(this.value)">
    <option value="1000">1s</option>
    <option value="2000" selected>2s</option>
    <option value="5000">5s</option>
  </select>
  <button onclick="fetchStatus()">Refresh now</button>
  <span id="last-update">never updated</span>
</div>

<div class="metrics" id="metrics"></div>

<div class="section">Critical nodes</div>
<div class="grid" id="nodes"></div>

<div class="section">Active topics</div>
<div class="topics-grid" id="topics"></div>

<div class="section">Event log</div>
<div class="log-box" id="log"></div>

<script>
const EXPECTED_NODES = [
  '/controller_manager', '/diff_drive_controller',
  '/joint_state_broadcaster', '/robot_state_publisher',
  '/rplidar', '/imu_node', '/ekf_filter_node',
  '/amcl', '/bt_navigator', '/controller_server',
  '/planner_server', '/twist_to_twist_stamped'
];

const EXPECTED_TOPICS = {
  '/scan': 10, '/odom': 30, '/wheel_odom': 50,
  '/imu/data_raw': 10, '/joint_states': 50,
  '/amcl_pose': 2, '/map': 0.2,
  '/cmd_vel': null, '/diff_drive_controller/cmd_vel': null, '/plan': null
};

let logs = [];
let refreshTimer = null;
let activeNodes = new Set();
let activeTopics = [];

function log(level, msg) {
  const t = new Date().toLocaleTimeString('en-GB', {hour12: false});
  logs.unshift({t, level, msg});
  if (logs.length > 40) logs.pop();
}

async function fetchStatus() {
  try {
    const res = await fetch('/status');
    const data = await res.json();
    activeNodes = new Set(data.nodes || []);
    activeTopics = data.topics || [];
    render();
    document.getElementById('last-update').textContent =
      'updated ' + new Date().toLocaleTimeString('en-GB', {hour12:false});
  } catch(e) {
    log('error', 'Failed to fetch /status — ' + e.message);
    renderLog();
  }
}

function getNodeStatus(name) {
  if (activeNodes.size === 0) return 'unknown';
  return activeNodes.has(name) ? 'ok' : 'error';
}

function render() {
  const ok    = EXPECTED_NODES.filter(n => getNodeStatus(n) === 'ok').length;
  const error = EXPECTED_NODES.filter(n => getNodeStatus(n) === 'error').length;
  const unk   = EXPECTED_NODES.filter(n => getNodeStatus(n) === 'unknown').length;
  const overall = unk === EXPECTED_NODES.length ? 'unknown'
                : error > 0 ? 'error' : 'ok';
  const label = unk === EXPECTED_NODES.length ? 'loading'
              : error > 0 ? 'degraded' : 'healthy';

  document.getElementById('metrics').innerHTML = `
    <div class="metric"><div class="metric-label">System status</div>
      <div class="metric-val ${overall}">${label}</div></div>
    <div class="metric"><div class="metric-label">Nodes active</div>
      <div class="metric-val ok">${ok} / ${EXPECTED_NODES.length}</div></div>
    <div class="metric"><div class="metric-label">Missing nodes</div>
      <div class="metric-val ${error>0?'error':''}">${error}</div></div>
    <div class="metric"><div class="metric-label">Total topics</div>
      <div class="metric-val">${activeTopics.length}</div></div>`;

  document.getElementById('nodes').innerHTML = EXPECTED_NODES.map(name => {
    const st = getNodeStatus(name);
    if (st === 'error') log('error', `${name} — not found`);
    return `<div class="card">
      <div class="card-header">
        <div class="card-name">${name}</div>
        <div class="dot ${st}"></div>
      </div>
      <div class="card-meta">${st === 'ok' ? 'active' : st === 'error' ? 'not running' : 'checking...'}</div>
    </div>`;
  }).join('');

  const topicSet = new Set(activeTopics);
  document.getElementById('topics').innerHTML =
    Object.entries(EXPECTED_TOPICS).map(([name, expHz]) => {
      const present = topicSet.has(name);
      const st = !present ? 'error' : 'ok';
      return `<div class="topic-card">
        <div class="topic-name">${name}</div>
        <div class="topic-row">
          <span>${present ? 'active' : 'missing'}</span>
          <span>${expHz ? expHz + ' Hz expected' : 'on demand'}</span>
        </div>
        ${expHz ? `<div class="hz-bar">
          <div class="hz-fill" style="width:${present?100:0}%"></div>
        </div>` : ''}
      </div>`;
    }).join('');

  renderLog();
}

function renderLog() {
  const box = document.getElementById('log');
  if (logs.length === 0) {
    box.innerHTML = '<div class="log-row"><span class="log-time">—</span><span class="log-info">No events yet</span></div>';
    return;
  }
  box.innerHTML = logs.map(l =>
    `<div class="log-row">
      <span class="log-time">${l.t}</span>
      <span class="log-${l.level}">${l.msg}</span>
    </div>`).join('');
}

function setInterval_(ms) {
  if (refreshTimer) clearInterval(refreshTimer);
  refreshTimer = setInterval(fetchStatus, parseInt(ms));
}

fetchStatus();
setInterval_(2000);
</script>
</body>
</html>"""


class MonitorNode(Node):
    def __init__(self):
        super().__init__('node_monitor_server')
        self.data = {'nodes': [], 'topics': []}
        self.create_timer(2.0, self.update)
        self.get_logger().info('Node monitor server starting...')

    def update(self):
        try:
            # Source ROS2 environment explicitly for subprocess
            env = os.environ.copy()
            env['PATH'] = '/opt/ros/jazzy/bin:' + env.get('PATH', '')
            env['PYTHONPATH'] = '/opt/ros/jazzy/lib/python3.12/site-packages:' + \
                                env.get('PYTHONPATH', '')
            env['LD_LIBRARY_PATH'] = '/opt/ros/jazzy/lib:' + \
                                    env.get('LD_LIBRARY_PATH', '')
            env['ROS_DISTRO'] = 'jazzy'
            env['AMENT_PREFIX_PATH'] = '/opt/ros/jazzy'
            env['ROS_PYTHON_VERSION'] = '3'

            r1 = subprocess.run(
                ['ros2', 'node', 'list'],
                capture_output=True, text=True,
                timeout=5, env=env)
            r2 = subprocess.run(
                ['ros2', 'topic', 'list'],
                capture_output=True, text=True,
                timeout=5, env=env)

            nodes  = [n.strip() for n in r1.stdout.strip().split('\n') if n.strip()]
            topics = [t.strip() for t in r2.stdout.strip().split('\n') if t.strip()]
            self.data = {'nodes': nodes, 'topics': topics}

        except Exception as e:
            self.get_logger().warn(f'Monitor update failed: {e}')


def make_handler(monitor_node):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/status':
                body = json.dumps(monitor_node.data).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(body)
            else:
                body = HTML.encode()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(body)

        def log_message(self, *args):
            pass

    return Handler


def main(args=None):
    rclpy.init(args=args)
    node = MonitorNode()

    spin_thread = threading.Thread(
        target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    port = 8888
    server = HTTPServer(('0.0.0.0', port), make_handler(node))
    node.get_logger().info(
        f'Dashboard available at http://<ROCKPI_IP>:{port}')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()