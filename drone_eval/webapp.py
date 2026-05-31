from __future__ import annotations

import io
import json
import tempfile
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from drone_eval.service.file_loader import FileLoader
from drone_eval.service.validator import Validator
from drone_eval.service.evaluator import Evaluator
from drone_eval.service.report_exporter import ReportExporter
from drone_eval.service.visualization_service import VisualizationService
from drone_eval.utils.exceptions import FileLoadError, ValidationError, EvaluationError

st.set_page_config(
    page_title="드론 임무 평가 시스템",
    page_icon="🚁",
    layout="wide",
)

# ── 세션 상태 초기화 ──────────────────────────────────────────────
if "eval_result" not in st.session_state:
    st.session_state.eval_result = None
if "mission" not in st.session_state:
    st.session_state.mission = None
if "validation_errors" not in st.session_state:
    st.session_state.validation_errors = []
if "capture_records" not in st.session_state:
    st.session_state.capture_records = []


def _save_upload(uploaded_file) -> Path:
    suffix = Path(uploaded_file.name).suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded_file.read())
    tmp.flush()
    return Path(tmp.name)


def _fig_to_bytes(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


# ── 사이드바: 파일 업로드 ─────────────────────────────────────────
st.sidebar.title("📂 입력 파일")

mission_file = st.sidebar.file_uploader("임무 설정 파일 (JSON)", type=["json"])
flight_file = st.sidebar.file_uploader("비행 로그 (CSV/JSON)", type=["csv", "json"])
capture_file = st.sidebar.file_uploader("촬영 로그 (CSV/JSON)", type=["csv", "json"])
collision_file = st.sidebar.file_uploader("충돌 로그 (CSV/JSON)", type=["csv", "json"])

run_btn = st.sidebar.button(
    "▶ 평가 실행",
    disabled=not all([mission_file, flight_file, capture_file, collision_file]),
    use_container_width=True,
)

# ── 평가 실행 ─────────────────────────────────────────────────────
if run_btn:
    st.session_state.eval_result = None
    st.session_state.mission = None
    st.session_state.validation_errors = []

    progress = st.sidebar.progress(0, text="시작 중...")

    try:
        progress.progress(10, text="임무 설정 로드 중...")
        mission_path = _save_upload(mission_file)
        mission = FileLoader.load_mission_config(mission_path)

        progress.progress(30, text="비행 로그 로드 중...")
        flight_path = _save_upload(flight_file)
        flight_records = FileLoader.load_flight_records(flight_path)

        progress.progress(50, text="촬영 로그 로드 중...")
        capture_path = _save_upload(capture_file)
        capture_records = FileLoader.load_capture_records(capture_path)

        progress.progress(65, text="충돌 로그 로드 중...")
        collision_path = _save_upload(collision_file)
        collision_records = FileLoader.load_collision_records(collision_path)

        progress.progress(75, text="입력 검증 중...")
        errors: list[str] = []
        errors.extend(Validator.validate_mission_config(mission))
        errors.extend(Validator.validate_flight_records(flight_records))
        errors.extend(Validator.validate_capture_records(capture_records))
        errors.extend(Validator.validate_collision_records(collision_records))
        st.session_state.validation_errors = errors

        progress.progress(90, text="평가 계산 중...")
        result = Evaluator.evaluate(mission, flight_records, capture_records, collision_records)

        st.session_state.eval_result = result
        st.session_state.mission = mission
        st.session_state.capture_records = capture_records
        progress.progress(100, text="완료!")
        st.sidebar.success("평가 완료!")

    except Exception as exc:
        st.sidebar.error(f"오류: {exc}")
        progress.empty()

# ── 메인 화면 ─────────────────────────────────────────────────────
st.title("🚁 드론 항공촬영 임무 평가 시스템")

tabs = st.tabs(["임무 설정", "결과 요약", "상세 결과", "시각화", "리포트 저장"])

# ── 탭 1: 임무 설정 ───────────────────────────────────────────────
with tabs[0]:
    st.subheader("임무 설정 확인")
    mission = st.session_state.mission
    if mission is None:
        st.info("왼쪽 사이드바에서 파일을 업로드하고 평가를 실행하세요.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("임무 ID", mission.mission_id)
        col2.metric("허용 위치 오차", f"{mission.allow_position_error:.2f} m")
        col3.metric("허용 Yaw 오차", f"{mission.allow_yaw_error:.2f}°")

        sp = mission.score_policy
        st.markdown("**감점 정책**")
        policy_df = pd.DataFrame([{
            "위치(/m)": sp.position_penalty_per_meter,
            "Yaw(/deg)": sp.direction_yaw_penalty_per_degree,
            "Pitch(/deg)": sp.direction_pitch_penalty_per_degree,
            "누락": sp.missing_capture_penalty,
            "충돌": sp.collision_penalty,
            "시간초과": sp.timeout_penalty,
        }])
        st.dataframe(policy_df, use_container_width=True)

        st.markdown("**목표 목록**")
        targets_df = pd.DataFrame([{
            "목표ID": t.target_id, "X": t.x, "Y": t.y, "Z": t.z,
            "Yaw": t.yaw, "Pitch": t.pitch, "제한시간(s)": t.time_limit,
        } for t in mission.targets])
        st.dataframe(targets_df, use_container_width=True)

    if st.session_state.validation_errors:
        with st.expander(f"⚠️ 검증 경고 {len(st.session_state.validation_errors)}건", expanded=False):
            for err in st.session_state.validation_errors:
                st.warning(err)

# ── 탭 2: 결과 요약 ───────────────────────────────────────────────
with tabs[1]:
    st.subheader("결과 요약")
    result = st.session_state.eval_result
    if result is None:
        st.info("평가를 먼저 실행하세요.")
    else:
        score_color = "normal" if result.final_score >= 80 else ("off" if result.final_score < 60 else "normal")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("최종 점수", f"{result.final_score:.1f} / 100")
        col2.metric("총 목표", result.total_targets)
        col3.metric("성공", result.success_count)
        col4.metric("누락", result.missing_count)
        col5.metric("충돌", result.collision_count)

        if result.score_detail:
            sd = result.score_detail
            st.markdown("**감점 내역**")
            deduction_df = pd.DataFrame([{
                "위치 감점": sd.total_position_deduction,
                "방향 감점": sd.total_direction_deduction,
                "누락 감점": sd.total_missing_deduction,
                "충돌 감점": sd.total_collision_deduction,
                "시간초과 감점": sd.total_timeout_deduction,
                "총 감점": sd.total_deduction,
            }])
            st.dataframe(deduction_df, use_container_width=True)

        col_a, col_b, col_c = st.columns(3)
        if result.avg_position_error is not None:
            col_a.metric("평균 위치 오차", f"{result.avg_position_error:.3f} m")
        if result.avg_yaw_error is not None:
            col_b.metric("평균 Yaw 오차", f"{result.avg_yaw_error:.2f}°")
        if result.avg_pitch_error is not None:
            col_c.metric("평균 Pitch 오차", f"{result.avg_pitch_error:.2f}°")

# ── 탭 3: 상세 결과 ───────────────────────────────────────────────
with tabs[2]:
    st.subheader("목표별 상세 결과")
    result = st.session_state.eval_result
    if result is None:
        st.info("평가를 먼저 실행하세요.")
    else:
        detail_rows = []
        for t in result.target_results:
            detail_rows.append({
                "목표ID": t.target_id,
                "매칭시각": f"{t.matched_capture_timestamp:.2f}" if t.matched_capture_timestamp else "-",
                "위치오차(m)": f"{t.position_error:.3f}" if t.position_error is not None else "-",
                "Yaw오차(°)": f"{t.yaw_error:.2f}" if t.yaw_error is not None else "-",
                "Pitch오차(°)": f"{t.pitch_error:.2f}" if t.pitch_error is not None else "-",
                "위치판정": "✅" if t.position_ok else "❌",
                "방향판정": "✅" if t.direction_ok else "❌",
                "시간판정": "✅" if t.time_ok else "❌",
                "성공": "✅" if (t.position_ok and t.direction_ok and t.time_ok and not t.is_missing) else "❌",
                "누락": "⚠️" if t.is_missing else "-",
                "이미지": "✅" if t.image_linked else "❌",
                "위치감점": f"{t.position_deduction:.2f}",
                "방향감점": f"{t.direction_deduction:.2f}",
                "시간감점": f"{t.timeout_deduction:.2f}",
            })
        detail_df = pd.DataFrame(detail_rows)
        st.dataframe(detail_df, use_container_width=True, height=400)

# ── 탭 4: 시각화 ──────────────────────────────────────────────────
with tabs[3]:
    st.subheader("시각화")
    result = st.session_state.eval_result
    if result is None:
        st.info("평가를 먼저 실행하세요.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**목표별 위치 오차**")
            fig = VisualizationService.position_error_figure(result)
            st.image(_fig_to_bytes(fig), use_column_width=True)

            st.markdown("**감점 항목별 합계**")
            fig = VisualizationService.deduction_breakdown_figure(result)
            st.image(_fig_to_bytes(fig), use_column_width=True)

        with col2:
            st.markdown("**목표별 방향 오차**")
            fig = VisualizationService.direction_error_figure(result)
            st.image(_fig_to_bytes(fig), use_column_width=True)

            st.markdown("**임무 결과 요약**")
            fig = VisualizationService.summary_figure(result)
            st.image(_fig_to_bytes(fig), use_column_width=True)

        st.markdown("**커버리지 모자이크**")
        if "capture_records" in st.session_state and st.session_state.capture_records:
            fig = VisualizationService.coverage_mosaic_figure(
                st.session_state.capture_records,
                st.session_state.mission,
            )
            st.image(_fig_to_bytes(fig), use_column_width=True)
        else:
            st.info("이미지 경로가 포함된 촬영 로그가 있어야 모자이크가 생성됩니다.")

# ── 탭 5: 리포트 저장 ─────────────────────────────────────────────
with tabs[4]:
    st.subheader("리포트 다운로드")
    result = st.session_state.eval_result
    if result is None:
        st.info("평가를 먼저 실행하세요.")
    else:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            col1, col2 = st.columns(2)
            with col1:
                path = tmp_path / "eval_result.json"
                ReportExporter.export_eval_result_json(result, path)
                st.download_button(
                    "⬇️ eval_result.json",
                    data=path.read_bytes(),
                    file_name="eval_result.json",
                    mime="application/json",
                    use_container_width=True,
                )

                path = tmp_path / "eval_detail.csv"
                ReportExporter.export_eval_detail_csv(result, path)
                st.download_button(
                    "⬇️ eval_detail.csv",
                    data=path.read_bytes(),
                    file_name="eval_detail.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            with col2:
                path = tmp_path / "eval_result.csv"
                ReportExporter.export_eval_result_csv(result, path)
                st.download_button(
                    "⬇️ eval_result.csv",
                    data=path.read_bytes(),
                    file_name="eval_result.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

                path = tmp_path / "eval_summary.json"
                ReportExporter.export_eval_summary_json(result, path)
                st.download_button(
                    "⬇️ eval_summary.json",
                    data=path.read_bytes(),
                    file_name="eval_summary.json",
                    mime="application/json",
                    use_container_width=True,
                )
