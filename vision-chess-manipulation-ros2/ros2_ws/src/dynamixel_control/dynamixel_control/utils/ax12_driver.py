import os
from turtle import speed
from dynamixel_sdk import *

class AX12Driver:
    def __init__(self, port_name):
        # AX-12A 프로토콜 설정
        self.PROTOCOL_VERSION = 1.0
        
        # 주소값 (Control Table)
        self.ADDR_TORQUE_ENABLE = 24
        self.ADDR_GOAL_POSITION = 30
        self.ADDR_PRESENT_POSITION = 36
        self.ADDR_MOVING_SPEED = 32
        self.ADDR_PRESENT_SPEED = 38
        self.ADDR_MOVING = 46

        # 포트 및 패킷 핸들러 초기화
        self.portHandler = PortHandler(port_name)
        self.packetHandler = PacketHandler(self.PROTOCOL_VERSION)

        self.baudrate = 1000000
        self.is_connected = False    

    def connect(self):
        """통신 연결"""
        if self.portHandler.openPort():
            print("Succeeded to open the port")
        else:
            print("Failed to open the port")
            return False
        
        if self.portHandler.setBaudRate(self.baudrate):
            print("Succeeded to change the baudrate")
        else:
            print("Failed to change the baudrate")
            return False
        
        self.is_connected = True
        return True
    
    def set_torque(self, enable, motor_id):
        """토크 켜기/끄기"""
        if not self.is_connected: return
        val = 1 if enable else 0
        self.packetHandler.write2ByteTxRx(self.portHandler, motor_id, self.ADDR_TORQUE_ENABLE, val)

    def set_position(self, position, motor_id):
        """목표 위치로 이동 (0 ~ 1023)"""
        if not self.is_connected: return
        self.motor_speed = 63
        if motor_id == 1:  # 1번 모터는 몸통
            self.motor_speed = 200
        #모터 속도 조정
        self.packetHandler.write2ByteTxRx(self.portHandler, motor_id, self.ADDR_MOVING_SPEED, self.motor_speed)

        #안전 범위 제한
        position = max(0, min(1023, position))
        self.packetHandler.write2ByteTxRx(self.portHandler, motor_id, self.ADDR_GOAL_POSITION, position)

    def check_moving(self, motor_id):
        """모터가 움직이고 있는지 확인"""
        if not self.is_connected: return False

        moving_status, result, error= self.packetHandler.read1ByteTxRx(self.portHandler, motor_id, self.ADDR_MOVING)
        
        if result != COMM_SUCCESS:
            return False
        elif error != 0:
            return False
        # print(f"모터 ID {motor_id} 이동 상태: {moving_status}")

        if moving_status == 1:
            return True
        else:
            return False

    def close(self):
        """포트 닫기"""
        self.portHandler.closePort()