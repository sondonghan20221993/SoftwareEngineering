# Implementation Plan
## 드론 항공촬영 임무 평가 시스템 구현 계획

**버전**: 1.0  
**작성일**: 2026-05-26

---

## 1. 목적

본 문서는 현재 구현된 드론 항공촬영 임무 평가 시스템을 과제 제출 수준의 완성형 프로젝트로 확장하기 위한 구현 계획을 정의한다. 목표는 품질을 유지하면서 5000줄 이상 규모의 자연스러운 코드베이스를 구성하는 것이다.

---

## 2. 현재 구현 상태

현재 구현 완료 범위:

- 데이터 모델
- 파일 로더
- 입력 검증기
- 목표-촬영 매칭기
- 점수 계산기
- 평가 엔진
- 결과 저장기
- 핵심 서비스 계층 자동화 테스트

현재 포함 파일 범위:

- `drone_eval/model/`
- `drone_eval/service/`
- `drone_eval/utils/`
- `tests/`

---

## 3. 확장 목표

5000줄 이상을 자연스럽게 달성하기 위해 다음 6개 영역을 확장한다.

1. PyQt5 UI 실제 구현
2. AppController 추가
3. 시각화 기능 강화
4. 로깅 및 예외 처리 체계 추가
5. 입력 미리보기 및 평가 이력 기능 추가
6. 테스트 범위 확대

---

## 4. 권장 디렉토리 구조

```text
drone_eval/
├── main.py
├── controller/
│   └── app_controller.py
├── model/
│   ├── mission.py
│   ├── logs.py
│   ├── result.py
│   └── history.py
├── service/
│   ├── file_loader.py
│   ├── validator.py
│   ├── evaluator.py
│   ├── matcher.py
│   ├── score_calculator.py
│   ├── report_exporter.py
│   ├── history_manager.py
│   ├── visualization_service.py
│   └── preview_service.py
├── view/
│   ├── main_window.py
│   ├── tab_file_select.py
│   ├── tab_mission.py
│   ├── tab_run.py
│   ├── tab_summary.py
│   ├── tab_detail.py
│   ├── tab_visual.py
│   ├── tab_report.py
│   ├── tab_preview.py
│   └── tab_history.py
├── utils/
│   ├── angle_utils.py
│   ├── logger.py
│   └── exceptions.py
└── assets/
    └── icons/
tests/
├── test_angle_utils.py
├── test_score_calculator.py
├── test_matcher.py
├── test_evaluator.py
├── test_file_loader.py
├── test_validator.py
├── test_report_exporter.py
├── test_history_manager.py
├── test_visualization_service.py
├── test_preview_service.py
└── test_app_controller.py
```

---

## 5. 기능 확장 항목

### 5.1 UI 실제 구현

구현 대상:

- `main_window.py`
- `tab_file_select.py`
- `tab_mission.py`
- `tab_run.py`
- `tab_summary.py`
- `tab_detail.py`
- `tab_visual.py`
- `tab_report.py`
- `tab_preview.py`
- `tab_history.py`

예상 줄 수:

- `1200~1800`줄

세부 기능:

- 파일 선택 탭
- 임무 설정 요약 표시
- 평가 진행률 표시
- 목표별 상세 결과 테이블
- 차트 표시
- 이미지 미리보기
- 입력 로그 미리보기
- 평가 이력 비교

### 5.2 AppController 추가

구현 대상:

- `controller/app_controller.py`

예상 줄 수:

- `250~400`줄

세부 기능:

- 파일 선택 상태 관리
- 서비스 호출 orchestration
- 오류 메시지 전달
- 진행 상태 갱신
- 저장 명령 처리

### 5.3 시각화 기능 강화

구현 대상:

- `service/visualization_service.py`

예상 줄 수:

- `250~450`줄

세부 기능:

- 위치 오차 그래프
- Yaw 오차 그래프
- Pitch 오차 그래프
- 감점 항목별 그래프
- 성공/누락/충돌/시간초과 집계 그래프
- 차트 PNG 저장

### 5.4 로깅 및 예외 처리

구현 대상:

- `utils/logger.py`
- `utils/exceptions.py`

예상 줄 수:

- `150~250`줄

세부 기능:

- 애플리케이션 로그 파일 생성
- 오류 상세 기록
- 사용자 표시용 예외와 내부 디버그 예외 분리
- 저장 실패, 형식 오류, 검증 오류 예외 클래스 정의

### 5.5 입력 미리보기 및 평가 이력

구현 대상:

- `service/preview_service.py`
- `service/history_manager.py`
- `model/history.py`
- `view/tab_preview.py`
- `view/tab_history.py`

예상 줄 수:

- `500~800`줄

세부 기능:

- 비행/촬영/충돌 로그 테이블 미리보기
- 오류 레코드 강조 표시
- 이전 평가 결과 JSON 불러오기
- 평가 결과 비교 테이블
- 최근 평가 기록 목록

### 5.6 테스트 확대

구현 대상:

- 추가 테스트 파일 일체

예상 줄 수:

- `900~1400`줄

세부 기능:

- 경계값 테스트
- 실패 케이스 테스트
- 컨트롤러 테스트
- 저장 실패 테스트
- 시각화 서비스 테스트
- 이력 기능 테스트

---

## 6. 예상 총 줄 수

| 영역 | 예상 줄 수 |
|---|---:|
| 현재 구현 코드 및 테스트 | 1800~2200 |
| UI 실제 구현 | 1200~1800 |
| AppController | 250~400 |
| 시각화 기능 | 250~450 |
| 로깅/예외 처리 | 150~250 |
| 입력 미리보기/이력 기능 | 500~800 |
| 테스트 확대 | 900~1400 |
| **합계** | **5050~7300** |

---

## 7. 구현 우선순위

1. `controller/app_controller.py`
2. `view/main_window.py` 및 핵심 탭 4개
3. `visualization_service.py`
4. `preview_service.py`
5. `history_manager.py`
6. `logger.py`, `exceptions.py`
7. 추가 테스트 작성

---

## 8. 권장 개발 원칙

- 테스트 가능한 서비스 계층을 우선 구현한다.
- UI는 컨트롤러를 통해서만 서비스 계층과 연결한다.
- 중복 로직을 만들지 않고 오차 계산, 감점 계산, 저장 포맷은 공통 함수로 유지한다.
- 줄 수 목표보다 문서, 테스트, 기능 일관성을 우선한다.
