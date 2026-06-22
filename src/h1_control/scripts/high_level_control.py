#!/usr/bin/env python3
"""
High-Level Motion Controller for Unitree H1 Robot

This node provides high-level motion control for the H1 humanoid robot,
including walking, running, and body pose control.

Subscribed Topics:
    /cmd_vel (geometry_msgs/Twist): Velocity commands (linear.x, linear.y, angular.z)
    /h1/mode (std_msgs/Int32): Robot mode command
    /h1/gait_type (std_msgs/Int32): Gait type command
    /h1/body_height (std_msgs/Float64): Body height adjustment
    /h1/foot_raise_height (std_msgs/Float64): Foot raise height

Published Topics:
    /h1/high_cmd (geometry_msgs/Twist): High-level command output
    /h1/robot_state (std_msgs/String): Current robot state

Robot Modes:
    0: Idle / Default Stand
    1: Forced Stand (lock position)
    2: Walk Continuously
    3: Stand Down
    4: Stand Up
    5: Damping Mode
    6: Recovery Stand

Gait Types:
    0: Idle
    1: Trot
    2: Trot Running
    3: Climb Stair
    4: Trot Obstacle
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from geometry_msgs.msg import Twist
from std_msgs.msg import Int32, Float64, String
from sensor_msgs.msg import Joy
import json


class H1HighLevelController(Node):
    """High-level motion controller for Unitree H1 robot."""

    # Robot Mode Constants
    MODE_IDLE = 0
    MODE_FORCED_STAND = 1
    MODE_WALK = 2
    MODE_STAND_DOWN = 3
    MODE_STAND_UP = 4
    MODE_DAMPING = 5
    MODE_RECOVERY = 6

    # Gait Type Constants
    GAIT_IDLE = 0
    GAIT_TROT = 1
    GAIT_TROT_RUNNING = 2
    GAIT_CLIMB_STAIR = 3
    GAIT_TROT_OBSTACLE = 4

    def __init__(self):
        super().__init__('h1_high_level_controller')

        # Declare parameters
        self.declare_parameter('max_linear_velocity_x', 1.0)  # m/s
        self.declare_parameter('max_linear_velocity_y', 0.5)  # m/s
        self.declare_parameter('max_angular_velocity', 1.5)   # rad/s
        self.declare_parameter('default_gait_type', 1)        # Trot
        self.declare_parameter('default_body_height', 0.0)    # meters
        self.declare_parameter('default_foot_raise_height', 0.08)  # meters
        self.declare_parameter('control_frequency', 500.0)    # Hz
        self.declare_parameter('velocity_smoothing', 0.1)     # Smoothing factor

        # Get parameters
        self.max_vx = self.get_parameter('max_linear_velocity_x').value
        self.max_vy = self.get_parameter('max_linear_velocity_y').value
        self.max_wz = self.get_parameter('max_angular_velocity').value
        self.default_gait = self.get_parameter('default_gait_type').value
        self.default_body_height = self.get_parameter('default_body_height').value
        self.default_foot_height = self.get_parameter('default_foot_raise_height').value
        self.control_freq = self.get_parameter('control_frequency').value
        self.smoothing = self.get_parameter('velocity_smoothing').value

        # State variables
        self.current_mode = self.MODE_IDLE
        self.current_gait = self.default_gait
        self.body_height = self.default_body_height
        self.foot_raise_height = self.default_foot_height

        # Velocity state (with smoothing)
        self.target_vx = 0.0
        self.target_vy = 0.0
        self.target_wz = 0.0
        self.current_vx = 0.0
        self.current_vy = 0.0
        self.current_wz = 0.0

        # Body orientation (euler angles)
        self.body_roll = 0.0
        self.body_pitch = 0.0
        self.body_yaw = 0.0

        # QoS Profile
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
        self.gait_sub = self.create_subscription(
            Int32, '/h1/gait_type', self.gait_callback, qos)
        self.body_height_sub = self.create_subscription(
            Float64, '/h1/body_height', self.body_height_callback, qos)
        self.foot_height_sub = self.create_subscription(
            Float64, '/h1/foot_raise_height', self.foot_height_callback, qos)
        self.joy_sub = self.create_subscription(
            Joy, '/joy', self.joy_callback, qos)

        # Publishers
        self.high_cmd_pub = self.create_publisher(Twist, '/h1/high_cmd', qos)
        self.state_pub = self.create_publisher(String, '/h1/robot_state', qos)

        # Control loop timer
        timer_period = 1.0 / self.control_freq
        self.control_timer = self.create_timer(timer_period, self.control_loop)

        # State publishing timer (10 Hz)
        self.state_timer = self.create_timer(0.1, self.publish_state)

        self.get_logger().info('H1 High-Level Controller initialized')
        self.get_logger().info(f'Max velocities: vx={self.max_vx}, vy={self.max_vy}, wz={self.max_wz}')

    def cmd_vel_callback(self, msg: Twist):
        """Handle velocity commands from /cmd_vel topic."""
        # Clamp velocities to safe limits
        self.target_vx = max(-self.max_vx, min(self.max_vx, msg.linear.x))
        self.target_vy = max(-self.max_vy, min(self.max_vy, msg.linear.y))
        self.target_wz = max(-self.max_wz, min(self.max_wz, msg.angular.z))

        # Auto-switch to walk mode if velocity is commanded
        if abs(self.target_vx) > 0.01 or abs(self.target_vy) > 0.01 or abs(self.target_wz) > 0.01:
            if self.current_mode == self.MODE_IDLE or self.current_mode == self.MODE_FORCED_STAND:
                self.current_mode = self.MODE_WALK
                self.get_logger().info('Auto-switching to WALK mode')

    def mode_callback(self, msg: Int32):
        """Handle mode change commands."""
        if 0 <= msg.data <= 6:
            old_mode = self.current_mode
            self.current_mode = msg.data
            self.get_logger().info(f'Mode changed: {old_mode} -> {self.current_mode}')
        else:
            self.get_logger().warn(f'Invalid mode: {msg.data}')

    def gait_callback(self, msg: Int32):
        """Handle gait type change commands."""
        if 0 <= msg.data <= 4:
            old_gait = self.current_gait
            self.current_gait = msg.data
            self.get_logger().info(f'Gait changed: {old_gait} -> {self.current_gait}')
        else:
            self.get_logger().warn(f'Invalid gait type: {msg.data}')

    def body_height_callback(self, msg: Float64):
        """Handle body height adjustment."""
        # Clamp body height to safe range (-0.25 to 0.1 meters)
        self.body_height = max(-0.25, min(0.1, msg.data))

    def foot_height_callback(self, msg: Float64):
        """Handle foot raise height adjustment."""
        # Clamp foot raise height to safe range (0 to 0.2 meters)
        self.foot_raise_height = max(0.0, min(0.2, msg.data))

    def joy_callback(self, msg: Joy):
        """Handle joystick input for teleoperation."""
        if len(msg.axes) >= 4:
            # Standard joystick mapping:
            # Left stick: axes[0]=left/right, axes[1]=forward/back
            # Right stick: axes[2]=left/right (rotation), axes[3]=up/down
            self.target_vx = msg.axes[1] * self.max_vx
            self.target_vy = msg.axes[0] * self.max_vy
            self.target_wz = msg.axes[2] * self.max_wz

        if len(msg.buttons) >= 4:
            # Button mappings
            if msg.buttons[0]:  # A button - Stand
                self.current_mode = self.MODE_FORCED_STAND
            if msg.buttons[1]:  # B button - Walk
                self.current_mode = self.MODE_WALK
            if msg.buttons[2]:  # X button - Idle
                self.current_mode = self.MODE_IDLE
            if msg.buttons[3]:  # Y button - Recovery
                self.current_mode = self.MODE_RECOVERY

    def control_loop(self):
        """Main control loop running at high frequency."""
        # Apply velocity smoothing
        alpha = self.smoothing
        self.current_vx = alpha * self.target_vx + (1 - alpha) * self.current_vx
        self.current_vy = alpha * self.target_vy + (1 - alpha) * self.current_vy
        self.current_wz = alpha * self.target_wz + (1 - alpha) * self.current_wz

        # If mode is not walk, zero out velocities
        if self.current_mode != self.MODE_WALK:
            self.current_vx = 0.0
            self.current_vy = 0.0
            self.current_wz = 0.0

        # Publish high-level command
        cmd = Twist()
        cmd.linear.x = self.current_vx
        cmd.linear.y = self.current_vy
        cmd.linear.z = self.body_height
        cmd.angular.x = self.body_roll
        cmd.angular.y = self.body_pitch
        cmd.angular.z = self.current_wz

        self.high_cmd_pub.publish(cmd)

    def publish_state(self):
        """Publish current robot state."""
        mode_names = {
            0: 'IDLE', 1: 'FORCED_STAND', 2: 'WALK',
            3: 'STAND_DOWN', 4: 'STAND_UP', 5: 'DAMPING', 6: 'RECOVERY'
        }
        gait_names = {
            0: 'IDLE', 1: 'TROT', 2: 'TROT_RUNNING',
            3: 'CLIMB_STAIR', 4: 'TROT_OBSTACLE'
        }

        state = {
            'mode': mode_names.get(self.current_mode, 'UNKNOWN'),
            'mode_id': self.current_mode,
            'gait': gait_names.get(self.current_gait, 'UNKNOWN'),
            'gait_id': self.current_gait,
            'velocity': {
                'x': round(self.current_vx, 3),
                'y': round(self.current_vy, 3),
                'yaw': round(self.current_wz, 3)
            },
            'body_height': round(self.body_height, 3),
            'foot_raise_height': round(self.foot_raise_height, 3)
        }

        msg = String()
        msg.data = json.dumps(state)
        self.state_pub.publish(msg)

    def set_mode(self, mode: int):
        """Set robot mode programmatically."""
        if 0 <= mode <= 6:
            self.current_mode = mode

    def set_gait(self, gait: int):
        """Set gait type programmatically."""
        if 0 <= gait <= 4:
            self.current_gait = gait

    def stop(self):
        """Emergency stop - zero all velocities and switch to idle."""
        self.target_vx = 0.0
        self.target_vy = 0.0
        self.target_wz = 0.0
        self.current_vx = 0.0
        self.current_vy = 0.0
        self.current_wz = 0.0
        self.current_mode = self.MODE_IDLE
        self.get_logger().warn('Emergency stop activated!')


def main(args=None):
    rclpy.init(args=args)
    node = H1HighLevelController()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.stop()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
