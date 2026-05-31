# Software Test Description (STD)
## 드론 항공촬영 임무 평가 시스템

**버전**: 1.0  
**작성일**: 2026-05-26  
**기준 문서**: `docs/SRS_드론_항공촬영_임무_평가_시스템.md`, `SDD_드론_항공촬영_임무_평가_시스템.md`

---

## 1. 목적

본 문서는 드론 항공촬영 임무 평가 시스템의 기능 요구사항과 설계 요구사항이 시험 가능하도록 시험 항목, 입력 조건, 기대 결과를 정의한다.

---

## 2. 시험 범위

- 입력 파일 로드
- 입력 데이터 검증
- 목표-촬영 매칭
- 오차 계산
- 감점 계산 및 최종 점수 산출
- 결과 파일 저장
- 예외 처리

---

## 3. 시험 환경

- 운영체제: Windows Desktop
- 실행 환경: Python 3.10 이상
- 테스트 프레임워크: `pytest`
- 기준 저장소: `C:\Users\sdh97\Documents\GitHub\SoftwareEngineering`

---

## 4. 시험 항목

### 4.1 입력 로드 시험

| 시험 ID | 시험 항목 | 입력 조건 | 기대 결과 |
|---|---|---|---|
| TL-01 | 임무 설정 파일 로드 | 정상 JSON 임무 설정 파일 | `mission_id`, 목표 정보, 감점 정책이 정상 로드되어야 한다. |
| TL-02 | 촬영 로그 CSV 로드 | 정상 CSV 촬영 로그 | 촬영 시각, 위치, 방향, 이미지 경로가 정상 로드되어야 한다. |
| TL-03 | 충돌 로그 bool 파싱 | `yes`, `false` 값 포함 CSV | `yes`는 `True`, `false`는 `False`로 해석되어야 한다. |
| TL-04 | 지원하지 않는 확장자 처리 | `.txt` 파일 입력 | 로더는 예외를 발생시켜야 한다. |

### 4.2 입력 검증 시험

| 시험 ID | 시험 항목 | 입력 조건 | 기대 결과 |
|---|---|---|---|
| TV-01 | 중복 목표 ID 검출 | 동일 `target_id` 2건 포함 | 검증 오류가 발생해야 한다. |
| TV-02 | 0 이하 가중치 검출 | `position_weight = 0` | 검증 오류가 발생해야 한다. |
| TV-03 | 비행 로그 NaN 검출 | 좌표값 중 `NaN` 포함 | 해당 오류가 보고되어야 한다. |
| TV-04 | 촬영 로그 NaN 검출 | `pitch = NaN` | 해당 오류가 보고되어야 한다. |
| TV-05 | 이미지 파일 누락 검출 | 존재하지 않는 `image_path` | 이미지 경로 오류가 보고되어야 한다. |
| TV-06 | 충돌 로그 NaN 검출 | 충돌 좌표 중 `NaN` 포함 | 해당 오류가 보고되어야 한다. |

### 4.3 오차 및 매칭 시험

| 시험 ID | 시험 항목 | 입력 조건 | 기대 결과 |
|---|---|---|---|
| TM-01 | 각도 정규화 | `190`, `-190`, `180` 입력 | 각각 `-170`, `170`, `-180`으로 정규화되어야 한다. |
| TM-02 | 비용 함수 비교 | 목표와 가까운 촬영 기록, 먼 촬영 기록 | 가까운 기록의 비용이 더 낮아야 한다. |
| TM-03 | 1:1 최적 매칭 | 목표 2개, 촬영 2개 | 전체 비용 합이 최소인 매칭이 선택되어야 한다. |
| TM-04 | 촬영 수 부족 | 목표 2개, 촬영 1개 | 1개만 매칭되고 나머지 목표는 누락 처리되어야 한다. |
| TM-05 | 촬영 수 초과 | 목표 2개, 촬영 3개 | 최적 2건만 매칭되고 나머지 촬영은 무시되어야 한다. |

### 4.4 점수 산출 시험

| 시험 ID | 시험 항목 | 입력 조건 | 기대 결과 |
|---|---|---|---|
| TS-01 | 위치 감점 계산 | 허용 오차 초과 위치 오차 입력 | 초과분에 비례한 감점이 계산되어야 한다. |
| TS-02 | 방향 감점 계산 | Yaw, Pitch 모두 허용 오차 초과 | 각 초과분 감점의 합이 계산되어야 한다. |
| TS-03 | 누락 목표 시간 감점 | `is_missing = True` | `timeout_deduction = 0`이어야 한다. |
| TS-04 | 최종 점수 하한 | 감점 총합이 100 초과 | 최종 점수는 0이어야 한다. |

### 4.5 평가 처리 시험

| 시험 ID | 시험 항목 | 입력 조건 | 기대 결과 |
|---|---|---|---|
| TE-01 | 성공/누락/충돌/시간초과 집계 | 정상 비행 로그, 촬영 로그, 충돌 로그 | `success_count`, `missing_count`, `collision_count`, `timeout_count`가 기대값과 일치해야 한다. |
| TE-02 | 평균 오차 계산 범위 | 일부 목표만 매칭 | 평균 오차는 매칭된 목표만 기준으로 계산되어야 한다. |
| TE-03 | 비행 로그 없음 | 빈 비행 로그 | 평가기는 예외를 발생시켜야 한다. |

### 4.6 결과 저장 시험

| 시험 ID | 시험 항목 | 입력 조건 | 기대 결과 |
|---|---|---|---|
| TR-01 | `eval_result.json` 저장 | 정상 `EvalResult` | 요약 필드와 `score_detail`이 JSON으로 저장되어야 한다. |
| TR-02 | `eval_result.csv` 저장 | 정상 `EvalResult` | 요약 정보가 단일 행 CSV로 평탄화되어야 한다. |
| TR-03 | `eval_detail.csv` 저장 | 매칭/누락 목표 혼합 | `matched_capture_timestamp`가 매칭 목표에는 값으로, 누락 목표에는 빈 값으로 저장되어야 한다. |
| TR-04 | `eval_summary.json` 저장 | 정상 `EvalResult` | 핵심 집계 값만 포함된 JSON이 저장되어야 한다. |

---

## 5. 시험 데이터 기준

- 정상 임무 설정 파일 1건
- 정상 비행 로그 1건 이상
- 정상 촬영 로그 1건 이상
- 정상 충돌 로그 0건 이상
- 이미지 존재 경로 1건
- 이미지 미존재 경로 1건
- NaN 포함 로그 샘플
- 필수 필드 누락 로그 샘플

---

## 6. 자동화 시험 매핑

현재 구현된 자동화 시험 파일:

- `tests/test_angle_utils.py`
- `tests/test_score_calculator.py`
- `tests/test_matcher.py`
- `tests/test_evaluator.py`
- `tests/test_file_loader.py`
- `tests/test_validator.py`
- `tests/test_report_exporter.py`

시험 ID별 자동화 시험 매핑:

| 시험 ID | 자동화 시험 파일 | 비고 |
|---|---|---|
| `TL-01` | `tests/test_file_loader.py` | 임무 설정 JSON 로드 |
| `TL-02` | `tests/test_file_loader.py` | 촬영 로그 CSV 로드 |
| `TL-03` | `tests/test_file_loader.py` | 충돌 로그 bool 파싱 |
| `TL-04` | `tests/test_file_loader.py` | 미지원 확장자 처리 |
| `TV-01` | `tests/test_validator.py` | 중복 목표 ID 검출 |
| `TV-02` | `tests/test_validator.py` | 가중치 값 검증 |
| `TV-03` | `tests/test_validator.py` | 비행 로그 NaN 검출 |
| `TV-04` | `tests/test_validator.py` | 촬영 로그 NaN 검출 |
| `TV-05` | `tests/test_validator.py` | 이미지 파일 누락 검출 |
| `TV-06` | `tests/test_validator.py` | 충돌 로그 NaN 검출 |
| `TM-01` | `tests/test_angle_utils.py` | 각도 정규화 |
| `TM-02` | `tests/test_matcher.py` | 비용 함수 비교 |
| `TM-03` | `tests/test_matcher.py` | 1:1 최적 매칭 |
| `TM-04` | `tests/test_matcher.py` | 촬영 수 부족 |
| `TM-05` | `tests/test_matcher.py` | 촬영 수 초과 |
| `TS-01` | `tests/test_score_calculator.py` | 위치 감점 계산 |
| `TS-02` | `tests/test_score_calculator.py` | 방향 감점 계산 |
| `TS-03` | `tests/test_score_calculator.py` | 누락 목표 시간 감점 |
| `TS-04` | `tests/test_score_calculator.py` | 최종 점수 하한 |
| `TE-01` | `tests/test_evaluator.py` | 성공/누락/충돌/시간초과 집계 |
| `TE-02` | `tests/test_evaluator.py` | 평균 오차 계산 범위 |
| `TE-03` | `tests/test_evaluator.py` | 빈 비행 로그 예외 |
| `TR-01` | `tests/test_report_exporter.py` | `eval_result.json` 저장 |
| `TR-02` | `tests/test_report_exporter.py` | `eval_result.csv` 저장 |
| `TR-03` | `tests/test_report_exporter.py` | `eval_detail.csv` 저장 |
| `TR-04` | `tests/test_report_exporter.py` | `eval_summary.json` 저장 |

---

---

## 6.5 ODM 연동 시험

### 자동화 시험

| 시험 ID | 파일 | 내용 |
|---|---|---|
| `TODM-01` | `tests/test_odm_service.py` | NED → GPS 좌표 변환 정확도 |
| `TODM-02` | `tests/test_odm_service.py` | geo.txt 생성 항목 수 일치 |
| `TODM-03` | `tests/test_odm_service.py` | Docker 미설치 시 오류 반환 |
| `TODM-04` | `tests/test_odm_service.py` | 정사영상 없을 때 None 반환 |

### 수동 시험

| 시험 ID | 내용 | 합격 기준 |
|---|---|---|
| `TODM-M01` | Docker 실행 후 ODM 로그 실시간 표시 | 로그가 UI에 실시간으로 출력됨 |
| `TODM-M02` | ODM 완료 후 정사영상 자동 로드 | orthophoto가 뷰어에 표시됨 |
| `TODM-M03` | 목표점/촬영점 오버레이 | 정사영상 위에 올바른 위치에 표시됨 |
| `TODM-M04` | Docker 미설치 환경 오류 메시지 | 명확한 오류 메시지가 표시됨 |

---

## 7. 합격 기준

- 모든 자동화 시험이 통과해야 한다.
- 수동 검증이 필요한 UI 항목은 요구사항과 일치해야 한다.
- 동일 입력에 대한 반복 실행 결과가 동일해야 한다.
- ODM 연동 기능은 Docker 환경에서 수동 시험을 통과해야 한다.
- 100MB 이하 입력 조건에서 목표 성능 기준을 만족해야 한다.
