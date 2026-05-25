#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

class XboxRoomba(Node):
    def __init__(self):
        super().__init__('xbox_roomba')
        
        # This is the EXACT QoS that made your echo work
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            durability=DurabilityPolicy.VOLATILE
        )

        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', qos_profile)
        self.joy_sub = self.create_subscription(Joy, 'joy', self.joy_callback, 10)
        
        # CRITICAL: Send a command every 0.05s (20Hz) to keep the robot awake
        self.timer = self.create_timer(0.05, self.timer_publish)
        
        self.current_twist = Twist()
        self.get_logger().info('Communication Link Established. Ready to Drive!')

    def joy_callback(self, msg):
        # Scale: Use A-button (buttons[0]) or Right Bumper (buttons[5]) for Turbo
        # Standard Xbox: Axes 1 = Left Stick Up/Down, Axes 3 = Right Stick Left/Right
        turbo = 1.0 if msg.buttons[0] == 1 else 0.4
        
        self.current_twist.linear.x = msg.axes[1] * 0.3 * turbo
        self.current_twist.angular.z = msg.axes[3] * 1.5 * turbo

    def timer_publish(self):
        # Robot needs a continuous stream of data
        self.cmd_pub.publish(self.current_twist)

def main():
    rclpy.init()
    node = XboxRoomba()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        # Send one last stop command
        stop = Twist()
        node.cmd_pub.publish(stop)
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()