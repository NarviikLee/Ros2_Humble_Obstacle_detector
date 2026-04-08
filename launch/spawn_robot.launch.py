import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    # 1. 패키지 및 파일 경로 설정
    pkg_name = 'my_obstacle_detector'
    urdf_file = 'my_robot.urdf' 
    
    pkg_path = get_package_share_directory(pkg_name)
    urdf_path = os.path.join(pkg_path, 'urdf', urdf_file)

    # 2. Gazebo 기본 실행 (가제보 서버 켜기)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py'
        )]),
        launch_arguments={'pause': 'false'}.items(),
    )

    # 3. robot_state_publisher (설계도 전파)
    # [핵심] use_sim_time을 True로 줘야 가제보 시계와 동기화됩니다!
    with open(urdf_path, 'r') as infp:
        robot_desc = infp.read()

    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_desc,
            'use_sim_time': True
        }]
    )

    # 4. Gazebo에 로봇을 생성하는 노드 (소환사)
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic', 'robot_description', '-entity', 'my_robot'],
        output='screen'
    )

    # 5. [VMware 필살기] 5초 지연 소환
    # 가제보가 완전히 켜지기 전에 소환 명령을 내리면 '유령 로봇'이 됩니다.
    # 5초 정도 여유 있게 기다렸다가 로봇을 소환하게 만듭니다.
    delayed_spawn_entity = TimerAction(
        period=5.0,
        actions=[spawn_entity]
    )

    return LaunchDescription([
        gazebo,
        rsp,
        delayed_spawn_entity  # 그냥 spawn_entity 대신 지연된 버전을 넣습니다!
    ])
