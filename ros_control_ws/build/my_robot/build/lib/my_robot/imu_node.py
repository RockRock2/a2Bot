import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import smbus2
import math
import time


# ── MPU-9265 Register Map ──────────────────────────────────────
MPU_ADDR        = 0x68
PWR_MGMT_1      = 0x6B
ACCEL_XOUT_H    = 0x3B
GYRO_XOUT_H     = 0x43
ACCEL_CONFIG    = 0x1C
GYRO_CONFIG     = 0x1B

# Sensitivity scale factors (default ±2g, ±250°/s)
ACCEL_SCALE     = 16384.0   # LSB/g  for ±2g range
GYRO_SCALE      = 131.0     # LSB/°/s for ±250°/s range
G               = 9.80665   # m/s²


class ImuNode(Node):

    def __init__(self):
        super().__init__('imu_node')

        self.declare_parameter('i2c_bus',        1)
        self.declare_parameter('i2c_address',    0x68)
        self.declare_parameter('publish_rate',   50.0)   # Hz
        self.declare_parameter('frame_id',       'imu_link')

        bus_num   = self.get_parameter('i2c_bus').value
        self.addr = self.get_parameter('i2c_address').value
        rate      = self.get_parameter('publish_rate').value
        self.frame_id = self.get_parameter('frame_id').value

        # Open I2C bus
        self.bus = smbus2.SMBus(bus_num)

        # Wake up MPU (it starts in sleep mode)
        self.bus.write_byte_data(self.addr, PWR_MGMT_1, 0x00)
        time.sleep(0.1)

        # ── Calibration (gyro bias) ────────────────────────────
        # Keep robot perfectly still for 2 seconds during startup
        self.get_logger().info('Calibrating IMU — keep robot still...')
        self.gyro_bias = self._calibrate_gyro(samples=200)
        self.get_logger().info(
            f'Gyro bias: x={self.gyro_bias[0]:.4f} '
            f'y={self.gyro_bias[1]:.4f} '
            f'z={self.gyro_bias[2]:.4f} rad/s')

        # Publisher
        self.imu_pub = self.create_publisher(Imu, '/imu/data_raw', 10)

        # Timer
        self.create_timer(1.0 / rate, self.publish_imu)
        self.get_logger().info(f'IMU node started at {rate}Hz.')

    def _read_word(self, reg):
        """Read a signed 16-bit value from two consecutive registers."""
        high = self.bus.read_byte_data(self.addr, reg)
        low  = self.bus.read_byte_data(self.addr, reg + 1)
        val  = (high << 8) | low
        return val - 65536 if val >= 32768 else val

    def _calibrate_gyro(self, samples=200):
        """Average gyro readings at rest to find bias."""
        bx, by, bz = 0.0, 0.0, 0.0
        for _ in range(samples):
            bx += self._read_word(GYRO_XOUT_H)
            by += self._read_word(GYRO_XOUT_H + 2)
            bz += self._read_word(GYRO_XOUT_H + 4)
            time.sleep(0.005)
        n = float(samples)
        # Convert to rad/s
        return (
            math.radians((bx / n) / GYRO_SCALE),
            math.radians((by / n) / GYRO_SCALE),
            math.radians((bz / n) / GYRO_SCALE),
        )

    def publish_imu(self):
        try:
            # Read raw accelerometer (m/s²)
            ax = (self._read_word(ACCEL_XOUT_H)     / ACCEL_SCALE) * G
            ay = (self._read_word(ACCEL_XOUT_H + 2) / ACCEL_SCALE) * G
            az = (self._read_word(ACCEL_XOUT_H + 4) / ACCEL_SCALE) * G

            # Read raw gyroscope (rad/s), subtract calibration bias
            gx = math.radians(self._read_word(GYRO_XOUT_H)     / GYRO_SCALE) \
                 - self.gyro_bias[0]
            gy = math.radians(self._read_word(GYRO_XOUT_H + 2) / GYRO_SCALE) \
                 - self.gyro_bias[1]
            gz = math.radians(self._read_word(GYRO_XOUT_H + 4) / GYRO_SCALE) \
                 - self.gyro_bias[2]

            msg = Imu()
            msg.header.stamp    = self.get_clock().now().to_msg()
            msg.header.frame_id = self.frame_id

            # Orientation unknown (not computed here — robot_localization handles it)
            msg.orientation_covariance[0] = -1.0   # signals "unknown"

            msg.angular_velocity.x = gx
            msg.angular_velocity.y = gy
            msg.angular_velocity.z = gz
            msg.angular_velocity_covariance[0] = 0.001
            msg.angular_velocity_covariance[4] = 0.001
            msg.angular_velocity_covariance[8] = 0.001

            msg.linear_acceleration.x = ax
            msg.linear_acceleration.y = ay
            msg.linear_acceleration.z = az
            msg.linear_acceleration_covariance[0] = 0.01
            msg.linear_acceleration_covariance[4] = 0.01
            msg.linear_acceleration_covariance[8] = 0.01

            self.imu_pub.publish(msg)

        except Exception as e:
            self.get_logger().warn(f'IMU read error: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = ImuNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
