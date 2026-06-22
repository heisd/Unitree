#!/usr/bin/env python3
"""
Gazebo Simulation Controller for Unitree H1 Robot

This node bridges high-level velocity commands (/cmd_vel) to Gazebo simulation.
It uses the ApplyLinkWrench system to apply forces and torques to move the robot.

For a realistic walking simulation, this would need to be replaced with a proper
locomotion controller that generates joint trajectories. This simplified version
allows basic movement for testing and visualization.

Subscribed Topics:
    /cmd_vel (geometry_msgs/Twist): Velocity commands
    /h1/mode (std_msgs/Int32): Robot mode
    /joint_states (sensor_msgs/JointState): Current joint states from Gazebo

Published Topics:
    /model/h1/joint/*/cmd_pos (std_msgs/Float64): Joint position commands to Gazebo

Services Used:
    /world/h1_world/set_pose: Set model pose in Gazebo
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from geometry_msgs.msg import Twist, Wrench, Vector3
from std_msgs.msg import Float64, Int32, String
from sensor_msgs.msg import JointState
import math
import time


class GazeboSimController(Node):
    """
    Controller that bridges ROS 2 commands to Gazebo simulation.
    """

    # H1 Robot Joint Names
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

    # Default standing pose joint positions (radians)
    STAND_POSE = {
        'left_hip_yaw_joint': 0.0,
        'left_hip_roll_joint': 0.0,
        'left_hip_pitch_joint': -0.4,
        'left_knee_joint': 0.8,
        'left_ankle_joint': -0.4,
        'right_hip_yaw_joint': 0.0,
        'right_hip_roll_joint': 0.0,
        'right_hip_pitch_joint': -0.4,
        'right_knee_joint': 0.8,
        'right_ankle_joint': -0.4,
        'torso_joint': 0.0,
        'left_shoulder_pitch_joint': 0.3,
        'left_shoulder_roll_joint': 0.3,
        'left_shoulder_yaw_joint': 0.0,
        'left_elbow_joint': 0.5,
        'right_shoulder_pitch_joint': 0.3,
        'right_shoulder_roll_joint': -0.3,
        'right_shoulder_yaw_joint': 0.0,
        'right_elbow_joint': 0.5,
    }

    def __init__(self):
        super().__init__('gazebo_sim_controller')

        # Parameters
        self.declare_parameter('control_rate', 100.0)  # Hz
        self.declare_parameter('force_scale', 500.0)   # Force multiplier for cmd_vel
        self.declare_parameter('torque_scale', 200.0)  # Torque multiplier for rotation

        self.control_rate = self.get_parameter('control_rate').value
        self.force_scale = self.get_parameter('force_scale').value
        self.torque_scale = self.get_parameter('torque_scale').value

        # State
        self.current_mode = 0  # 0=Idle, 2=Walk
        self.cmd_vx = 0.0
        self.cmd_vy = 0.0
        self.cmd_wz = 0.0
        self.current_joint_states = {}
        self.walk_phase = 0.0
        self.last_time = time.time()

        # QoS
        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )

        # Subscribers
        self.cmd_vel_sub = self.create_subscription(
            Twist, '/cmd_vel', self.cmd_vel_callback, qos)
        self.mode_sub = self.create_subscription(
            Int32, '/h1/mode', self.mode_callback, qos)
        self.joint_state_sub = self.create_subscription(
            JointState, '/joint_states', self.joint_state_callback, qos)

        # Publishers for joint position commands (Ignition Gazebo format)
        # Each joint controller subscribes to /model/h1/joint/<joint_name>/0/cmd_pos
        self.joint_cmd_pubs = {}
        for joint_name in self.JOINT_NAMES:
            topic = f'/model/h1/joint/{joint_name}/cmd_pos'
            self.joint_cmd_pubs[joint_name] = self.create_publisher(Float64, topic, qos)

        # Control loop timer
        timer_period = 1.0 / self.control_rate
        self.control_timer = self.create_timer(timer_period, self.control_loop)

        # Status timer
        self.status_timer = self.create_timer(1.0, self.print_status)

        self.get_logger().info('Gazebo Simulation Controller initialized')
        self.get_logger().info(f'Control rate: {self.control_rate} Hz')
        self.get_logger().info('Publishing joint commands for walking simulation')

    def cmd_vel_callback(self, msg: Twist):
        """Handle velocity commands."""
        self.cmd_vx = msg.linear.x
        self.cmd_vy = msg.linear.y
        self.cmd_wz = msg.angular.z

    def mode_callback(self, msg: Int32):
        """Handle mode changes."""
        old_mode = self.current_mode
        self.current_mode = msg.data
        if old_mode != self.current_mode:
            self.get_logger().info(f'Mode changed: {old_mode} -> {self.current_mode}')

    def joint_state_callback(self, msg: JointState):
        """Update current joint states."""
        for i, name in enumerate(msg.name):
            if i < len(msg.position):
                self.current_joint_states[name] = msg.position[i]

    def control_loop(self):
        """Main control loop - generates joint commands based on mode and velocity."""
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time

        # Calculate walking speed
        speed = math.sqrt(self.cmd_vx**2 + self.cmd_vy**2)
        
        # Update walk phase based on velocity
        if self.current_mode == 2 and speed > 0.01:  # Walk mode with velocity
            # Walking frequency scales with speed (0.5 - 2.0 Hz)
            walk_freq = min(2.0, 0.5 + speed * 1.5)
            self.walk_phase += 2.0 * math.pi * walk_freq * dt
            if self.walk_phase > 2.0 * math.pi:
                self.walk_phase -= 2.0 * math.pi
        else:
            # Smoothly return to stand
            self.walk_phase *= 0.95

        # Generate joint positions
        joint_positions = self.generate_joint_positions(speed)

        # Publish joint commands
        for joint_name, position in joint_positions.items():
            if joint_name in self.joint_cmd_pubs:
                msg = Float64()
                msg.data = position
                self.joint_cmd_pubs[joint_name].publish(msg)

    def generate_joint_positions(self, speed: float) -> dict:
        """
        Generate joint positions for walking motion.
        
        This is a simplified gait generator. For realistic walking,
        you would use a proper locomotion controller or MPC.
        """
        positions = dict(self.STAND_POSE)

        if self.current_mode != 2 or speed < 0.01:
            # Return standing pose
            return positions

        # Walking amplitude scales with speed
        amp = min(0.3, speed * 0.3)  # Max 0.3 radians
        
        # Phase offset between legs (180 degrees for alternating gait)
        phase_offset = math.pi

        # Left leg motion
        positions['left_hip_pitch_joint'] = self.STAND_POSE['left_hip_pitch_joint'] + \
            amp * math.sin(self.walk_phase)
        positions['left_knee_joint'] = self.STAND_POSE['left_knee_joint'] + \
            abs(amp * 0.5 * math.sin(self.walk_phase))
        positions['left_ankle_joint'] = self.STAND_POSE['left_ankle_joint'] - \
            amp * 0.3 * math.sin(self.walk_phase)

        # Right leg motion (opposite phase)
        positions['right_hip_pitch_joint'] = self.STAND_POSE['right_hip_pitch_joint'] + \
            amp * math.sin(self.walk_phase + phase_offset)
        positions['right_knee_joint'] = self.STAND_POSE['right_knee_joint'] + \
            abs(amp * 0.5 * math.sin(self.walk_phase + phase_offset))
        positions['right_ankle_joint'] = self.STAND_POSE['right_ankle_joint'] - \
            amp * 0.3 * math.sin(self.walk_phase + phase_offset)

        # Hip yaw for turning
        if abs(self.cmd_wz) > 0.01:
            turn_amp = min(0.1, abs(self.cmd_wz) * 0.1)
            direction = 1.0 if self.cmd_wz > 0 else -1.0
            positions['left_hip_yaw_joint'] = turn_amp * direction * math.sin(self.walk_phase)
            positions['right_hip_yaw_joint'] = -turn_amp * direction * math.sin(self.walk_phase + phase_offset)

        # Arm swing (natural walking motion)
        arm_amp = amp * 0.5
        positions['left_shoulder_pitch_joint'] = self.STAND_POSE['left_shoulder_pitch_joint'] - \
            arm_amp * math.sin(self.walk_phase)
        positions['right_shoulder_pitch_joint'] = self.STAND_POSE['right_shoulder_pitch_joint'] - \
            arm_amp * math.sin(self.walk_phase + phase_offset)

        return positions

    def print_status(self):
        """Print status periodically."""
        mode_names = {0: 'IDLE', 1: 'STAND', 2: 'WALK', 3: 'DOWN', 4: 'UP', 5: 'DAMP', 6: 'RECOVERY'}
        mode_name = mode_names.get(self.current_mode, 'UNKNOWN')
        speed = math.sqrt(self.cmd_vx**2 + self.cmd_vy**2)
        
        if speed > 0.01 or self.current_mode == 2:
            self.get_logger().info(
                f'Mode: {mode_name} | Vel: vx={self.cmd_vx:.2f}, vy={self.cmd_vy:.2f}, wz={self.cmd_wz:.2f}'
            )


def main(args=None):
    rclpy.init(args=args)
    node = GazeboSimController()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
