from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='teleop_twist_keyboard',
            executable='teleop_twist_keyboard',
            name='test_teleop',
            namespace='minchan',
            remappings=[('/cmd_vel', '/minchan/cmd_vel')],
            output='screen',
            prefix='xterm -e' # This opens it in a new window if you have a GUI
        )
    ])