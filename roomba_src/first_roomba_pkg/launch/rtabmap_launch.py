#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.conditions import IfCondition
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


import os
import subprocess



def generate_launch_description():

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

    localization = LaunchConfiguration('localization')
    use_rviz     = LaunchConfiguration('rviz')

    # 1. Unitree LiDAR - use official launch file directly
    unitree_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('unitree_lidar_ros2'),
                # 'launch',
                'launch.py'
            )
        )
    )

    # 2. Camera node
    camera_node = Node(
        package='first_roomba_pkg',
        executable='camera_node',
        name='camera_node',
        output='screen',
    )

    # 3. LiDAR obstacle detection node
    lidar_node = Node(
        package='first_roomba_pkg',
        executable='lidar_node',
        name='lidar_node',
        output='screen',
    )

    # 4. Joy driver
    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        output='screen',
    )

    # 5. Xbox controller node
    xbox_node = Node(
        package='first_roomba_pkg',
        executable='xbox_controller_node',
        name='xbox_controller_node',
        output='screen',
    )

    # 6. Driver node
    driver_node = Node(
        package='first_roomba_pkg',
        executable='driver_node',
        name='driver_node',
        output='screen',
    )

    # 7. RTABMap
    rtabmap_node = Node(
        package='rtabmap_slam',
        executable='rtabmap',
        name='rtabmap',
        output='screen',
        parameters=[{
            'Mem/IncrementalMemory': PythonExpression(
                ['"false" if "', localization, '" == "true" else "true"']
            ),
            'Mem/InitWMWithAllNodes':  localization,
            'subscribe_depth':         'true',
            'subscribe_scan_cloud':    'true',
            'subscribe_scan':          'false',
            'frame_id':                'base_link',
            'odom_frame_id':           'odom',
            'Rtabmap/DetectionRate':   '1.0',
            'Kp/MaxFeatures':          '500',
            'RGBD/ProximityBySpace':   'true',
            'database_path':           '/media/wolfwagen1/c9c2a9fe-c435-4115-9237-57bc783cf964/rtabmap.db',
        }],
        remappings=[
            ('rgb/image',       '/zed/zed_node/left/image_rect_color'),
            ('rgb/camera_info', '/zed/zed_node/left/camera_info'),
            ('depth/image',     '/zed/zed_node/depth/depth_registered'),
            ('odom',            '/zed/zed_node/odom'),
            ('scan_cloud',      '/unilidar/cloud'),
        ],
    )



    # # Run Rviz
    # package_path = subprocess.check_output(['ros2', 'pkg', 'prefix', 'unitree_lidar_ros2']).decode('utf-8').rstrip()
    # rviz_config_file = os.path.join(package_path, 'share', 'unitree_lidar_ros2', 'view.rviz')
    # print("rviz_config_file = " + rviz_config_file)
    # rviz_node = Node(
    #     package='rviz2',
    #     executable='rviz2',
    #     name='rviz2',
    #     arguments=['-d', rviz_config_file],
    #     output='log'
    # )


    # # 8. RViz2
    # rviz_node = Node(
    #     package='rviz2',
    #     executable='rviz2',
    #     name='rviz2',
    #     output='screen',
    #     condition=IfCondition(use_rviz),
    # )

    # LiDAR → base_link transform


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
    )


    # Camera → base_link transform
    camera_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='camera_to_base_link',
        arguments=['0.1', '0', '0.3', '0', '0', '0', 'base_link', 'zed_left_camera_frame'],
    )




    return LaunchDescription([
        localization_arg,
        rviz_arg,
        unitree_launch,
        camera_node,
        lidar_node,
        joy_node,
        xbox_node,
        driver_node,
        rtabmap_node,
        rviz_node,
        lidar_root_tf,
        camera_tf

    ])