import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float64MultiArray
from cv_bridge import CvBridge
import cv2
import numpy as np


class DetectionNode(Node):
    def __init__(self):
        super().__init__('detection_node')
        self.get_logger().info('Detection Node has been started.')

        self.bridge = CvBridge()

        # Parameters for topic names and color detection thresholds.
        self.declare_parameter('input_topic', 'raw_camera_image')
        self.declare_parameter('output_topic', 'detection_results')
        self.declare_parameter('min_area', 50.0)

        self.red_lower_1 = np.array([0, 120, 80], dtype=np.uint8)
        self.red_upper_1 = np.array([10, 255, 255], dtype=np.uint8)
        self.red_lower_2 = np.array([170, 120, 80], dtype=np.uint8)
        self.red_upper_2 = np.array([180, 255, 255], dtype=np.uint8)
        self.min_area = float(self.get_parameter('min_area').value)

        input_topic = str(self.get_parameter('input_topic').value)
        output_topic = str(self.get_parameter('output_topic').value)

        self.result_pub = self.create_publisher(Float64MultiArray, output_topic, 10)
        self.image_sub = self.create_subscription(Image, input_topic, self.detection_callback, 10)
        self.get_logger().info(f'Subscribed to "{input_topic}", publishing center pixels to "{output_topic}"')

    def detection_callback(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as exc:
            self.get_logger().error(f'Failed to convert image: {exc}')
            return

        center = self._detect_largest_red_center(frame)
        if center is None:
            return

        cx, cy = center
        out_msg = Float64MultiArray()
        out_msg.data = [float(cx), float(cy)]
        self.result_pub.publish(out_msg)

    def _detect_largest_red_center(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask_1 = cv2.inRange(hsv, self.red_lower_1, self.red_upper_1)
        mask_2 = cv2.inRange(hsv, self.red_lower_2, self.red_upper_2)
        mask = cv2.bitwise_or(mask_1, mask_2)

        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)
        if area < self.min_area:
            return None

        moments = cv2.moments(largest)
        if moments['m00'] == 0:
            return None

        cx = int(moments['m10'] / moments['m00'])
        cy = int(moments['m01'] / moments['m00'])
        return (cx, cy)


def main(args=None):
    rclpy.init(args=args)
    node = DetectionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
