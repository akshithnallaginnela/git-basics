from enum import Enum
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from backend.models.health_record import VitalReading
from backend.ml.trend_analyzer import VitalTrendAnalyzer


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


_SEVERITY_RANK = {
    AlertSeverity.LOW: 0,
    AlertSeverity.MEDIUM: 1,
    AlertSeverity.HIGH: 2,
    AlertSeverity.CRITICAL: 3,
}


class PreventiveAnalysisEngine:
    """
    Generates "What your body is telling you" insights from real vitals.
    All thresholds follow WHO/AHA guidelines.
    """

    def __init__(self, db: Session, trend_analyzer: VitalTrendAnalyzer):
        self.db = db
        self.trend_analyzer = trend_analyzer

    def generate_body_status(self, user_id: int) -> Dict:
        vitals = self._latest_vitals(user_id)
        trends = {
            "bp": self.trend_analyzer.calculate_bp_trends(user_id),
            "glucose": self.trend_analyzer.calculate_glucose_trends(user_id),
        }
        alerts = self._generate_alerts(user_id, vitals, trends)
        summary = self._synthesize(vitals, trends, alerts)

        return {
            "status": summary["status"],
            "headline": summary["headline"],
            "message": summary["message"],
            "alerts": alerts,
            "recommendations": summary["recommendations"],
            "generated_at": datetime.utcnow().isoformat(),
        }

    # ── private helpers ──────────────────────────────────────────────────────

    def _latest_vitals(self, user_id: int) -> Optional[VitalReading]:
        return (
            self.db.query(VitalReading)
            .filter(VitalReading.user_id == user_id)
            .order_by(VitalReading.reading_time.desc())
            .first()
        )

    def _generate_alerts(self, user_id: int, vitals, trends: Dict) -> List[Dict]:
        alerts = []
        if vitals is None:
            return alerts

        if vitals.systolic_bp:
            category, severity = self._classify_bp(vitals.systolic_bp, vitals.diastolic_bp or 80)
            if severity in (AlertSeverity.HIGH, AlertSeverity.CRITICAL):
                alerts.append({
                    "type": "bp_alert",
                    "severity": severity,
                    "current_value": f"{vitals.systolic_bp}/{vitals.diastolic_bp}",
                    "category": category,
                    "message": f"Blood pressure is {category}",
                    "action": self._bp_action(category),
                })

        if vitals.blood_glucose:
            category, severity = self._classify_glucose(vitals.blood_glucose)
            if severity in (AlertSeverity.MEDIUM, AlertSeverity.HIGH, AlertSeverity.CRITICAL):
                alerts.append({
                    "type": "glucose_alert",
                    "severity": severity,
                    "current_value": vitals.blood_glucose,
                    "category": category,
                    "message": f"Glucose level is {category}",
                    "action": self._glucose_action(category),
                })

        bp_trend = trends.get("bp", {}).get("systolic", {})
        if isinstance(bp_trend, dict) and abs(bp_trend.get("velocity", 0)) > 2:
            alerts.append({
                "type": "bp_trend_warning",
                "severity": AlertSeverity.MEDIUM,
                "message": f"BP is trending {bp_trend['trend']}",
                "velocity": bp_trend["velocity"],
                "action": "Monitor BP more frequently; consider lifestyle changes",
            })

        return alerts

    def _classify_bp(self, sys: int, dia: int):
        if sys >= 190 or dia >= 120:
            return "BP Crisis", AlertSeverity.CRITICAL
        if sys >= 140 or dia >= 90:
            return "Stage 2 Hypertension", AlertSeverity.HIGH
        if sys >= 130 or dia >= 85:
            return "Stage 1 Hypertension", AlertSeverity.MEDIUM
        if sys >= 120 or dia >= 80:
            return "Elevated BP", AlertSeverity.LOW
        return "Normal BP", AlertSeverity.LOW

    def _classify_glucose(self, g: float):
        if g >= 400:
            return "Critical Hyperglycemia", AlertSeverity.CRITICAL
        if g >= 200:
            return "Very High Glucose", AlertSeverity.HIGH
        if g >= 126:
            return "Possible Diabetes Range", AlertSeverity.MEDIUM
        if g >= 100:
            return "Prediabetic Range", AlertSeverity.LOW
        if g < 70:
            return "Hypoglycemia Risk", AlertSeverity.HIGH
        return "Normal Glucose", AlertSeverity.LOW

    def _bp_action(self, category: str) -> str:
        return {
            "Normal BP": "Continue healthy lifestyle",
            "Elevated BP": "Reduce sodium, increase exercise",
            "Stage 1 Hypertension": "Consult doctor; lifestyle changes recommended",
            "Stage 2 Hypertension": "URGENT: Consult healthcare provider",
            "BP Crisis": "EMERGENCY: Contact emergency services",
        }.get(category, "Monitor and consult doctor")

    def _glucose_action(self, category: str) -> str:
        return {
            "Normal Glucose": "Maintain current diet and exercise",
            "Prediabetic Range": "Reduce refined carbs; increase activity",
            "Possible Diabetes Range": "Consult endocrinologist for testing",
            "Very High Glucose": "Follow treatment plan; check for complications",
            "Critical Hyperglycemia": "EMERGENCY: Seek immediate medical attention",
            "Hypoglycemia Risk": "Consume fast-acting carbs; monitor closely",
        }.get(category, "Consult healthcare provider")

    def _synthesize(self, vitals, trends: Dict, alerts: List[Dict]) -> Dict:
        if not alerts:
            return {
                "status": "healthy",
                "headline": "Your vitals look good",
                "message": "All readings are within normal ranges. Keep it up.",
                "recommendations": ["Stay hydrated", "Regular exercise", "Continue current routine"],
            }

        max_sev = max(alerts, key=lambda a: _SEVERITY_RANK.get(a["severity"], 0))["severity"]
        status_map = {
            AlertSeverity.LOW: "stable",
            AlertSeverity.MEDIUM: "caution",
            AlertSeverity.HIGH: "warning",
            AlertSeverity.CRITICAL: "alert",
        }

        headline = alerts[0]["message"] if len(alerts) == 1 else f"{len(alerts)} vitals need attention"
        message = "\n".join(f"• {a['message']}" for a in alerts)
        recommendations = [a["action"] for a in alerts if "action" in a][:3]

        return {
            "status": status_map[max_sev],
            "headline": headline,
            "message": message,
            "recommendations": recommendations,
        }
