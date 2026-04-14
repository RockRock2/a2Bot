import cv2
import os
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import GestureRecognizer
from mediapipe.tasks.python.vision import GestureRecognizerOptions
from mediapipe.tasks.python.vision import RunningMode
import numpy as np


class GestureControlNode(Node):

    def __init__(self):
        super().__init__('gesture_control_node')

        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        base_options = python.BaseOptions(
            model_asset_path=os.path.expanduser(
                '~/gesture_recognizer.task'))

        options = GestureRecognizerOptions(
            base_options=base_options,
            running_mode=RunningMode.IMAGE,
            num_hands=1,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.7,
            min_tracking_confidence=0.7
        )

        self.recognizer = GestureRecognizer.create_from_options(options)

        self.cap = cv2.VideoCapture(4)
        if not self.cap.isOpened():
            self.get_logger().error('Cannot open camera')

        self.create_timer(1.0 / 15.0, self.loop)
        self.get_logger().info('Gesture control node started')
        self.get_logger().info('👍 Thumb Up         = move forward')
        self.get_logger().info('✌️  Index + Middle   = rotate right')
        self.get_logger().info('🤙 Index + Thumb     = rotate left')

    def is_peace_sign(self, lm):
        index_up     = lm[8].y  < lm[6].y
        middle_up    = lm[12].y < lm[10].y
        ring_folded  = lm[16].y > lm[14].y
        pinky_folded = lm[20].y > lm[18].y
        thumb_folded = lm[4].y  > lm[3].y
        return (index_up and middle_up
                and ring_folded and pinky_folded
                and thumb_folded)

    def is_l_sign(self, lm):
        index_up      = lm[8].y  < lm[6].y
        thumb_up      = lm[4].y  < lm[2].y
        middle_folded = lm[12].y > lm[10].y
        ring_folded   = lm[16].y > lm[14].y
        pinky_folded  = lm[20].y > lm[18].y
        return (index_up and thumb_up
                and middle_folded and ring_folded
                and pinky_folded)

    def draw_landmarks(self, frame, lm):
        h, w = frame.shape[:2]
        points = []
        for p in lm:
            cx = int(p.x * w)
            cy = int(p.y * h)
            points.append((cx, cy))
            cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)

        connections = [
            (0,1),(1,2),(2,3),(3,4),
            (0,5),(5,6),(6,7),(7,8),
            (0,9),(9,10),(10,11),(11,12),
            (0,13),(13,14),(14,15),(15,16),
            (0,17),(17,18),(18,19),(19,20),
            (5,9),(9,13),(13,17),
        ]
        for a, b in connections:
            cv2.line(frame, points[a], points[b], (0, 200, 255), 2)

    def loop(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=np.array(rgb)
        )

        result = self.recognizer.recognize(mp_image)

        twist       = Twist()
        label_text  = "No gesture — stopped"
        label_color = (100, 100, 100)

        if result.gestures and result.hand_landmarks:
            gesture = result.gestures[0][0]
            label   = gesture.category_name
            score   = gesture.score
            lm      = result.hand_landmarks[0]

            # Draw skeleton
            self.draw_landmarks(frame, lm)

            # Thumb Up → forward
            if label == 'Thumb_Up' and score > 0.7:
                twist.linear.x  = 0.2
                twist.angular.z = 0.0
                label_text  = "THUMBS UP — Forward!"
                label_color = (0, 255, 0)
                self.get_logger().info('THUMBS UP — moving forward!')

            # Peace ✌️ → rotate right
            elif self.is_peace_sign(lm):
                twist.linear.x  = 0.0
                twist.angular.z = -0.5
                label_text  = "PEACE — Rotate Right"
                label_color = (0, 165, 255)
                self.get_logger().info('PEACE — rotating right')

            # L sign 🤙 → rotate left
            elif self.is_l_sign(lm):
                twist.linear.x  = 0.0
                twist.angular.z = 0.5
                label_text  = "L SIGN — Rotate Left"
                label_color = (255, 100, 0)
                self.get_logger().info('L SIGN — rotating left')

            else:
                label_text  = f"Unknown: {label} ({score:.2f})"
                label_color = (100, 100, 100)

        # HUD — top bar
        cv2.rectangle(frame, (0, 0),
                      (frame.shape[1], 60), (30, 30, 30), -1)
        cv2.putText(frame, label_text, (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                    label_color, 2)

        # HUD — bottom legend
        h = frame.shape[0]
        cv2.rectangle(frame, (0, h - 80),
                      (frame.shape[1], h), (30, 30, 30), -1)
        cv2.putText(frame,
                    "Thumb Up=Fwd  Peace=Right  L Sign=Left",
                    (10, h - 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                    (200, 200, 200), 1)
        cv2.putText(frame,
                    "No gesture = Stop  |  Q to quit",
                    (10, h - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                    (200, 200, 200), 1)

        # Always publish
        self.cmd_pub.publish(twist)

        cv2.imshow("Gesture Control", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.destroy_node()

    def destroy_node(self):
        self.cap.release()
        cv2.destroyAllWindows()
        self.recognizer.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = GestureControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()