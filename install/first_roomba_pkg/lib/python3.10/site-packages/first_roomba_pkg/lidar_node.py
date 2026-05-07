#!/usr/bin/env python3

import rclpy
import threading
import math
import numpy as np
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from std_msgs.msg import Bool
import sensor_msgs_py.point_cloud2 as pc2

# ── Obstacle detection thresholds ────────────────────────────────────────────
DIST_THRESH  = 1.5          # m — anything closer triggers alert
FOV_HALF     = math.pi / 12 # ±15° forward cone
HEIGHT_MIN   = -0.5         # m — ignore points below this (ground noise)
HEIGHT_MAX   =  2.0         # m — ignore points above this (ceiling/sky)

cloud_data: PointCloud2 = None


class LidarNode(Node):
    def __init__(self):
        super().__init__("lidar_node")

        # ── Subscriber ────────────────────────────────────────────────────────
        self.create_subscription(
            PointCloud2,
            '/unilidar/cloud',       # ← changed from /scan
            self.cloud_callback,
            10
        )

        # ── Publisher ─────────────────────────────────────────────────────────
        self.pub_obstacle = self.create_publisher(Bool, 'lidar_od_signal', 1)

        self.get_logger().info("LiDAR node started — listening on /unilidar/cloud")

    def cloud_callback(self, data: PointCloud2):
        global cloud_data
        cloud_data = data


def main(args=None):
    rclpy.init(args=args)
    node = LidarNode()

    thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    thread.start()

    FREQ = 5
    rate = node.create_rate(FREQ, node.get_clock())
    msg  = Bool()

    # ── Wait for first cloud ──────────────────────────────────────────────────
    while rclpy.ok():
        if cloud_data is None:
            node.get_logger().info("Waiting for LiDAR data…")
            rate.sleep()
        else:
            break
    node.get_logger().info("LiDAR data received — starting obstacle detection")

    # ── Main loop ─────────────────────────────────────────────────────────────
    while rclpy.ok():
        min_dist = float('inf')

        # Read XYZ points from the PointCloud2 message
        # pc2.read_points returns an iterator of (x, y, z) tuples
        for point in pc2.read_points(cloud_data, field_names=('x', 'y', 'z'), skip_nans=True):
            x, y, z = point

            # ── Height filter — ignore ground and sky ─────────────────────────
            if z < HEIGHT_MIN or z > HEIGHT_MAX:
                continue

            # ── Forward cone filter ±15° in XY plane ─────────────────────────
            # theta = 0 means directly ahead (+X direction)
            theta = math.atan2(y, x)
            if not (-FOV_HALF < theta < FOV_HALF):
                continue

            # ── Distance in XY plane (horizontal distance) ────────────────────
            distance = math.sqrt(x**2 + y**2)

            if distance < min_dist:
                min_dist = distance

        # ── Publish obstacle signal ───────────────────────────────────────────
        if min_dist == float('inf'):
            # No valid points found in cone
            msg.data = False
        else:
            msg.data = min_dist < DIST_THRESH

        node.pub_obstacle.publish(msg)
        node.get_logger().info( f"Closest object: {min_dist:.2f} m  |  Obstacle: {msg.data}" )

        rate.sleep()

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()