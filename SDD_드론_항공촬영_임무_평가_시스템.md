# Software Design Document (SDD)
## 드론 항공촬영 임무 평가 시스템

**버전**: 1.0  
**작성일**: 2026-05-21  
**기반 문서**: 사용자 제공 SDD 초안, `소프트웨어공학_프로젝트.docx (SRS)` 확인 필요

---

## 1. 개요

### 1.1 목적

본 문서는 AirSim 기반 드론 항공촬영 시뮬레이션 결과를 평가하는 교육용 실습 플랫폼의 소프트웨어 설계를 정의한다. 본 문서의 목적은 구현 구조, 데이터 인터페이스, 평가 알고리즘, 예외 처리, UI 동작을 명확히 규정하여 구현자와 검증자가 동일한 기준으로 시스템을 개발하고 시험할 수 있도록 하는 것이다.

### 1.2 범위

본 시스템의 범위는 다음과 같다.

- 입력 파일 로드: 임무 설정 파일, 비행 로그, 촬영 로그, 충돌 로그
- 입력 데이터 검증: 형식, 필수 필드, 값 범위, 이미지 경로
- 목표-촬영 매칭: 목표 지점과 촬영 기록 간 1:1 매칭
- 평가 수행: 위치, 방향, 시간, 누락, 충돌 기준 평가
- 결과 표시: 점수, 상세 결과, 그래프, 이미지 미리보기
- 결과 저장: JSON 및 CSV 형식의 평가 결과 파일 생성

본 시스템의 범위에 포함되지 않는 항목은 다음과 같다.

- AirSim 시뮬레이션 실행 기능
- 드론 제어 기능
- 이미지 품질 분석 기능
- 네트워크 기반 다중 사용자 기능

### 1.3 실행 환경 및 기술 제약

- 구현 언어: Python 3.x
- UI 프레임워크: PyQt5
- 시각화 라이브러리: matplotlib
- 실행 환경: Windows 기반 Desktop PC
- 문자 인코딩: UTF-8
- 좌표계: AirSim NED 좌표계

### 1.4 용어 정의

| 용어 | 정의 |
|------|------|
| 임무 설정 파일 | 목표 촬영 위치, 방향, 제한 시간, 평가 기준을 정의한 JSON 파일 |
| 목표 | 하나의 촬영 평가 단위가 되는 목표 지점 정의 |
| 촬영 기록 | 드론이 촬영한 1건의 로그 레코드 |
| 비행 로그 | 드론의 시간별 위치, 자세, 속도 기록 |
| 충돌 로그 | 충돌 발생 여부와 관련 정보를 저장한 기록 |
| 허용 오차 | 목표 만족 판정에 사용하는 최대 허용 위치/방향 오차 |
| 종합 비용 | 목표-촬영 매칭에 사용하는 비용 값 |
| 누락 | 어떤 촬영 기록에도 매칭되지 않은 목표 |
| 시간 초과 | 매칭된 촬영 기록의 촬영 시각이 목표 제한 시간을 초과한 상태 |
| NED 좌표계 | North-East-Down 좌표계. 단위는 meter |

### 1.5 확인 필요 사항

다음 항목은 현재 제공된 초안만으로 확정할 수 없으므로 SRS 원본 확인 후 확정해야 한다.

- JSON 로그 파일의 최상위 구조가 모든 로그 유형에서 동일한지 여부
- `collision` 필드의 허용 표현이 `true/false`만인지, `0/1`도 허용하는지 여부
- 결과 파일 자동 저장이 필수인지, 사용자 수동 저장만 허용하는지 여부
- 평가 진행률 표시가 실제 단계 기반인지, 레코드 단위 세부 진행률이 필요한지 여부

---

## 2. 시스템 아키텍처

### 2.1 아키텍처 패턴

시스템은 MVC(Model-View-Controller) 패턴을 적용한다.

```text
+----------------+       +------------------+       +----------------+
| View           | <---> | AppController    | <---> | Model          |
| PyQt5 UI       |       | Workflow Control |       | Data Classes   |
+----------------+       +------------------+       +----------------+
                                 |
                 +---------------+------------------------------+
                 |               |              |               |
          +------+-----+  +------+-----+ +------+-----+ +-------+------+
          | FileLoader |  | Validator  | | Evaluator  | | ReportExporter|
          +------------+  +------------+ +------+-----+ +--------------+
                                               |
                                      +--------+--------+
                                      |                 |
                                 +----+-----+     +-----+-----------+
                                 | Matcher   |     | ScoreCalculator|
                                 +----------+     +-----------------+
```

### 2.2 컴포넌트 책임

| 컴포넌트 | 책임 | 입력 | 출력 |
|----------|------|------|------|
| MainWindow | UI 이벤트 수신 및 결과 표시 | 사용자 입력, Controller 응답 | 화면 상태 |
| AppController | 전체 처리 흐름 제어 | UI 요청 | 평가 결과, 오류 정보 |
| FileLoader | CSV/JSON 파일 파싱 | 파일 경로 | 모델 객체 목록 |
| Validator | 구조/값/경로 검증 | 모델 객체, 파일 경로 | 검증 결과, 오류 목록 |
| Evaluator | 매칭과 점수 계산 orchestration | 검증 완료 데이터 | `EvalResult` |
| Matcher | 목표-촬영 최적 1:1 매칭 | 목표 목록, 촬영 목록, 가중치 | 매칭 쌍 |
| ScoreCalculator | 감점 및 최종 점수 계산 | 매칭 결과, 정책 값 | `ScoreDetail`, `final_score` |
| ReportExporter | 결과 저장 | `EvalResult`, 저장 경로 | JSON/CSV 파일 |

### 2.3 처리 흐름

1. 사용자가 입력 파일 경로를 선택한다.
2. `AppController`가 파일 존재 여부를 확인한다.
3. `FileLoader`가 각 입력 파일을 파싱하여 모델 객체를 생성한다.
4. `Validator`가 구조 및 값 검증을 수행한다.
5. 검증 실패 시 평가를 중단하고 오류를 UI에 표시한다.
6. 검증 성공 시 `Evaluator`가 매칭, 조건 판정, 점수 계산을 수행한다.
7. `AppController`가 결과를 UI에 전달한다.
8. 사용자가 선택하면 `ReportExporter`가 결과 파일을 저장한다.

---

## 3. 모듈 설계

### 3.1 디렉토리 구조

```text
drone_eval/
├── main.py
├── controller/
│   └── app_controller.py
├── model/
│   ├── mission.py
│   ├── logs.py
│   └── result.py
├── service/
│   ├── file_loader.py
│   ├── validator.py
│   ├── evaluator.py
│   ├── matcher.py
│   ├── score_calculator.py
│   └── report_exporter.py
├── view/
│   ├── main_window.py
│   ├── tab_file_select.py
│   ├── tab_mission.py
│   ├── tab_run.py
│   ├── tab_summary.py
│   ├── tab_detail.py
│   ├── tab_visual.py
│   └── tab_report.py
└── utils/
    └── angle_utils.py
```

### 3.2 주요 데이터 모델

```python
@dataclass
class TargetPoint:
    target_id: str
    x: float
    y: float
    z: float
    yaw: float
    pitch: float
    time_limit: float

@dataclass
class ScorePolicy:
    position_penalty_per_meter: float
    direction_yaw_penalty_per_degree: float
    direction_pitch_penalty_per_degree: float
    missing_capture_penalty: float
    collision_penalty: float
    timeout_penalty: float
    position_weight: float
    direction_weight: float

@dataclass
class MissionConfig:
    mission_id: str
    allow_position_error: float
    allow_yaw_error: float
    allow_pitch_error: float
    targets: List[TargetPoint]
    score_policy: ScorePolicy

@dataclass
class FlightRecord:
    timestamp: float
    x: float
    y: float
    z: float
    roll: float
    pitch: float
    yaw: float
    speed: float

@dataclass
class CaptureRecord:
    timestamp: float
    x: float
    y: float
    z: float
    roll: float
    pitch: float
    yaw: float
    image_path: str

@dataclass
class CollisionRecord:
    timestamp: float
    collision: bool
    x: float
    y: float
    z: float

@dataclass
class TargetResult:
    target_id: str
    matched_capture: Optional[CaptureRecord]
    matched_capture_timestamp: Optional[float]
    position_error: Optional[float]
    yaw_error: Optional[float]
    pitch_error: Optional[float]
    position_ok: bool
    direction_ok: bool
    time_ok: bool
    image_linked: bool
    is_missing: bool
    is_timeout: bool
    position_deduction: float
    direction_deduction: float
    timeout_deduction: float

@dataclass
class ScoreDetail:
    total_position_deduction: float
    total_direction_deduction: float
    total_missing_deduction: float
    total_collision_deduction: float
    total_timeout_deduction: float
    total_deduction: float
    base_score: float

@dataclass
class EvalResult:
    mission_id: str
    target_results: List[TargetResult]
    collision_records: List[CollisionRecord]
    total_targets: int
    success_count: int
    missing_count: int
    collision_count: int
    timeout_count: int
    avg_position_error: Optional[float]
    avg_yaw_error: Optional[float]
    avg_pitch_error: Optional[float]
    score_detail: ScoreDetail
    final_score: float
```

### 3.3 설계 제약

- `TargetResult.position_error`, `yaw_error`, `pitch_error`는 목표가 누락된 경우 `None`이어야 한다.
- `TargetResult.matched_capture_timestamp`는 매칭된 촬영 기록이 있을 때 해당 `CaptureRecord.timestamp`와 동일해야 하며, 누락된 목표는 `None`이어야 한다.
- 누락된 목표의 `timeout_deduction`은 항상 `0`이어야 한다.
- 평균 오차 값은 매칭된 촬영 기록이 1건 이상일 때만 계산하며, 그렇지 않으면 `None`이어야 한다.
- 평균 오차는 누락되지 않은 목표 중 매칭된 촬영 기록이 있는 목표만을 대상으로 계산해야 한다.
- `success_count`는 누락되지 않은 목표 중 `position_ok`, `direction_ok`, `time_ok`가 모두 `True`인 목표 수여야 한다.
- 점수 관련 필드명은 `score`와 `deduction`을 혼용하지 않고, 감점값은 모두 `deduction`으로 통일한다.
- `TargetPoint.time_limit`은 목표별 제한 시간을 의미하며, 임무 전체 공통 제한 시간을 의미하지 않는다.

---

## 4. 데이터 명세

### 4.1 공통 규칙

- 모든 입력 파일은 UTF-8 인코딩이어야 한다.
- 숫자 필드는 부동소수점으로 파싱 가능해야 한다.
- 필수 필드가 누락된 레코드는 평가에서 제외하고 오류 목록에 기록해야 한다.
- 로그 레코드 순서는 입력 순서를 유지하되, 시간 계산은 각 레코드의 `timestamp` 값으로 수행해야 한다.

### 4.2 임무 설정 파일

- 형식: JSON 객체
- 필수 최상위 필드:
  - `mission_id`
  - `allow_position_error`
  - `allow_yaw_error`
  - `allow_pitch_error`
  - `targets`
  - `score_policy`

예시:

```json
{
  "mission_id": "mission_001",
  "allow_position_error": 2.0,
  "allow_yaw_error": 10.0,
  "allow_pitch_error": 10.0,
  "targets": [
    {
      "target_id": "T1",
      "x": 10.0,
      "y": 5.0,
      "z": -20.0,
      "yaw": 90.0,
      "pitch": -30.0,
      "time_limit": 60.0
    }
  ],
  "score_policy": {
    "position_penalty_per_meter": 5.0,
    "direction_yaw_penalty_per_degree": 2.0,
    "direction_pitch_penalty_per_degree": 2.0,
    "missing_capture_penalty": 10.0,
    "collision_penalty": 20.0,
    "timeout_penalty": 5.0,
    "position_weight": 1.0,
    "direction_weight": 1.0
  }
}
```

검증 규칙:

- `targets`는 길이 1 이상의 배열이어야 한다.
- `target_id`는 임무 내에서 중복되면 안 된다.
- 허용 오차와 감점 계수는 0 이상이어야 한다.
- `position_weight`와 `direction_weight`는 0보다 커야 한다.

### 4.3 비행 로그

- 형식: CSV 또는 JSON
- CSV 헤더:

```text
timestamp,x,y,z,roll,pitch,yaw,speed
```

- 필수 필드: `timestamp`, `x`, `y`, `z`, `roll`, `pitch`, `yaw`, `speed`

### 4.4 촬영 로그

- 형식: CSV 또는 JSON
- CSV 헤더:

```text
timestamp,x,y,z,roll,pitch,yaw,image_path
```

- 필수 필드: `timestamp`, `x`, `y`, `z`, `roll`, `pitch`, `yaw`, `image_path`
- `roll` 필드는 입력으로는 유지하되 평가 계산에는 사용하지 않는다. 본 시스템은 촬영 방향 평가를 yaw/pitch 기준으로만 수행하며, roll은 표시 및 원본 로그 보존 목적의 보조 정보로 취급한다.

### 4.5 충돌 로그

- 형식: CSV 또는 JSON
- CSV 헤더:

```text
timestamp,collision,x,y,z
```

- 필수 필드: `timestamp`, `collision`, `x`, `y`, `z`
- `collision == true`인 레코드만 충돌 이벤트로 처리한다.

### 4.6 JSON 로그 형식

CSV 대신 JSON을 사용할 경우, 각 로그 파일은 레코드 객체 배열이어야 한다.

예시:

```json
[
  {
    "timestamp": 1.0,
    "x": 10.1,
    "y": 5.2,
    "z": -20.0,
    "roll": 0.0,
    "pitch": -30.0,
    "yaw": 90.0,
    "image_path": "C:/images/cap001.png"
  }
]
```

---

## 5. 평가 알고리즘 설계

### 5.1 임무 시작 시각

- 임무 시작 시각 `t_start`는 비행 로그의 첫 번째 유효 레코드의 `timestamp`로 정의한다.
- 비행 로그에 유효 레코드가 없으면 평가를 중단하고 오류를 반환해야 한다.

### 5.2 오차 계산

위치 오차:

```text
position_error = sqrt((cx - tx)^2 + (cy - ty)^2 + (cz - tz)^2)
```

방향 오차:

```text
yaw_error   = abs(normalize_angle(capture.yaw   - target.yaw))
pitch_error = abs(normalize_angle(capture.pitch - target.pitch))
```

각도 정규화:

```text
normalize_angle(a) = ((a + 180) % 360) - 180
```

### 5.3 판정 규칙

- `position_ok = position_error <= allow_position_error`
- `direction_ok = (yaw_error <= allow_yaw_error) AND (pitch_error <= allow_pitch_error)`
- `time_ok = (capture.timestamp - t_start) <= target.time_limit`
- `is_timeout = NOT time_ok`
- `image_linked = Path(image_path).is_file()`

성공 판정 규칙:

- `success_count`는 다음 조건을 모두 만족하는 목표 수로 계산한다.
- 목표가 누락되지 않아야 한다.
- `position_ok`가 `True`여야 한다.
- `direction_ok`가 `True`여야 한다.
- `time_ok`가 `True`여야 한다.

### 5.4 목표-촬영 매칭 비용

```text
cost(target_i, capture_j) =
    position_error(i, j) * position_weight
  + yaw_error(i, j)      * direction_weight
  + pitch_error(i, j)    * direction_weight
```

매칭 후보 규칙:

- 비용 행렬에는 모든 유효 촬영 기록을 포함해야 한다.
- `time_ok` 위반 촬영 기록도 매칭 후보에서 사전 제외하지 않는다.
- 허용 위치 오차 또는 허용 방향 오차를 초과한 촬영 기록도 매칭 후보에서 사전 제외하지 않는다.
- 조건 위반 여부는 매칭 후 `position_ok`, `direction_ok`, `time_ok` 판정과 감점 계산으로 처리해야 한다.

### 5.5 감점 규칙

위치 감점:

```text
if position_error > allow_position_error:
    position_deduction =
        (position_error - allow_position_error) * position_penalty_per_meter
else:
    position_deduction = 0
```

방향 감점:

```text
if yaw_error > allow_yaw_error:
    yaw_deduction =
        (yaw_error - allow_yaw_error) * direction_yaw_penalty_per_degree
else:
    yaw_deduction = 0

if pitch_error > allow_pitch_error:
    pitch_deduction =
        (pitch_error - allow_pitch_error) * direction_pitch_penalty_per_degree
else:
    pitch_deduction = 0

direction_deduction = yaw_deduction + pitch_deduction
```

시간 초과 감점:

```text
if is_missing is True:
    timeout_deduction = 0
elif time_ok is False:
    timeout_deduction = timeout_penalty
else:
    timeout_deduction = 0
```

누락 및 충돌 감점:

```text
missing_deduction   = missing_count   * missing_capture_penalty
collision_deduction = collision_count * collision_penalty
```

### 5.6 최종 점수

```text
base_score = 100.0

total_deduction =
    sum(position_deduction for all matched targets)
  + sum(direction_deduction for all matched targets)
  + sum(timeout_deduction for all matched targets)
  + missing_deduction
  + collision_deduction

final_score = max(0.0, base_score - total_deduction)
```

---

## 6. 목표-촬영 매칭 알고리즘

### 6.1 적용 알고리즘

- 구현은 `scipy.optimize.linear_sum_assignment`를 사용한다.
- 매칭은 전역 최적 1:1 매칭이어야 한다.
- 매칭 단계는 비용 최소화만 수행하며, 시간 초과 및 허용 오차 초과 여부는 매칭 이후 평가 단계에서 판정해야 한다.

### 6.2 처리 절차

1. 목표 수를 `N`, 촬영 수를 `M`으로 정의한다.
2. 크기 `N x M` 비용 행렬을 생성한다.
3. `linear_sum_assignment`를 호출한다.
4. 반환된 인덱스를 기준으로 목표와 촬영 기록을 매칭한다.
5. 매칭되지 않은 목표는 누락으로 처리한다.
6. 매칭되지 않은 촬영 기록은 평가 결과에 반영하지 않는다.

### 6.3 경계 조건

- `N > 0`이고 `M = 0`이면 모든 목표를 누락으로 처리한다.
- `N = 0`인 임무 설정 파일은 유효하지 않으며 입력 검증 실패로 처리한다.
- 동일 비용의 복수 해가 있을 수 있다. 이 경우 `linear_sum_assignment`의 반환 결과를 그대로 사용한다.

---

## 7. UI 설계

### 7.1 화면 구성

시스템은 `QMainWindow`와 `QTabWidget` 기반의 7개 탭으로 구성한다.

| 탭 | 이름 | 목적 |
|----|------|------|
| 1 | 파일 선택 | 입력 파일 경로 지정 및 기본 검증 결과 표시 |
| 2 | 임무 설정 확인 | 목표 목록과 평가 기준 확인 |
| 3 | 평가 실행 | 평가 시작 및 진행 상태 표시 |
| 4 | 결과 요약 | 최종 점수와 주요 집계 결과 표시 |
| 5 | 상세 결과 | 목표별 상세 판정과 이미지 미리보기 표시 |
| 6 | 시각화 | 그래프 기반 분석 결과 표시 |
| 7 | 리포트 저장 | 평가 결과 파일 저장 |

### 7.2 파일 선택 탭

와이어프레임:

```text
[임무 설정 파일]  [경로 표시................................] [찾아보기]
[비행 로그]       [경로 표시................................] [찾아보기]
[촬영 로그]       [경로 표시................................] [찾아보기]
[충돌 로그]       [경로 표시................................] [찾아보기]
[이미지 폴더]     [경로 표시................................] [찾아보기]

[오류 메시지 영역 - 읽기 전용]
```

입력 항목:

- 임무 설정 파일
- 비행 로그
- 촬영 로그
- 충돌 로그
- 이미지 폴더

동작 요구사항:

- 각 입력 항목은 경로 표시 영역과 파일 선택 버튼을 포함해야 한다.
- 필수 입력 누락 시 평가 시작 버튼은 비활성화되어야 한다.
- 오류 메시지 영역은 읽기 전용이어야 한다.

### 7.3 임무 설정 확인 탭

와이어프레임:

```text
[임무 ID] mission_001
[허용 위치 오차] 2.0 m   [허용 Yaw 오차] 10.0 deg   [허용 Pitch 오차] 10.0 deg
[감점 정책 요약] 위치 5.0/m, Yaw 2.0/deg, Pitch 2.0/deg, 누락 10.0, 충돌 20.0, 시간초과 5.0

[목표 목록 테이블]
| 목표ID | X | Y | Z | Yaw | Pitch | 제한시간 |
| T1     |   |   |   |     |       |          |
```

동작 요구사항:

- 임무 설정 파일 로드 성공 시 목표 목록과 평가 기준 요약을 표시해야 한다.
- 임무 설정 파일 로드 실패 시 테이블을 비우고 오류 메시지를 표시해야 한다.
- 목표 목록은 `target_id` 기준 입력 순서를 유지해야 한다.

### 7.4 평가 실행 탭

와이어프레임:

```text
[평가 시작]

진행 단계
[파일 로드    ] [████████░░] 80%
[입력 검증    ] [████████░░] 80%
[매칭 및 평가 ] [░░░░░░░░░░]  0%
[결과 준비    ] [░░░░░░░░░░]  0%

상태 메시지: 촬영 로그 로드 중...
```

동작 요구사항:

- 사용자가 `평가 시작` 버튼을 누르면 중복 실행이 불가능해야 한다.
- 진행 상태는 최소 다음 4단계를 표시해야 한다.
  - 파일 로드
  - 입력 검증
  - 매칭 및 평가
  - 결과 표시 준비
- 단계 실패 시 현재 단계와 오류 메시지를 표시해야 한다.

### 7.5 결과 요약 탭

와이어프레임:

```text
[최종 점수] 72.5 / 100

[요약 테이블]
| 항목            | 값   |
| 총 목표 수      | 5    |
| 성공 수         | 3    |
| 누락 수         | 1    |
| 충돌 수         | 2    |
| 시간 초과 수    | 1    |
| 총 위치 감점    | 8.0  |
| 총 방향 감점    | 4.5  |
| 총 누락 감점    | 10.0 |
| 총 충돌 감점    | 40.0 |
| 총 시간 감점    | 5.0  |
```

동작 요구사항:

- 최종 점수는 소수점 표시 규칙을 구현 시 1개 기준으로 통일해야 한다.
- 요약 테이블 값은 `EvalResult`와 `ScoreDetail`에서 직접 계산 가능한 값만 표시해야 한다.

### 7.6 상세 결과 탭

와이어프레임:

```text
[목표별 상세 결과 테이블]
| 목표ID | 매칭시각 | 위치오차 | Yaw오차 | Pitch오차 | 위치판정 | 방향판정 | 시간판정 | 누락 | 이미지 |

[선택된 행의 이미지 미리보기]
```

표시 컬럼:

- 목표ID
- 매칭 촬영 시각
- 위치오차
- Yaw오차
- Pitch오차
- 위치 판정
- 방향 판정
- 시간 판정
- 누락 여부
- 이미지 연결 여부

동작 요구사항:

- 사용자가 테이블 행을 선택하면 해당 행의 매칭 이미지 미리보기를 시도해야 한다.
- 이미지가 없거나 열 수 없으면 대체 텍스트를 표시해야 한다.

### 7.7 시각화 탭

표시 차트:

- 목표별 위치 오차 그래프
- 목표별 방향 오차 그래프
- 감점 항목별 합계 그래프
- 성공/누락/충돌/시간 초과 집계 그래프

### 7.8 리포트 저장 탭

와이어프레임:

```text
[저장 폴더] [경로 표시................................] [찾아보기]

[저장할 파일]
[ ] eval_result.json
[ ] eval_result.csv
[ ] eval_detail.csv
[ ] eval_summary.json

[리포트 저장]
[저장 결과 메시지 영역]
```

동작 요구사항:

- 기본 선택 상태와 파일 선택 가능 여부는 SRS 확인 후 확정해야 한다.
- 저장 성공 시 생성된 파일 목록을 표시해야 한다.
- 저장 실패 시 실패 원인과 실패 파일 목록을 표시해야 한다.

---

## 8. 파일 입출력 인터페이스

### 8.1 입력 로드 순서

1. 임무 설정 파일 로드
2. 비행 로그 로드
3. 촬영 로그 로드
4. 충돌 로그 로드
5. 이미지 경로 검증

### 8.2 출력 파일

출력 파일은 사용자가 지정한 폴더에 저장해야 한다.

필수 출력 파일:

- `eval_result.json`
- `eval_result.csv`
- `eval_detail.csv`
- `eval_summary.json`

출력 파일 용도:

- `eval_result.json`은 구조화된 결과 데이터를 다른 프로그램이나 후속 처리 로직이 읽기 쉽도록 저장하는 용도이다.
- `eval_result.csv`는 동일한 요약 정보를 단일 행 표 형식으로 저장하여 스프레드시트 확인, 과제 제출, 수동 비교에 사용하기 위한 용도이다.
- `eval_detail.csv`는 목표별 상세 판정과 감점 내역을 표 형식으로 확인하기 위한 용도이다.
- `eval_summary.json`은 화면 요약과 동일한 핵심 집계 정보만 별도로 제공하기 위한 용도이다.

### 8.3 출력 JSON 구조

`eval_result.json` 예시:

```json
{
  "mission_id": "mission_001",
  "final_score": 72.5,
  "total_targets": 5,
  "success_count": 3,
  "missing_count": 1,
  "collision_count": 2,
  "timeout_count": 1,
  "score_detail": {
    "total_position_deduction": 8.0,
    "total_direction_deduction": 4.5,
    "total_missing_deduction": 10.0,
    "total_collision_deduction": 40.0,
    "total_timeout_deduction": 5.0,
    "total_deduction": 67.5,
    "base_score": 100.0
  }
}
```

`eval_result.csv` 헤더:

```text
mission_id,final_score,total_targets,success_count,missing_count,collision_count,timeout_count,total_position_deduction,total_direction_deduction,total_missing_deduction,total_collision_deduction,total_timeout_deduction,total_deduction,base_score
```

`eval_result.csv`는 `eval_result.json`의 요약 필드를 단일 행으로 평탄화하여 저장해야 한다.

`eval_detail.csv` 헤더:

```text
target_id,matched_capture_timestamp,position_error,yaw_error,pitch_error,position_ok,direction_ok,time_ok,image_linked,is_missing,is_timeout,position_deduction,direction_deduction,timeout_deduction
```

`matched_capture_timestamp`는 매칭된 촬영 기록의 `timestamp` 값을 저장하며, 매칭되지 않은 목표는 빈 값으로 기록해야 한다.

`eval_summary.json` 예시:

```json
{
  "mission_id": "mission_001",
  "total_targets": 5,
  "success_count": 3,
  "missing_count": 1,
  "collision_count": 2,
  "timeout_count": 1,
  "avg_position_error": 1.8,
  "avg_yaw_error": 6.2,
  "avg_pitch_error": 4.1,
  "final_score": 72.5
}
```

### 8.4 저장 실패 처리

- 저장 경로가 없거나 쓰기 권한이 없으면 저장을 중단하고 오류 메시지를 표시해야 한다.
- 일부 파일 저장에 실패한 경우, 성공/실패 파일 목록을 사용자에게 표시해야 한다.

---

## 9. 예외 처리 설계

| 예외 상황 | 판정 기준 | 처리 방식 |
|-----------|-----------|-----------|
| 필수 입력 파일 누락 | 필수 경로 미지정 또는 파일 없음 | 평가 시작 불가, 오류 메시지 표시 |
| 임무 설정 파일 형식 오류 | JSON 파싱 실패 또는 필수 필드 누락 | 로드 실패, 평가 중단 |
| 로그 파일 형식 오류 | CSV/JSON 파싱 실패 | 로드 실패, 평가 중단 |
| 필수 필드 누락 | 필수 컬럼 또는 키 미존재 | 해당 레코드 제외, 오류 목록 기록 |
| 숫자 변환 실패 | float 변환 실패, NaN 포함 | 해당 레코드 제외, 오류 목록 기록 |
| 비행 로그 유효 레코드 없음 | `t_start` 계산 불가 | 평가 중단 |
| 촬영 로그 없음 | 유효 촬영 기록 수 0 | 모든 목표 누락 처리 후 평가 계속 |
| 충돌 로그 없음 | 파일 미선택 또는 유효 이벤트 0 | 충돌 0건으로 평가 계속 |
| 이미지 파일 없음 | `image_path` 대상 파일 미존재 | `image_linked=False`, 평가 계속 |
| 한글 경로 포함 | 경로 문자열에 비ASCII 문자 포함 | `pathlib.Path` 기반 처리 |

---

## 10. 비기능 요구사항 대응

| 요구사항 | 설계 대응 | 검증 기준 |
|----------|-----------|-----------|
| 성능 | 벡터 연산 및 Hungarian algorithm 사용 | 100MB 이하 입력에서 30초 이내 완료 |
| 신뢰성 | 랜덤 요소 없이 동일 입력에 동일 결과 보장 | 동일 입력 3회 실행 시 결과 동일 |
| 유지보수성 | 기능별 모듈 분리 및 데이터 모델 분리 | 주요 서비스 모듈 독립 단위 테스트 가능 |
| 확장성 | `ScorePolicy` 및 `Evaluator` 확장 구조 사용 | 신규 평가 항목 추가 시 기존 UI 구조 유지 가능 |
| 사용성 | 탭 기반 UI와 한국어 오류 메시지 제공 | 비전문가 사용 시 파일 선택부터 저장까지 단일 흐름 수행 가능 |

---

## 11. 시험 가능성 기준

본 문서의 모든 핵심 요구사항은 다음 방식으로 시험 가능해야 한다.

- 입력 검증: 정상/오류 샘플 파일로 성공 및 실패 여부 확인
- 매칭 알고리즘: 소규모 고정 데이터셋으로 기대 매칭 결과 비교
- 점수 계산: 수작업 계산값과 프로그램 출력 비교
- UI 동작: 필수 입력 누락, 평가 실행, 결과 표시, 저장 실패 상황 확인
- 예외 처리: 손상 파일, 누락 필드, 이미지 누락, 빈 로그 파일 확인

---

## 12. 문서 일관성 메모

- 본 문서에서는 `감점`의 내부 데이터 표현을 모두 `deduction`으로 통일하였다.
- 초안에 있던 `score_detail.position_score`, `direction_score`, `time_score`는 실제 값이 감점인지 점수인지 모호하므로 제거하고 감점 합계 구조로 정리하였다.
- 출력 예시와 데이터 클래스 간 필드명을 일치시켰다.
