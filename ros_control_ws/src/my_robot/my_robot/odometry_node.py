import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster
import math


class OdometryNode(Node):

    def __init__(self):
        super().__init__('odometry_node')

        # ── Parameters ─────────────────────────────────────────────
        self.declare_parameter('wheel_radius',    0.033)
        self.declare_parameter('wheel_separation', 0.25)
        self.declare_parameter('ticks_per_rev',   3000)   # ← SET YOUR ENCODER TPR

        self.wheel_radius     = self.get_parameter('wheel_radius').value
        self.wheel_separation = self.get_parameter('wheel_separation').value
        self.ticks_per_rev    = self.get_parameter('ticks_per_rev').value

        self.dist_per_tick = (2 * math.pi * self.wheel_radius) / self.ticks_per_rev

        # Robot pose state
        self.x     = 0.0
        self.y     = 0.0
        self.theta = 0.0

        # Previous encoder ticks
        self.prev_left_ticks  = None
        self.prev_right_ticks = None

        # TF broadcaster
        self.tf_broadcaster = TransformBroadcaster(self)

        # Odometry publisher
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)

        # Subscribe to encoder ticks from Arduino bridge
        self.enc_sub = self.create_subscription(
            Int32MultiArray, '/encoder_ticks',
            self.encoder_callback, 10)

        self.get_logger().info(
            f'Odometry node started. '
            f'dist_per_tick={self.dist_per_tick*1000:.3f}mm')

    def encoder_callback(self, msg):
        if len(msg.data) < 2:
            return

        left_ticks  = msg.data[0]
        right_ticks = msg.data[1]

        # Initialize on first message
        if self.prev_left_ticks is None:
            self.prev_left_ticks  = left_ticks
            self.prev_right_ticks = right_ticks
            return

        # Delta ticks
        dl = (left_ticks  - self.prev_left_ticks)  * self.dist_per_tick
        dr = (right_ticks - self.prev_right_ticks) * self.dist_per_tick

        self.prev_left_ticks  = left_ticks
        self.prev_right_ticks = right_ticks

        # Differential drive odometry equations
        d_center = (dl + dr) / 2.0
        d_theta  = (dr - dl) / self.wheel_separation

        self.x     += d_center * math.cos(self.theta + d_theta / 2.0)
        self.y     += d_center * math.sin(self.theta + d_theta / 2.0)
        self.theta += d_theta
        # Keep theta in [-π, π]
        self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))

        now = self.get_clock().now().to_msg()

        # ── Publish Odometry message ──────────────────────────────
        odom = Odometry()
        odom.header.stamp    = now
        odom.header.frame_id = 'odom'
        odom.child_frame_id  = 'base_footprint'

        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y

        # Quaternion from yaw
        odom.pose.pose.orientation.z = math.sin(self.theta / 2.0)
        odom.pose.pose.orientation.w = math.cos(self.theta / 2.0)

        # Covariance (simple diagonal)
        odom.pose.covariance[0]  = 0.01
        odom.pose.covariance[7]  = 0.01
        odom.pose.covariance[35] = 0.05

        self.odom_pub.publish(odom)

        # ── Broadcast TF: odom → base_footprint ───────────────────────
        t = TransformStamped()
        t.header.stamp    = now
        t.header.frame_id = 'odom'
        t.child_frame_id  = 'base_footprint'

        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0
        t.transform.rotation.z    = math.sin(self.theta / 2.0)
        t.transform.rotation.w    = math.cos(self.theta / 2.0)

        self.tf_broadcaster.sendTransform(t)


def main(args=None):
    rclpy.init(args=args)
    node = OdometryNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()