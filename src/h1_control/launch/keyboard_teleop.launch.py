"""
Launch file for keyboard teleoperation of H1 robot
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare('h1_control')
    config_file = PathJoinSubstitution([pkg_share, 'config', 'control_params.yaml'])
    
    use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time'
    )
    
    keyboard_teleop = Node(
        package='h1_control',
        executable='keyboard_teleop.py',
        name='h1_keyboard_teleop',
        output='screen',
        prefix='xterm -e',  # Run in separate terminal for keyboard input
        parameters=[
            config_file,
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ]
    )
    
    return LaunchDescription([
        use_sim_time,
        keyboard_teleop,
    ])
