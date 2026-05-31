# 드론 항공촬영 임무 평가 시스템

AirSim 시뮬레이터에서 수행된 드론 항공촬영 임무 결과를 평가하는 데스크톱 애플리케이션입니다.

비행 로그, 촬영 로그, 충돌 로그를 입력으로 받아 목표 위치·방향·시간 조건을 자동으로 평가하고 최종 점수를 산출합니다.

---

## 주요 기능

- 목표별 위치 오차·방향 오차·시간 초과 자동 판정
- Hungarian algorithm 기반 목표-촬영 1:1 최적 매칭
- 충돌 감점, 누락 감점 포함 최종 점수 산출
- 비행 경로·위치 분포·감점 내역 등 차트 6종 시각화
- 평가 결과 JSON/CSV 내보내기
- 평가 이력 저장 및 비교

---

## 다운로드

**Python 설치 없이 바로 실행하려면:**

[DroneEval.exe 다운로드 (v1.0.0)](https://github.com/sondonghan20221993/SoftwareEngineering/releases/download/v1.0.0/DroneEval.exe)

---

## 요구 사항

- Python 3.10 이상
- Windows 환경 (PyQt5 GUI)

---

## 설치

```bash
pip install -e ".[test]"
```

또는 conda 환경:

```bash
conda install pyqt matplotlib scipy numpy
pip install -e ".[test]"
```

---

## 실행 방법 (3가지 선택)

### 1. 데스크톱 앱 (PyQt5)
```bash
python -m drone_eval.main
```

### 2. 웹앱 (브라우저)
```bash
pip install streamlit pandas
streamlit run drone_eval/webapp.py
```
브라우저가 자동으로 열립니다.

### 3. exe 실행 파일 빌드 (Windows)
```
build_exe.bat
```
빌드 완료 후 `dist\DroneEval.exe`를 더블클릭하면 됩니다.

---

## 테스트

```bash
pytest
```

---

## 입력 파일 형식

### 임무 설정 (`mission.json`)

```json
{
  "mission_id": "mission_001",
  "allow_position_error": 2.0,
  "allow_yaw_error": 15.0,
  "allow_pitch_error": 15.0,
  "targets": [
    { "target_id": "T1", "x": 0.0, "y": 0.0, "z": -10.0,
      "yaw": 90.0, "pitch": -30.0, "time_limit": 60.0 }
  ],
  "score_policy": {
    "position_penalty_per_meter": 5.0,
    "direction_yaw_penalty_per_degree": 1.0,
    "direction_pitch_penalty_per_degree": 1.0,
    "missing_capture_penalty": 10.0,
    "collision_penalty": 20.0,
    "timeout_penalty": 5.0,
    "position_weight": 1.0,
    "direction_weight": 1.0
  }
}
```

### 비행 로그 (`flight_log.csv`)

```
timestamp,x,y,z,roll,pitch,yaw,speed
10.0,0.0,0.0,-10.0,0.0,-30.0,90.0,3.0
```

### 촬영 로그 (`capture_log.csv`)

```
timestamp,x,y,z,roll,pitch,yaw,image_path
20.0,0.5,0.3,-10.0,0.0,-29.0,91.0,rgb/000000.png
```

### 충돌 로그 (`collision_log.csv`)

```
timestamp,collision,x,y,z
12.0,False,0.0,0.0,-10.0
14.0,True,1.0,1.0,-9.0
```

CSV 대신 JSON 형식도 지원합니다.

---

## AirSim 데이터셋 변환

AirSim에서 수집한 데이터셋을 평가 입력 형식으로 변환하려면:

```bash
python tools/convert_airsim.py <데이터셋_폴더> <출력_폴더>
```

예시:

```bash
python tools/convert_airsim.py "D:/airsim_dataset" "D:/output"
```

비행 로그, 촬영 로그, 충돌 로그, 샘플 mission.json이 자동 생성됩니다.

---

## 출력 파일

| 파일 | 내용 |
|---|---|
| `eval_result.json` | 최종 점수, 감점 세부 내역 |
| `eval_result.csv` | 위와 동일 (CSV 형식) |
| `eval_detail.csv` | 목표별 상세 평가 결과 |
| `eval_summary.json` | 임무 요약 (평균 오차, 성공 수 등) |

---

## 프로젝트 구조

```
drone_eval/
├── main.py               # 진입점
├── controller/           # AppController (UI-서비스 연결)
├── model/                # 데이터 클래스
├── service/              # 핵심 로직 (평가, 매칭, 점수 계산 등)
├── utils/                # 유틸리티 (각도 계산, 예외, 로거)
└── view/                 # PyQt5 UI 탭
docs/                     # SRS, SDD, STD 문서
tests/                    # 단위 테스트
tools/                    # AirSim 변환 도구
```
