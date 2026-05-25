from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'vlm_roomba_pkg'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        # Register the package with ament
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),

        # Install launch files so ros2 launch can find them
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.py')),

        # Install config files
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),
            
        # Install URDF files
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*.xacro')),
        (os.path.join('share', package_name, 'urdf/sensors'), glob('urdf/sensors/*.xacro')),
            
        # ✅ Add this line:
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='wolfwagen',
    maintainer_email='you@example.com',
    description='Roomba mapping package with ZED camera and LiDAR',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
            'console_scripts': [
                'Zed_to_VLM_node = vlm_roomba_pkg.Zed_to_VLM_node:main',
                'processing_video = vlm_roomba_pkg.processing_video:main',
                'processing_video_4090 = vlm_roomba_pkg.processing_video_4090:main'
            ],
        },

)