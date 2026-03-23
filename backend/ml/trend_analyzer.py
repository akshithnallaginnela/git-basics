import numpy as np
import pandas as pd
from scipy import stats
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Dict, Optional

from backend.models.health_record import VitalReading


class VitalTrendAnalyzer:
    """
    Calculates BP, glucose, and weight trends from real DB readings.
    No mock data — all calculations use actual VitalReading records.
    """

    def __init__(self, db: Session):
        self.db = db

    def calculate_bp_trends(self, user_id: int, days: int = 30) -> Dict:
        readings = (
            self.db.query(VitalReading)
            .filter(
                VitalReading.user_id == user_id,
                VitalReading.reading_time >= datetime.utcnow() - timedelta(days=days),
                VitalReading.systolic_bp.isnot(None),
            )
            .order_by(VitalReading.reading_time)
            .all()
        )

        if len(readings) < 2:
            return {"error": "Insufficient data", "data_points": len(readings)}

        df = pd.DataFrame(
            [{"systolic": r.systolic_bp, "diastolic": r.diastolic_bp} for r in readings]
        )

        result = {}
        for col, normal_range in [("systolic", (90, 120)), ("diastolic", (60, 80))]:
            values = df[col].dropna().values
            x = np.arange(len(values))
            slope, _, r_value, p_value, std_err = stats.linregress(x, values)

            trend = "stable"
            if p_value < 0.05:
                trend = "increasing" if slope > 0 else "decreasing"

            result[col] = {
                "trend": trend,
                "velocity": round(float(slope), 3),
                "avg": round(float(np.mean(values)), 1),
                "min": round(float(np.min(values)), 1),
                "max": round(float(np.max(values)), 1),
                "std_dev": round(float(np.std(values)), 2),
                "r_squared": round(float(r_value ** 2), 3),
                "data_points": len(values),
                "confidence_score": round(self._confidence(len(values), r_value, std_err), 2),
                "last_reading": float(values[-1]),
                "normal_range": normal_range,
            }

        return result

    def calculate_glucose_trends(self, user_id: int, days: int = 30) -> Dict:
        readings = (
            self.db.query(VitalReading)
            .filter(
                VitalReading.user_id == user_id,
                VitalReading.reading_time >= datetime.utcnow() - timedelta(days=days),
                VitalReading.blood_glucose.isnot(None),
            )
            .order_by(VitalReading.reading_time)
            .all()
        )

        if len(readings) < 2:
            return {"error": "Insufficient glucose data", "data_points": len(readings)}

        values = np.array([r.blood_glucose for r in readings])
        x = np.arange(len(values))
        slope, _, r_value, p_value, std_err = stats.linregress(x, values)

        trend = "stable"
        if p_value < 0.05:
            trend = "increasing" if slope > 0 else "decreasing"

        return {
            "trend": trend,
            "velocity": round(float(slope), 3),
            "avg": round(float(np.mean(values)), 1),
            "min": round(float(np.min(values)), 1),
            "max": round(float(np.max(values)), 1),
            "std_dev": round(float(np.std(values)), 2),
            "last_reading": float(values[-1]),
            "normal_range": (70, 100),
            "data_points": len(values),
            "confidence_score": round(self._confidence(len(values), r_value, std_err), 2),
        }

    def detect_anomalies(self, user_id: int, vital_type: str) -> Dict:
        readings = (
            self.db.query(VitalReading)
            .filter(VitalReading.user_id == user_id)
            .order_by(VitalReading.reading_time.desc())
            .limit(100)
            .all()
        )

        if len(readings) < 5:
            return {"error": "Insufficient data for anomaly detection"}

        values = [getattr(r, vital_type) for r in readings if getattr(r, vital_type) is not None]
        if len(values) < 5:
            return {"error": f"No {vital_type} data found"}

        arr = np.array(values)
        z_scores = np.abs(stats.zscore(arr))
        anomaly_indices = np.where(z_scores > 3)[0]

        return {
            "anomalies_detected": len(anomaly_indices),
            "anomaly_values": arr[anomaly_indices].tolist(),
            "severity": "high" if len(anomaly_indices) > 0 else "none",
        }

    def _confidence(self, n: int, r_value: float, std_err: float) -> float:
        data_conf = min(n / 30, 1.0)
        trend_conf = abs(r_value)
        err_conf = 1.0 / (1.0 + std_err)
        return data_conf * 0.4 + trend_conf * 0.4 + err_conf * 0.2
