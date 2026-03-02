import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'dynamixel_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share',package_name,'launch'), glob(os.path.join('launch','*launch.[pxy][yma]*'))),
        ('share/' + package_name + '/urdf', glob(os.path.join('dynamixel_control', 'urdf', '*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='shin',
    maintainer_email='maintainer@example.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'motor_node = dynamixel_control.main.motor_node:main',
            'motor_publisher = dynamixel_control.main.motor_publisher:main',
            'chess_brain = dynamixel_control.main.chess_brain:main',
            'chess_mapper = dynamixel_control.main.chess_mapper:main',
            'rviz_bridge = dynamixel_control.utils.rviz_bridge:main',
            'camera_node = dynamixel_control.vision.camera_node:main',
            'detection_node = dynamixel_control.vision.detection_node:main',
            'camera_bridge_node = dynamixel_control.vision.camera_bridge_node:main',
            'chess_timer = dynamixel_control.vision.chess_timer:main',
        ],
    },
)
