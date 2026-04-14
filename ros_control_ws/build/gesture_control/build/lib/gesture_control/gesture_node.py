import cv2
import mediapipe as mp
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from flask import Flask, Response
import threading

app  = Flask(__name__)
latest_frame = None

def generate():
    global latest_frame
    while True:
        if latest_frame is None:
            continue
        _, buffer = cv2.imencode('.jpg', latest_frame,
                                  [cv2.IMWRITE_JPEG_QUALITY, 70])
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n'
               + frame_bytes + b'\r\n')

@app.route('/video')
def video():
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return '''
    <html>
    <body style="background:black;margin:0">
    <img src="/video" style="width:100%;height:100vh;object-fit:contain">
    </body>
    </html>
    '''

class GestureControlNode(Node):

    def __init__(self):
        super().__init__('gesture_control_node')

        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        mp_hands      = mp.solutions.hands
        self.mp_hands = mp_hands
        self.mp_draw  = mp.solutions.drawing_utils
        self.hands    = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

        self.cap = cv2.VideoCapture(-1)
        if not self.cap.isOpened():
            self.get_logger().error('Cannot open camera')

        # Start Flask stream in background thread
        flask_thread = threading.Thread(
            target=lambda: app.run(
                host='0.0.0.0', port=5000, threaded=True),
            daemon=True
        )
        flask_thread.start()
        self.get_logger().info('Stream available at http://robot.local:5000')

        self.create_timer(1.0 / 15.0, self.loop)
        self.get_logger().info('Gesture control node started')

    def is_thumbs_up(self, landmarks, handedness):
        lm = landmarks.landmark
        is_back_of_hand = handedness.classification[0].label == 'Left'
        thumb_up        = lm[4].y < lm[3].y
        index_folded    = lm[8].y  > lm[6].y
        middle_folded   = lm[12].y > lm[10].y
        ring_folded     = lm[16].y > lm[14].y
        pinky_folded    = lm[20].y > lm[18].y
        fingers_folded  = (index_folded and middle_folded
                           and ring_folded and pinky_folded)
        return is_back_of_hand and thumb_up and fingers_folded

    def loop(self):
        global latest_frame
        ret, frame = self.cap.read()
        if not ret:
            return

        rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        twist = Twist()

        if results.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(
                    results.multi_hand_landmarks,
                    results.multi_handedness):

                # Draw skeleton on frame for stream
                self.mp_draw.draw_landmarks(
                    frame, hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS)

                if self.is_thumbs_up(hand_landmarks, handedness):
                    twist.linear.x  = 0.2
                    twist.angular.z = 0.0
                    label = "THUMBS UP - Moving!"
                    color = (0, 255, 0)
                    self.get_logger().info('THUMBS UP — moving forward')
                else:
                    label = "Hand detected — stopped"
                    color = (0, 0, 255)

                cv2.putText(frame, label, (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        self.cmd_pub.publish(twist)

        # Update stream frame
        latest_frame = frame

    def destroy_node(self):
        self.cap.release()
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