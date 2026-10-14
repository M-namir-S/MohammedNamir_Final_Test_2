#!/usr/bin/env python3
"""Q1: subscribe to image + yaw+ heading, centre-crop to 1:1, overlay values, republish."""
import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import BatteryState, Image
from std_msgs.msg import Float32


class CameraAnnotator(Node):
    def __init__(self):
        super().__init__('camera_annotator')
        self.bridge = CvBridge()
        self.voltage = None   # latest yawvoltage [V]
        self.heading = None   # latest heading [deg]

        self.create_subscription(BatteryState, '/battery_state', self.on_battery, 10)
        self.create_subscription(Float32, '/compass/heading', self.on_heading, 10)
        self.create_subscription(Image, '/camera/rgb', self.on_image, qos_profile_sensor_data)
        self.pub = self.create_publisher(Image, '/camera/annotated', 10)

    def on_battery(self, msg: BatteryState):
        self.voltage = msg.voltage

    def on_heading(self, msg: Float32):
        self.heading = msg.data

    @staticmethod
    def centre_crop_square(img):
        h, w = img.shape[:2]
        s = min(h, w)
        y0, x0 = (h - s) // 2, (w - s) // 2
        return img[y0:y0 + s, x0:x0 + s].copy()

    def on_image(self, msg: Image):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
        sq = self.centre_crop_square(frame)

        volt = f'{self.voltage:.2f} V' if self.voltage is not None else 'N/A'
        head = f'{self.heading:.1f} deg' if self.heading is not None else 'N/A'
        lines = [f'Battery: {volt}', f'Heading: {head}']

        scale = max(sq.shape[0] / 640.0, 0.4)
        thick = max(1, int(round(2 * scale)))
        font = cv2.FONT_HERSHEY_SIMPLEX
        y = int(30 * scale) + 5
        for text in lines:
            (tw, th), base = cv2.getTextSize(text, font, 0.8 * scale, thick)
            cv2.rectangle(sq, (5, y - th - 5), (5 + tw + 10, y + base), (0, 0, 0), -1)  # backing box
            cv2.putText(sq, text, (10, y), font, 0.8 * scale, (0, 255, 0), thick, cv2.LINE_AA)
            y += int(40 * scale)

        out = self.bridge.cv2_to_imgmsg(sq, encoding='rgb8')
        out.header = msg.header
        self.pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = CameraAnnotator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
