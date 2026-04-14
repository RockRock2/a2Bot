from setuptools import setup
import os
from glob import glob

package_name = 'my_robot'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),
        (os.path.join('share', package_name, 'urdf'),
            glob('urdf/*.xml')),
    ],
    install_requires=['setuptools'],
    entry_points={
        'console_scripts': [
            'diff_drive_controller = my_robot.diff_drive_controller:main',
            'odometry_node = my_robot.odometry_node:main',
            'imu_node = my_robot.imu_node:main',
            'twist_to_twist_stamped = my_robot.twist_to_twist_stamped:main',
            'node_monitor_server = my_robot.node_monitor_server:main',
            'robot_dashboard = my_robot.robot_dashboard:main',
        ],
    },
)