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
import time
import tempfile
import os




frame_buffer = []          # raw OpenCV frames
BUFFER_SIZE = 8           # how many frames to accumulate

def image_callback(msg: Image):
    global latest_frame
    latest_frame = br.imgmsg_to_cv2(msg, desired_encoding='bgr8')
    
    # Keep a rolling buffer of raw frames for video assembly
    frame_buffer.append(latest_frame.copy())
    if len(frame_buffer) > BUFFER_SIZE:
        frame_buffer.pop(0)




def frames_to_base64_video(frames, fps=5):
    """Write frames to a temp MP4 and return base64 string."""
    if not frames:
        return None

    h, w = frames[0].shape[:2]
    
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
        tmp_path = f.name

    try:
        writer = cv.VideoWriter( tmp_path, cv.VideoWriter_fourcc(*'mp4v'), fps, (w, h)  )
        for frame in frames:
            writer.write(frame)
        writer.release()

        with open(tmp_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    finally:
        os.unlink(tmp_path)   # clean up temp file




def parse_and_publish_velocity(text: str):
    twist = Twist()

    # 1. Try to extract text after </think> tag (Cosmos-Reason2 format)
    think_match = re.search(r'</think>\s*(.*)', text, re.IGNORECASE | re.DOTALL)
    if think_match:
        decision = think_match.group(1).strip().lower()
    else:
        # 2. Fallback: try <answer> tag (old format)
        answer_match = re.search(r'<answer>(.*?)</answer>', text, re.IGNORECASE)
        decision = answer_match.group(1).strip().lower() if answer_match else text.strip().lower()

    node_logger.info(f"Parsed decision: [{decision}]")

    if "go straight" in decision:
        twist.linear.x = 0.2
        twist.angular.z = 0.0
    elif "turn left" in decision:
        twist.linear.x = 0.1
        twist.angular.z = 0.4
    elif "turn right" in decision:
        twist.linear.x = 0.1
        twist.angular.z = -0.4
    elif "stop" in decision:
        twist.linear.x = 0.0
        twist.angular.z = 0.0
    else:
        node_logger.warn(f"No valid decision parsed from: [{decision}]")
        twist.linear.x = 0.0
        twist.angular.z = 0.0

    cmd_vel_pub.publish(twist)


TIME_OUT = 2

def vlm_inference_loop():
    global TIME_OUT
    if latest_frame is None :
        node_logger.info("returning1")
        return
    if len(frame_buffer) < 2:
        node_logger.info("returning2")
        return
    try:
        frames_to_send = frame_buffer.copy()
        b64_video = frames_to_base64_video(frames_to_send, fps=5)
        
        if b64_video is None:
            node_logger.info(f"there's nothing in the video")
            return
        payload = {
            "model": "nvidia/Cosmos-Reason2-2B",
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "video_url",
                        "video_url": {
                            "url": f"data:video/mp4;base64,{b64_video}"
                        }
                    },
                    {
                        "type": "text",
                        "text": (
                            "You are controlling a robot .\n"
                            # "your task is first GO forward and crash to the red brick\n"
                            "your task is GO straight and turn left in front of the blue brick and stop in front of the red brick.\n"
                            "Respond with ONLY one of: go straight, turn left, turn right, stop\n"
                            "No explanation. One phrase only.\n"
                            # "Answer the question using the following format: \n"
                            # "<think>\n"
                            # "Your reasoning.\n"
                            # "</think>\n"
                            # "Write your final answer immediately after the </think> tag."
                        )
                    }
                ]
            }],
            "max_tokens": 512
        }

        response = requests.post(
            "http://localhost:8000/v1/chat/completions",
            json=payload,
            timeout=5
        )

        if response.status_code == 200:
            message = response.json()['choices'][0]['message']
            result_text = message.get('content') or message.get('reasoning_content') or ""
            node_logger.info(f"Cosmos Output: {result_text}")
            parse_and_publish_velocity(result_text)
        else:
            node_logger.error(f"vLLM Error {response.status_code}: {response.text}")

    except Exception as e:
        node_logger.error(f"VLM loop failed: {str(e)}")



br = CvBridge()
latest_frame = None
cmd_vel_pub = None
node_logger = None
start_time = time.time()


def main(args=None):

    global cmd_vel_pub, node_logger, TIME_OUT
    rclpy.init(args=args)
    node = Node("VLM_process_node")
    node.create_subscription(Image, '/zed/zed_node/rgb/color/rect/image', image_callback, 1)
    cmd_vel_pub = node.create_publisher(Twist, '/cmd_vel', 10)
    node_logger = node.get_logger()
    node.create_timer(TIME_OUT, vlm_inference_loop)

    node_logger.info("Start")
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
