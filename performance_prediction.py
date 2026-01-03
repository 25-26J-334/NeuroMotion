from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


def _to_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            pass
        try:
            return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
    return None


def _safe_div(n: float, d: float, default: float = 0.0) -> float:
    if d == 0:
        return default
    return n / d


def _linear_forecast(xs: np.ndarray, ys: np.ndarray, x_next: float) -> Tuple[float, float]:
    if xs.size < 2 or ys.size < 2:
        y = float(ys[-1]) if ys.size else 0.0
        return y, 0.0
    try:
        slope, intercept = np.polyfit(xs, ys, 1)
        return float(slope * x_next + intercept), float(slope)
    except Exception:
        y = float(ys[-1]) if ys.size else 0.0
        return y, 0.0


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _exercise_key(exercise_type: str) -> str:
    et = (exercise_type or "").lower()
    if et in {"jump", "jumps"}:
        return "jump"
    if et in {"squat", "squats"}:
        return "squat"
    if et in {"pushup", "push-up", "pushups", "push-ups"}:
        return "pushup"
    return "jump"


def _session_count_field(exercise_type: str) -> str:
    et = _exercise_key(exercise_type)
    if et == "jump":
        return "total_jumps"
    if et == "squat":
        return "total_squats"
    return "total_pushups"


@dataclass
class PredictionResult:
    predicted_speed_rpm: float
    predicted_endurance_score: float
    predicted_rating: float
    trend: str
    forecast: List[Dict[str, float]]
    history_points: int


def compute_performance_prediction(
    recent_sessions: List[Dict[str, Any]],
    exercise_type: str,
    current_count: int,
    current_points: int,
    current_bad_moves: int,
    current_session_start: Optional[datetime],
) -> PredictionResult:
    et = _exercise_key(exercise_type)
    count_field = _session_count_field(et)

    hist_counts: List[float] = []
    hist_points: List[float] = []
    hist_bad_moves: List[float] = []
    hist_minutes: List[float] = []

    for row in recent_sessions:
        start_dt = _to_datetime(row.get("start_time"))
        end_dt = _to_datetime(row.get("end_time"))
        if not start_dt or not end_dt:
            continue
        minutes = max((end_dt - start_dt).total_seconds() / 60.0, 0.1)
        cnt = float(row.get(count_field) or 0)
        pts = float(row.get("total_points") or 0)
        bad = float(row.get("total_bad_moves") or 0)
        if cnt <= 0:
            continue

        hist_counts.append(cnt)
        hist_points.append(pts)
        hist_bad_moves.append(bad)
        hist_minutes.append(minutes)

    history_points = len(hist_counts)

    if current_session_start is not None:
        elapsed_min = max((datetime.now() - current_session_start).total_seconds() / 60.0, 0.1)
    else:
        elapsed_min = 0.0

    current_speed = _safe_div(float(current_count), elapsed_min, default=0.0) if elapsed_min > 0 else 0.0
    current_bad_rate = _safe_div(float(current_bad_moves), float(current_count), default=0.0) if current_count > 0 else 0.0
    current_quality = _clamp(1.0 - current_bad_rate, 0.0, 1.0)

    if history_points == 0:
        base_speed = current_speed if current_speed > 0 else 10.0
        base_volume = max(float(current_count), 10.0)
        base_quality = current_quality if current_count > 0 else 0.85
    else:
        hist_speeds = np.array([_safe_div(c, m, default=0.0) for c, m in zip(hist_counts, hist_minutes)], dtype=float)
        base_speed = float(np.nanmean(hist_speeds)) if np.isfinite(hist_speeds).any() else 10.0
        base_volume = float(np.nanmean(np.array(hist_counts, dtype=float)))
        hist_bad_rates = np.array([_safe_div(b, c, default=0.0) for b, c in zip(hist_bad_moves, hist_counts)], dtype=float)
        base_quality = float(_clamp(1.0 - float(np.nanmean(hist_bad_rates)), 0.0, 1.0))

    xs = np.arange(history_points, dtype=float)
    next_x = float(history_points)

    if history_points >= 2:
        speeds = np.array([_safe_div(c, m, default=0.0) for c, m in zip(hist_counts, hist_minutes)], dtype=float)
        pred_speed, speed_slope = _linear_forecast(xs, speeds, next_x)
        counts = np.array(hist_counts, dtype=float)
        pred_count, count_slope = _linear_forecast(xs, counts, next_x)
        bad_rates = np.array([_safe_div(b, c, default=0.0) for b, c in zip(hist_bad_moves, hist_counts)], dtype=float)
        pred_bad_rate, bad_slope = _linear_forecast(xs, bad_rates, next_x)
    elif history_points == 1:
        pred_speed = float(_safe_div(hist_counts[0], hist_minutes[0], default=base_speed))
        speed_slope = 0.0
        pred_count = float(hist_counts[0])
        count_slope = 0.0
        pred_bad_rate = float(_safe_div(hist_bad_moves[0], hist_counts[0], default=0.0))
        bad_slope = 0.0
    else:
        pred_speed = base_speed
        speed_slope = 0.0
        pred_count = base_volume
        count_slope = 0.0
        pred_bad_rate = 1.0 - base_quality
        bad_slope = 0.0

    pred_speed = _clamp(pred_speed, 0.0, 200.0)
    pred_count = _clamp(pred_count, 0.0, 500.0)
    pred_bad_rate = _clamp(pred_bad_rate, 0.0, 1.0)

    if speed_slope > 0.15 or count_slope > 0.5:
        trend = "improving"
    elif speed_slope < -0.15 or count_slope < -0.5:
        trend = "declining"
    else:
        trend = "stable"

    predicted_quality = _clamp(1.0 - pred_bad_rate, 0.0, 1.0)

    speed_norm = _clamp(_safe_div(pred_speed, max(base_speed, 1e-6), default=1.0), 0.0, 2.0)
    volume_norm = _clamp(_safe_div(pred_count, max(base_volume, 1e-6), default=1.0), 0.0, 2.0)

    predicted_endurance_score = 100.0 * _clamp(0.55 * volume_norm + 0.45 * speed_norm, 0.0, 1.2)
    predicted_endurance_score = _clamp(predicted_endurance_score, 0.0, 100.0)

    predicted_rating = 100.0 * _clamp(0.45 * speed_norm + 0.30 * volume_norm + 0.25 * predicted_quality, 0.0, 1.2)
    predicted_rating = _clamp(predicted_rating, 0.0, 100.0)

    fatigue_k = 0.25
    forecast: List[Dict[str, float]] = []
    for load in (0.8, 1.0, 1.2):
        fatigue = 1.0 - fatigue_k * max(load - 1.0, 0.0)
        effective_load = load * _clamp(fatigue, 0.7, 1.0)
        f_speed = pred_speed * _clamp(effective_load, 0.6, 1.3)
        f_count = pred_count * _clamp(effective_load, 0.6, 1.3)
        f_bad = _clamp(pred_bad_rate + 0.08 * max(load - 1.0, 0.0), 0.0, 1.0)
        f_quality = _clamp(1.0 - f_bad, 0.0, 1.0)

        f_speed_norm = _clamp(_safe_div(f_speed, max(base_speed, 1e-6), default=1.0), 0.0, 2.0)
        f_volume_norm = _clamp(_safe_div(f_count, max(base_volume, 1e-6), default=1.0), 0.0, 2.0)
        f_endurance = 100.0 * _clamp(0.55 * f_volume_norm + 0.45 * f_speed_norm, 0.0, 1.2)
        f_endurance = _clamp(f_endurance, 0.0, 100.0)
        f_rating = 100.0 * _clamp(0.45 * f_speed_norm + 0.30 * f_volume_norm + 0.25 * f_quality, 0.0, 1.2)
        f_rating = _clamp(f_rating, 0.0, 100.0)

        forecast.append(
            {
                "training_load": float(load),
                "pred_speed_rpm": float(f_speed),
                "pred_endurance_score": float(f_endurance),
                "pred_rating": float(f_rating),
            }
        )

    return PredictionResult(
        predicted_speed_rpm=float(pred_speed),
        predicted_endurance_score=float(predicted_endurance_score),
        predicted_rating=float(predicted_rating),
        trend=trend,
        forecast=forecast,
        history_points=history_points,
    )
