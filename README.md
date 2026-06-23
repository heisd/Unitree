# Unitree H1 ROS 2 SDK

ROS 2 Humble + Ignition Gazebo Fortress 下的 Unitree H1 人形机器人仿真 SDK。
提供运动学浮动底座驱动、步态动画、键盘/手柄遥控，以及多种仿真场景。

---

## 功能特性

- **H1 机器人描述**：完整 URDF 模型，含 19 个受控关节（含带手版本 `h1_with_hand.urdf`）
- **Gazebo 仿真**：Ignition Gazebo Fortress 集成，支持 5 种内置场景
- **运动学浮动底座**：通过 `set_pose` 服务硬设定骨盆位姿，机器人永远直立、无需平衡控制器
- **行走步态动画**：正弦步态随速度缩放，腿部前后摆动、手臂反向配合，视觉逼真
- **键盘遥控**：`W/A/S/D/Q/E` 实时控制
- **手柄支持**：Gamepad/Joystick 遥控

---

## 环境要求

- Ubuntu 22.04
- ROS 2 Humble
- Ignition Gazebo Fortress：`sudo apt install ros-humble-ros-gz`
- 依赖包：`ros_gz_sim`、`ros_gz_bridge`、`ros_gz_interfaces`、`robot_state_publisher`、`rviz2`、`joint_state_publisher`
- **WSL2 用户**：已在 launch 文件中强制使用 OGRE v1 渲染引擎（`--render-engine ogre`），无需手动配置

---

## 安装

```bash
git clone <repo-url>
cd Unitree

# 构建工作区
./ros2_launch.sh build
```

> 工作区使用 `--symlink-install`。修改 Python 脚本、launch 文件、URDF **无需重新构建**；
> 只有新增可执行脚本或修改 `CMakeLists.txt` 时才需再次 `build`。

---

## 快速启动

所有命令通过 `ros2_launch.sh` 运行。该脚本自动配置干净环境（强制 FastRTPS、绕开 conda 冲突）。

```bash
# 终端 1：启动完整仿真（Gazebo + 运动学底座驱动）
./ros2_launch.sh full

# 终端 2：键盘遥控
./ros2_launch.sh teleop
```

---

## 命令参考

| 命令 | 说明 |
|------|------|
| `./ros2_launch.sh build` | 构建工作区 |
| `./ros2_launch.sh gazebo` | 仅启动 Gazebo 仿真（无底座驱动，机器人会倒） |
| `./ros2_launch.sh gazebo --world <name>` | 指定场景文件（默认 `h1_world`） |
| `./ros2_launch.sh gazebo --no-rviz` | 不启动 RViz |
| `./ros2_launch.sh gazebo --no-gui` | 无头模式（不开 Gazebo GUI） |
| `./ros2_launch.sh full` | **推荐**。Gazebo + 运动学底座驱动，机器人直立可遥控 |
| `./ros2_launch.sh full --world <name>` | 完整仿真并指定场景 |
| `./ros2_launch.sh teleop` | 键盘遥控（需另开终端） |
| `./ros2_launch.sh control` | 启动高层控制节点 |
| `./ros2_launch.sh worlds` | 列出所有可用场景 |
| `./ros2_launch.sh topic list` | 列出 ROS 2 话题 |
| `./ros2_launch.sh node list` | 列出 ROS 2 节点 |
| `./ros2_launch.sh run <pkg> <exe>` | 运行任意 ROS 2 可执行文件 |

---

## 可用仿真场景

场景文件位于 `src/h1_gazebo/worlds/`：

| 名称 | 说明 |
|------|------|
| `h1_world`（默认） | 带建筑、道路、植被的城市街道场景 |
| `empty` | 空白平地，调试用 |
| `obstacle_course` | 障碍物场地 |
| `office` | 室内办公室场景 |
| `warehouse` | 仓库场景 |

```bash
# 示例：在仓库场景中启动
./ros2_launch.sh full --world warehouse

# 列出所有场景
./ros2_launch.sh worlds
```

---

## 键盘遥控操作

```
移动控制：
  W / S   —— 前进 / 后退
  A / D   —— 左平移 / 右平移
  Q / E   —— 左转 / 右转

速度调节：
  Z / X   —— 增大 / 减小线速度
  C / V   —— 增大 / 减小角速度

SPACE   —— 急停
ESC     —— 退出
```

---

## 包结构

```
Unitree/
├── ros2_launch.sh                  # 统一启动脚本
└── src/
    ├── h1_control/                 # 控制层
    │   ├── scripts/
    │   │   ├── kinematic_base_driver.py   # 运动学浮动底座 + 步态动画（核心）
    │   │   ├── keyboard_teleop.py         # 键盘遥控
    │   │   ├── joystick_teleop.py         # 手柄遥控
    │   │   ├── high_level_control.py      # 高层控制节点
    │   │   ├── gazebo_sim_controller.py   # Gazebo 仿真控制器
    │   │   └── velocity_controller.py     # 速度控制器
    │   ├── launch/
    │   │   ├── simulation_control.launch.py  # full 模式入口
    │   │   ├── keyboard_teleop.launch.py
    │   │   ├── joystick_teleop.launch.py
    │   │   └── h1_control.launch.py
    │   └── config/
    │       └── control_params.yaml
    │
    ├── h1_gazebo/                  # 仿真层
    │   ├── launch/
    │   │   ├── h1_gazebo.launch.py        # gazebo 模式入口
    │   │   └── h1_rviz.launch.py
    │   ├── worlds/
    │   │   ├── h1_world.sdf
    │   │   ├── empty.sdf
    │   │   ├── obstacle_course.sdf
    │   │   ├── office.sdf
    │   │   └── warehouse.sdf
    │   ├── urdf/
    │   │   └── h1_gazebo.urdf.xacro
    │   └── config/
    │       ├── bridge_config.yaml
    │       ├── h1_controllers.yaml
    │       └── h1_display.rviz
    │
    └── robots/
        └── h1_description/         # H1 机器人模型（激活）
            └── urdf/
                ├── h1.urdf
                └── h1_with_hand.urdf
```

> `robots/` 下其他型号（A1、B2、G1、Go2 等）均含 `COLCON_IGNORE`，不参与构建，仅作参考。

---

## 话题与服务

### Gazebo → ROS 2（`ros_gz_bridge` 桥接）

| 话题 | 类型 | 说明 |
|------|------|------|
| `/clock` | `rosgraph_msgs/Clock` | 仿真时钟 |
| `/joint_states` | `sensor_msgs/JointState` | 19 个关节状态 |
| `/imu` | `sensor_msgs/Imu` | IMU 数据 |
| `/odom` | `nav_msgs/Odometry` | 里程计 |

### ROS 2 → Gazebo

| 话题 / 服务 | 类型 | 说明 |
|-------------|------|------|
| `/cmd_vel` | `geometry_msgs/Twist` | 速度指令（遥控输入） |
| `/world/h1_world/set_pose` | `ros_gz_interfaces/srv/SetEntityPose` | 底座驱动强设骨盆位姿 |
| `/model/h1/joint/<关节>/cmd_pos` × 19 | `std_msgs/Float64` | 步态关节位置指令 |

---

## 运动学底座原理

> **为什么需要运动学底座？**
> 双足机器人是不稳定倒立摆。没有平衡控制器时，仿真一开始物理就会让机器人倒下。

`kinematic_base_driver.py` 的方案：

1. 订阅 `/cmd_vel`，按**机体坐标系**积分出底座世界位姿 `(x, y, yaw)`，高度 `z` 和 `roll/pitch` 固定；
2. 每 20 ms（50 Hz）调用 Gazebo `set_pose` 服务**直接写入骨盆位姿**——机器人永远直立；
3. 同时生成正弦步态目标，发送到 19 个关节的 `JointPositionController`——速度越大步频越高（0.8 ~ 2.2 Hz），静止时平滑回站姿。

```
keyboard_teleop ─/cmd_vel─▶ kinematic_base_driver ─┬─ set_pose 服务 ──▶ Gazebo 骨盆位姿
                                                    └─ /joint/cmd_pos ──▶ 关节控制器（步态动画）
                                （均由 ros_gz_bridge 桥接）
```

---

## 可调参数

`simulation_control.launch.py` / `kinematic_base_driver.py`：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `stand_height` | `0.98` | 骨盆保持高度（米） |
| `update_rate` | `50.0` | 底座位姿刷新频率（Hz） |
| `max_vx` | `1.0` | 前后速度上限（m/s） |
| `max_vy` | `0.5` | 横向速度上限（m/s） |
| `max_wz` | `1.5` | 转向角速度上限（rad/s） |
| `animate_gait` | `True` | 是否启用行走动画 |

```bash
# 示例：调整站立高度并关闭 RViz
ros2 launch h1_control simulation_control.launch.py stand_height:=0.95 rviz:=false
```

---

## 排错

**机器人一开始就倒下**
使用了 `./ros2_launch.sh gazebo`（无底座驱动）。请改用 `./ros2_launch.sh full`。

**`teleop` 报 `No executable found`**
脚本缺少可执行权限：
```bash
chmod +x src/h1_control/scripts/*.py
```
建议将此权限提交进 git。

**Gazebo 崩溃：`Ogre::UnimplementedException ... GL3PlusTextureGpu::copyTo`**
WSL2 的 OpenGL 受限。已在 `h1_gazebo.launch.py` 中通过 `--render-engine ogre`（v1）解决，无需手动处理。
若使用带 GPU 直通的物理机，可移除该参数以获得更好画质。

**CycloneDDS 网卡错误 `enp7s0: does not match an available interface`**
脚本已强制使用 `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`，绕过此问题。

**conda 与 ROS 2 Python 冲突**
`ros2_launch.sh` 使用 `env -i` 启动干净环境，自动隔离 conda。请勿绕过脚本直接调用 `colcon`/`ros2`。

**日志中 `joint_state_publisher ... process has died`**
此节点在 `h1_gazebo.launch.py` 中是冗余的（关节状态已由 URDF 插件 + 桥接提供），报错无害，可忽略。

---

## 局限与说明

- 当前为**运动学可视化**：底座由 `set_pose` 驱动滑行，脚与地面**无真实约束**（会滑动）；
- 步态为视觉动画，非物理意义上的行走；
- 如需真正的自由站立/行走，需实现完整平衡控制器（MPC/WBC），超出本 SDK 范围。

---

## 许可证

Apache License 2.0

## 致谢

- [Unitree Robotics](https://www.unitree.com/) — H1 机器人
- [unitree_ros](https://github.com/unitreerobotics/unitree_ros) — 原始机器人描述文件
