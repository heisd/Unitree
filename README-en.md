<div align="right">

**English** | [中文](README.md)

</div>

<div align="center">

# Unitree H1 ROS 2 SDK

**ROS 2 simulation development kit for the Unitree H1 humanoid robot**

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![ROS2](https://img.shields.io/badge/ROS2-Humble-brightgreen.svg)](https://docs.ros.org/en/humble/)
[![Gazebo](https://img.shields.io/badge/Gazebo-Fortress-orange.svg)](https://gazebosim.org/)
[![Platform](https://img.shields.io/badge/platform-Ubuntu%2022.04-purple.svg)](https://releases.ubuntu.com/22.04/)
[![WSL2](https://img.shields.io/badge/WSL2-supported-lightgrey.svg)](#troubleshooting)

</div>

---

## Overview

This project provides a complete ROS 2 simulation environment for the [Unitree H1](https://www.unitree.com/h1) humanoid robot. The core approach is a **kinematic floating base**: instead of implementing a balance controller, the pelvis pose is written directly into Gazebo via the `set_pose` service at 50 Hz, keeping the robot permanently upright while responding to velocity commands and playing a sinusoidal walking animation.

> **Use cases**: ROS 2 learning, pre-validation of motion planning algorithms, sensor integration testing.

---

## Features

| Feature | Description |
|---------|-------------|
| H1 URDF model | Full 19-joint model, including hand variant (`h1_with_hand.urdf`) |
| Multi-world simulation | 5 built-in Gazebo worlds (city, empty, obstacle, office, warehouse) |
| Kinematic floating base | 50 Hz `set_pose` drive — robot stays upright, no balance controller needed |
| Walking animation | Speed-scaled sinusoidal gait (0.8–2.2 Hz), coordinated leg and arm swing |
| Keyboard teleoperation | `W/A/S/D/Q/E` + speed control + 5 mode switches |
| Joystick support | Full Xbox / PS4 button mapping |
| WSL2 compatible | Auto-selects OGRE v1 renderer, no manual setup required |

---

## Prerequisites

- **OS**: Ubuntu 22.04
- **ROS 2**: Humble
- **Gazebo**: Ignition Fortress

```bash
# Install Gazebo and bridge packages
sudo apt install ros-humble-ros-gz
```

Required packages: `ros_gz_sim` · `ros_gz_bridge` · `ros_gz_interfaces` · `robot_state_publisher` · `rviz2` · `joint_state_publisher`

---

## Quick Start

```bash
# 1. Clone the repository
git clone <repo-url> && cd Unitree

# 2. Build (one-time only)
./ros2_launch.sh build

# 3. Launch simulation (terminal 1)
./ros2_launch.sh full

# 4. Keyboard teleoperation (terminal 2)
./ros2_launch.sh teleop
```

> **Tip**: `ros2_launch.sh` runs inside a clean `env -i` environment with FastRTPS enforced, automatically isolating conda and CycloneDDS issues.
> Python scripts, launch files, and URDFs **do not require a rebuild** after edits (`--symlink-install` takes effect immediately).

---

## Command Reference

```bash
./ros2_launch.sh <command> [options]
```

| Command | Description |
|---------|-------------|
| `build` | Build the workspace |
| `gazebo` | Launch Gazebo only (no base driver — robot will fall) |
| `gazebo --world <name>` | Select a world (default: `h1_world`) |
| `gazebo --no-rviz` | Disable RViz |
| `gazebo --no-gui` | Headless mode |
| `full` | **Recommended**: Gazebo + kinematic base + gait animation |
| `full --world <name>` | Full simulation with a specific world |
| `teleop` | Keyboard teleoperation (open in a second terminal) |
| `control` | High-level control node |
| `worlds` | List all available worlds |
| `topic list` | List ROS 2 topics |
| `node list` | List ROS 2 nodes |
| `run <pkg> <exe>` | Run any ROS 2 executable |

---

## Simulation Worlds

World files are located in `src/h1_gazebo/worlds/`:

| World | Description |
|-------|-------------|
| `h1_world` *(default)* | City street: buildings, roads, vegetation |
| `empty` | Flat empty plane, for algorithm debugging |
| `obstacle_course` | Obstacle field |
| `office` | Indoor office environment |
| `warehouse` | Warehouse environment |

```bash
./ros2_launch.sh full --world warehouse
./ros2_launch.sh worlds          # list all worlds
```

---

## Controls

### Keyboard (`./ros2_launch.sh teleop`)

```
Movement      Speed           Mode
──────────    ────────────    ─────────────────────────────
W  Forward    Z  Linear  -    1  Idle
S  Backward   X  Linear  +    2  Forced Stand
A  Strafe L   C  Angular -    3  Walk / Trot
D  Strafe R   V  Angular +    4  Trot Running
Q  Turn L                     5  Recovery
E  Turn R
              SPACE  Emergency stop · ESC  Quit
```

### Joystick (Xbox / PS4)

| Input | Function |
|-------|----------|
| Left stick ↑↓ | Forward / Backward |
| Left stick ←→ | Strafe left / right |
| Right stick ←→ | Turn left / right |
| A / X | Walk mode (Trot) |
| B / O | Forced Stand |
| X / □ | Idle |
| Y / △ | Recovery |
| LB / L1 | Decrease speed |
| RB / R1 | Increase speed |
| Back / Select | Emergency stop |
| Start | Enable walking |

```bash
# Launch joystick teleoperation
./ros2_launch.sh run h1_control joystick_teleop.py
```

---

## Repository Structure

```
Unitree/
├── ros2_launch.sh                        # Unified launch script
├── src/
│   ├── h1_control/                       # Control layer
│   │   ├── scripts/
│   │   │   ├── kinematic_base_driver.py  # ★ Kinematic base + gait animation (core)
│   │   │   ├── keyboard_teleop.py        # Keyboard teleoperation
│   │   │   ├── joystick_teleop.py        # Joystick teleoperation
│   │   │   ├── high_level_control.py     # High-level control node
│   │   │   ├── gazebo_sim_controller.py  # Gazebo simulation controller
│   │   │   └── velocity_controller.py   # Velocity controller
│   │   ├── launch/
│   │   │   ├── simulation_control.launch.py  # Entry for `full` mode
│   │   │   ├── keyboard_teleop.launch.py
│   │   │   ├── joystick_teleop.launch.py
│   │   │   └── h1_control.launch.py
│   │   └── config/
│   │       └── control_params.yaml
│   │
│   ├── h1_gazebo/                        # Simulation layer
│   │   ├── launch/
│   │   │   ├── h1_gazebo.launch.py       # Entry for `gazebo` mode
│   │   │   └── h1_rviz.launch.py
│   │   ├── worlds/                       # 5 world files
│   │   │   ├── h1_world.sdf
│   │   │   ├── empty.sdf
│   │   │   ├── obstacle_course.sdf
│   │   │   ├── office.sdf
│   │   │   └── warehouse.sdf
│   │   ├── urdf/
│   │   │   └── h1_gazebo.urdf.xacro
│   │   └── config/
│   │       ├── bridge_config.yaml
│   │       ├── h1_controllers.yaml
│   │       └── h1_display.rviz
│   │
│   └── robots/
│       └── h1_description/               # H1 robot URDF (active)
│           └── urdf/
│               ├── h1.urdf
│               └── h1_with_hand.urdf
└── 使用说明.md                            # Detailed usage guide (Chinese)
```

> Other robot models under `robots/` (A1, B2, G1, Go2, etc.) contain `COLCON_IGNORE` and are excluded from the build — kept for reference only.

---

## Architecture

### Why a kinematic floating base?

A bipedal robot is an inherently unstable inverted pendulum — without a closed-loop balance controller, physics simulation will topple it instantly. This project sidesteps the problem with a **kinematic floating base**:

```
Keyboard / Joystick
    │
    ▼  /cmd_vel (geometry_msgs/Twist)
kinematic_base_driver
    ├─► set_pose service ────────────────► Gazebo pelvis pose
    │     (ros_gz_interfaces/SetEntityPose)  (upright · fixed height · smooth glide)
    │
    └─► /model/h1/joint/<j>/cmd_pos ──► JointPositionController × 19
          (std_msgs/Float64)               (sinusoidal walking animation)

        All topics / services bridged by ros_gz_bridge
```

**How it works:**
1. Subscribes to `/cmd_vel` and integrates body-frame velocity into a world-frame pose `(x, y, yaw)`; height `z` and `roll/pitch` are held constant.
2. Every 20 ms (50 Hz) calls `set_pose` to hard-set the pelvis pose — the robot never falls.
3. Simultaneously generates sinusoidal gait targets; cadence scales from 0.8 Hz to 2.2 Hz with speed. Returns smoothly to the standing pose when idle.

> **Note**: Feet have no real contact constraints (they slide). The gait is a visual animation, not dynamic walking.

---

## Topics & Services

### Gazebo → ROS 2 (via `ros_gz_bridge`)

| Topic | Type | Description |
|-------|------|-------------|
| `/clock` | `rosgraph_msgs/Clock` | Simulation clock |
| `/joint_states` | `sensor_msgs/JointState` | 19 joint states |
| `/imu` | `sensor_msgs/Imu` | IMU data |
| `/odom` | `nav_msgs/Odometry` | Odometry |

### ROS 2 → Gazebo

| Topic / Service | Type | Description |
|-----------------|------|-------------|
| `/cmd_vel` | `geometry_msgs/Twist` | Velocity command input |
| `/world/h1_world/set_pose` | `ros_gz_interfaces/srv/SetEntityPose` | Pelvis pose injection |
| `/model/h1/joint/<joint>/cmd_pos` × 19 | `std_msgs/Float64` | Per-joint position targets |

---

## Parameters

`kinematic_base_driver.py` / `simulation_control.launch.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `stand_height` | `0.98` | Pelvis height held by the driver (m) |
| `update_rate` | `50.0` | Pose update frequency (Hz) |
| `max_vx` | `1.0` | Max forward/backward speed (m/s) |
| `max_vy` | `0.5` | Max lateral speed (m/s) |
| `max_wz` | `1.5` | Max yaw rate (rad/s) |
| `animate_gait` | `True` | Enable walking animation |

```bash
# Example: lower stand height, disable RViz
ros2 launch h1_control simulation_control.launch.py stand_height:=0.95 rviz:=false
```

---

## Troubleshooting

<details>
<summary><b>Robot falls over immediately</b></summary>

You launched with `gazebo` (no base driver). Use instead:
```bash
./ros2_launch.sh full
```
</details>

<details>
<summary><b>teleop: <code>No executable found</code></b></summary>

Scripts are missing execute permission:
```bash
chmod +x src/h1_control/scripts/*.py
```
Consider committing this permission to git.
</details>

<details>
<summary><b>Gazebo crash: <code>Ogre::UnimplementedException</code></b></summary>

WSL2 has a limited OpenGL stack. This is already fixed in `h1_gazebo.launch.py` via `--render-engine ogre` (v1). On a physical machine with GPU pass-through, remove that argument for better rendering quality.
</details>

<details>
<summary><b>CycloneDDS network interface error</b></summary>

`ros2_launch.sh` enforces `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`, bypassing this automatically.
</details>

<details>
<summary><b>conda / ROS 2 Python conflict</b></summary>

The script runs in a clean `env -i` environment that isolates conda. Do not bypass the script and call `colcon` / `ros2` directly.
</details>

<details>
<summary><b><code>joint_state_publisher ... process has died</code> in logs</b></summary>

This node is redundant in `h1_gazebo.launch.py` (joint states are already provided by the URDF plugin + bridge). The error is harmless and can be ignored.
</details>

---

## Roadmap

- [ ] True dynamic walking (MPC / WBC balance controller)
- [ ] Foot contact constraints to eliminate foot sliding
- [ ] ROS 2 Nav2 navigation integration
- [ ] Support for H1-2 model

---

## License

This project is released under the [Apache License 2.0](LICENSE).

---

## Acknowledgements

- [Unitree Robotics](https://www.unitree.com/) — H1 robot hardware and SDK
- [unitree_ros](https://github.com/unitreerobotics/unitree_ros) — Original robot description files
