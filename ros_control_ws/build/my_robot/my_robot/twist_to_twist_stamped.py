import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped


class TwistToTwistStamped(Node):
    def __init__(self):
        super().__init__('twist_to_twist_stamped')

        self.pub = self.create_publisher(
            TwistStamped, '/diff_drive_controller/cmd_vel', 10)

        self.sub = self.create_subscription(
            Twist, '/cmd_vel',
            self.callback, 10)

        self.get_logger().info('Twist → TwistStamped converter started.')

    def callback(self, msg):
        stamped = TwistStamped()
        stamped.header.stamp    = self.get_clock().now().to_msg()
        stamped.header.frame_id = 'base_footprint'
        stamped.twist           = msg
        self.pub.publish(stamped)


def main(args=None):
    rclpy.init(args=args)
    node = TwistToTwistStamped()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()