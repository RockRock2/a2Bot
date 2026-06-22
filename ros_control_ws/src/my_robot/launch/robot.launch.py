import os
import subprocess
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import TimerAction
from launch_ros.actions import Node


def _stop_rplidar():
    """Send STOP command to RPLidar via serial to cleanly stop motor before relaunch.
    Prevents 80008002 / OPERATION_TIMEOUT errors caused by killing mid-scan."""
    import time
    try:
        import serial
        with serial.Serial('/dev/rplidar', 115200, timeout=0.5) as ser:
            ser.write(b'\xa5\x25')  # RPLIDAR_CMD_STOP
            time.sleep(0.5)
            ser.write(b'\xa5\x40')  # RPLIDAR_CMD_RESET (firmware reboot)
            time.sleep(3.0)         # wait for device to reinitialise
    except Exception:
        pass  # device absent or pyserial missing — silently skip


def generate_launch_description():
    # Clean up stale FastDDS SHM locks and any held ports from a previous run
    subprocess.run('rm -rf /dev/shm/fastrtps_*', shell=True, check=False)
    subprocess.run('pkill -f robot_dashboard', shell=True, check=False)
    _stop_rplidar()

    pkg_share   = get_package_share_directory('my_robot')
    urdf_file   = os.path.join(pkg_share, 'urdf', 'robot.urdf.xml')
    ctrl_config = os.path.join(pkg_share, 'config', 'controllers.yaml')

    with open(urdf_file, 'r') as f:
        robot_description = f.read()

    return LaunchDescription([

        # ── Robot State Publisher ────────────────────────────────
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{
                'robot_description': robot_description,
                'publish_frequency': 50.0,
            }],
        ),

        # ── ros2_control Manager ─────────────────────────────────
        # Loads hardware interface, manages controller lifecycle
        Node(
            package='controller_manager',
            executable='ros2_control_node',
            parameters=[
                {'robot_description': robot_description},
                ctrl_config,
            ],
            output='screen',
        ),

        # ── Spawners (activated after controller_manager starts) ─
        # joint_state_broadcaster first — diff_drive needs joint states
        TimerAction(
            period=8.0,
            actions=[
                Node(
                    package='controller_manager',
                    executable='spawner',
                    arguments=['joint_state_broadcaster',
                               '--controller-manager', '/controller_manager'],
                ),
            ],
        ),

        TimerAction(
            period=4.0,
            actions=[
                Node(
                    package='controller_manager',
                    executable='spawner',
                    arguments=['diff_drive_controller',
                               '--controller-manager', '/controller_manager'],
                ),
            ],
        ),

        # ── IMU Node (disabled until I2C wiring verified) ────────
        # Node(
        #     package='my_robot',
        #     executable='imu_node',
        #     name='imu_node',
        #     parameters=[{
        #         'i2c_bus':      1,
        #         'i2c_address':  0x68,
        #         'publish_rate': 10.0,
        #         'frame_id':     'imu_link',
        #     }],
        # ),

        # ── EKF Sensor Fusion ────────────────────────────────────
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            parameters=[
                os.path.join(pkg_share, 'config', 'ekf.yaml')
            ],
            remappings=[('odometry/filtered', '/odom')],
        ),

        # ── RPLidar ─────────────────────────────────────────────
        Node(
            package='rplidar_ros',
            executable='rplidar_composition',
            name='rplidar',
            parameters=[{
                'serial_port':     '/dev/rplidar',
                'serial_baudrate': 115200,
                'frame_id':        'laser',
                'channel_type':    'serial',
                'scan_mode':       'Standard',
            }],
        ),

        Node(
            package='my_robot',
            executable='twist_to_twist_stamped',
            name='twist_to_twist_stamped',
        ),

        Node(
            package='my_robot',
            executable='robot_dashboard',
            name='robot_dashboard',
            output='screen',
        ),
    ])