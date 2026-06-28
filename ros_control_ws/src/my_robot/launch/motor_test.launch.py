import os
import subprocess
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import TimerAction
from launch_ros.actions import Node


def generate_launch_description():
    # Same stale-lock cleanup as robot.launch.py, minus the lidar/dashboard
    # cleanup since those nodes aren't started here.
    subprocess.run('rm -rf /dev/shm/fastrtps_*', shell=True, check=False)

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
        Node(
            package='controller_manager',
            executable='ros2_control_node',
            parameters=[
                {'robot_description': robot_description},
                ctrl_config,
            ],
            output='screen',
        ),

        # ── Spawners ──────────────────────────────────────────────
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

        # ── Twist -> TwistStamped converter ──────────────────────
        # Required since controllers.yaml has use_stamped_vel: true
        Node(
            package='my_robot',
            executable='twist_to_twist_stamped',
            name='twist_to_twist_stamped',
        ),

        # No EKF, no RPLidar, no dashboard — this launch file is only for
        # bench-testing motors/encoders/odometry with the robot lifted off
        # the ground. Watch /diff_drive_controller/odom and /joint_states
        # directly; there's no /odom topic here since EKF isn't running.
    ])
