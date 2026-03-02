import rclpy
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup # 👈 추가 필수!
from rclpy.executors import MultiThreadedExecutor
from std_msgs.msg import String, Int32MultiArray, Bool
# dynamixel 연결 해서 모터가 가동되는지 알기위한 불러오기
import sys
import time


class MotorPublisher(Node):
    def __init__(self):
        super().__init__('motor_publisher')

        self.callback_group = ReentrantCallbackGroup()

        self.is_moving = False
        
        # 1. Publisher 생성 (motor_node로 보냄 토픽 이름이 Subscriber와 같아야함: /set_position_array)
        self.publisher_ = self.create_publisher(
            Int32MultiArray, 
            'set_position_array', 
            10)
        self.get_logger().info(' 로봇팔 제어가 시작되었습니다. ')

        # 2. subscription 생성 chess_mapper.py로부터 motor_torque 토픽을 Int형태로 받음
        self.subscription_ = self.create_subscription(
            String, 
            "motor_torque",
            self.move_callback,
            10,
            callback_group=self.callback_group)
        
        self.moving_sub = self.create_subscription(
            Bool,
            "moving_array",
            self.moving_callback,
            10,
            callback_group=self.callback_group)
        
    def motor(self, positions):
        """입력받은 위치 리스트를 퍼블리시하는 함수"""       
        msg = Int32MultiArray()
        msg.data = positions
        self.publisher_.publish(msg)
        self.get_logger().info(f' 명령 전송: {positions}')

    def moving_callback(self, msg):
        """모터가 움직이고 있는지 확인하는 함수""" 
        self.get_logger().info(f'모터 이동 상태 수신: {msg.data}') 
        self.is_moving = msg.data

    def wait_motor(self):
        """모터가 움직이는 것을 기다리는 함수"""  
        # 잠깐 기다려서 안정성 확보
        start_timeout = 2.0  # 출발 신호(True)가 올 때까지 기다리는 시간
        move_timeout = 5.0   # 동작이 완료될 때까지 기다리는 시간
        start_time = time.time()
        self.get_logger().info(f'현 상태 : {self.is_moving} ')

        while not self.is_moving:
            time.sleep(0.05) # is_moving 값을 바꿀 때까지 잠시 대기                
            # 만약 1초가 지나도 True가 안 오면? (이미 도착했거나 통신 문제)
            # 상황에 따라 break 하거나 계속 기다림
            if time.time() - start_time > start_timeout:
                self.get_logger().warn('경고: 모터가 움직임 시작 신호를 안 보냄 (또는 이미 완료됨)')
                break 

        # 로봇이 움직이는 동안 무한 루프
        move_start_time = time.time()

        while self.is_moving:
        # 중요: 이 코드가 있어야 대기하는 동안에도 다른 메시지를 수신함
            rclpy.spin_once(self, timeout_sec=0.05)
            self.get_logger().info(' 모터 동작 중... ')
            if time.time() - move_start_time > move_timeout:
                self.get_logger().warn('시간 초과! 강제로 다음 명령 진행')
                break

        self.get_logger().info('--> 동작 완료. 다음 명령 진행.')

            

    def send_command(self, position):
        """모터를 지정된 각도로 움직이게 하는 함수"""  
        self.get_logger().info(f'send command 입력')
        self.motor(position)
        self.wait_motor()

    def move_callback(self, msg):
        data_list = msg.data.split(',')
        command = [int(data_list[0]),
                    int(data_list[1]),
                    int(data_list[2]),
                    int(data_list[3]),
                    data_list[4].strip(),
                    int(data_list[5]),
                    int(data_list[6]),  
                    int(data_list[7]),
                    int(data_list[8])]
        self.get_logger().info(f'받은 위치 값 {command}')
        
        ###### 높이가 1010 -> 위(up), 0 -> 아래(down),
        ###### 그리퍼가 512 -> 열림(open), 0 -> 닫힘(close)
        # 기본적인 행동
        up = 810
        down = 91
        open = 416
        close = 512
        neutral_shoulder = 700 # 중립 위치의 어깨 관절 값
        neutral_arm = 1000  # 중립 위치의 어깨 관절 값
        queen_pos_shoulder = 10  # 퀸 놓여있는 위치의 어깨 관절 값
        queen_pos_arm = 10       # 퀸 놓여있는 위치의 팔 관절 값
        capture_pos_shoulder = 800  # 캡쳐 위치의 어깨 관절 값
        capture_pos_arm = 1200      # 캡쳐 위치의 팔 관절 값
        firstmove = True # 첫 번째 행동인지 체크하는 변수


        if command[4] == 'move':
            self.get_logger().info(f'타입{command[4]}')
            ##첫번째 행동일때 모터 초기 상태로 이동하는거 필요할듯
            if firstmove == True:
                position = [up, neutral_shoulder, neutral_arm, open]
                self.send_command(position)
                firstmove = False
            # 1. 첫번째 위치 이동
            position = [up, command[0], neutral_arm, open]
            self.send_command(position)
            position = [up, command[0], command[1], open]
            self.send_command(position)
            # 2. 몸통 내리기
            position = [down, command[0], command[1], open]
            self.send_command(position)
            # 3. 그리퍼 닫기
            position = [down, command[0], command[1], close]
            self.send_command(position)
            # 4. 몸통 올리기
            position = [up, command[0], command[1], close]
            self.send_command(position)
            # 5. 두번째 위치 이동
            position = [up, neutral_shoulder, neutral_arm, close]
            self.send_command(position)
            position = [up, command[2], neutral_arm, close]
            self.send_command(position)   
            position = [up, command[2], command[3], close]
            self.send_command(position)
            # 6. 몸통 내리기
            position = [down, command[2], command[3], close]
            self.send_command(position)  
            # 7. 그리퍼 열기
            position = [down, command[2], command[3], open]
            self.send_command(position)
            # 8. 몸통 올리기
            position = [up, command[2], command[3], open]
            self.send_command(position)
            # 9. 초기 상태 이동
            position = [up, neutral_shoulder, command[3], open]
            self.send_command(position)
            position = [up, neutral_shoulder, neutral_arm, open]
            self.send_command(position)

        elif command[4] == 'capture':
            self.get_logger().info(f'타입{command[4]}')
            # 잡힐 기물 위치로 이동
            position = [up, command[2], neutral_arm, open]
            self.send_command(position)
            position = [up, command[2], command[3], open]
            self.send_command(position)
            # 몸통내리기
            position = [down, command[2], command[3], open]
            self.send_command(position)
            # 그리퍼 닫기 
            position = [down, command[2], command[3], close]
            self.send_command(position)
            # 몸통올리기
            position = [up, command[2], command[3], close]
            self.send_command(position)
            # 버리는 자리 이동
            position = [up, capture_pos_shoulder, command[3], close]
            self.send_command(position)
            position = [up, capture_pos_shoulder, capture_pos_arm, close]
            self.send_command(position)
            # 놓기
            position = [up, capture_pos_shoulder, capture_pos_arm, open]
            self.send_command(position)
            # 1. 첫번째 위치 이동
            position = [up, command[0], capture_pos_arm, open]
            self.send_command(position)
            position = [up, command[0], command[1], open]
            self.send_command(position)
            # 2. 몸통 내리기
            position = [down, command[0], command[1], open]
            self.send_command(position)
            # 3. 그리퍼 닫기
            position = [down, command[0], command[1], close]
            self.send_command(position)
            # 4. 몸통 올리기
            position = [up, command[0], command[1], close]
            self.send_command(position)
            # 5. 두번째 위치 이동
            position = [up, neutral_shoulder, neutral_arm, close]
            self.send_command(position)
            position = [up, command[2], neutral_arm, close]
            self.send_command(position)
            position = [up, command[2], command[3], close]
            self.send_command(position)
            # 6. 몸통 내리기
            position = [down, command[2], command[3], close]
            self.send_command(position)  
            # 7. 그리퍼 열기
            position = [down, command[2], command[3], open]
            self.send_command(position)
            # 8. 몸통 올리기
            position = [up, command[2], command[3], open]
            self.send_command(position)
            # 9. 초기 상태 이동
            position = [up, neutral_shoulder, command[3], open]
            self.send_command(position)
            position = [up, neutral_shoulder, neutral_arm, open]
            self.send_command(position)

        elif command[4] in ['king_castling','queen_castling']:
            self.get_logger().info(f'타입{command[4]}')            
            # 1. 첫번째 위치 이동
            position = [up, command[0], neutral_arm, open]
            self.send_command(position)
            position = [up, command[0], command[1], open]
            self.send_command(position)
            # 2. 몸통 내리기
            position = [down, command[0], command[1], open]
            self.send_command(position)
            # 3. 그리퍼 닫기
            position = [down, command[0], command[1], close]
            self.send_command(position)
            # 4. 몸통 올리기
            position = [up, command[0], command[1], close]
            self.send_command(position)
            # 5. 두번째 위치 이동
            position = [up, command[2], command[1], close]
            self.send_command(position)
            position = [up, command[2], command[3], close]
            self.send_command(position)
            # 6. 몸통 내리기
            position = [down, command[2], command[3], close]
            self.send_command(position)  
            # 7. 그리퍼 열기
            position = [down, command[2], command[3], open]
            self.send_command(position)
            # 8. 몸통 올리기
            position = [up, command[2], command[3], open]
            self.send_command(position)
            # 10. 룩 첫번째 위치 이동
            position = [up, command[5], command[3], open]
            self.send_command(position)
            position = [up, command[5], command[6], open]
            self.send_command(position)
            # 11. 몸통 내리기
            position = [down, command[5], command[6], open]
            self.send_command(position)
            # 12. 그리퍼 닫기
            position = [down, command[5], command[6], close]
            self.send_command(position)
            # 13. 몸통 올리기
            position = [up, command[5], command[6], close]
            self.send_command(position)
            # 14. 룩 두번째 위치 이동
            position = [up, command[7], command[6], close]
            self.send_command(position)
            position = [up, command[7], command[8], close]
            self.send_command(position)
            # 15. 몸통 내리기
            position = [down, command[7], command[8], close]
            self.send_command(position)
            # 16. 그리퍼 열기
            position = [down, command[7], command[8], open]
            self.send_command(position)
            # 17. 몸통 올리기
            position = [up, command[7], command[8], open]
            self.send_command(position)
            # 18. 초기 상태 이동
            position = [up, neutral_shoulder, command[8], open]
            self.send_command(position)
            position = [up, neutral_shoulder, neutral_arm, open]
            self.send_command(position)

        elif command[4] == ':promotion':
            self.get_logger().info(f'타입{command[4]}')
            # 1. 첫번째 위치 이동
            position = [up, command[0], neutral_arm, open]
            self.send_command(position)
            position = [up, command[0], command[1], open]
            self.send_command(position)
            # 2. 몸통 내리기
            position = [down, command[0], command[1], open]
            self.send_command(position)
            # 3. 그리퍼 닫기
            position = [down, command[0], command[1], close]
            self.send_command(position)
            # 4. 몸통 올리기
            position = [up, command[0], command[1], close]
            self.send_command(position)
            # 5. 두번째 위치 이동
            position = [up, neutral_shoulder, neutral_arm, close]
            self.send_command(position)
            position = [up, command[2], neutral_arm, close]
            self.send_command(position)
            position = [up, command[2], command[3], close]
            self.send_command(position)
            # 6. 몸통 내리기
            position = [down, command[2], command[3], close]
            self.send_command(position)  
            # 7. 그리퍼 열기
            position = [down, command[2], command[3], open]
            self.send_command(position)
            # 8. 몸통 올리기
            position = [up, command[2], command[3], open]
            self.send_command(position)
            # 9. 몸통 내리기
            position = [down, command[2], command[3], open]
            self.send_command(position)
            # 10. 그리퍼 닫기
            position = [down, command[2], command[3], close]
            self.send_command(position)
            # 11. 몸통 올리기
            position = [up, command[2], command[3], close]
            self.send_command(position)
            # 12. 버리는 위치로 이동
            position = [up, capture_pos_shoulder, command[3], close]
            self.send_command(position)
            position = [up, capture_pos_shoulder, capture_pos_arm, close]
            self.send_command(position)
            # 13. 놓기
            position = [up, capture_pos_shoulder, capture_pos_arm, open]
            self.send_command(position)

            # 14. 퀸 놓여있는 위치로 이동
            # 이거 퀀 놔둘 위치의 토크값을 알아서 찾아서 바꾸기
            ##########################################################
            position = [up, queen_pos_shoulder, capture_pos_arm, open]
            self.send_command(position)
            position = [up, queen_pos_shoulder, queen_pos_arm, open]
            self.send_command(position)
            # 15.몸통 내리기
            position = [down, queen_pos_shoulder, queen_pos_arm, open]
            self.send_command(position)
            # 16. 그리퍼 닫기
            position = [down, queen_pos_shoulder, queen_pos_arm, close]
            self.send_command(position)
            # 17. 몸통 올리기
            position = [up, queen_pos_shoulder, queen_pos_arm, close]
            self.send_command(position)
            ##########################################################
            # 18. 두번째 위치 이동x
            position = [up, command[2], queen_pos_arm, close]
            self.send_command(position)
            position = [up, command[2], command[3], close]
            self.send_command(position)
            # 19. 몸통 내리기
            position = [down, command[2], command[3], close]
            self.send_command(position)  
            # 20. 그리퍼 열기
            position = [down, command[2], command[3], open]
            self.send_command(position)
            # 21. 몸통 올리기
            position = [up, command[2], command[3], open]
            self.send_command(position)
            # 22. 초기 상태로 이동
            position = [up, neutral_shoulder, command[3], open]
            self.send_command(position)
            position = [up, neutral_shoulder, neutral_arm, open]
            self.send_command(position)
            

def main(args=None):
    rclpy.init(args=args)
    
    motor_publisher = MotorPublisher()
    
    # [핵심 4] 멀티스레드 실행기 사용
    # 스레드 2개 이상을 사용하여 콜백을 동시에 처리하게 함
    executor = MultiThreadedExecutor()
    executor.add_node(motor_publisher)

    try:
        executor.spin() # rclpy.spin(node) 대신 이걸 사용!
    except KeyboardInterrupt:
        pass
    finally:
        motor_publisher.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()