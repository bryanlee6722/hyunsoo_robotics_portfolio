# hyunsoo_robotics_portfolio

## Main Contents
해당 repository는 Kane's Dynamics Based QP-WBC, Chess Robot Manipulation, Teleoperation 관련 프로젝트를 정리한 개인 portfolio입니다.
각 프로젝트에는 전체 control 및 software pipeline과 주요 구현 내용을 요약하였습니다.

해당 레포지토리는 다음의 세 프로젝트의 내용을 담고 있습니다: 

1. Kane's Dynamics Based Quadruped Robot QP-WBC (Quadratic Programming-Based Whole-Body Control)

   MuJoCo 환경에서 contact constraint를 Kane's Method 기반 independent generalized speed로 모델링하고, 이를 reduced-dimension QP-WBC에 적용하였습니다.
   Conventional WBC와 computation time을 비교하였으며, 전체 control pipeline 구현과 dynamics/QP formulation의 수식 전개에 기여하였습니다.

2. Vision Based Chess Manipulation Using SCARA Hardware:

   Camera-based chess recognition, move generation, motor mapping을 ROS2 pipeline으로 통합하여 SCARA robot이 사용자의 행동에 대응하도록 구현하였습니다.
   전체 pipeline 및 주요 node 구현에 기여하였습니다.
   
3. Teleoperation Leader Arm:

   Leader Arm의 Dynamixel encoder data를 joint angle로 변환하고 filtering 및 calibration을 적용하여 follower arm용 joint-state를 생성하는 ROS2 pipeline을 구현하였습니다.
   전체 node 및 주요 signal-processing 기능 구현에 기여하였습니다.

# Kane's Dynamics Based QP-WBC

## Pipeline

<div align="center">
  <figure>
    <img src="https://github.com/user-attachments/assets/71ebcf47-8d26-4e13-8889-412bfb6e0162" width="100%">
    <figcaption><b>[Figure 1]</b> Kane-based MPC-WBC Pipeline</figcaption>
  </figure>
</div>

<br>

1. 상위 MPC에서 robot의 desired base motion과 contact mode를 생성합니다.
2. 현재 stance contact를 기준으로 contact Jacobian을 계산하고, null-space basis를 구성합니다.
3. Generalized velocity를 표현하여 active contact constraint를 만족하는 independent generalized speed를 정의합니다.
4. Full rigid-body dynamics를 contact-consistent subspace로 projection하여 reduced dynamics를 구성합니다.
5. Reduced generalized acceleration과 joint torque를 decision variable로 하는 QP-WBC를 구성합니다.
6. QP에서 reduced dynamics와 actuator limit을 hard constraint로 적용하고, base tracking, swing-foot tracking의 task를 최적화합니다.
7. Contact force는 independent decision variable로 사용하지 않고 dynamics로부터 reconstruction하여 friction 및 unilateral contact feasibility를 확인합니다.
8. 최적화된 joint torque를 MuJoCo robot에 입력하고, conventional WBC와 동일한 locomotion condition에서 tracking performance와 computation time을 비교합니다.

## Images

<div align="center">
  <figure>
    <img src="https://github.com/user-attachments/assets/838492c8-dd61-4729-a851-00fdab19988f" width="100%">
    <figcaption><b>[Figure 2]</b> Quadruped Locomotion Simulation</figcaption>
  </figure>
</div>

<br>

MuJoCo 환경에서 conventional WBC와 Kane-based WBC를 동일한 robot model과 trotting condition으로 비교하였습니다.

<br>

<div align="center">
  <figure>
    <img src="https://github.com/user-attachments/assets/e2fc66e5-b308-4e2e-84f4-e0020619cf71" width="100%">
    <figcaption><b>[Figure 3]</b> Total WBC Cycle Time Comparison</figcaption>
  </figure>
</div>

<br>

Kane-based reduced formulation을 적용함으로써 평균 WBC cycle time이 2.7252 ms에서 2.1351 ms로 감소하여, dimension reduction이 전체 control-loop computation time 감소로 이어짐을 확인하였습니다.

# Vision Chess Manipulation

## Pipeline
1. `camera_node`가 `raw_camera_image`를 발행합니다.
2. `camera_bridge_node`가 보드 보정을 수행하고 사용자 착수 결과를 `notation`으로 발행합니다.
3. `detection_node`는 추가 비전 처리를 위해 `detection_results`(빨간 점의 픽셀 위치)를 선택적으로 발행합니다.
4. `chess_brain`이 다음 수를 계산하여 `next_move`를 발행합니다.
5. `chess_mapper`가 체스 수를 모터 명령으로 변환하여 `motor_torque`를 발행합니다.
6. `motor_publisher`가 이를 `set_position_array` 형식으로 변환합니다.
7. `motor_node`가 다이나믹셀 명령으로 실제 동작을 수행합니다.

## Video

https://github.com/user-attachments/assets/836d1f97-f6c7-40a2-acc7-006d7f06512f

# Teleoperation Leader Arm

## Pipeline
1. `bridge_node`가 `GroupSyncRead`를 통해 리더 암의 다이나믹셀 14개 현재 위치를 읽습니다.
2. 엔코더 값을 rad으로 변환합니다 (`0..4096` -> `0..2pi`).
3. 각 관절 값에 `LowPassFilter`(`plugins/filters.py`)를 적용하여 신호를 완화합니다.
4. 각 팔의 앞 4개 관절 값을 변환한 뒤 `Calibration.calibrate(...)`(`plugins/calibration.py`)에 전달하여 리더 자세를 follower_arm의 joint configuration에 맞게 보정합니다.
5. 보정된 관절 값을 `[0, 2pi)` 범위로 정리한 후 `/leader/joint_states`로 `sensor_msgs/JointState`를 publish합니다.

## Video

https://github.com/user-attachments/assets/0006c42c-5d85-43ac-bec1-fccc3eb352a0

