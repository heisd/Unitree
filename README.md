# Unitree H1 ROS 2 SDK

ROS 2 Humble SDK for the Unitree H1 humanoid robot with Gazebo simulation and high-level motion control.

## Features

- **H1 Robot Description**: Complete URDF model with all 19 controllable joints
- **Gazebo Simulation**: Ignition Gazebo (Fortress) integration with physics simulation
- **High-Level Control**: Velocity-based motion control with walking modes
- **Keyboard Teleoperation**: Control the robot with keyboard commands
- **Joystick Support**: Gamepad/joystick teleoperation

## Prerequisites

- Ubuntu 22.04
- ROS 2 Humble
- Ignition Gazebo Fortress (`ros-humble-ros-gz`)

## Installation

```bash
# Clone the repository
git clone https://github.com/YasiruDEX/unitree-h1-ros-sdk.git
cd unitree-h1-ros-sdk

# Build the workspace
./ros2_launch.sh build
```

## Usage

### Quick Start - Simplified Launch Script

The `ros2_launch.sh` script handles all environment setup automatically:

```bash
# Launch Gazebo simulation
./ros2_launch.sh gazebo

# Launch keyboard teleoperation (in another terminal)
./ros2_launch.sh teleop

# Launch full simulation with control system
./ros2_launch.sh full

# Build the workspace
./ros2_launch.sh build
```

### Available Commands

| Command | Description |
|---------|-------------|
| `./ros2_launch.sh gazebo` | Launch Gazebo simulation with H1 robot |
| `./ros2_launch.sh gazebo --no-rviz` | Launch without RViz |
| `./ros2_launch.sh teleop` | Launch keyboard teleoperation |
| `./ros2_launch.sh control` | Launch high-level control node |
| `./ros2_launch.sh full` | Launch Gazebo + control + bridge |
| `./ros2_launch.sh build` | Build the workspace |
| `./ros2_launch.sh topic list` | List ROS 2 topics |
| `./ros2_launch.sh node list` | List ROS 2 nodes |

### Keyboard Teleoperation Controls

```
Movement:
  W/S - Forward/Backward
  A/D - Strafe Left/Right
  Q/E - Turn Left/Right

Speed Control:
  Z/X - Increase/Decrease linear speed
  C/V - Increase/Decrease angular speed

Mode Control:
  1 - Idle Mode
  2 - Walk Mode
  3 - Trot Gait
  4 - Running Gait
  5 - Recovery Mode

SPACE - Emergency Stop
ESC   - Quit
```

## Package Structure

```
unitree-h1-ros-sdk/
├── ros2_launch.sh          # Simplified launch script
├── src/
│   ├── h1_control/         # High-level motion control
│   │   ├── scripts/
│   │   │   ├── high_level_control.py    # Main controller
│   │   │   ├── keyboard_teleop.py       # Keyboard control
│   │   │   ├── joystick_teleop.py       # Gamepad control
│   │   │   └── gazebo_sim_controller.py # Gazebo bridge
│   │   ├── config/
│   │   │   └── control_params.yaml      # Control parameters
│   │   └── launch/
│   │       └── simulation_control.launch.py
│   │
│   ├── h1_gazebo/          # Gazebo simulation
│   │   ├── launch/
│   │   │   └── h1_gazebo.launch.py
│   │   ├── worlds/
│   │   │   └── h1_world.sdf
│   │   └── config/
│   │
│   └── robots/             # Robot descriptions
│       └── h1_description/
│           ├── urdf/h1.urdf
│           └── meshes/
```

## ROS 2 Topics

### Subscribed (Control Input)
- `/cmd_vel` (geometry_msgs/Twist) - Velocity commands
- `/h1/mode` (std_msgs/Int32) - Robot mode
- `/h1/gait_type` (std_msgs/Int32) - Gait type

### Published (Status)
- `/h1/robot_state` (std_msgs/String) - Robot state JSON
- `/joint_states` (sensor_msgs/JointState) - Joint positions

## Robot Modes

| Mode | Name | Description |
|------|------|-------------|
| 0 | IDLE | Default standing position |
| 1 | FORCED_STAND | Lock position |
| 2 | WALK | Walking locomotion |
| 3 | STAND_DOWN | Lower to ground |
| 4 | STAND_UP | Rise to standing |
| 5 | DAMPING | Compliant mode |
| 6 | RECOVERY | Recovery from fall |

## Gait Types

| Gait | Name | Description |
|------|------|-------------|
| 0 | IDLE | No movement |
| 1 | TROT | Standard walking |
| 2 | TROT_RUNNING | Fast walking |
| 3 | CLIMB_STAIR | Stair climbing |
| 4 | TROT_OBSTACLE | Obstacle traversal |

## Troubleshooting

### Network Interface Error (CycloneDDS)

If you see errors like "enp7s0: does not match an available interface", the launch script automatically uses FastRTPS middleware to avoid this issue.

### Conda Conflicts

The launch script uses a clean environment to avoid conda Python conflicts with ROS 2.

### Gazebo Not Starting

Ensure you have the Ignition Gazebo packages installed:
```bash
sudo apt install ros-humble-ros-gz
```

## License

Apache License 2.0

## Acknowledgments

- [Unitree Robotics](https://www.unitree.com/) for the H1 robot
- [unitree_ros](https://github.com/unitreerobotics/unitree_ros) for original robot descriptions
