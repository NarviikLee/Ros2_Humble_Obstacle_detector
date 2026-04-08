from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    # 1. YDLidar 드라이버 런칭 포함
    ydlidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ydlidar_ros2_driver'), 'launch', 'ydlidar_launch.py')
        )
    )

    # 2. 내가 만든 감지 노드 실행
    my_detector = Node(
        package='my_obstacle_detector',
        executable='detector_node',
        name='detector_node',
        output='screen'
    )
    imu_reader = Node(
        package='my_obstacle_detector',
        executable='imu_reader_node',
        name='imu_reader_node',
        output='screen'
    )
    static_tf_laser = Node(
        package='tf2_ros', 
        executable='static_transform_publisher',
        arguments=['0', '0', '0.15', '0', '0', '0', 'base_link', 'laser_frame']
    )
             
    static_tf_imu = Node(
        package='tf2_ros', 
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'imu_link']
    )
    
    static_tf_odom = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0', 'odom', 'base_link']
    )
    return LaunchDescription([
        ydlidar_launch,
        my_detector,
        imu_reader,
        static_tf_laser, # 리스트에 추가!
        static_tf_imu,    # 리스트에 추가!
        static_tf_odom
    ])
