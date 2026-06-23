<div align="right">

[English](README-en.md) | **中文**

</div>

<div align="center">

# Unitree H1 ROS 2 SDK

**基于 ROS 2 Humble 的宇树 H1 人形机器人仿真开发套件**

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![ROS2](https://img.shields.io/badge/ROS2-Humble-brightgreen.svg)](https://docs.ros.org/en/humble/)
[![Gazebo](https://img.shields.io/badge/Gazebo-Fortress-orange.svg)](https://gazebosim.org/)
[![Platform](https://img.shields.io/badge/platform-Ubuntu%2022.04-purple.svg)](https://releases.ubuntu.com/22.04/)
[![WSL2](https://img.shields.io/badge/WSL2-supported-lightgrey.svg)](#排错)

</div>

---

## 简介

本项目为 [Unitree H1](https://www.unitree.com/h1) 人形机器人提供完整的 ROS 2 仿真环境。
核心思路是**运动学浮动底座**——通过 Gazebo `set_pose` 服务直接写入骨盆位姿，绕过平衡控制器的需求，让机器人在仿真中保持直立并响应速度指令，同时播放正弦步态动画。

> **适用场景**：ROS 2 学习、运动规划算法开发前的可视化验证、传感器集成测试。

---

## 功能特性

| 功能 | 说明 |
|------|------|
| H1 URDF 模型 | 完整 19 关节模型，含带手版本（`h1_with_hand.urdf`） |
| 多场景仿真 | 5 种内置 Gazebo 场景（城市、空地、障碍、办公室、仓库） |
| 运动学浮动底座 | 50 Hz `set_pose` 驱动，机器人永远直立，无需平衡控制器 |
| 步态动画 | 正弦步态随速度缩放（0.8–2.2 Hz），腿臂协调摆动 |
| 键盘遥控 | `W/A/S/D/Q/E` + 速度调节 + 5 种模式切换 |
| 手柄遥控 | Xbox / PS4 完整按键映射 |
| WSL2 兼容 | 自动使用 OGRE v1 渲染，无需手动配置 |

---

## 环境要求

- **OS**：Ubuntu 22.04
- **ROS 2**：Humble
- **Gazebo**：Ignition Fortress

```bash
# 安装 Gazebo 及桥接包
sudo apt install ros-humble-ros-gz
```

依赖包：`ros_gz_sim` · `ros_gz_bridge` · `ros_gz_interfaces` · `robot_state_publisher` · `rviz2` · `joint_state_publisher`

---

## 快速上手

```bash
# 1. 克隆仓库
git clone <repo-url> && cd Unitree

# 2. 构建（仅需一次）
./ros2_launch.sh build

# 3. 启动仿真（终端 1）
./ros2_launch.sh full

# 4. 键盘遥控（终端 2）
./ros2_launch.sh teleop
```

> **提示**：`ros2_launch.sh` 使用 `env -i` + 强制 FastRTPS 启动干净环境，自动隔离 conda 和 CycloneDDS 冲突。
> 修改 Python 脚本或 launch 文件后**无需重新构建**（`--symlink-install` 即时生效）。

---

## 命令参考

```bash
./ros2_launch.sh <command> [options]
```

| 命令 | 说明 |
|------|------|
| `build` | 构建工作区 |
| `gazebo` | 仅启动 Gazebo（无底座驱动，机器人会倒） |
| `gazebo --world <name>` | 指定场景（默认 `h1_world`） |
| `gazebo --no-rviz` | 不启动 RViz |
| `gazebo --no-gui` | 无头模式 |
| `full` | **推荐**：Gazebo + 运动学底座 + 步态动画 |
| `full --world <name>` | 完整仿真并指定场景 |
| `teleop` | 键盘遥控（另开终端） |
| `control` | 高层控制节点 |
| `worlds` | 列出所有可用场景 |
| `topic list` | 列出 ROS 2 话题 |
| `node list` | 列出 ROS 2 节点 |
| `run <pkg> <exe>` | 运行任意 ROS 2 可执行文件 |

---

## 仿真场景

场景文件位于 `src/h1_gazebo/worlds/`：

| 场景名 | 说明 |
|--------|------|
| `h1_world` *(默认)* | 城市街道：建筑、道路、植被 |
| `empty` | 空白平地，适合算法调试 |
| `obstacle_course` | 障碍物场地 |
| `office` | 室内办公室 |
| `warehouse` | 仓库场景 |

```bash
./ros2_launch.sh full --world warehouse
./ros2_launch.sh worlds          # 列出所有场景
```

---

## 遥控操作

### 键盘（`./ros2_launch.sh teleop`）

```
移动          速度调节        模式切换
──────────    ────────────    ─────────────────────────
W  前进        Z  线速度 -     1  Idle（待机）
S  后退        X  线速度 +     2  Forced Stand（锁定站姿）
A  左平移      C  角速度 -     3  Walk / Trot（步行）
D  右平移      V  角速度 +     4  Trot Running（快走）
Q  左转                        5  Recovery（恢复）
E  右转
                SPACE  急停 · ESC  退出
```

### 手柄（Xbox / PS4）

| 输入 | 功能 |
|------|------|
| 左摇杆 ↑↓ | 前进 / 后退 |
| 左摇杆 ←→ | 左平移 / 右平移 |
| 右摇杆 ←→ | 左转 / 右转 |
| A / X | Walk 模式（Trot） |
| B / O | Forced Stand |
| X / □ | Idle |
| Y / △ | Recovery |
| LB / L1 | 减小速度 |
| RB / R1 | 增大速度 |
| Back / Select | 急停 |
| Start | 启用行走 |

```bash
# 启动手柄遥控
./ros2_launch.sh run h1_control joystick_teleop.py
```

---

## 项目结构

```
Unitree/
├── ros2_launch.sh                        # 统一启动脚本
├── src/
│   ├── h1_control/                       # 控制层
│   │   ├── scripts/
│   │   │   ├── kinematic_base_driver.py  # ★ 运动学底座 + 步态动画（核心）
│   │   │   ├── keyboard_teleop.py        # 键盘遥控
│   │   │   ├── joystick_teleop.py        # 手柄遥控
│   │   │   ├── high_level_control.py     # 高层控制节点
│   │   │   ├── gazebo_sim_controller.py  # Gazebo 仿真控制器
│   │   │   └── velocity_controller.py   # 速度控制器
│   │   ├── launch/
│   │   │   ├── simulation_control.launch.py  # full 模式入口
│   │   │   ├── keyboard_teleop.launch.py
│   │   │   ├── joystick_teleop.launch.py
│   │   │   └── h1_control.launch.py
│   │   └── config/
│   │       └── control_params.yaml
│   │
│   ├── h1_gazebo/                        # 仿真层
│   │   ├── launch/
│   │   │   ├── h1_gazebo.launch.py       # gazebo 模式入口
│   │   │   └── h1_rviz.launch.py
│   │   ├── worlds/                       # 5 种场景
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
│       └── h1_description/               # H1 机器人 URDF（激活）
│           └── urdf/
│               ├── h1.urdf
│               └── h1_with_hand.urdf
└── 使用说明.md                            # 中文详细使用文档
```

> `robots/` 下其他型号（A1、B2、G1、Go2 等）均含 `COLCON_IGNORE`，不参与构建，保留为参考。

---

## 架构与原理

### 为什么需要运动学底座？

双足机器人是不稳定倒立摆，没有闭环平衡控制器时仿真一开始就会倒下。
本项目通过**运动学浮动底座**绕过这一问题：

```
键盘 / 手柄
    │
    ▼  /cmd_vel (geometry_msgs/Twist)
kinematic_base_driver
    ├─► set_pose 服务 ──────────────────► Gazebo 骨盆位姿
    │     (ros_gz_interfaces/SetEntityPose)  (直立 · 高度恒定 · 按指令滑行)
    │
    └─► /model/h1/joint/<j>/cmd_pos ──► JointPositionController × 19
          (std_msgs/Float64)               (腿臂正弦步态动画)

        以上话题 / 服务均由 ros_gz_bridge 桥接
```

**工作流程：**
1. 订阅 `/cmd_vel`，在机体坐标系中积分出世界位姿 `(x, y, yaw)`，高度 `z` 和 `roll/pitch` 恒定；
2. 每 20 ms（50 Hz）调用 `set_pose` 直接写入骨盆位姿——机器人永远直立不倒；
3. 同步生成正弦步态目标，步频随速度从 0.8 Hz 线性提升至 2.2 Hz；静止时平滑回到站姿。

> **注意**：脚与地面无真实物理约束（会滑动），步态为视觉动画，非动力学行走。

---

## 话题与服务

### Gazebo → ROS 2（`ros_gz_bridge` 桥接）

| 话题 | 类型 | 说明 |
|------|------|------|
| `/clock` | `rosgraph_msgs/Clock` | 仿真时钟 |
| `/joint_states` | `sensor_msgs/JointState` | 19 关节状态 |
| `/imu` | `sensor_msgs/Imu` | IMU 数据 |
| `/odom` | `nav_msgs/Odometry` | 里程计 |

### ROS 2 → Gazebo

| 话题 / 服务 | 类型 | 说明 |
|-------------|------|------|
| `/cmd_vel` | `geometry_msgs/Twist` | 速度指令输入 |
| `/world/h1_world/set_pose` | `ros_gz_interfaces/srv/SetEntityPose` | 骨盆位姿写入 |
| `/model/h1/joint/<joint>/cmd_pos` × 19 | `std_msgs/Float64` | 关节位置指令 |

---

## 可调参数

`kinematic_base_driver.py` / `simulation_control.launch.py`：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `stand_height` | `0.98` | 骨盆保持高度（m） |
| `update_rate` | `50.0` | 位姿刷新频率（Hz） |
| `max_vx` | `1.0` | 前后速度上限（m/s） |
| `max_vy` | `0.5` | 横向速度上限（m/s） |
| `max_wz` | `1.5` | 转向角速度上限（rad/s） |
| `animate_gait` | `True` | 是否启用步态动画 |

```bash
# 示例
ros2 launch h1_control simulation_control.launch.py stand_height:=0.95 rviz:=false
```

---

## 排错

<details>
<summary><b>机器人一开就倒下</b></summary>

使用了 `gazebo` 命令（无底座驱动）。改用：
```bash
./ros2_launch.sh full
```
</details>

<details>
<summary><b>teleop 报 <code>No executable found</code></b></summary>

脚本缺少可执行权限：
```bash
chmod +x src/h1_control/scripts/*.py
```
</details>

<details>
<summary><b>Gazebo 崩溃：<code>Ogre::UnimplementedException</code></b></summary>

WSL2 OpenGL 受限问题，已在 `h1_gazebo.launch.py` 中通过 `--render-engine ogre`（v1）自动修复。
物理机（含 GPU 直通）如需更好画质，可从 launch 文件中移除该参数。
</details>

<details>
<summary><b>CycloneDDS 网卡错误</b></summary>

`ros2_launch.sh` 已强制 `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`，自动绕过。
</details>

<details>
<summary><b>conda 与 ROS 2 Python 冲突</b></summary>

脚本使用 `env -i` 启动干净环境，自动隔离 conda。请勿绕过脚本直接调用 `colcon` / `ros2`。
</details>

<details>
<summary><b>日志中 <code>joint_state_publisher ... process has died</code></b></summary>

此节点在 `h1_gazebo.launch.py` 中冗余（关节状态已由 URDF 插件 + 桥接提供），报错无害可忽略。
</details>

---

## 路线图

- [ ] 真实物理行走（MPC / WBC 平衡控制器）
- [ ] 脚部接触约束，消除滑步
- [ ] ROS 2 Nav2 导航集成
- [ ] 支持 H1-2 型号

---

## 许可证

本项目基于 [Apache License 2.0](LICENSE) 发布。

---

## 致谢

- [Unitree Robotics](https://www.unitree.com/) — H1 机器人硬件与 SDK
- [unitree_ros](https://github.com/unitreerobotics/unitree_ros) — 原始机器人描述文件
