import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import TimerAction
from launch_ros.actions import Node


def generate_launch_description():
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

        # ── IMU Node ─────────────────────────────────────────────
        Node(
            package='my_robot',
            executable='imu_node',
            name='imu_node',
            parameters=[{
                'i2c_bus':      1,
                'i2c_address':  0x68,
                'publish_rate': 10.0,
                'frame_id':     'imu_link',
            }],
        ),

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
                'serial_port': '/dev/rplidar',
                'frame_id':    'laser',
            }],
        ),

        # ── Static TF publisher ──────────────────────────────────
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_link_to_laser',
            arguments=['0.08', '0', '0.065', '0', '0', '0',
                       'base_link', 'laser'],
        ),

        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_link_to_imu',
            arguments=['0.0', '0.0', '0.02', '0', '0', '0',
                       'base_link', 'imu_link'],
        ),

        Node(
            package='my_robot',
            executable='twist_to_twist_stamped',
            name='twist_to_twist_stamped',
        ),  

        TimerAction(
            period=4.0,
            actions=[
                Node(
                    package='controller_manager',
                    executable='spawner',
                    arguments=['diff_drive_controller',
                            '--controller-manager', '/controller_manager'],
                    remappings=[
                        ('/diff_drive_controller/odom', '/wheel_odom'),
                    ],
                ),
            ],
        ),

        Node(
            package='my_robot',
            executable='node_monitor_server',
            name='node_monitor_server',
            output='screen',
        ),
    ])