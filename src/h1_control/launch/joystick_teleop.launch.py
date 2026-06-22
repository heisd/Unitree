"""
Launch file for joystick teleoperation of H1 robot
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
    
    # Joy node for reading joystick
    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        output='screen',
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'deadzone': 0.1,
            'autorepeat_rate': 20.0,
        }]
    )
    
    # Joystick teleop node
    joystick_teleop = Node(
        package='h1_control',
        executable='joystick_teleop.py',
        name='h1_joystick_teleop',
        output='screen',
        parameters=[
            config_file,
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ]
    )
    
    return LaunchDescription([
        use_sim_time,
        joy_node,
        joystick_teleop,
    ])
