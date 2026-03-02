import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray, Bool
from dynamixel_control.utils.ax12_driver import AX12Driver
import time

class MotorSubscriber(Node):
    def __init__(self):
        super().__init__('motor_node')
        # 1번: 몸통 / 2번: 어깨 / 3번: 팔 / 4번: 그리퍼
        self.motor_ids =[1, 5, 3, 16]

        # 1. 라이브러리 객체 생성 (나중에 포트 수정을 여기서)
        self.driver = AX12Driver(port_name='/dev/ttyUSB_DEVICE')
        self.is_connected = False
        
        # 2. 하드웨어 연결 시도
        try:
            if self.driver.connect():
                self.get_logger().info('Port Connected Successfully!')
                for motor_id in self.motor_ids:
                    self.driver.motor_id = motor_id
                    self.driver.set_torque(True, motor_id)
                    self.get_logger().info(f'Motor ID {motor_id} Torque ON')
                self.is_connected = True
            else:
                self.get_logger().error('Failed to connect to Motor.')
        except Exception as e:
            # 보드가 없어서 에러가 나면 이쪽으로 옵니다.
            self.get_logger().warn(f' Connection Error: {e}')
            self.get_logger().warn(' 하드웨어 없음: 가상 모드(Dummy Mode)로 실행합니다.')
            self.is_connected = False # 연결 실패 표시

        # 3.Subscriber 생성 (motor_publisher에서 받음, 토픽 이름: /set_position_array)
        # 터미널에서 'ros2 topic pub --once /set_position_array std_msgs/msg/Int32MultiArray "{data: [500, 500, 500, 500]}"' 명령으로 제어 가능
        self._subscription = self.create_subscription(
            Int32MultiArray,
            'set_position_array',
            self.listener_callback,
            10)
        
        # motor_publisher로 모터가 움직이고 있는지 보냄
        self.moving_pub = self.create_publisher(Bool, 'moving_array', 10)

        # self.timer = self.create_timer(0.1, self.check_moving_status)
        
    #메시지가 들어오면 실행되는 함수
    def listener_callback(self, msg):

        target_pos = msg.data

        if len(target_pos) != len(self.motor_ids):
            self.get_logger().warn(f'데이터 개수 불일치! (필요 : {len(self.motor_ids)}개 / 받음 : {len(target_pos)})')
            return
        self.get_logger().info(f'Moving Motors: ID{self.motor_ids} -> Pos {target_pos}') 
        
        # 연결되어 있을 때만 실제로 모터를 움직임
        if self.is_connected:
            for i, target_position in enumerate(target_pos):
                current_motor_id = self.motor_ids[i]
                    
                self.driver.motor_id = current_motor_id
                self.driver.set_position(target_position, self.driver.motor_id)

                #안정성을 위한 짧은 딜래이
                # time.sleep(0.005)
        else:
            # 연결 안 되어 있으면 로그만 출력 (가짜 동작)
            for i, target_position in enumerate(target_pos):
                self.get_logger().info(f'[Simulation] ID {self.motor_ids[i]} -> {target_position} 이동')


    def check_moving_status(self):
        """ 주기적으로 모든 모터를 검사해서 상태 보고 """
        if not self.is_connected:
            return

        is_any_moving = False
        
        # 모든 모터를 돌면서 하나라도 움직이는지 확인
        for motor_id in self.motor_ids:
            # AX12Driver의 check_moving이 True/False를 반환한다고 가정
            if self.driver.check_moving(motor_id):
                is_any_moving = True
                break # 하나라도 움직이면 더 볼 필요 없음
        
        # 결과 전송 (Bool)
        msg = Bool()
        msg.data = is_any_moving
        self.moving_pub.publish(msg)
        self._logger.info(f'Moving Status Published: {msg.data}')

def main(args=None):
    rclpy.init(args=args)
    node = MotorSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # 종료 시 안전하게 토크 끄고 닫기
        if hasattr(node, 'is_connected') and node.is_connected:
            for motor_id in node.motor_ids:
                node.driver.motor_id = motor_id
                node.driver.set_torque(False, node.driver.motor_id)
            node.driver.close()

        node.destroy_node()
        rclpy.shutdown()

    if __name__ == '__main__':
        main()