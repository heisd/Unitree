#!/usr/bin/env python3
"""
Velocity Controller Node for Unitree H1 Robot

This node provides a simple velocity control interface that can be used
for simulation testing. It takes cmd_vel commands and applies them to
control the robot's base movement in Gazebo.

For real robot, use high_level_control.py which interfaces with
the Unitree SDK.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64MultiArray
import math


class VelocityController(Node):
    """Velocity controller for H1 robot simulation."""

    def __init__(self):
        super().__init__('h1_velocity_controller')

        # Parameters
        self.declare_parameter('max_linear_x', 1.0)
        self.declare_parameter('max_linear_y', 0.5)
        self.declare_parameter('max_angular_z', 1.5)

        self.max_vx = self.get_parameter('max_linear_x').value
        self.max_vy = self.get_parameter('max_linear_y').value
        self.max_wz = self.get_parameter('max_angular_z').value

        # Current velocities
        self.vx = 0.0
        self.vy = 0.0
        self.wz = 0.0

        # Subscribe to cmd_vel
        self.cmd_vel_sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        # Publish to Gazebo joint controllers (if using ros2_control)
        self.joint_cmd_pub = self.create_publisher(
            Float64MultiArray,
            '/h1/joint_commands',
            10
        )

        # Timer for control loop
        self.create_timer(0.01, self.control_loop)  # 100 Hz

        self.get_logger().info('H1 Velocity Controller started')
        self.get_logger().info(f'Limits: vx={self.max_vx}, vy={self.max_vy}, wz={self.max_wz}')

    def cmd_vel_callback(self, msg: Twist):
        """Process velocity commands."""
        self.vx = max(-self.max_vx, min(self.max_vx, msg.linear.x))
        self.vy = max(-self.max_vy, min(self.max_vy, msg.linear.y))
        self.wz = max(-self.max_wz, min(self.max_wz, msg.angular.z))

        self.get_logger().debug(f'Velocity: vx={self.vx:.2f}, vy={self.vy:.2f}, wz={self.wz:.2f}')

    def control_loop(self):
        """
        Control loop - In a real implementation, this would:
        1. Convert velocities to joint commands
        2. Use inverse kinematics for walking gait
        3. Publish to joint controllers
        
        For simulation, this is a placeholder for the locomotion controller.
        """
        # This is where locomotion algorithms would be implemented
        # For now, just log if there's motion commanded
        if abs(self.vx) > 0.01 or abs(self.vy) > 0.01 or abs(self.wz) > 0.01:
            pass  # Locomotion would happen here


def main(args=None):
    rclpy.init(args=args)
    node = VelocityController()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
