#!/usr/bin/env python3
"""
Kinematic Floating-Base Driver + walking gait animation for the Unitree H1.

The H1 SDK has no balance/locomotion controller, so a physically free humanoid
falls over the instant physics starts. This node provides a *kinematic* floating
base instead: it integrates /cmd_vel in the body frame and hard-sets the robot's
base pose every tick via the Gazebo `set_pose` service. Because position AND
orientation are prescribed, the robot stays perfectly upright at a fixed height
and glides/turns around the world without ever toppling.

On top of that it animates a simple walking gait: when commanded to move it sends
sinusoidal targets to the per-joint JointPositionController plugins so the legs
swing and the arms counter-swing, matching cadence to speed. This is a visual
animation (the feet still slide), not real dynamic walking.

Subscribed:
    /cmd_vel (geometry_msgs/Twist): body-frame velocity (x fwd, y left, wz yaw)

Publishes (bridged to the gz JointPositionController plugins via ros_gz_bridge):
    /model/<model>/joint/<joint>/cmd_pos (std_msgs/Float64)

Service used (bridged via ros_gz_bridge):
    /world/<world>/set_pose (ros_gz_interfaces/srv/SetEntityPose)
"""

import math
import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64
from ros_gz_interfaces.srv import SetEntityPose


# Standing pose (radians) - the neutral stance the legs hold and swing around.
STAND_POSE = {
    'left_hip_yaw_joint': 0.0, 'left_hip_roll_joint': 0.0, 'left_hip_pitch_joint': -0.4,
    'left_knee_joint': 0.8, 'left_ankle_joint': -0.4,
    'right_hip_yaw_joint': 0.0, 'right_hip_roll_joint': 0.0, 'right_hip_pitch_joint': -0.4,
    'right_knee_joint': 0.8, 'right_ankle_joint': -0.4,
    'torso_joint': 0.0,
    'left_shoulder_pitch_joint': 0.3, 'left_shoulder_roll_joint': 0.3,
    'left_shoulder_yaw_joint': 0.0, 'left_elbow_joint': 0.5,
    'right_shoulder_pitch_joint': 0.3, 'right_shoulder_roll_joint': -0.3,
    'right_shoulder_yaw_joint': 0.0, 'right_elbow_joint': 0.5,
}


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
        self.declare_parameter('animate_gait', True)   # leg/arm walking animation

        self.world = self.get_parameter('world').value
        self.model = self.get_parameter('model').value
        self.z = self.get_parameter('stand_height').value
        rate = self.get_parameter('update_rate').value
        self.max_vx = self.get_parameter('max_vx').value
        self.max_vy = self.get_parameter('max_vy').value
        self.max_wz = self.get_parameter('max_wz').value
        self.animate = self.get_parameter('animate_gait').value

        # Integrated base pose (world frame)
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        # Latest commanded body-frame velocity
        self.vx = 0.0
        self.vy = 0.0
        self.wz = 0.0
        # Gait state
        self.walk_phase = 0.0
        self.gait_env = 0.0   # 0..1 envelope, ramps gait in/out smoothly

        self.dt = 1.0 / rate
        self._pending = None  # in-flight service future (avoid pile-up)

        self.create_subscription(Twist, '/cmd_vel', self.cmd_vel_cb, 10)

        # Joint command publishers (bridged to the gz position controllers)
        self.joint_pubs = {}
        if self.animate:
            for j in STAND_POSE:
                topic = f'/model/{self.model}/joint/{j}/cmd_pos'
                self.joint_pubs[j] = self.create_publisher(Float64, topic, 10)

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
        # --- Base motion: integrate body-frame velocity into a world pose ---
        self.yaw += self.wz * self.dt
        self.x += (self.vx * math.cos(self.yaw) - self.vy * math.sin(self.yaw)) * self.dt
        self.y += (self.vx * math.sin(self.yaw) + self.vy * math.cos(self.yaw)) * self.dt

        if self.animate:
            self.update_gait()

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

    def update_gait(self):
        """Generate and publish a speed-scaled walking animation."""
        speed = math.hypot(self.vx, self.vy)
        motion = max(speed, abs(self.wz) * 0.3)   # turning also steps in place
        moving = motion > 0.02

        # Smoothly ramp the gait envelope in/out so start/stop isn't jarring
        target = 1.0 if moving else 0.0
        self.gait_env += max(-0.04, min(0.04, target - self.gait_env))

        # Advance the step phase; cadence rises with speed (~0.8 .. 2.2 Hz)
        if self.gait_env > 1e-3:
            freq = min(2.2, 0.8 + motion * 1.4)
            self.walk_phase = (self.walk_phase + 2.0 * math.pi * freq * self.dt) % (2.0 * math.pi)

        pos = dict(STAND_POSE)
        env = self.gait_env
        if env > 1e-3:
            amp = (0.25 + 0.30 * min(motion, 1.0)) * env   # swing amplitude
            ph = self.walk_phase
            off = math.pi                                  # legs 180deg out of phase

            for side, p in (('left', ph), ('right', ph + off)):
                s = math.sin(p)
                pos[f'{side}_hip_pitch_joint'] = STAND_POSE[f'{side}_hip_pitch_joint'] + amp * s
                # knee only flexes (lift foot) during the swing half-cycle
                pos[f'{side}_knee_joint'] = STAND_POSE[f'{side}_knee_joint'] + \
                    max(0.0, 1.3 * amp * math.sin(p - 0.4))
                pos[f'{side}_ankle_joint'] = STAND_POSE[f'{side}_ankle_joint'] - 0.4 * amp * s
                # arms counter-swing relative to the opposite leg
                pos[f'{side}_shoulder_pitch_joint'] = \
                    STAND_POSE[f'{side}_shoulder_pitch_joint'] - 0.6 * amp * s

        for j, pub in self.joint_pubs.items():
            msg = Float64()
            msg.data = float(pos[j])
            pub.publish(msg)


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
