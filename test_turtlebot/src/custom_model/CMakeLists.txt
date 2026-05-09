cmake_minimum_required(VERSION 3.8)
project(custom_model)

find_package(ament_cmake REQUIRED)

# Install urdf and launch folders so ROS2 can find them
install(DIRECTORY urdf launch config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
