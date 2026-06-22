#!/usr/bin/env python3
"""
Joystick Teleoperation for Unitree H1 Robot

Control the H1 robot using a gamepad/joystick.

Default Button Mapping (Xbox/PS4):
    Left Stick  : Move forward/backward and strafe
    Right Stick : Rotate
    A/X Button  : Toggle Walk Mode
    B/O Button  : Forced Stand
    X/□ Button  : Idle Mode
    Y/△ Button  : Recovery Mode
    LB/L1       : Decrease speed
    RB/R1       : Increase speed
    Start       : Enable walking
    Back/Select : Emergency stop
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist
from std_msgs.msg import Int32


class JoystickTeleop(Node):
    """Joystick teleoperation node for H1 robot."""

    def __init__(self):
        super().__init__('h1_joystick_teleop')

        # Parameters
        self.declare_parameter('max_linear_x', 1.0)
        self.declare_parameter('max_linear_y', 0.5)
        self.declare_parameter('max_angular_z', 1.5)
        self.declare_parameter('speed_multiplier', 1.0)
        self.declare_parameter('deadzone', 0.1)
        self.declare_parameter('axis_linear_x', 1)
        self.declare_parameter('axis_linear_y', 0)
        self.declare_parameter('axis_angular_z', 3)
        self.declare_parameter('button_walk', 0)      # A
        self.declare_parameter('button_stand', 1)     # B
        self.declare_parameter('button_idle', 2)      # X
        self.declare_parameter('button_recovery', 3)  # Y
        self.declare_parameter('button_speed_down', 4)  # LB
        self.declare_parameter('button_speed_up', 5)    # RB
        self.declare_parameter('button_estop', 6)       # Back

        # Get parameters
        self.max_vx = self.get_parameter('max_linear_x').value
        self.max_vy = self.get_parameter('max_linear_y').value
        self.max_wz = self.get_parameter('max_angular_z').value
        self.speed_mult = self.get_parameter('speed_multiplier').value
        self.deadzone = self.get_parameter('deadzone').value

        # Axis mappings
        self.axis_vx = self.get_parameter('axis_linear_x').value
        self.axis_vy = self.get_parameter('axis_linear_y').value
        self.axis_wz = self.get_parameter('axis_angular_z').value

        # Button mappings
        self.btn_walk = self.get_parameter('button_walk').value
        self.btn_stand = self.get_parameter('button_stand').value
        self.btn_idle = self.get_parameter('button_idle').value
        self.btn_recovery = self.get_parameter('button_recovery').value
        self.btn_speed_down = self.get_parameter('button_speed_down').value
        self.btn_speed_up = self.get_parameter('button_speed_up').value
        self.btn_estop = self.get_parameter('button_estop').value

        # State
        self.enabled = False
        self.last_buttons = []

        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.mode_pub = self.create_publisher(Int32, '/h1/mode', 10)
        self.gait_pub = self.create_publisher(Int32, '/h1/gait_type', 10)

        # Subscriber
        self.joy_sub = self.create_subscription(Joy, '/joy', self.joy_callback, 10)

        self.get_logger().info('Joystick Teleop started')
        self.get_logger().info('Press START to enable, BACK for emergency stop')

    def apply_deadzone(self, value: float) -> float:
        """Apply deadzone to axis value."""
        if abs(value) < self.deadzone:
            return 0.0
        # Scale the remaining range
        sign = 1.0 if value > 0 else -1.0
        return sign * (abs(value) - self.deadzone) / (1.0 - self.deadzone)

    def joy_callback(self, msg: Joy):
        """Process joystick input."""
        # Check for button presses (edge detection)
        buttons = msg.buttons

        def button_pressed(btn_idx):
            if btn_idx >= len(buttons):
                return False
            if len(self.last_buttons) <= btn_idx:
                return buttons[btn_idx] == 1
            return buttons[btn_idx] == 1 and self.last_buttons[btn_idx] == 0

        # Mode buttons
        if button_pressed(self.btn_walk):
            self.publish_mode(2)
            self.publish_gait(1)
            self.enabled = True
            self.get_logger().info('WALK mode enabled (Trot)')

        if button_pressed(self.btn_stand):
            self.publish_mode(1)
            self.enabled = False
            self.get_logger().info('FORCED STAND mode')

        if button_pressed(self.btn_idle):
            self.publish_mode(0)
            self.enabled = False
            self.get_logger().info('IDLE mode')

        if button_pressed(self.btn_recovery):
            self.publish_mode(6)
            self.get_logger().info('RECOVERY mode')

        if button_pressed(self.btn_estop):
            self.enabled = False
            self.publish_mode(0)
            self.publish_stop()
            self.get_logger().warn('EMERGENCY STOP!')

        # Speed adjustment
        if button_pressed(self.btn_speed_up):
            self.speed_mult = min(1.5, self.speed_mult + 0.1)
            self.get_logger().info(f'Speed: {self.speed_mult:.1f}x')

        if button_pressed(self.btn_speed_down):
            self.speed_mult = max(0.3, self.speed_mult - 0.1)
            self.get_logger().info(f'Speed: {self.speed_mult:.1f}x')

        # Store button state for edge detection
        self.last_buttons = list(buttons)

        # Process axes for velocity
        if self.enabled and len(msg.axes) > max(self.axis_vx, self.axis_vy, self.axis_wz):
            vx = self.apply_deadzone(msg.axes[self.axis_vx]) * self.max_vx * self.speed_mult
            vy = self.apply_deadzone(msg.axes[self.axis_vy]) * self.max_vy * self.speed_mult
            wz = self.apply_deadzone(msg.axes[self.axis_wz]) * self.max_wz * self.speed_mult

            self.publish_velocity(vx, vy, wz)
        elif not self.enabled:
            self.publish_velocity(0.0, 0.0, 0.0)

    def publish_velocity(self, vx: float, vy: float, wz: float):
        """Publish velocity command."""
        msg = Twist()
        msg.linear.x = vx
        msg.linear.y = vy
        msg.angular.z = wz
        self.cmd_vel_pub.publish(msg)

    def publish_stop(self):
        """Publish stop command."""
        self.publish_velocity(0.0, 0.0, 0.0)

    def publish_mode(self, mode: int):
        """Publish mode command."""
        msg = Int32()
        msg.data = mode
        self.mode_pub.publish(msg)

    def publish_gait(self, gait: int):
        """Publish gait type command."""
        msg = Int32()
        msg.data = gait
        self.gait_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = JoystickTeleop()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
