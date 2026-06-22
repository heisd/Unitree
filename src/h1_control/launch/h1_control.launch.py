"""
Launch file for H1 high-level control system
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Find package share directory
    pkg_share = FindPackageShare('h1_control')
    
    # Config file
    config_file = PathJoinSubstitution([pkg_share, 'config', 'control_params.yaml'])
    
    # Declare launch arguments
    use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time'
    )
    
    teleop_type = DeclareLaunchArgument(
        'teleop',
        default_value='keyboard',
        description='Teleoperation type: keyboard or joystick'
    )
    
    # High-level controller node
    high_level_controller = Node(
        package='h1_control',
        executable='high_level_control.py',
        name='h1_high_level_controller',
        output='screen',
        parameters=[
            config_file,
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ]
    )
    
    return LaunchDescription([
        use_sim_time,
        teleop_type,
        high_level_controller,
    ])
