#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
from cv_bridge import CvBridge
import cv2 as cv
import requests
import base64
import re

import threading
import time


def parse_and_publish_velocity( text: str):
        twist = Twist()
        text_lower = text.lower()

        # Simple regex extraction or sub-string matching from the generated answer
        if "go straight" in text_lower:
            twist.linear.x = 0.2   # Forward speed (m/s)
            twist.angular.z = 0.0
        elif "turn left" in text_lower:
            twist.linear.x = 0.1   # Slow down slightly while turning
            twist.angular.z = 0.4  # Left turn rotation speed (rad/s)
        elif "turn right" in text_lower:
            twist.linear.x = 0.1
            twist.angular.z = -0.4 # Right turn rotation speed (rad/s)
        elif "stop" in text_lower:
            twist.linear.x = 0.0
            twist.angular.z = 0.0
        else:
            # Safe Fallback: If the model gives weird output, stop vehicle movement immediately
            twist.linear.x = 0.0
            twist.angular.z = 0.0

        cmd_vel_pub.publish(twist)



def vlm_inference_loop():

        # blocker
        if latest_frame is None:   
            return

        # 1. Copy the current frame quickly so it doesn't get overwritten mid-process
        frame_to_process = latest_frame.copy()

        try:
            # 2. Encode OpenCV image directly to Base64 string in memory
            _, buffer = cv.imencode('.jpg', frame_to_process)
            base64_image = base64.b64encode(buffer).decode('utf-8')

            # 3. use tuple
            payload = {
                "model": "/models/cosmos-reason2",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type":     "image_url",
                                "image_url":  {"url": f"data:image/jpeg;base64,{base64_image}"}
                            },
                            {
                                "type":     "text",
                                "text":     "You are controlling a robot navigating a track. Your mission is to find a BLUE BLOCK.\n"
                                            # "Analyze the image carefully. Look for a blue-colored cube or block object.\n"
                                            # "Output your final driving decision inside an <answer> tag.\n"
                                            "Choices: [go straight, turn left, turn right, stop]\n"
                                            # "Example: <answer>go straight</answer>\n"
                                            # "Only output the answer tag. No explanation."
                                            "Again, Output should be one of three [go straight, turn left, turn right, stop]\n"
                            }
                        ]
                    }
                ],
                "max_tokens": 150
            }

            # !!!!!!!!!!!!!!!SEND THE DATA TO VLM SERVER!!!!!!!!!!!!!!!!!!!!
            response = requests.post("http://localhost:8000/v1/chat/completions", json=payload, timeout=5.0)
            
            # if the response is normal
            if response.status_code == 200:
                result_text = response.json()['choices'][0]['message']['content']
                # full_text = response.json()
                node_logger.info(f"Cosmos Output: {result_text}")
                # node_logger.info(f"Full text: {full_text}")
                parse_and_publish_velocity(result_text)                # RIGHT HERE!!! it publish Twist to /cmd_vel
            
            #else it get wrong
            else:
                node_logger.error(f"vLLM Server Error: {response.status_code}")

        except Exception as e:
            node_logger.error(f"Failed VLM Inference Loop: {str(e)}")





def image_callback( msg: Image):
    # Convert ROS Image to OpenCV matrix instantly
    global latest_frame 
    latest_frame = br.imgmsg_to_cv2(msg, desired_encoding='bgr8')



br = CvBridge()
latest_frame = None
cmd_vel_pub = None      # will be set in main()
node_logger = None      # will be set in main()
start_time = time.time()



def main(args=None):
    # global cmd_vel_pub, node_logger      
    rclpy.init(args=args)
    node = Node("VLM_process_node")
    node.create_subscription( Image,  '/zed/zed_node/rgb/color/rect/image', image_callback,  1 )        # it doesnt do anything. doest store image to disk, or nothing, just store in memory that vlm can process
    cmd_vel_pub = node.create_publisher(Twist, '/cmd_vel', 10)              # ✅ save publisher reference
    node_logger = node.get_logger()                                         # ✅ save logger reference
    node.create_timer(5, vlm_inference_loop )                              # not publish when it get data. just every 0.5 second



    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()