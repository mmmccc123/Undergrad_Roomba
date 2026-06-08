#!/usr/bin/env python3

import requests
import base64
import re
import time
import os
import json




# # ====================================================================
# def move_robot(direction: str):
#     cmd_vel_pub.publish(twist)
#     return f"Robot moving {direction}"

# def stop_robot():
#     return "Robot stopped"

# def go_straight(distance):
#     return f"Current Action is go straight cm "
# # ====================================================================









# ====================================================================

# Create the JSON schema for the LLM
def make_payload(prompt : str = "hi" , image_url = None,  reasoning = None , calling_tools = None):
    tools = [
        {
            "type": "function",
            "function": {
                "name": "move_robot",
                "description": " make vehicle go straight, turn left, turn right ",
                "parameters": { "type": "object", "properties": { "direction": {"type": "string", "description":"the direction vihecle have to move. option is straight, right , left"} }, }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "stop_robot",
                "description": " making vehicle stop "
            }
        },
        {
            "type": "function",
            "function": {
                "name": "next_task",
                "description": "make to do next instruction"
            }
        }
    ]



# =============processing option==============
    if reasoning == True:
        reasoning_prompt  = ("Answer the question using the following format:\n\n"
                        "<think>\n"
                        "Your reasoning.\n"
                        "</think>\n\n"
                        "Write your final answer immediately after the </think> tag."
                        )
    else:
        reasoning_prompt = ""


    mesage_system =    {  "role": 'system',    "content": 'you are controlling the vehicle with egocentric view' }
    mesage_user =      {  "role": "user"  ,    "content": [   { "type": "text", "text": ( f"{prompt + reasoning_prompt }" ) } ]}   


    if image_url != None:

        if os.path.exists(image_url) : # ig give real path
            with open(image_url,"rb") as i:
                base64_img =  base64.b64encode(i.read()).decode('utf-8')

        elif image_url.startswith("data:image/"):
            base64_img =  image_url

        else:
            base64_img =  f"data:video/mp4;base64,{image_url}"



        mesage_user["content"].append( { "type": "image_url", "image_url":  {"url": base64_img} } )
    else:
        print("Error: No given image url or image")

# =============processing option==============



    if calling_tools:
        payload = {
            "model": "nvidia/Cosmos-Reason2-2B", 
            "messages": [ mesage_system , mesage_user ],
            "tools" : tools,
            "tool_choice" : "required"
        }
        return payload
    else: 
        payload = {
            "model": "nvidia/Cosmos-Reason2-2B", 
            "messages": [ mesage_system , mesage_user ],
        }
        return payload

# ====================================================================








                # VLM LOOPs

# ====================================================================

# def vlm_inference_loop(payload):
#     global TIME_OUT

#     try:
#         response = requests.post( "http://localhost:8000/v1/chat/completions", json=payload, timeout=5         )

#         if response.status_code == 200:
#             a = response.json()['choices']
#             token = response.json()["usage"]
#             # result_text = message.get('content') or message.get('reasoning_content') or ""
#             # print(f"Cosmos Output: {result_text}")
#             return a , token
#         else:
#             return (f"vLLM Error {response.status_code}: {response.text}")

#     except Exception as e:
#         return (f"VLM loop failed: {str(e)}")


def main():
    payload = make_payload()
    for i in range(5):
        a , token = vlm_inference_loop(payload)
        print(a)
        print(token)
        


if __name__ == '__main__':
    main()
# ====================================================================
