import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    pkg_share   = get_package_share_directory('my_robot')
    slam_pkg    = get_package_share_directory('slam_toolbox')
    slam_params = os.path.join(pkg_share, 'config', 'slam_toolbox_params.yaml')

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(slam_pkg, 'launch', 'online_async_launch.py')
            ),
            launch_arguments={
                'params_file':   slam_params,
                'use_sim_time':  'false',
            }.items(),
        ),
    ])