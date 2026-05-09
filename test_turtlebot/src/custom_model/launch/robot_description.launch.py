from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

ARGUMENTS = [
    DeclareLaunchArgument('use_sim_time', default_value='true',
                          choices=['true', 'false'],
                          description='use_sim_time'),
    # Keep 'model' arg so original launch chain doesn't break
    DeclareLaunchArgument('model', default_value='lite',
                          choices=['standard', 'lite'],
                          description='Turtlebot4 Model'),
]

def generate_launch_description():
    pkg_custom_model = get_package_share_directory('custom_model')

    robot_description_command = ParameterValue(
            Command([
                'xacro ',
                PathJoinSubstitution([
                    pkg_custom_model, 'urdf', 'minchan_turtlebot4.urdf.xacro'
                ]),
                ' gazebo:=ignition'
            ]),
            value_type=str
        )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'robot_description': robot_description_command,
        }]
    )

    ld = LaunchDescription(ARGUMENTS)
    ld.add_action(robot_state_publisher)
    return ld
    

    