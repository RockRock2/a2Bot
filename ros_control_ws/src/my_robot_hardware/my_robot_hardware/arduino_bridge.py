import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray, Float32MultiArray
import serial
import threading
import time


class ArduinoBridge(Node):

    def __init__(self):
        super().__init__('arduino_bridge')

        # Parameters
        self.declare_parameter('serial_port', '/dev/arduino')
        self.declare_parameter('baud_rate', 57600)
        self.declare_parameter('timeout', 1.0)

        port     = self.get_parameter('serial_port').value
        baud     = self.get_parameter('baud_rate').value
        timeout  = self.get_parameter('timeout').value

        # Open serial port
        try:
            self.ser = serial.Serial(port, baud, timeout=timeout)
            self.ser.reset_input_buffer()   # flush bootloader garbage
            time.sleep(2)                   # wait for Arduino to finish booting
            self.get_logger().info(f'Connected to Arduino on {port}')
        except serial.SerialException as e:
            self.get_logger().error(f'Failed to open serial port: {e}')
            raise

        self.ser = serial.Serial(port, baud, timeout=timeout)
        self.ser.setDTR(False)   # ← prevents Arduino reset on connect
        time.sleep(0.5)
        self.ser.setDTR(True)
        time.sleep(2)
        self.ser.reset_input_buffer()

        # Publisher: encoder ticks [left_ticks, right_ticks]
        self.enc_pub = self.create_publisher(
            Int32MultiArray, '/encoder_ticks', 10)

        # Subscriber: wheel commands [left_pwm, left_dir, right_pwm, right_dir]
        self.cmd_sub = self.create_subscription(
            Float32MultiArray, '/wheel_cmd',
            self.wheel_cmd_callback, 10)

        # Read serial in background thread
        self.read_thread = threading.Thread(
            target=self.read_serial_loop, daemon=True)
        self.read_thread.start()

        self.get_logger().info('Arduino bridge node started.')

    def wheel_cmd_callback(self, msg):
        """Receive [l_pwm, l_dir, r_pwm, r_dir] and forward to Arduino."""
        if len(msg.data) < 4:
            return
        l_pwm = int(abs(msg.data[0]))
        l_dir = int(msg.data[1])
        r_pwm = int(abs(msg.data[2]))
        r_dir = int(msg.data[3])

        cmd = f'L{l_pwm},{l_dir} R{r_pwm},{r_dir}\n'
        try:
            self.ser.write(cmd.encode())
        except serial.SerialException as e:
            self.get_logger().warn(f'Serial write error: {e}')

    def read_serial_loop(self):
        while rclpy.ok():
            try:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()

                # Ignore empty or obviously corrupt lines
                if not line.startswith('ENC'):
                    continue

                parts = line.split()
                if len(parts) != 3:
                    continue

                # Validate both values are clean integers before parsing
                if not parts[1].lstrip('-').isdigit():
                    continue
                if not parts[2].lstrip('-').isdigit():
                    continue

                left_ticks  = int(parts[1])
                right_ticks = int(parts[2])

                msg = Int32MultiArray()
                msg.data = [right_ticks, left_ticks]
                self.enc_pub.publish(msg)

            except Exception as e:
                self.get_logger().warn(f'Serial read error: {e}')

    def destroy_node(self):
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ArduinoBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()