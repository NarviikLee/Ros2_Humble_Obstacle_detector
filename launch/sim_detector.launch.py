from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 1. 감지 노드만 실행 (가상 센서 데이터를 구독함)
        Node(
            package='my_obstacle_detector',
            executable='detector_node',
            name='sim_detector',
            output='screen'
        ),
        
        # 2. RViz2 (가상 세계가 어떻게 보이는지 시각화)
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            # 미리 저장된 rviz 설정 파일이 있다면 여기에 추가 가능
        )
    ])
