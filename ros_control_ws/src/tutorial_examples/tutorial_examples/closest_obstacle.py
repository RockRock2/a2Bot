#!/usr/bin/env python3
"""
SUBSCRIBER EXAMPLE — closest_obstacle

What this teaches:
  - How to create a ROS2 node
  - How to create a subscriber and write a callback function
  - How to read fields out of a real sensor message (sensor_msgs/LaserScan)

What it does:
  Listens to /scan (the RPLidar's data) and prints the distance to
  whatever is closest to the robot, along with which direction it's in.
  No publishing here — this node only reads, it never commands the robot.

Run it:
  ros2 run tutorial_examples closest_obstacle
"""
import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

WARNING_DISTANCE_M = 0.3  # flag distances closer than this


class ClosestObstacle(Node):

    def __init__(self):
        super().__init__('closest_obstacle')

        # A subscriber needs: the message type, the topic name, the
        # callback function to run on every new message, and the same
        # queue-size concept as a publisher.
        self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)

        self.get_logger().info('closest_obstacle started — listening to /scan')

    def scan_callback(self, msg: LaserScan):
        # msg.ranges is a list of distances, one per angle step.
        # The lidar reports 'inf' for "nothing detected" at that angle
        # (out of range), so we filter those out before finding the min.
        valid = [(i, r) for i, r in enumerate(msg.ranges)
                 if not math.isinf(r) and not math.isnan(r) and r > 0.0]

        if not valid:
            self.get_logger().info('No valid readings this scan')
            return

        closest_index, closest_distance = min(valid, key=lambda pair: pair[1])

        # Each reading's angle = angle_min + index * angle_increment
        angle_rad = msg.angle_min + closest_index * msg.angle_increment
        angle_deg = math.degrees(angle_rad)

        if closest_distance < WARNING_DISTANCE_M:
            self.get_logger().warn(
                f'Obstacle close! {closest_distance:.2f}m at {angle_deg:.0f} degrees'
            )
        else:
            self.get_logger().info(
                f'Closest object: {closest_distance:.2f}m at {angle_deg:.0f} degrees'
            )


def main(args=None):
    rclpy.init(args=args)
    node = ClosestObstacle()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
