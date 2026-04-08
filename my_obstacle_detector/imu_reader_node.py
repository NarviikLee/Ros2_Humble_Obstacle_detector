import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import serial
import math

class ImuReaderNode(Node):
    def __init__(self):
        super().__init__('imu_reader_node')
        self.publisher_ = self.create_publisher(Imu, 'imu/data_raw', 10)
        
        # 설정: udev rule로 잡은 포트명
        self.port = '/dev/arduino_imu'
        self.baudrate = 115200 
        
        self.window_size = 5
        self.accel_x_buffer = []
        self.accel_y_buffer = []
        self.accel_z_buffer = []

        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.1)
            self.ser.flushInput()
            self.get_logger().info(f'✅ IMU 연결 성공 ({self.port})')
        except Exception as e:
            self.get_logger().error(f'❌ IMU 연결 실패: {e}')

        self.timer = self.create_timer(0.02, self.read_serial_and_publish)

    def moving_average(self, buffer, new_value):
        buffer.append(new_value)
        if len(buffer) > self.window_size:
            buffer.pop(0)
        return sum(buffer) / len(buffer)
        
    def read_serial_and_publish(self):
        try:
            # [지연 방지] 버퍼가 쌓이면 청소
            if self.ser.in_waiting > 100:
                self.ser.reset_input_buffer()
                return

            if self.ser.in_waiting > 0:
                raw_line = self.ser.readline()
                line = raw_line.decode('utf-8', errors='ignore').strip()
                if not line: return

                data = line.split(',')
                if len(data) == 6:
                    ax = self.moving_average(self.accel_x_buffer, float(data[0]))
                    ay = self.moving_average(self.accel_y_buffer, float(data[1]))
                    az = self.moving_average(self.accel_z_buffer, float(data[2]))
                    gx, gy, gz = float(data[3]), float(data[4]), float(data[5])

                    # Pitch/Roll 계산
                    pitch_rad = math.atan2(-ax, math.sqrt(ay*ay + az*az))
                    roll_rad = math.atan2(ay, az)

                    # 쿼터니언 변환 (Yaw=0 가정)
                    cp, sp = math.cos(pitch_rad * 0.5), math.sin(pitch_rad * 0.5)
                    cr, sr = math.cos(roll_rad * 0.5), math.sin(roll_rad * 0.5)

                    msg = Imu()
                    msg.header.stamp = self.get_clock().now().to_msg()
                    msg.header.frame_id = 'imu_link'
                    msg.orientation.x = sr * cp
                    msg.orientation.y = cr * sp
                    msg.orientation.z = -sr * sp
                    msg.orientation.w = cr * cp
                    
                    msg.linear_acceleration.x, msg.linear_acceleration.y, msg.linear_acceleration.z = ax, ay, az
                    msg.angular_velocity.x, msg.angular_velocity.y, msg.angular_velocity.z = gx, gy, gz
                    msg.orientation_covariance = [0.01] * 9
                    msg.angular_velocity_covariance = [0.01] * 9
                    msg.linear_acceleration_covariance = [0.01] * 9
                    self.publisher_.publish(msg)
        except Exception: pass

def main():
    rclpy.init()
    node = ImuReaderNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
