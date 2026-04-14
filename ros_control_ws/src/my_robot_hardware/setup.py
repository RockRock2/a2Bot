from setuptools import setup

package_name = 'my_robot_hardware'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'pyserial'],
    entry_points={
        'console_scripts': [
            'arduino_bridge = my_robot_hardware.arduino_bridge:main',
        ],
    },
)