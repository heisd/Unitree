#!/usr/bin/env python3
"""
Kinematic Floating-Base Driver for the Unitree H1 in Ignition Gazebo.

The H1 SDK has no balance/locomotion controller, so a physically free humanoid
falls over the instant physics starts. This node provides a *kinematic* floating
base instead: it integrates /cmd_vel in the body frame and hard-sets the robot's
base pose every tick via the Gazebo `set_pose` service. Because position AND
orientation are prescribed, the robot stays perfectly upright at a fixed height
and glides/turns around the world without ever toppling.

The leg joints hold their standing pose through the per-joint JointPositionController
plugins (see <initial_position> in h1.urdf); this node only drives the base.

Subscribed:
    /cmd_vel (geometry_msgs/Twist): body-frame velocity (linear.x fwd, linear.y
                                    left, angular.z yaw)

Service used (bridged from Ignition via ros_gz_bridge):
    /world/<world>/set_pose (ros_gz_interfaces/srv/SetEntityPose)
"""

import math
import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from geometry_msgs.msg import Twist
from ros_gz_interfaces.srv import SetEntityPose


class KinematicBaseDriver(Node):
    def __init__(self):
        super().__init__('kinematic_base_driver')

        self.declare_parameter('world', 'h1_world')
        self.declare_parameter('model', 'h1')
        self.declare_parameter('stand_height', 0.98)   # pelvis height held (m)
        self.declare_parameter('update_rate', 50.0)    # Hz
        self.declare_parameter('max_vx', 1.0)
        self.declare_parameter('max_vy', 0.5)
        self.declare_parameter('max_wz', 1.5)

        self.world = self.get_parameter('world').value
        self.model = self.get_parameter('model').value
        self.z = self.get_parameter('stand_height').value
        rate = self.get_parameter('update_rate').value
        self.max_vx = self.get_parameter('max_vx').value
        self.max_vy = self.get_parameter('max_vy').value
        self.max_wz = self.get_parameter('max_wz').value

        # Integrated base pose (world frame)
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        # Latest commanded body-frame velocity
        self.vx = 0.0
        self.vy = 0.0
        self.wz = 0.0

        self.dt = 1.0 / rate
        self._pending = None  # in-flight service future (avoid pile-up)

        self.create_subscription(Twist, '/cmd_vel', self.cmd_vel_cb, 10)

        srv_name = f'/world/{self.world}/set_pose'
        self.cli = self.create_client(SetEntityPose, srv_name)
        self.get_logger().info(f'Waiting for {srv_name} (ros_gz service bridge) ...')
        if not self.cli.wait_for_service(timeout_sec=30.0):
            self.get_logger().error(
                f'{srv_name} not available. Is the SetEntityPose bridge running?')
        else:
            self.get_logger().info('set_pose service ready - kinematic base active')

        self.create_timer(self.dt, self.update)

    def cmd_vel_cb(self, msg: Twist):
        self.vx = max(-self.max_vx, min(self.max_vx, msg.linear.x))
        self.vy = max(-self.max_vy, min(self.max_vy, msg.linear.y))
        self.wz = max(-self.max_wz, min(self.max_wz, msg.angular.z))

    def update(self):
        # Integrate body-frame velocity into a world-frame pose
        self.yaw += self.wz * self.dt
        self.x += (self.vx * math.cos(self.yaw) - self.vy * math.sin(self.yaw)) * self.dt
        self.y += (self.vx * math.sin(self.yaw) + self.vy * math.cos(self.yaw)) * self.dt

        if not self.cli.service_is_ready():
            return
        # Skip if a previous request is still in flight (keeps us real-time)
        if self._pending is not None and not self._pending.done():
            return

        req = SetEntityPose.Request()
        req.entity.name = self.model
        req.pose.position.x = self.x
        req.pose.position.y = self.y
        req.pose.position.z = self.z
        # Upright: roll = pitch = 0, yaw only
        req.pose.orientation.z = math.sin(self.yaw / 2.0)
        req.pose.orientation.w = math.cos(self.yaw / 2.0)
        self._pending = self.cli.call_async(req)


def main(args=None):
    rclpy.init(args=args)
    node = KinematicBaseDriver()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
