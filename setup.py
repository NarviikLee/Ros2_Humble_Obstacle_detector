from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'my_obstacle_detector'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        
        # 1. Launch 파일들 추가
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        
        # 2. URDF 파일들 추가
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*')),
        
        # 3. [추가] Config 폴더 내의 YAML 설정 파일들 추가
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='lee',
    maintainer_email='lee@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'detector_node = my_obstacle_detector.detector_node:main',
            'imu_reader_node = my_obstacle_detector.imu_reader_node:main',
        ],
    }
)
