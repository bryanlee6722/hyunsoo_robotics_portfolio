cmake_minimum_required(VERSION 3.8)
project(dynamixel_control)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)
find_package(rclpy REQUIRED)
find_package(python_cmake_module REQUIRED)
find_package(PythonExtra REQUIRED)

# Generate action interfaces
rosidl_generate_interfaces(${PROJECT_NAME}
  "action/ChessTimer.action"
  DEPENDENCIES std_msgs
)

# Install Python module
install(
  DIRECTORY ${PROJECT_NAME}/
  DESTINATION "${PYTHON_INSTALL_DIR}/${PROJECT_NAME}"
  PATTERN "*.pyc" EXCLUDE
  PATTERN "__pycache__" EXCLUDE
)

# Install Python executables (make them executable)
install(PROGRAMS
  scripts/motor_node
  scripts/motor_publisher
  scripts/chess_mapper
  scripts/camera_node
  scripts/camera_bridge_node
  scripts/timer_node
  scripts/chess_brain
  scripts/rviz_bridge
  scripts/timer_client
  DESTINATION lib/${PROJECT_NAME}
)

# Install launch and urdf files
install(DIRECTORY launch DESTINATION share/${PROJECT_NAME} USE_SOURCE_PERMISSIONS)
install(DIRECTORY urdf DESTINATION share/${PROJECT_NAME})

ament_package()
