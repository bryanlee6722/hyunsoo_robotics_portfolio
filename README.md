# hyunsoo_robotics_portfolio

## Main Contents
해당 레포지토리는 다음의 두 프로젝트의 내용을 담고 있습니다: 

1. Vision Based Chess Manipulation Using SCARA Hardware:

   카메라 정보를 받아들여 사용자의 체스 동작을 인식하고 자동으로 다음 수를 계산한 후, 이를 하드웨어가 구현하는 파이프라인입니다.
   전체 파이프라인 구현, 세부 코드 구현에 기여하였습니다.

   세부사항의 경우 vision-chess-manipulation-ros2/docs/pipeline.md에 정리하였습니다.
   
2. Teleoperation Leader Arm:

   로봇 상체 Teleoperation Pipeline의 Leader Arm 코드입니다.
   Leader Arm으로부터의 엔코딩 값을을 각도로 변환 한 후, 이에 필터를 적용하고 Calibration을 적용하였습니다. 전체 노드 및 세부 기능 구현에 기여하였습니다. 

   세부사항의 경우 teleop-leader-arm-ros2/docs/pipeline.md에 정리하였습니다.


# Vision Chess Manipulation

## Pipeline
1. `camera_node`가 `raw_camera_image`를 발행합니다.
2. `camera_bridge_node`가 보드 보정을 수행하고 사용자 착수 결과를 `notation`으로 발행합니다.
3. `detection_node`는 추가 비전 처리를 위해 `detection_results`(빨간 점의 픽셀 위치)를 선택적으로 발행합니다.
4. `chess_brain`이 다음 수를 계산하여 `next_move`를 발행합니다.
5. `chess_mapper`가 체스 수를 모터 명령으로 변환하여 `motor_torque`를 발행합니다.
6. `motor_publisher`가 이를 `set_position_array` 형식으로 변환합니다.
7. `motor_node`가 다이나믹셀 명령으로 실제 동작을 수행합니다.

## Details of Each Node
1. `camera_node`
   - 카메라를 열고(`camera_device` + fallback 인덱스), 약 30 FPS로 프레임을 수집합니다.
   - 필요 시 `90도` 반시계 회전(`rotate_90_ccw`)을 적용합니다.
   - `sensor_msgs/Image`를 `raw_camera_image` Topic으로 Publish합니다.
2. `chess_timer`
   - 턴 전환을 위한 OpenCV 타이머 UI를 제공합니다.
   - 턴이 바뀔 때만 `camera_timer`로 `std_msgs/Int32`를 Publish합니다 (`1`: 사람, `2`: AI).
3. `camera_bridge_node`
   - `raw_camera_image`, `camera_timer`를 Subscribe합니다.
   - 턴 단계 이벤트에서 보드 보정, 이전/이후 보드 크롭 저장, 칸 단위 비교를 수행합니다.
   - 사람의 착수를 UCI 문자열로 `notation`에 Publish합니다 (예: `e2e4`, 캐슬링: `e1g1`/`e1c1`).
4. `chess_brain`
   - `notation`을 Subscribe하고, `python-chess` 보드 상태 기준으로 유효성을 검사합니다.
   - Stockfish(`/usr/games/stockfish`)로 AI 수를 계산합니다.
   - `next_move`를 `uci:move_type` 형식으로 Publish합니다 (예: `e7e5:move`, `e1g1:king_castling`).
5. `chess_mapper`
   - `next_move`를 Subscribe하여 체스 좌표를 평면 XY로 변환한 뒤 IK 기반 모터 값으로 계산합니다.
   - `move`, `capture`, `king_castling`, `queen_castling`, `promotion` 유형을 처리합니다.
   - 동작 명령 문자열 `motor_torque`를 Publish합니다.
6. `motor_publisher`
   - `motor_torque`를 Subscribe해 단계별 `Int32MultiArray` 자세 시퀀스로 변환합니다.
   - 저수준 관절 목표를 `set_position_array`로 Publish합니다.
   - `moving_array` 피드백으로 단계 사이 대기를 수행합니다 (`send_command` + `wait_motor`).
7. `motor_node`
   - `set_position_array`를 Subscribe하여 AX-12 드라이버로 목표 위치를 전송합니다.
   - 모터 동작 상태를 `moving_array`(bool)로 Publish합니다.
   - 하드웨어 연결 실패 시 더미(시뮬레이션 유사) 모드를 지원합니다.

## Filters and Calibration
1. Board to Camera Calibration (`dynamixel_control/utils/calibration.py`)
   - `detect_edges`: Gray Scaling -> Gaussian Blur -> Canny Edge Detection 순으로 처리합니다.
   - `find_outer_corners`: 윤곽선 기반으로 바깥 모서리를 찾고 TL/TR/BR/BL 순서로 정렬합니다.
   - `create_transformation_matrix`: 자동/수동 코너 기반 원근 변환 행렬을 생성합니다.
   - `apply_transformation`: 이미지를 보정된 Top-View 형태로 워핑합니다.
2. 수동 Calibration (`camera_bridge_node`)
   - `manual_corners` 파라미터를 지원합니다 (`[TLx,TLy, TRx,TRy, BRx,BRy, BLx,BLy]`).
   - 설정 시 초기 단계에서 사용자 클릭 기반 코너 선택도 지원합니다.
   - 보정된 보드 중심 행렬과 변환 데이터를 YAML(`board_yaml_path`)에 저장합니다.

## Video

https://github.com/user-attachments/assets/836d1f97-f6c7-40a2-acc7-006d7f06512f



2. Teleoperation:



https://github.com/user-attachments/assets/0006c42c-5d85-43ac-bec1-fccc3eb352a0

