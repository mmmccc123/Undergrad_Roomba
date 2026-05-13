#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import cv2 as cv
import threading
import time



class CameraNode(Node):
    def __init__(self):
        super().__init__("camera_node")

        self.br = CvBridge()
        self.frame = None
        self.last_save_time = time.time()

        # ── Subscribers ──────────────────────────────────────────────────────
        self.create_subscription(
            Image,
            '/zed/zed_node/left/image_rect_color',
            self.image_callback,
            5
        )

		
        # ── Publishers (relay topics for RTABMap) ────────────────────────────
        # RTABMap expects these remapped topic names
        self.image_pub = self.create_publisher(Image, '/rtabmap/rgb/image', 5)

        self.get_logger().info("Camera node started — publishing to /rtabmap/rgb/image")

    def image_callback(self, msg: Image):
        """
        Receives ZED image, optionally saves to disk,
        and re-publishes so RTABMap can consume it.
        """
        self.frame = self.br.imgmsg_to_cv2(msg)

        # ── Save a frame every second (data collection) ───────────────────────
        now = time.time()
        if now - self.last_save_time > 1.0:
            save_path = (
                '/media/wolfwagen1/c9c2a9fe-c435-4115-9237-57bc783cf964'
                '/outdoor_test_images/frame_'
                + str(int(now * 1000)) + '.png'
            )
            cv.imwrite(save_path, self.frame)
            self.last_save_time = now
            self.get_logger().info(f"Saved frame → {save_path}")

        # ── Forward to RTABMap ────────────────────────────────────────────────
        self.image_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = CameraNode()

    thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    thread.start()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()