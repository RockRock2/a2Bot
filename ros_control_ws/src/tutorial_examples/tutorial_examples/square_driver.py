#!/usr/bin/env python3
"""
PUBLISHER EXAMPLE — square_driver

What this teaches:
  - How to create a ROS2 node
  - How to create a publisher
  - How to use a timer to publish on a schedule
  - How to build and send a geometry_msgs/Twist message

What it does:
  Drives the robot in a square: forward for 3s, turn ~90 degrees, repeat
  4 times, then stops. Publishes to /cmd_vel, the same topic the web
  dashboard's drive pad uses — diff_drive_controller picks it up exactly
  the same way either way.

Run it:
  ros2 run tutorial_examples square_driver
"""
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

FORWARD_SPEED = 0.08    # m/s — kept well under controllers.yaml's 0.10 m/s cap
TURN_SPEED = 0.4        # rad/s — kept under controllers.yaml's 0.5 rad/s cap
FORWARD_SECONDS = 3.0
TURN_SECONDS = 2.0      # roughly a 90 degree turn at TURN_SPEED — tune by testing
TIMER_PERIOD = 0.1      # publish at 10Hz


class SquareDriver(Node):

    def __init__(self):
        super().__init__('square_driver')

        # A publisher needs: the message type, the topic name, and a
        # "queue size" (how many messages to buffer if nobody is reading
        # them fast enough — 10 is a common safe default).
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # State machine: alternate between driving forward and turning,
        # four times each, then stop.
        self.state = 'forward'
        self.state_elapsed = 0.0
        self.legs_completed = 0
        self.total_legs = 4

        # create_timer calls the given function repeatedly, every
        # TIMER_PERIOD seconds, for as long as the node is running.
        self.timer = self.create_timer(TIMER_PERIOD, self.tick)

        self.get_logger().info('square_driver started — driving a square')

    def tick(self):
        twist = Twist()

        if self.legs_completed >= self.total_legs:
            # Done — publish a stop command and leave it there.
            self.cmd_vel_pub.publish(twist)  # all-zero Twist = stop
            return

        if self.state == 'forward':
            twist.linear.x = FORWARD_SPEED
            duration = FORWARD_SECONDS
        else:  # self.state == 'turn'
            twist.angular.z = TURN_SPEED
            duration = TURN_SECONDS

        self.cmd_vel_pub.publish(twist)
        self.state_elapsed += TIMER_PERIOD

        if self.state_elapsed >= duration:
            self.state_elapsed = 0.0
            if self.state == 'forward':
                self.state = 'turn'
            else:
                self.state = 'forward'
                self.legs_completed += 1
                self.get_logger().info(f'Completed side {self.legs_completed}/{self.total_legs}')


def main(args=None):
    rclpy.init(args=args)
    node = SquareDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Always publish a stop before shutting down — otherwise the
        # robot keeps executing the last command it received forever.
        node.cmd_vel_pub.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
