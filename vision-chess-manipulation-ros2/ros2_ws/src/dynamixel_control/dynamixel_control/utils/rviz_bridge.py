import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray
from sensor_msgs.msg import JointState
import math

class RvizBridge(Node):
    def __init__(self):
        super().__init__('rviz_bridge')

        self.joint_names = ['shoulder_revolute_joint', 'motor_joint', 'arm_joint', 'hand_revolute_joint']

        self.current_rads = [0.0] * 4

        # 3. subcription (motor_publisher 노드로부터 모터 위치 데이터 수신)
        self.sub = self.create_subscription(
            Int32MultiArray,
            'set_position_array',
            self.motor_callback,
            10)
        
        # 4. 발행 (Rviz에게 조인트 상태 보고)
        self.pub = self.create_publisher(JointState, 'joint_states', 10)

        # 5. 주기적 발행(30Hz)
        self.timer = self.create_timer(0.033, self.publish_joint_state)

        self.get_logger().info('Rviz브릿지 노드 시작')

    def convert_value_to_radian(self, value):
        """Dynamixel 모터의 값을 라디안으로 변환하는 함수"""
        # Dynamixel 모터의 값 설정
        CENTER_VALUE = 512  
        UNIT_DEGREE = 0.293    
        
        # 라디안으로 변환
        degree = (value - CENTER_VALUE) * UNIT_DEGREE
        radian = degree * (math.pi / 180.0)
        self.get_logger().info(f'{degree} -> {radian}')
        return radian

    def motor_callback(self, msg):
        raw_data = msg.data 

        if len(raw_data) < 4:
            return
        
        for i in range(4):

            new_rad = self.convert_value_to_radian(raw_data[i])
            
            if new_rad is not None:
                self.current_rads[i] = new_rad

    def publish_joint_state(self):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = self.joint_names
        msg.position = self.current_rads

        self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = RvizBridge()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__name__':
    main()