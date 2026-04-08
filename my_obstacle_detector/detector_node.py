import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan, Imu
import math

class DetectorNode(Node):
    def __init__(self):
        super().__init__('detector_node')
        self.scan_sub = self.create_subscription(LaserScan, '/scan', self.scan_callback, rclpy.qos.qos_profile_sensor_data)
        self.imu_sub = self.create_subscription(Imu, '/imu/data_raw', self.imu_callback, 10)

        self.lidar_height = 0.15  # 실제 설치 높이(m)
        self.ground_threshold = 0.05
        self.current_pitch = 0.0
        self.obstacle_count = 0
        self.last_imu_time = self.get_clock().now()

    def imu_callback(self, msg):
        self.last_imu_time = self.get_clock().now()
        q = msg.orientation
        sinp = 2 * (q.w * q.y - q.z * q.x)
        self.current_pitch = math.asin(max(-1.0, min(1.0, sinp)))

    def scan_callback(self, msg):
        if (self.get_clock().now() - self.last_imu_time).nanoseconds / 1e9 > 0.5:
            return

        front_indices = list(range(0, 20)) + list(range(len(msg.ranges)-20, len(msg.ranges)))
        is_detected = False
        min_d = 999.0

        for i in front_indices:
            r = msg.ranges[i]
            if msg.range_min < r < msg.range_max:
                # 삼각함수 지면 보정
                z_point = self.lidar_height + (r * math.sin(self.current_pitch))
                d_horiz = r * math.cos(self.current_pitch)
                
                if abs(z_point) > self.ground_threshold and d_horiz < 0.5:
                    is_detected = True
                    min_d = min(min_d, d_horiz)

        if is_detected:
            self.obstacle_count = min(self.obstacle_count + 1, 10)
        elif self.obstacle_count > 0:
            self.obstacle_count -= 1

        if self.obstacle_count >= 5:
            self.get_logger().warn(f'🚨 장애물! 거리: {min_d:.2f}m, 각도: {math.degrees(self.current_pitch):.1f}°')

def main():
    rclpy.init()
    node = DetectorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
