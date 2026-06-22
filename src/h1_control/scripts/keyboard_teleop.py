#!/usr/bin/env python3
"""
Keyboard Teleoperation for Unitree H1 Robot

Control the H1 robot using keyboard inputs.

Controls:
    Movement:
        w/s : Forward/Backward
        a/d : Strafe Left/Right
        q/e : Rotate Left/Right
    
    Speed Control:
        z/x : Decrease/Increase linear speed
        c/v : Decrease/Increase angular speed
    
    Mode Control:
        1 : Idle Mode
        2 : Forced Stand
        3 : Walk Mode
        4 : Trot Running
        5 : Recovery
    
    Other:
        SPACE : Emergency Stop
        ESC   : Quit
"""

import sys
import termios
import tty
import select
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Int32


HELP_MSG = """
╔═══════════════════════════════════════════════════════════╗
║          Unitree H1 Keyboard Teleoperation                ║
╠═══════════════════════════════════════════════════════════╣
║  Movement:           │  Mode Control:                     ║
║    w - Forward       │    1 - Idle                        ║
║    s - Backward      │    2 - Forced Stand                ║
║    a - Strafe Left   │    3 - Walk Mode                   ║
║    d - Strafe Right  │    4 - Trot Running                ║
║    q - Turn Left     │    5 - Recovery                    ║
║    e - Turn Right    │                                    ║
║                      │  Speed Control:                    ║
║  SPACE - Stop        │    z/x - Linear speed -/+          ║
║  ESC   - Quit        │    c/v - Angular speed -/+         ║
╚═══════════════════════════════════════════════════════════╝
"""


class KeyboardTeleop(Node):
    """Keyboard teleoperation node for H1 robot."""

    def __init__(self):
        super().__init__('h1_keyboard_teleop')

        # Parameters
        self.declare_parameter('linear_speed', 0.3)
        self.declare_parameter('angular_speed', 0.5)
        self.declare_parameter('linear_speed_step', 0.1)
        self.declare_parameter('angular_speed_step', 0.1)
        self.declare_parameter('max_linear_speed', 1.0)
        self.declare_parameter('max_angular_speed', 1.5)

        self.linear_speed = self.get_parameter('linear_speed').value
        self.angular_speed = self.get_parameter('angular_speed').value
        self.linear_step = self.get_parameter('linear_speed_step').value
        self.angular_step = self.get_parameter('angular_speed_step').value
        self.max_linear = self.get_parameter('max_linear_speed').value
        self.max_angular = self.get_parameter('max_angular_speed').value

        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.mode_pub = self.create_publisher(Int32, '/h1/mode', 10)
        self.gait_pub = self.create_publisher(Int32, '/h1/gait_type', 10)

        # Current velocity
        self.vx = 0.0
        self.vy = 0.0
        self.wz = 0.0

        # Terminal settings
        self.settings = termios.tcgetattr(sys.stdin)

        self.get_logger().info('Keyboard Teleop started')
        print(HELP_MSG)
        self.print_status()

    def get_key(self, timeout=0.1):
        """Get keyboard input."""
        tty.setraw(sys.stdin.fileno())
        rlist, _, _ = select.select([sys.stdin], [], [], timeout)
        if rlist:
            key = sys.stdin.read(1)
        else:
            key = ''
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return key

    def print_status(self):
        """Print current status."""
        print(f'\rSpeed: linear={self.linear_speed:.2f} angular={self.angular_speed:.2f} | '
              f'Vel: vx={self.vx:.2f} vy={self.vy:.2f} wz={self.wz:.2f}    ', end='')

    def run(self):
        """Main loop."""
        try:
            while rclpy.ok():
                key = self.get_key()

                if key == '\x1b':  # ESC
                    break

                # Movement keys
                if key == 'w':
                    self.vx = self.linear_speed
                    self.vy = 0.0
                elif key == 's':
                    self.vx = -self.linear_speed
                    self.vy = 0.0
                elif key == 'a':
                    self.vy = self.linear_speed
                    self.vx = 0.0
                elif key == 'd':
                    self.vy = -self.linear_speed
                    self.vx = 0.0
                elif key == 'q':
                    self.wz = self.angular_speed
                elif key == 'e':
                    self.wz = -self.angular_speed
                elif key == ' ':
                    self.vx = 0.0
                    self.vy = 0.0
                    self.wz = 0.0

                # Speed control
                elif key == 'z':
                    self.linear_speed = max(0.1, self.linear_speed - self.linear_step)
                elif key == 'x':
                    self.linear_speed = min(self.max_linear, self.linear_speed + self.linear_step)
                elif key == 'c':
                    self.angular_speed = max(0.1, self.angular_speed - self.angular_step)
                elif key == 'v':
                    self.angular_speed = min(self.max_angular, self.angular_speed + self.angular_step)

                # Mode control
                elif key == '1':
                    self.publish_mode(0)  # Idle
                    print('\nMode: IDLE')
                elif key == '2':
                    self.publish_mode(1)  # Forced Stand
                    print('\nMode: FORCED STAND')
                elif key == '3':
                    self.publish_mode(2)  # Walk
                    self.publish_gait(1)  # Trot
                    print('\nMode: WALK (Trot)')
                elif key == '4':
                    self.publish_mode(2)  # Walk
                    self.publish_gait(2)  # Trot Running
                    print('\nMode: WALK (Trot Running)')
                elif key == '5':
                    self.publish_mode(6)  # Recovery
                    print('\nMode: RECOVERY')

                # If no key pressed, gradually reduce velocity
                if key == '':
                    self.vx *= 0.9
                    self.vy *= 0.9
                    self.wz *= 0.9
                    if abs(self.vx) < 0.01:
                        self.vx = 0.0
                    if abs(self.vy) < 0.01:
                        self.vy = 0.0
                    if abs(self.wz) < 0.01:
                        self.wz = 0.0

                # Publish velocity
                self.publish_velocity()
                self.print_status()

        except Exception as e:
            self.get_logger().error(f'Error: {e}')
        finally:
            # Restore terminal settings
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
            # Stop robot
            self.vx = 0.0
            self.vy = 0.0
            self.wz = 0.0
            self.publish_velocity()
            print('\nKeyboard teleop stopped.')

    def publish_velocity(self):
        """Publish velocity command."""
        msg = Twist()
        msg.linear.x = self.vx
        msg.linear.y = self.vy
        msg.angular.z = self.wz
        self.cmd_vel_pub.publish(msg)

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
    node = KeyboardTeleop()

    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
