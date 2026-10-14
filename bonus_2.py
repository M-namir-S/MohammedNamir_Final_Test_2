import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
def generate_launch_description():
    camera_topic_arg = DeclareLaunchArgument(
        'camera_topic',
        default_value='/camera/image_raw',
    )

    lidar_topic_arg = DeclareLaunchArgument(
        'lidar_topic',
        default_value='/scan',
    )
    camera_topic_config = LaunchConfiguration('camera_topic')
    lidar_topic_config = LaunchConfiguration('lidar_topic')
    node_parameters = [
        {
            'camera_topic': camera_topic_config,
            'lidar_topic': lidar_topic_config
        }
    ]
    perception_node = Node(
        package='my_perception_package',  
        executable='perception_node',
        name='perception_node',
        parameters=node_parameters,
        output='screen'
    )
    navigation_node = Node(
        package='my_navigation_package',  
        executable='navigation_node',
        name='navigation_node',
        parameters=node_parameters,
        output='screen'
    )
    return LaunchDescription([
        camera_topic_arg,
        lidar_topic_arg,
        perception_node,
        navigation_node
    ])
