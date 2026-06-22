"""
Combined launch: H1 Gazebo simulation + kinematic floating-base teleop.

Starts:
  - Gazebo simulation with the H1 robot (h1_gazebo)
  - ros_gz service bridge for /world/h1_world/set_pose (SetEntityPose)
  - kinematic_base_driver: integrates /cmd_vel and hard-sets the base pose so the
    robot stays upright and glides around the world (no balance controller needed).

The leg joints hold their standing pose via the JointPositionController plugins
(<initial_position> in h1.urdf). Drive the robot with:
    ./ros2_launch.sh teleop          # then W/A/S/D/Q/E
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


# H1 actuated joints - their JointPositionController plugins listen on the gz
# topic /model/h1/joint/<joint>/cmd_pos (set via <topic> in h1.urdf).
JOINT_NAMES = [
    'left_hip_yaw_joint', 'left_hip_roll_joint', 'left_hip_pitch_joint',
    'left_knee_joint', 'left_ankle_joint',
    'right_hip_yaw_joint', 'right_hip_roll_joint', 'right_hip_pitch_joint',
    'right_knee_joint', 'right_ankle_joint',
    'torso_joint',
    'left_shoulder_pitch_joint', 'left_shoulder_roll_joint',
    'left_shoulder_yaw_joint', 'left_elbow_joint',
    'right_shoulder_pitch_joint', 'right_shoulder_roll_joint',
    'right_shoulder_yaw_joint', 'right_elbow_joint',
]


def generate_launch_description():
    pkg_h1_gazebo = get_package_share_directory('h1_gazebo')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='true', description='Use simulation time')
    declare_rviz = DeclareLaunchArgument(
        'rviz', default_value='true', description='Launch RViz')
    # NOTE: must NOT be named 'world' - IncludeLaunchDescription inherits parent
    # LaunchConfigurations, and h1_gazebo.launch.py uses 'world' for the world
    # FILE path. Reusing the name would override its path with this bare name.
    declare_world = DeclareLaunchArgument(
        'world_name', default_value='h1_world', description='Gazebo world name')
    declare_stand_height = DeclareLaunchArgument(
        'stand_height', default_value='0.98',
        description='Pelvis height the kinematic base holds (m)')

    # Gazebo simulation
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_h1_gazebo, 'launch', 'h1_gazebo.launch.py')
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'rviz': LaunchConfiguration('rviz'),
        }.items()
    )

    # ros_gz service bridge so the kinematic driver can call set_pose from ROS 2
    set_pose_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='set_pose_bridge',
        arguments=['/world/h1_world/set_pose@ros_gz_interfaces/srv/SetEntityPose'],
        output='screen',
    )

    # Bridge the 19 joint position-command topics (ROS Float64 -> gz Double) so the
    # driver's walking-gait targets reach the JointPositionController plugins.
    joint_cmd_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='joint_cmd_bridge',
        arguments=[
            f'/model/h1/joint/{j}/cmd_pos@std_msgs/msg/Float64]ignition.msgs.Double'
            for j in JOINT_NAMES
        ],
        output='screen',
    )

    # Kinematic floating-base driver - delayed so Gazebo + bridge are up first
    base_driver = TimerAction(
        period=4.0,
        actions=[
            Node(
                package='h1_control',
                executable='kinematic_base_driver.py',
                name='kinematic_base_driver',
                output='screen',
                parameters=[{
                    'use_sim_time': LaunchConfiguration('use_sim_time'),
                    'world': LaunchConfiguration('world_name'),
                    'model': 'h1',
                    'stand_height': ParameterValue(
                        LaunchConfiguration('stand_height'), value_type=float),
                }],
            )
        ]
    )

    return LaunchDescription([
        declare_use_sim_time,
        declare_rviz,
        declare_world,
        declare_stand_height,
        gazebo_launch,
        set_pose_bridge,
        joint_cmd_bridge,
        base_driver,
    ])
