#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist

MAX_LINEAR  = 0.22   # m/s  (Burger max)
MAX_ANGULAR = 2.84   # rad/s (Burger max)

class XboxTurtleBot(Node):
    def __init__(self):
        super().__init__('xbox_turtlebot')

        self.cmd_pub = self.create_publisher(Twist, 'minchan/cmd_vel', 10)
        self.joy_sub = self.create_subscription(Joy, 'joy', self.joy_callback, 10)

        self.get_logger().info('Xbox TurtleBot node started')

    def joy_callback(self, msg):
        a_button = msg.buttons[7] == 1  # turbo
        speed_scale = 1.0 if a_button else 0.3

        # Left stick Y = forward/back, Right stick X = turn
        linear_x  = msg.axes[1] * MAX_LINEAR  * speed_scale
        angular_z = msg.axes[3] * MAX_ANGULAR * speed_scale

        twist = Twist()
        twist.linear.x  = linear_x
        twist.angular.z = angular_z

        self.cmd_pub.publish(twist)


def main():
    rclpy.init()
    node = XboxTurtleBot()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Send stop on exit
        stop = Twist()
        node.cmd_pub.publish(stop)
        rclpy.shutdown()

if __name__ == '__main__':
    main()