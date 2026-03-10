from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Try to import sklearn, fallback to basic implementations if not available
try:
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    
    # Fallback implementations
    def mean_squared_error(y_true, y_pred):
        return float(np.mean((np.array(y_true) - np.array(y_pred)) ** 2))
    
    def mean_absolute_error(y_true, y_pred):
        return float(np.mean(np.abs(np.array(y_true) - np.array(y_pred))))
    
    def r2_score(y_true, y_pred):
        y_true_arr = np.array(y_true)
        y_pred_arr = np.array(y_pred)
        ss_res = np.sum((y_true_arr - y_pred_arr) ** 2)
        ss_tot = np.sum((y_true_arr - np.mean(y_true_arr)) ** 2)
        return float(1 - (ss_res / ss_tot)) if ss_tot != 0 else 0.0
    
    class LinearRegression:
        def __init__(self):
            self.coef_ = None
            self.intercept_ = None
        
        def fit(self, X, y):
            X_arr = np.array(X).flatten()
            y_arr = np.array(y)
            # Simple linear regression using least squares
            n = len(X_arr)
            if n < 2:
                self.coef_ = np.array([0.0])
                self.intercept_ = 0.0
                return
            
            sum_x = np.sum(X_arr)
            sum_y = np.sum(y_arr)
            sum_xy = np.sum(X_arr * y_arr)
            sum_x2 = np.sum(X_arr ** 2)
            
            denominator = n * sum_x2 - sum_x ** 2
            if denominator == 0:
                self.coef_ = np.array([0.0])
                self.intercept_ = np.mean(y_arr)
            else:
                self.coef_ = np.array([(n * sum_xy - sum_x * sum_y) / denominator])
                self.intercept_ = (sum_y - self.coef_[0] * sum_x) / n
        
        def predict(self, X):
            X_arr = np.array(X).flatten()
            if self.coef_ is None or self.intercept_ is None:
                return np.zeros_like(X_arr)
            return self.coef_[0] * X_arr + self.intercept_


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


def _calculate_error_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float, float]:
    """Calculate RMSE, MAE, and R² error metrics"""
    if len(y_true) < 2:
        return 0.0, 0.0, 0.0
    
    try:
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        return float(rmse), float(mae), float(r2)
    except Exception:
        return 0.0, 0.0, 0.0


def _enhanced_forecast(xs: np.ndarray, ys: np.ndarray, x_next: float) -> Tuple[float, float, float, np.ndarray]:
    """Enhanced forecasting with confidence intervals"""
    if xs.size < 2 or ys.size < 2:
        y = float(ys[-1]) if ys.size else 0.0
        return y, 0.0, 0.0, np.array([y, y])
    
    try:
        # Use LinearRegression for better predictions
        model = LinearRegression()
        X = xs.reshape(-1, 1)
        model.fit(X, ys)
        
        # Predict next value
        pred_y = float(model.predict([[x_next]])[0])
        
        # Calculate trend strength (coefficient magnitude)
        trend_strength = float(abs(model.coef_[0]))
        
        # Calculate confidence interval (simple approximation)
        residuals = ys - model.predict(X)
        std_error = np.std(residuals)
        confidence = 1.96 * std_error  # 95% confidence interval
        
        return pred_y, float(model.coef_[0]), trend_strength, np.array([pred_y - confidence, pred_y + confidence])
    except Exception:
        y = float(ys[-1]) if ys.size else 0.0
        return y, 0.0, 0.0, np.array([y, y])


def _calculate_performance_history(recent_sessions: List[Dict[str, Any]], count_field: str) -> List[Dict[str, Any]]:
    """Calculate performance history for visualization"""
    history = []
    for i, session in enumerate(recent_sessions):
        start_dt = _to_datetime(session.get("start_time"))
        end_dt = _to_datetime(session.get("end_time"))
        if not start_dt or not end_dt:
            continue
            
        minutes = max((end_dt - start_dt).total_seconds() / 60.0, 0.1)
        count = float(session.get(count_field) or 0)
        points = float(session.get("total_points") or 0)
        bad_moves = float(session.get("total_bad_moves") or 0)
        
        if count <= 0:
            continue
            
        speed = _safe_div(count, minutes, default=0.0)
        bad_rate = _safe_div(bad_moves, count, default=0.0)
        quality = _clamp(1.0 - bad_rate, 0.0, 1.0)
        
        # Calculate performance scores
        volume_norm = _clamp(_safe_div(count, 50.0, default=1.0), 0.0, 2.0)  # Normalize to 50 reps baseline
        speed_norm = _clamp(_safe_div(speed, 20.0, default=1.0), 0.0, 2.0)  # Normalize to 20 reps/min baseline
        
        endurance_score = 100.0 * _clamp(0.55 * volume_norm + 0.45 * speed_norm, 0.0, 1.2)
        endurance_score = _clamp(endurance_score, 0.0, 100.0)
        
        rating = 100.0 * _clamp(0.45 * speed_norm + 0.30 * volume_norm + 0.25 * quality, 0.0, 1.2)
        rating = _clamp(rating, 0.0, 100.0)
        
        history.append({
            "session_number": i + 1,
            "date": end_dt.strftime("%Y-%m-%d"),
            "speed_rpm": float(speed),
            "endurance_score": float(endurance_score),
            "rating": float(rating),
            "count": int(count),
            "quality": float(quality)
        })
    
    return history


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
    # Error metrics
    rmse_speed: float
    mae_speed: float
    r2_speed: float
    rmse_endurance: float
    mae_endurance: float
    r2_endurance: float
    rmse_rating: float
    mae_rating: float
    r2_rating: float
    # Performance history for visualization
    performance_history: List[Dict[str, Any]]
    # Trend analysis
    trend_strength: float
    confidence_interval: Dict[str, float]


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
    performance_history = _calculate_performance_history(recent_sessions, count_field)

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

    # Initialize error metrics
    rmse_speed = mae_speed = r2_speed = 0.0
    rmse_endurance = mae_endurance = r2_endurance = 0.0
    rmse_rating = mae_rating = r2_rating = 0.0
    trend_strength = 0.0
    confidence_interval = {"lower": 0.0, "upper": 0.0}

    if history_points >= 2:
        # Calculate historical performance for error metrics
        hist_speeds = np.array([_safe_div(c, m, default=0.0) for c, m in zip(hist_counts, hist_minutes)], dtype=float)
        hist_counts_arr = np.array(hist_counts, dtype=float)
        hist_bad_rates = np.array([_safe_div(b, c, default=0.0) for b, c in zip(hist_bad_moves, hist_counts)], dtype=float)
        
        # Calculate historical endurance and rating scores
        hist_endurance_scores = []
        hist_ratings = []
        for i in range(history_points):
            speed_norm = _clamp(_safe_div(hist_speeds[i], max(base_speed, 1e-6), default=1.0), 0.0, 2.0)
            volume_norm = _clamp(_safe_div(hist_counts_arr[i], max(base_volume, 1e-6), default=1.0), 0.0, 2.0)
            quality = _clamp(1.0 - hist_bad_rates[i], 0.0, 1.0)
            
            endurance = 100.0 * _clamp(0.55 * volume_norm + 0.45 * speed_norm, 0.0, 1.2)
            rating = 100.0 * _clamp(0.45 * speed_norm + 0.30 * volume_norm + 0.25 * quality, 0.0, 1.2)
            
            hist_endurance_scores.append(_clamp(endurance, 0.0, 100.0))
            hist_ratings.append(_clamp(rating, 0.0, 100.0))
        
        hist_endurance_scores = np.array(hist_endurance_scores, dtype=float)
        hist_ratings = np.array(hist_ratings, dtype=float)
        
        # Enhanced forecasting with confidence intervals
        pred_speed, speed_slope, speed_trend_strength, speed_confidence = _enhanced_forecast(xs, hist_speeds, next_x)
        pred_count, count_slope, count_trend_strength, count_confidence = _enhanced_forecast(xs, hist_counts_arr, next_x)
        pred_bad_rate, bad_slope, bad_trend_strength, bad_confidence = _enhanced_forecast(xs, hist_bad_rates, next_x)
        
        # Calculate predictions for endurance and rating
        pred_endurance, endurance_slope, endurance_trend_strength, endurance_confidence = _enhanced_forecast(xs, hist_endurance_scores, next_x)
        pred_rating, rating_slope, rating_trend_strength, rating_confidence = _enhanced_forecast(xs, hist_ratings, next_x)
        
        # Calculate error metrics
        speed_preds = []
        endurance_preds = []
        rating_preds = []
        
        for i in range(history_points):
            # Simple linear prediction for each historical point
            if i > 0:
                speed_pred = hist_speeds[i-1] + speed_slope * 1
                endurance_pred = hist_endurance_scores[i-1] + endurance_slope * 1
                rating_pred = hist_ratings[i-1] + rating_slope * 1
            else:
                speed_pred = hist_speeds[i]
                endurance_pred = hist_endurance_scores[i]
                rating_pred = hist_ratings[i]
            
            speed_preds.append(speed_pred)
            endurance_preds.append(endurance_pred)
            rating_preds.append(rating_pred)
        
        speed_preds = np.array(speed_preds)
        endurance_preds = np.array(endurance_preds)
        rating_preds = np.array(rating_preds)
        
        # Calculate error metrics
        rmse_speed, mae_speed, r2_speed = _calculate_error_metrics(hist_speeds[1:], speed_preds[1:])
        rmse_endurance, mae_endurance, r2_endurance = _calculate_error_metrics(hist_endurance_scores[1:], endurance_preds[1:])
        rmse_rating, mae_rating, r2_rating = _calculate_error_metrics(hist_ratings[1:], rating_preds[1:])
        
        # Overall trend strength
        trend_strength = (speed_trend_strength + endurance_trend_strength + rating_trend_strength) / 3.0
        confidence_interval = {
            "lower": float(min(speed_confidence[0], endurance_confidence[0], rating_confidence[0])),
            "upper": float(max(speed_confidence[1], endurance_confidence[1], rating_confidence[1]))
        }
        
    elif history_points == 1:
        pred_speed = float(_safe_div(hist_counts[0], hist_minutes[0], default=base_speed))
        speed_slope = 0.0
        pred_count = float(hist_counts[0])
        count_slope = 0.0
        pred_bad_rate = float(_safe_div(hist_bad_moves[0], hist_counts[0], default=0.0))
        bad_slope = 0.0
        pred_endurance = 50.0  # Default baseline
        pred_rating = 50.0  # Default baseline
        trend_strength = 0.0
        confidence_interval = {"lower": 0.0, "upper": 100.0}
    else:
        pred_speed = base_speed
        speed_slope = 0.0
        pred_count = base_volume
        count_slope = 0.0
        pred_bad_rate = 1.0 - base_quality
        bad_slope = 0.0
        pred_endurance = 50.0  # Default baseline
        pred_rating = 50.0  # Default baseline
        trend_strength = 0.0
        confidence_interval = {"lower": 0.0, "upper": 100.0}

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

    if history_points >= 2:
        # Use the enhanced predictions
        predicted_endurance_score = _clamp(pred_endurance, 0.0, 100.0)
        predicted_rating = _clamp(pred_rating, 0.0, 100.0)
    else:
        # Calculate using the original method for single/no data points
        predicted_endurance_score = 100.0 * _clamp(0.55 * volume_norm + 0.45 * speed_norm, 0.0, 1.2)
        predicted_endurance_score = _clamp(predicted_endurance_score, 0.0, 100.0)

        predicted_rating = 100.0 * _clamp(0.45 * speed_norm + 0.30 * volume_norm + 0.25 * predicted_quality, 0.0, 1.2)
        predicted_rating = _clamp(predicted_rating, 0.0, 100.0)

    # Enhanced forecasting with different training loads
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
        rmse_speed=rmse_speed,
        mae_speed=mae_speed,
        r2_speed=r2_speed,
        rmse_endurance=rmse_endurance,
        mae_endurance=mae_endurance,
        r2_endurance=r2_endurance,
        rmse_rating=rmse_rating,
        mae_rating=mae_rating,
        r2_rating=r2_rating,
        performance_history=performance_history,
        trend_strength=trend_strength,
        confidence_interval=confidence_interval,
    )
