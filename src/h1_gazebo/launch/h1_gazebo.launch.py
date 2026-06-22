"""
Launch file for Unitree H1 robot simulation in Gazebo (Ignition).

This launch file starts:
- Gazebo simulation with H1 world
- robot_state_publisher: Publishes robot TF transforms
- ros_gz_bridge: Bridges Gazebo topics to ROS 2
- rviz2 (optional): Visualization
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    # Get package directories
    pkg_h1_gazebo = get_package_share_directory('h1_gazebo')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    
    # Find the workspace root directory
    # pkg_h1_gazebo is: /path/to/ws/install/h1_gazebo/share/h1_gazebo
    # We need workspace root: /path/to/ws
    # Go up: share -> h1_gazebo -> install -> ws
    share_dir = os.path.dirname(pkg_h1_gazebo)  # share/
    pkg_install_dir = os.path.dirname(share_dir)  # h1_gazebo/ (in install)
    install_dir = os.path.dirname(pkg_install_dir)  # install/
    ws_dir = os.path.dirname(install_dir)  # workspace root
    
    # URDF file from robots/h1_description in src
    urdf_file = os.path.join(ws_dir, 'src', 'robots', 'h1_description', 'urdf', 'h1.urdf')
    
    # Check if file exists, if not raise clear error
    if not os.path.exists(urdf_file):
        raise FileNotFoundError(f"URDF file not found: {urdf_file}")
    
    rviz_config = os.path.join(pkg_h1_gazebo, 'config', 'h1_display.rviz')

    # Resolve the selected world by NAME to worlds/<name>.sdf at launch time.
    # All shipped worlds keep <world name="h1_world"> internally so that
    # `full` mode (set_pose service) works regardless of which file is loaded.
    world_path = PathJoinSubstitution([
        pkg_h1_gazebo, 'worlds', LaunchConfiguration('world')
    ])
    
    # Set Gazebo resource path to find meshes.
    # - src/robots: H1 URDF meshes (model://h1_description)
    # - ~/.gazebo/models: classic Gazebo model database used by h1_world.sdf
    #   (gas_station, lamp_post, trees, cars, signs, ...). Appended so the
    #   street-scene <include> tags resolve their model:// URIs.
    home_models_path = os.path.join(os.path.expanduser('~'), '.gazebo', 'models')
    existing_resource_path = os.environ.get('GZ_SIM_RESOURCE_PATH', '')
    resource_paths = [os.path.join(ws_dir, 'src', 'robots'), home_models_path]
    if existing_resource_path:
        resource_paths.append(existing_resource_path)
    gz_models_path = os.pathsep.join(resource_paths)

    gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=gz_models_path
    )

    ign_resource_path = SetEnvironmentVariable(
        name='IGN_GAZEBO_RESOURCE_PATH',
        value=gz_models_path
    )
    
    # Declare arguments
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )
    
    declare_world = DeclareLaunchArgument(
        'world',
        default_value='h1_world',
        description='World file name (without .sdf) in h1_gazebo/worlds/, '
                    'e.g. h1_world | empty | obstacle_course'
    )
    
    declare_rviz = DeclareLaunchArgument(
        'rviz',
        default_value='true',
        description='Launch RViz2 if true'
    )
    
    declare_gui = DeclareLaunchArgument(
        'gui',
        default_value='true',
        description='Launch Gazebo GUI if true'
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
    
    # Gazebo Sim
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            # --render-engine ogre: use OGRE v1 instead of the default ogre2.
            # ogre2's GL3Plus backend crashes on WSL2 / limited-GL drivers
            # (Ogre::UnimplementedException in GL3PlusTextureGpu::copyTo).
            'gz_args': ['-r -v4 --render-engine ogre ', world_path, '.sdf'],
        }.items()
    )
    
    # Spawn robot in Gazebo
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'h1',
            '-topic', 'robot_description',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '1.05',  # Start height (standing position)
        ],
        output='screen'
    )
    
    # ROS-Gazebo Bridge - bridges topics between Gazebo and ROS 2
    ros_gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            # Clock bridge
            '/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock',
            # Joint states from Gazebo
            '/joint_states@sensor_msgs/msg/JointState[ignition.msgs.Model',
            # IMU sensor
            '/imu@sensor_msgs/msg/Imu[ignition.msgs.IMU',
            # Odometry
            '/odom@nav_msgs/msg/Odometry[ignition.msgs.Odometry',
            # Command velocity - ROS to Gazebo
            '/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist',
        ],
        output='screen',
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time')
        }]
    )
    
    # Joint State Publisher (publishes joint states for TF)
    # This reads from robot_description and publishes joint states
    # Since we're in simulation without real joint feedback yet,
    # we use joint_state_publisher with zeros or gui for manual control
    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'rate': 50.0,
        }]
    )
    
    # RViz2
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time')
        }],
        condition=IfCondition(LaunchConfiguration('rviz'))
    )
    
    return LaunchDescription([
        gz_resource_path,
        ign_resource_path,
        declare_use_sim_time,
        declare_world,
        declare_rviz,
        declare_gui,
        robot_state_publisher_node,
        gazebo,
        spawn_robot,
        ros_gz_bridge,
        joint_state_publisher_node,
        rviz_node,
    ])
