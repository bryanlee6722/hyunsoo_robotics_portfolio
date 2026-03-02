# 파이프라인

## Pipeline
1. `bridge_node`가 `GroupSyncRead`를 통해 리더 암의 다이나믹셀 14개 현재 위치를 읽습니다.
2. 엔코더 값을 rad으로 변환합니다 (`0..4096` -> `0..2pi`).
3. 각 관절 값에 `LowPassFilter`(`plugins/filters.py`)를 적용하여 신호를 완화합니다.
4. 각 팔의 앞 4개 관절 값을 변환한 뒤 `Calibration.calibrate(...)`(`plugins/calibration.py`)에 전달하여 리더 자세를 follower_arm의 Scale에 맞게 보정합니다.
5. 보정된 관절 값을 `[0, 2pi)` 범위로 정리한 후 `/leader/joint_states`로 `sensor_msgs/JointState`를 publish합니다.

## Details of Each File
1. `bridge_node`
   - 주요 파라미터: `serial_port`, `serial_baud`, `hz`, `lpf_cutoff_hz`, `operation_mode`
   - 실행 루프(`tick`): Sync Read -> 라디안 변환 -> LPF -> Calibration -> `/leader/joint_states` 순서로 동작합니다.
2. `plugins/filters.py`
   - 1st Order Low-Pass-Filter를 구현합니다 (`tau = 1 / (2*pi*cutoff_hz)`).
   - `alpha = dt / (tau + dt)`를 사용하며, 관절별 내부 상태 `y`를 유지합니다.
3. `plugins/calibration.py`
   - FK(leader_arm) -> 링크 길이 비율 Scaling -> IK(follower_arm) 순서로 계산합니다.
   - `side='right'|'left'`에 따라 서로 다른 어깨 offset을 적용합니다.
   - Jacobian은 수치 미분으로 근사하며 반복적으로 풉니다 (`max_iter=1000`, damping `0.1`).

## Filters and Calibration
1. Low-Pass Filter
   - `bridge_node`에서 모터 ID별로 각각 적용합니다.
   - 기본 컷오프는 `5.0 Hz`(`lpf_cutoff_hz`)이며, 갱신 주기는 `dt = 1/hz`입니다.
   - 목적은 기구학 보정 전에 엔코더의 떨림을 무시하는 것입니다.
2. Calibration
   - 양팔 모두 어깨/팔꿈치 체인(`각 팔 [0:4]`)에 대해서만 Calibration을 수행합니다.
   - 발행 전후로 오른팔/왼팔에 대해 `pi` 오프셋 및 부호 규칙을 적용합니다.
   - 핵심 흐름은 `forward_kinematics_leader` -> `scaling_to_follower` -> `inverse_kinematics_follower`입니다.
