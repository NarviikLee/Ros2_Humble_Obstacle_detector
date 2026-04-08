오늘 하루 동안 VMware라는 까다로운 가상 환경에서 실제 라이다(LiDAR)와 IMU 센서를 활용해 SLAM 지도를 완성하기까지의 모든 기술적 여정을 마크다운 형식으로 정리해 드립니다. Notion이나 GitHub에 그대로 복사해서 사용하세요!

---

# 🚀 ROS 2 SLAM 실전 정복기: VMware 및 하드웨어 최적화 가이드

이 문서는 가상 머신(VMware) 환경에서 발생하는 연산 지연 및 하드웨어 통신 문제를 극복하고, **SLAM Toolbox**를 사용하여 실시간 지도를 생성 및 저장하는 과정을 기록합니다.

---

## 📂 1. 패키지 배포 및 빌드 설정 (`setup.py`)

파이썬 기반 ROS 2 패키지에서 커스텀 설정 파일(YAML, URDF, Launch)이 `install` 폴더로 정상적으로 설치되도록 경로를 지정하는 것이 필수입니다.

```python
# setup.py
import os
from glob import glob
from setuptools import setup

package_name = 'my_obstacle_detector'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        
        # Launch 파일: launch 폴더 내 모든 .py 포함
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        
        # URDF 파일: urdf 폴더 내 모든 파일 포함
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*')),
        
        # Config 파일: SLAM 파라미터 등 YAML 설정 파일 포함
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    # ... 후략 ...
)
```

> **💡 핵심 팁**: 빌드 시 `colcon build --symlink-install` 옵션을 사용하면 소스 코드의 YAML이나 런치 파일을 수정해도 재빌드 없이 바로 반영되어 개발 효율이 극대화됩니다.

---

## 🤖 2. 시뮬레이션 및 하드웨어 런치 시스템

### 2.1 Gazebo 런치 최적화 (`combined_gazebo.launch.py`)
VMware는 윈도우 자원을 공유하므로 가제보 서버가 뜨는 속도가 느립니다. 이를 위해 `TimerAction`을 사용하여 '엇박자'를 해결했습니다.

* **TimerAction**: 가제보 서버가 완전히 켜질 때까지 5초간 대기한 후 로봇 소환(`spawn_entity`) 노드를 실행.
* **use_sim_time**: 시뮬레이션 환경에서는 가상 시계와 동기화하기 위해 `True`로 설정.



---

## 🗺️ 3. SLAM Toolbox 최적화 설정 (`my_slam_params.yaml`)

가상 환경의 CPU 성능 한계와 실제 센서(YDLidar)의 통신 특성을 반영한 핵심 튜닝 값입니다.

```yaml
slam_toolbox:
  ros__parameters:
    # 1. 좌표계(TF) 설정
    odom_frame: odom
    map_frame: map
    base_frame: base_link
    scan_topic: /scan

    # 2. [필수] QoS 불일치 해결
    # Lidar 드라이버의 Best Effort 방식에 맞춰 수신 모드를 강제 일치시킴
    scan_reliability: best_effort 

    # 3. [VMware 최적화] 연산 부하 다이어트
    # 해상도를 낮추고 처리 범위를 제한하여 CPU 점유율을 관리함
    resolution: 0.1              # 0.05에서 0.1로 완화 (10cm 단위)
    max_laser_range: 8.0         # 20m에서 8m로 제한 (불필요한 원거리 계산 차단)
    minimum_time_interval: 0.2   # 초당 데이터 처리 횟수 조절
    transform_timeout: 1.0       # 좌표 변환 대기 시간을 늘려 연산 지연 허용

    # 4. 업데이트 민감도 조절
    # 손으로 들고 움직일 때 미세한 움직임도 지도에 즉시 반영
    minimum_travel_distance: 0.01
    minimum_travel_heading: 0.01
```

---

## 🛠️ 4. 주요 트러블슈팅 리포트

### ⚠️ QoS Mismatch (데이터 흐름 차단)
* **증상**: `requesting incompatible QoS. No messages will be sent to it.` 경고 발생.
* **원인**: 발행자(Lidar)와 구독자(SLAM)의 신뢰성 정책 불일치.
* **해결**: YAML에서 `scan_reliability: best_effort`로 설정하여 통신 통로 확보.



### ⚠️ Queue Full (데이터 드랍)
* **증상**: `Message Filter dropping message` 로그 반복.
* **원인**: VMware 연산 속도가 라이다 주사율을 따라가지 못함.
* **해결**: 위 YAML 설정의 **'연산 부하 다이어트'** 파라미터 적용으로 해결.

### ⚠️ RViz2 그래픽 에러 (Vertex Program)
* **증상**: GLSL 링크 에러와 함께 지도가 갱신되지 않음.
* **해결**:
    1.  환경 변수 적용: `export OGRE_RTT_MODE=Copy`
    2.  Ubuntu 로그인 시 **Xorg** 세션 선택.
    3.  최후의 수단: VMware 설정에서 **"Accelerate 3D graphics" 체크 해제**.

---

## 💾 5. 결과물 확인 및 저장

성공적으로 완성된 지도는 `map_saver`를 통해 영구적인 파일로 저장되었습니다.

```bash
# 맵 저장 명령어
ros2 run nav2_map_server map_saver_cli -f ~/my_first_map
```

### 생성된 전리품
* **`my_first_map.pgm`**: 2D 격자 지도 이미지 (검은색: 벽, 흰색: 이동 가능 공간).
* **`my_first_map.yaml`**: 지도의 해상도(0.1), 원점 정보 등을 포함한 설정 파일.



---

**기록 완료일**: 2026-04-08
**환경**: ROS 2 Humble / Ubuntu 22.04 (VMware)
**핵심 성과**: 가상 환경의 제약을 극복하고 실제 하드웨어 기반 SLAM 파이프라인 완성.