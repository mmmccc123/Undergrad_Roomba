import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from rclpy.qos import QoSProfile, ReliabilityPolicy
import sys
import termios
import tty

class TeleopRoomba(Node):
    def __init__(self):
        super().__init__('teleop_roomba')
        # This matches the working 'pub' command exactly
        qos = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT, depth=10)
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', qos)
        print("--- Node Started. Use W-A-S-D to drive. Press 'q' to quit. ---")

    def send_cmd(self, x, z):
        msg = Twist()
        msg.linear.x = float(x)
        msg.angular.z = float(z)
        self.publisher_.publish(msg)

def get_key(settings):
    tty.setraw(sys.stdin.fileno())
    key = sys.stdin.read(1)
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

def main():
    settings = termios.tcgetattr(sys.stdin)
    rclpy.init()
    node = TeleopRoomba()

    try:
        while True:
            key = get_key(settings)
            if key == 'w':
                node.send_cmd(0.2, 0.0)
                print("Moving Forward")
            elif key == 's':
                node.send_cmd(-0.2, 0.0)
                print("Moving Backward")
            elif key == 'a':
                node.send_cmd(0.0, 0.5)
                print("Turning Left")
            elif key == 'd':
                node.send_cmd(0.0, -0.5)
                print("Turning Right")
            elif key == ' ':
                node.send_cmd(0.0, 0.0)
                print("STOP")
            elif key == 'q':
                break
    except Exception as e:
        print(f"Error: {e}")
    finally:
        node.send_cmd(0.0, 0.0)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()