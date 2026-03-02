import cv2
import time
import numpy as np
import rclpy
from std_msgs.msg import Int32

from rclpy.node import Node

class ChessTimer(Node):
    def __init__(self):
        super().__init__('chess_timer')
        self.get_logger().info("Chess Timer Node Initialized")
        
        # [수정 1] int -> Int32로 변경
        # bridge_node로 보냄
        self.timer_pub = self.create_publisher(Int32, 'camera_timer', 10)

        # 게임 설정 변수들을 self로 관리
        self.width, self.height = 800, 600
        self.p1_time = 600.0  # 초 단위 (float)
        self.p2_time = 600.0
        self.current_player = 0  # 0: 대기, 1: P1(Human), 2: P2(AI)
        self.last_tick = time.time()
        self.prev_player = 0

        # GUI 윈도우 생성
        cv2.namedWindow("Chess Timer")
        # 마우스 콜백에 self를 넘겨주기 위해 람다(lambda) 사용 또는 전역 함수 회피
        cv2.setMouseCallback("Chess Timer", self.mouse_callback)

    def mouse_callback(self, event, x, y, flags, param):
        """ 마우스 클릭으로 턴을 변경하는 함수 """
        if event == cv2.EVENT_LBUTTONDOWN:
            if self.current_player == 0:
                self.current_player = 1  # 게임 시작
            else:
                # 화면 왼쪽(P1 영역) 클릭 -> P1 턴 종료 -> P2 턴 시작
                if x < self.width // 2:
                    self.current_player = 2
                # 화면 오른쪽(P2 영역) 클릭 -> P2 턴 종료 -> P1 턴 시작
                else:
                    self.current_player = 1
            
            # 클릭 즉시 로그 출력
            self.get_logger().info(f"Mouse Click Detected -> Turn: {self.current_player}")

    def run(self):
        """ GUI 루프와 ROS 퍼블리시를 담당하는 메인 함수 """
        while rclpy.ok():
            # 1. 배경 초기화
            img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
            # 2. 시간 계산 (dt)
            now = time.time()
            dt = now - self.last_tick
            self.last_tick = now
            
            if self.current_player == 1 and self.p1_time > 0:
                self.p1_time -= dt
            elif self.current_player == 2 and self.p2_time > 0:
                self.p2_time -= dt

            # 3. GUI 그리기 (영역 표시)
            # P1 (왼쪽) 색상
            p1_color = (0, 255, 0) if self.current_player == 1 else (100, 100, 100)
            cv2.rectangle(img, (0, 0), (self.width // 2, self.height), p1_color, -1 if self.current_player == 1 else 3)   
            
            # P2 (오른쪽) 색상
            p2_color = (0, 255, 0) if self.current_player == 2 else (100, 100, 100)
            cv2.rectangle(img, (self.width // 2, 0), (self.width, self.height), p2_color, -1 if self.current_player == 2 else 3)

            # 4. 텍스트 표시
            line_x = 50
            line_y = 200
            
            # Player 1 텍스트
            cv2.putText(img, "CHALLENGER", (line_x, line_y), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
            p1_str = f'{int(self.p1_time // 60):02d}:{int(self.p1_time % 60):02d}'
            cv2.putText(img, p1_str, (line_x, line_y + 60), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 4)

            # Player 2 텍스트
            cv2.putText(img, "AI", (line_x + 400, line_y), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
            p2_str = f'{int(self.p2_time // 60):02d}:{int(self.p2_time % 60):02d}'
            cv2.putText(img, p2_str, (line_x + 400, line_y + 60), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 4)

            cv2.imshow("Chess Timer", img)

            # 5. 키보드 입력 처리
            key = cv2.waitKey(10) # 10ms 대기
            if key == 27:  # ESC 종료
                break   
            elif key == 32: # SPACEBAR 턴 변경
                if self.current_player == 0:
                    self.current_player = 1
                elif self.current_player == 1:
                    self.current_player = 2
                else:
                    self.current_player = 1 
            
            # 6. 턴 변경 감지 및 토픽 전송 (상태가 변했을 때만 전송)
            if self.current_player != self.prev_player:
                if self.current_player != 0:
                    msg = Int32()
                    msg.data = int(self.current_player) # 1 or 2
                    self.timer_pub.publish(msg)
                    self.get_logger().info(f'Turn Changed: {self.current_player} (Published)')
                
                self.prev_player = self.current_player
            
            # [중요] ROS 2 콜백 처리 (이게 없으면 노드가 먹통됨)
            rclpy.spin_once(self, timeout_sec=0.001)

        cv2.destroyAllWindows()

def main(args=None):
    rclpy.init(args=args) 
    node = ChessTimer()
    
    try:
        # 무한 루프는 run() 함수 안에서 돕니다.
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()