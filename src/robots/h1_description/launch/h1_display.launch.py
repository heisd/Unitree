"""
Launch file for displaying the Unitree H1 robot in RViz2.

This launch file starts:
- robot_state_publisher: Publishes the robot's TF transforms
- joint_state_publisher_gui: Provides a GUI to manipulate joint states
- rviz2: Visualization tool
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node


def generate_launch_description():
    # Get package share directory
    pkg_h1_description = get_package_share_directory('h1_description')
    
    # URDF file path
    urdf_file = os.path.join(pkg_h1_description, 'urdf', 'h1.urdf')
    
    # RViz config file
    rviz_config_file = os.path.join(pkg_h1_description, 'rviz', 'h1_display.rviz')
    
    # Declare arguments
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time if true'
    )
    
    declare_use_gui = DeclareLaunchArgument(
        'use_gui',
        default_value='true',
        description='Use joint_state_publisher_gui if true'
    )
    
    # Read URDF file
    with open(urdf_file, 'r') as file:
        robot_description = file.read()
    
    # Robot State Publisher
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': LaunchConfiguration('use_sim_time')
        }]
    )
    
    # Joint State Publisher GUI
    joint_state_publisher_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        output='screen',
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time')
        }]
    )
    
    # RViz2
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file],
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time')
        }]
    )
    
    return LaunchDescription([
        declare_use_sim_time,
        declare_use_gui,
        robot_state_publisher_node,
        joint_state_publisher_gui_node,
        rviz_node
    ])
