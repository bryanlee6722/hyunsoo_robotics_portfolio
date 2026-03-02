import rclpy
from rclpy.node import Node
import chess
import chess.engine
from std_msgs.msg import String

# 스톡피쉬 엔진 경로 (터미널 which stockfish로 확인 가능)
STOCKFISH_PATH = "/usr/games/stockfish"

class ChessBrain(Node):
    def __init__(self):
        super().__init__('chess_brain')

        self.last_move = None
        self.engine = None

        self.get_logger().info(' 체스 AI 두뇌 가동 중...')

        self.move_publisher = self.create_publisher(String, 'next_move', 10)

        self.notation_sub = self.create_subscription(String, 'notation', self.move_callback, 10)

        # 1. 체스보드 생성(초기화)
        self.board = chess.Board()

        # 2. 스톡피쉬 엔진 연결
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
            self.engine.configure({"Skill Level": 20})
            self.get_logger().info(' 스톡피쉬 엔진 연결 성공!')
        except Exception as e:
            self.get_logger().error(
                f' 스톡피쉬 엔진 초기화 실패 ({STOCKFISH_PATH}): {e}'
            )
            self.engine = None
        
    def move_callback(self,msg):
        # --- 2. 사용자 입력 (HUMAN MOVE) ---
        current_move_str = msg.data.strip()
        self.get_logger().info(f'사용자 입력 수신: {current_move_str}')

        if current_move_str == None or current_move_str == "":
            self.get_logger().info("빈 입력입니다. 무시합니다.")
            return

        # 중복 수 처리: 이전에 처리한 수와 동일하면 무시
        if self.last_move == current_move_str: 
            self.get_logger().info("이미 처리된 수입니다. 무시합니다.")
            return
        
        self.last_move = current_move_str

        if self.board.is_game_over():
            self.get_logger().info("게임이 이미 종료되었습니다.")
            return

        try: 
            # 입력받은 문자 확인
            move = chess.Move.from_uci(current_move_str)
            move_alt = chess.Move.from_uci(self.swap_uci(current_move_str))
            if move in self.board.legal_moves:
                self.board.push(move) #보드에 수 적용
            elif move_alt in self.board.legal_moves:
                self.board.push(move_alt) #보드에 수 적용
            else:
                print("잘못된 수 입니다. 다시 작성해주세요")
                return
            
        except ValueError:
            print(" 잘못된 입력 형식입니다. (예: e2e4)")
            return
        except Exception as e:
            self.get_logger().error(f'수 처리 중 예외 발생: {e}')
            return

        # 게임 종료 체크 (사람이 둔 직후)
        if self.board.is_game_over():
            self.handle_game_over()
            return

        # --- 3. AI 생각 (Stockfish Move) ---
        if self.engine is None:
            self.get_logger().error('엔진이 준비되지 않아 AI 수를 계산할 수 없습니다.')
            return
        print("\n AI가 생각 중입니다...")

        
        #0.1초 동안 생각하고 가장 좋은 수 두기(시간 조절 가능)
        result = self.engine.play(self.board, chess.engine.Limit(time=0.5))
        ai_move = result.move
        ai_move_str = ai_move.uci() # ai_move의 string 버전

        is_capture = self.board.is_capture(ai_move)
        is_castling = self.board.is_castling(ai_move)
        move_type = "move"
        if is_capture:
            move_type = "capture"
        elif is_castling:
            # e > g king side / e > c queen side
            if ai_move_str[2] == 'g':
                move_type = "king_castling"
            else:
                move_type = "queen_castling"
        if len(ai_move_str) == 5:
            move_type = 'promotion'

        msg = String()
        msg.data = f"{ai_move_str}:{move_type}"
        self.board.push(ai_move) #AI 수 적용
        print(f" AI의 선택: {ai_move}")
        self.move_publisher.publish(msg)
        self.get_logger().info(f'이동 명령 전송: {ai_move}(타입: {move_type})')

        # 게임 종료 체크 (AI가 둔 직후)
        if self.board.is_game_over():
            self.handle_game_over()

    def handle_game_over(self):
        outcome = self.board.outcome()
        self.get_logger().info(f"게임 종료! 결과: {outcome.result()} ({outcome.termination.name})")
        # 필요하다면 여기서 게임 종료 메시지를 퍼블리시 할 수도 있음

    @staticmethod
    def swap_uci(move_str: str) -> str:
        if len(move_str) not in (4,5):
            raise ValueError("Invalid UCI move format")
        return move_str[2:4] + move_str[0:2] + (move_str[4:] if len(move_str) == 5 else '')

    def close_engine(self):
        if self.engine is None:
            return
        try:
            self.engine.quit()
        except Exception as e:
            self.get_logger().warn(f'엔진 종료 중 예외 발생: {e}')
        finally:
            self.engine = None
         
            
    
def main(args=None):
    rclpy.init(args=args)
    node = ChessBrain()

    try:
        rclpy.spin(node)
        
    except KeyboardInterrupt:
        # Ctrl+C를 눌렀을 때 조용히 종료
        pass
    except SystemExit:
        pass
    finally:
        # [수정] 안전하게 종료 처리
        node.close_engine()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
