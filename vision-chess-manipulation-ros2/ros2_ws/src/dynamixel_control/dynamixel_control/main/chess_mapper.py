import math
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import time


# 체스판 위치 토크 변환 코드
class pos_torque_trans(Node):
    def __init__(self):
        super().__init__('calculator')

        # 로봇 팔 길이 (cm 단위)
        self.L1 = 25.18 #어께-팔꿈치
        self.L2 = 20.05#팔꿈치-손

        #다이나믹셀 설정 (0~1023, 512가 중앙, 1단위 당 0.29도)
        self.CENTER_VAL = 512
        self.DEG_PER_UNIT = 0.293

        # 자로 크기 입력
        self.SQUARE_SIZE_Y = 4.25 # 체스 한 칸의 가로4.25
        self.SQUARE_SIZE_X = 4.20 # 체스 한 칸의 세로길이4.2

        # 로봇 어깨 중심(0,0)에서 체스판의 a1까지의 길이
        self.OFFSET_X = 11.05 # 로봇 앞쪽으로 얼마나 먼지 2.55 + 8.5
        self.OFFSET_Y = -17 #로봇 중심선에서 얼마나 좌/우로 치우쳤는지

        #chess_brain.py로부터 next_move 토픽을 string형태로 받음
        self.subscription = self.create_subscription(
            String,
            'next_move',
            self.get_motor_angle,
            10)

        #chess_mapper.py에서 motor_torque 토픽을 Int형태로 motor_publisher로 보냄
        self.publisher_ = self.create_publisher(
            String, 
            "motor_torque",
            10)
        
    # 계산기
    def calculate(self, square_name):
    
        col_idx = ( ord(square_name[0]) - ord('a') )
        row_idx = 7 - ( int(square_name[1]) - 1 )

        # 공식: 시작점 + (칸 개수 * 칸 크기) + (칸 크기 / 2)
        x = self.OFFSET_X + (row_idx * self.SQUARE_SIZE_X) + (self.SQUARE_SIZE_X / 2)
        y = self.OFFSET_Y + (col_idx * self.SQUARE_SIZE_Y) + (self.SQUARE_SIZE_Y / 2)


        print(f"목표 좌표: x={x: .2f}cm, y={y: .2f}cm")
        
        distance = math.sqrt(x**2 + y**2)

        #임시방편으로 만든 오류가 났을때 모터 토크 
        error_val = 512

        # 도달 불가능한 영역 체크 (팔이 짧거나, 몸쪽이거나)
        if distance > (self.L1 + self.L2):
            print(f"도달 불가: 너무 멉니다! (거리: {distance: .2f}cm)")
            return error_val, error_val

        if distance == 0:
            print("도달 불가: 원점입니다.")
            return error_val, error_val
        
        # 코사인 법칙을 이용한 역기구학
        try:
            cos_angle2 = (x**2 + y**2 - self.L1**2 - self.L2**2) / (2 * self.L1 * self.L2)
            cos_angle2 = max(-1.0, min(1.0, cos_angle2))

            # 2번 모터(팔꿈치)의 각도(라디안)
            theta2 = math.acos(cos_angle2)

            # 1번 모터(어깨)의 각도(라디안)
            #alpha : 원점과 목표점을 잇는 직선의 각도
            #beta : 그 직선과 첫 번째 팔 사이의 각도
            alpha = math.atan2(y, x)
            beta = math.acos((x**2 + y**2 + self.L1**2 - self.L2**2) / (2*self.L1*math.sqrt(x**2 + y**2)))

            theta1 = alpha - beta # 오른팔

        except ValueError:
            print("계산 오류(수학적 도달 불가)")
            return error_val, error_val
        
        # 라디안 -> 도(Degree)로 변환
        # deg: 0~150?
        deg1 = math.degrees(theta1) - 45
        deg2 = math.degrees(theta2)
        print(f"계산된 각도: 모터1: {deg1: .2f}도, 모터2: {deg2: .2f}도")

        # 512를 0도로 기준 잡고 모터변환
        val1 = int(self.CENTER_VAL + (deg1 / self.DEG_PER_UNIT))
        val2 = int(self.CENTER_VAL + (deg2 / self.DEG_PER_UNIT))

        return val1, val2

    def get_motor_angle(self, msg):

        # 좌표로 변환
        # 가로 세로 숫자로 변환
        # ord('a')는 97입니다. 따라서 'a' -> 0 ,'b' -> 1
        move_str = msg.data
        start_square_name = move_str[:2]#앞 2글자자
        end_square_name = move_str[2:4]#뒤 2글자
        move_type = move_str[5:]
        start_rook_val1, start_rook_val2, end_rook_val1, end_rook_val2 = 0,0,0,0

        if move_type == 'king_castling':
            start_rook_val1, start_rook_val2 = self.calculate(f"{'h'}{move_str[1]}")
            end_rook_val1, end_rook_val2 = self.calculate(f"{'f'}{move_str[1]}")
        elif move_type == 'queen_castling':
            start_rook_val1, start_rook_val2 = self.calculate(f"{'a'}{move_str[1]}")
            end_rook_val1, end_rook_val2 = self.calculate(f"{'d'}{move_str[1]}")

        start_val1, start_val2 = self.calculate(start_square_name)
        end_val1, end_val2 = self.calculate(end_square_name)

        msg = String()
        msg.data = f"{start_val1}, {start_val2}, {end_val1}, {end_val2}, {move_type}, {start_rook_val1}, {start_rook_val2}, {end_rook_val1}, {end_rook_val2}"
        self.publisher_.publish(msg)
        self.get_logger().info(f"motor_publisher로 전송 : {msg.data}")
        

def main(args=None):
    rclpy.init(args=args)
    node = pos_torque_trans()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
        

   