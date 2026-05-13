#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression, PathJoinSubstitution
from launch.conditions import IfCondition
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
# Add at the top with other imports
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction
from launch_ros.actions import Node, SetRemap


import os
import subprocess

from launch_ros.substitutions import FindPackageShare

def generate_launch_description():

    # Declare arguments
    is_sim_arg = DeclareLaunchArgument(
        'is_sim',
        default_value='false',
        choices=['true', 'false'],
        description='Whether to run in simulation'
    )
    localization_arg = DeclareLaunchArgument(
        'localization',
        default_value='false',
        description='true = load existing map and localise only'
    )
    rviz_arg = DeclareLaunchArgument(
        'rviz',
        default_value='true',
        description='Launch RViz2 for live visualisation'
    )

    # Configuration
    is_sim = LaunchConfiguration('is_sim')
    use_sim_time = LaunchConfiguration('is_sim') # Simulation time matches is_sim
    localization = LaunchConfiguration('localization')
    use_rviz     = LaunchConfiguration('rviz')

    # 1. Unitree LiDAR - only if not simulation
    unitree_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('unitree_lidar_ros2'),
                'launch.py'
            )
        ),
        launch_arguments={
            'cloud_frame': 'unilidar_l2_link'
        }.items(),
        condition=IfCondition(PythonExpression(["'", is_sim, "' == 'false'"]))
    )

    # 2. ZED Camera - only if not simulation
    zed_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('zed_wrapper'),
                'launch',
                'zed_camera.launch.py'
            )
        ),
        launch_arguments={
            'camera_model': 'zed2',
            'publish_tf':   'false',
            'publish_map_tf': 'false',
            'publish_urdf': 'false',

            # --- USE THESE STRINGS TO LIGHTEN THE LOAD ---
            'grab_resolution': 'VGA',        # Lowest resolution (672x376)
            'grab_frame_rate': '15',         # Lowest frame rate
            'depth_mode': 'PERFORMANCE',     # Changes math from heavy to light
            'ros_params_override_path': '',  # Ensure no other config is overriding this
            # ----------------------------------
        }.items(),
        condition=IfCondition(PythonExpression(["'", is_sim, "' == 'false'"]))
    )

    # 3. Robot Description - uses local package now
    pkg_first_roomba = get_package_share_directory('first_roomba_pkg')
    custom_robot_description = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_first_roomba, 'launch', 'robot_description.launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'is_sim': is_sim
        }.items()
    )

    # 4. Hardware Nodes - only if not simulation
    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        output='screen',
        condition=IfCondition(PythonExpression(["'", is_sim, "' == 'false'"]))
    )
    xbox_node = Node(
        package='first_roomba_pkg',
        executable='xbox_controller_node',
        name='xbox_controller_node',
        output='screen',
        condition=IfCondition(PythonExpression(["'", is_sim, "' == 'false'"]))
    )
    driver_node = Node(
        package='first_roomba_pkg',
        executable='driver_node',
        name='driver_node',
        output='screen',
        condition=IfCondition(PythonExpression(["'", is_sim, "' == 'false'"]))
    )
    lidar_node = Node(
        package='first_roomba_pkg',
        executable='lidar_node',
        name='lidar_node',
        output='screen',
        condition=IfCondition(PythonExpression(["'", is_sim, "' == 'false'"]))
    )

    # 5. RTAB-Map remappings (adjusted for sim/real)
    # If sim, we might need simpler paths if the bridge doesn't match zed_wrapper exactly
    rgb_topic = PythonExpression(["'/zed/image_raw' if '", is_sim, "' == 'true' else '/zed/zed_node/left/image_rect_color'"])
    # Note: Depth/Info usually need matching remappings in the bridge to work flawlessly in sim
    
    # rtabmap_node = Node(
    #     package='rtabmap_launch',
    #     executable='rtabmap.launch.py',
    #     name='rtabmap',
    #     output='screen',
    #     parameters=[{
    #         'use_sim_time': use_sim_time,
    #         'Mem/IncrementalMemory': PythonExpression( ['"false" if "', localization, '" == "true" else "true"'] ),
    #         'Mem/InitWMWithAllNodes':  localization,
    #         'subscribe_depth':         'true',
    #         'subscribe_scan_cloud':    'true',
    #         'subscribe_scan':          'false',
    #         'frame_id':                'base_link',
    #         'odom_frame_id':           'odom',
    #         'approx_sync':             'true',  # CRITICAL for syncing ZED + LiDAR
    #         'Rtabmap/DetectionRate':   '1.0',
    #         'database_path':           '/media/wolfwagen1/c9c2a9fe-c435-4115-9237-57bc783cf964/rtabmap.db',

    #         # Performance Tweaks for your setup
    #         'RGBD/ProximityBySpace': 'true',
    #         'RGBD/AngularUpdate':    '0.01',
    #         'RGBD/LinearUpdate':     '0.01',
    #         'Grid/FromDepth':        'false', # Set to false to use LiDAR for the 2D Map instead of ZED
    #         'Grid/RayTracing':       'true',
    #         'Kp/MaxFeatures':        '500',

    #     }],
    #     remappings=[
    #         ('rgb/image',       rgb_topic),
    #         ('rgb/camera_info', '/zed/zed_node/left/camera_info'),
    #         ('depth/image',     '/zed/zed_node/depth/depth_registered'),
    #         ('odom',            '/zed/zed_node/odom'),
    #         ('scan_cloud',      '/unilidar/cloud'),
    #     ],
    #     arguments=['-d'] # This deletes the database on every start (optional)
    # )




# 1. Setup Configurations
    use_sim_time = LaunchConfiguration('use_sim_time')
    localization = LaunchConfiguration('localization')

    # 2. Define the exact arguments from your Node setup
    # These are passed to the included rtabmap.launch.py
    rtabmap_args = {
        'use_sim_time': use_sim_time,
        'localization': localization,
        'frame_id': 'base_link',
        'odom_frame_id': 'odom',
        'subscribe_depth': 'true',
        'subscribe_scan_cloud': 'true',
        'subscribe_scan': 'false',
        'approx_sync': 'true',
        'wait_for_transform': '0.2',
        'database_path': '/media/wolfwagen1/c9c2a9fe-c435-4115-9237-57bc783cf964/rtabmap.db',
        
        # Topic Remappings (ZED and UniLiDAR)
        'rgb_topic': '/zed/zed_node/rgb/image_rect_color',
        'depth_topic': '/zed/zed_node/depth/depth_registered',
        'camera_info_topic': '/zed/zed_node/left/camera_info',
        'odom_topic': '/zed/zed_node/odom',
        'scan_cloud_topic': '/unilidar/cloud',
        
        # Performance/Library Parameters
        # Note: We pass these as a single string to 'rtabmap_args' 
        # because the official launch file injects them into the node
        'rtabmap_args': [
            '--delete_db_on_start ', # This is your '-d' argument
            '--RGBD/ProximityBySpace true ',
            '--RGBD/AngularUpdate 0.01 ',
            '--RGBD/LinearUpdate 0.01 ',
            '--Grid/FromDepth false ',
            '--Grid/RayTracing true ',
            '--Kp/MaxFeatures 500 ',
            '--Rtabmap/DetectionRate 1.0'
        ]
    }

    # 3. Include the official rtabmap_launch file
    included_rtabmap = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('rtabmap_launch'),
                'launch',
                'rtabmap.launch.py'
            ])
        ]),
        launch_arguments=rtabmap_args.items()
    )






    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', os.path.join(
            get_package_share_directory('first_roomba_pkg'),
            'rviz',
            'rtabmap_rviz.rviz'   # ← replace with your actual .rviz filename
        )],
        condition=IfCondition(use_rviz),
    )

    lidar_root_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='lidar_root_to_base',
        arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'unilidar_imu_initial'],
        condition=IfCondition(PythonExpression(["'", is_sim, "' == 'false'"]))
    )


    # # Camera → base_link transform
    # camera_tf = Node(
    #     package='tf2_ros',
    #     executable='static_transform_publisher',
    #     name='camera_to_base_link',
    #     arguments=['0.1', '0', '0.3', '0', '0', '0', 'base_link', 'zed_left_camera_frame'],
    # )


# # --- Create a group that forces all TF traffic into the namespace ---
#     namespaced_tf_group = GroupAction([
#         # Force these nodes to use the namespaced TF tree
#         SetRemap(src='/tf', dst='/minchan/tf'),
#         SetRemap(src='/tf_static', dst='/minchan/tf_static'),

#         custom_robot_description, # <--- YOUR XACRO IS NOW LIVE HERE
#         zed_launch,
#         unitree_launch,
#        # rtabmap_node,
#         rviz_node,
#         lidar_root_tf,
#         lidar_node,
#     ])



    return LaunchDescription([
        is_sim_arg,           # <-- Added this
        localization_arg,
        rviz_arg,
        joy_node,
        xbox_node,
        # driver_node,
        # namespaced_tf_group
        custom_robot_description, # <--- YOUR XACRO IS NOW LIVE HERE
        zed_launch,
        unitree_launch,
        rviz_node,
        lidar_root_tf,
        # lidar_node,
        # rtabmap_node,
        # included_rtabmap
    ])