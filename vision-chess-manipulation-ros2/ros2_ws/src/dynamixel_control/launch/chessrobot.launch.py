from launch import LaunchDescription
from launch_ros.actions import Node


#chess_mapper, motor_node, motor_publisher 노드 한번에 실행
def generate_launch_description():
    # chess_brain 노드 실행
    node_1 = Node(
        package='dynamixel_control',
        executable='chess_mapper',
        name='chess_mapper_node',
        output='screen',
    )
    node_2 = Node(
        package='dynamixel_control',
        executable='motor_node',
        name='motor_node_node',
        output='screen',   
    )
    node_3 = Node(
        package='dynamixel_control',       
        executable='motor_publisher',
        name='motor_publisher_node',
        output='screen',
    )

    return LaunchDescription([
        node_1,
        node_2,
        node_3,
    ])