import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32MultiArray
import math


class DiffDriveController(Node):

    def __init__(self):
        super().__init__('diff_drive_controller')

        # ── Robot Physical Parameters ──────────────────────────────
        # MEASURE THESE ON YOUR ACTUAL ROBOT!
        self.declare_parameter('wheel_radius',    0.033)   # meters (JGB37-520 wheel)
        self.declare_parameter('wheel_separation', 0.25)   # meters (distance between wheels)
        self.declare_parameter('max_motor_rpm',   10.0)   # RPM at full PWM
        self.declare_parameter('pwm_deadband',    30)      # Minimum PWM to overcome stiction
        self.declare_parameter('max_pwm',         255)

        self.wheel_radius     = self.get_parameter('wheel_radius').value
        self.wheel_separation = self.get_parameter('wheel_separation').value
        self.max_motor_rpm    = self.get_parameter('max_motor_rpm').value
        self.pwm_deadband     = self.get_parameter('pwm_deadband').value
        self.max_pwm          = self.get_parameter('max_pwm').value

        # Max wheel speed in m/s
        self.max_wheel_speed = (self.max_motor_rpm / 60.0) * \
                               (2 * math.pi * self.wheel_radius)

        # Publisher to hardware bridge
        self.wheel_cmd_pub = self.create_publisher(
            Float32MultiArray, '/wheel_cmd', 10)

        # Subscribe to velocity commands
        self.cmd_vel_sub = self.create_subscription(
            Twist, '/cmd_vel', self.cmd_vel_callback, 10)

        # Watchdog: stop motors if no cmd_vel received for 0.5s
        self.last_cmd_time = self.get_clock().now()
        self.watchdog_timer = self.create_timer(0.1, self.watchdog_callback)

        self.get_logger().info('Differential drive controller started.')
        self.get_logger().info(
            f'Wheel radius: {self.wheel_radius}m, '
            f'Separation: {self.wheel_separation}m, '
            f'Max speed: {self.max_wheel_speed:.2f}m/s')

    def velocity_to_pwm(self, vel_ms):
        """Convert wheel velocity (m/s) to (pwm, direction)."""
        if abs(vel_ms) < 0.001:
            return 0, 1

        direction = 1 if vel_ms > 0 else 0
        ratio = abs(vel_ms) / self.max_wheel_speed
        pwm   = int(ratio * self.max_pwm)

        # Apply deadband to prevent stalling
        if 0 < pwm < self.pwm_deadband:
            pwm = self.pwm_deadband

        pwm = min(pwm, 80)
        return pwm, direction

    def cmd_vel_callback(self, msg):
        """Convert Twist to wheel PWM commands."""
        self.last_cmd_time = self.get_clock().now()

        linear  = msg.linear.x
        angular = -msg.angular.z

        # Differential drive kinematics
        v_left  = linear - angular * (self.wheel_separation / 2.0)
        v_right = linear + angular * (self.wheel_separation / 2.0)

        # Clamp to max speed
        v_left  = max(-self.max_wheel_speed, min(self.max_wheel_speed, v_left))
        v_right = max(-self.max_wheel_speed, min(self.max_wheel_speed, v_right))

        l_pwm, l_dir = self.velocity_to_pwm(v_left)
        r_pwm, r_dir = self.velocity_to_pwm(v_right)

        wheel_cmd = Float32MultiArray()
        wheel_cmd.data = [
            float(l_pwm), float(l_dir),
            float(r_pwm), float(r_dir)
        ]
        self.wheel_cmd_pub.publish(wheel_cmd)

    def watchdog_callback(self):
        """Stop motors if no command received recently."""
        now = self.get_clock().now()
        elapsed = (now - self.last_cmd_time).nanoseconds / 1e9
        if elapsed > 0.5:
            # Send stop command
            wheel_cmd = Float32MultiArray()
            wheel_cmd.data = [0.0, 1.0, 0.0, 1.0]
            self.wheel_cmd_pub.publish(wheel_cmd)


def main(args=None):
    rclpy.init(args=args)
    node = DiffDriveController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()