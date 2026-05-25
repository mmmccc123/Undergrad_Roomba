#!/usr/bin/env python3

from launch_ros.actions import Node
from launch import LaunchDescription
from launch.conditions import IfCondition
from launch_ros.actions import Node, SetRemap
from launch.actions import IncludeLaunchDescription
from launch_ros.substitutions import FindPackageShare
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction
from launch.substitutions import LaunchConfiguration, PythonExpression, PathJoinSubstitution
from ament_index_python.packages import get_package_share_directory
import os
import subprocess


def generate_launch_description():
    # Declare arguments
    is_sim_arg = DeclareLaunchArgument( 'is_sim',               default_value='false', choices=['true', 'false'],   description='Whether to run in simulation' )
    localization_arg = DeclareLaunchArgument( 'localization',   default_value='false',                              description='true = load existing map and localise only' )
    rviz_arg = DeclareLaunchArgument( 'rviz',                   default_value='true',                               description='Launch RViz2 for live visualisation' )

    # Configuration
    is_sim = LaunchConfiguration('is_sim')
    use_sim_time = LaunchConfiguration('is_sim') 
    localization = LaunchConfiguration('localization')
    use_rviz     = LaunchConfiguration('rviz')

    # 2. ZED Camera - only if not simulation
    zed_launch = IncludeLaunchDescription( PythonLaunchDescriptionSource( os.path.join( get_package_share_directory('zed_wrapper'), 'launch', 'zed_camera.launch.py' ) ),
        launch_arguments={
            'camera_model': 'zed2i',
            'publish_tf':   'false',
            'publish_map_tf': 'false',
            'publish_urdf': 'false',
        }.items(),
        condition=IfCondition(PythonExpression(["'", is_sim, "' == 'false'"]))
    )

    # 3. Robot Description - Publising Robot_Descroption TOPIC
    pkg_first_roomba = get_package_share_directory('first_roomba_pkg')
    custom_robot_description = IncludeLaunchDescription( PythonLaunchDescriptionSource( os.path.join(pkg_first_roomba, 'launch', 'robot_description.launch.py') ),
        launch_arguments={ 'use_sim_time': use_sim_time, 'is_sim': is_sim }.items()
    )

    # 4. Hardware Nodes - only if not simulation
    joy_node = Node(                # this is for xbox default node
        package='joy',
        executable='joy_node',
        name='joy_node',
        output='screen',
        condition=IfCondition(PythonExpression(["'", is_sim, "' == 'false'"]))
    )
    xbox_node = Node(              # this is publishing data from /joy to /cmd_vel for turtlebot create 3
        package='first_roomba_pkg',
        executable='xbox_controller_node',
        name='xbox_controller_node',
        output='screen',
        condition=IfCondition(PythonExpression(["'", is_sim, "' == 'false'"]))
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', os.path.join( get_package_share_directory('first_roomba_pkg'), 'rviz', 'rtabmap_rviz.rviz'    )],
        condition=IfCondition(use_rviz),
    )



    return LaunchDescription([
        is_sim_arg,          
        localization_arg,
        rviz_arg,
        joy_node,
        xbox_node,
        unitree_launch,
        custom_robot_description, 
        rviz_node,
        zed_launch,
    ])