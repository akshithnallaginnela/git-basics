from enum import Enum
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session

from backend.models.task import Task
from backend.models.health_record import LoginEvent
from backend.ml.preventive_analysis import PreventiveAnalysisEngine, AlertSeverity
from backend.ml.trend_analyzer import VitalTrendAnalyzer


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


_PRIORITY_RANK = {TaskPriority.URGENT: 0, TaskPriority.HIGH: 1, TaskPriority.MEDIUM: 2, TaskPriority.LOW: 3}

STANDARD_TASKS = [
    {"title": "Log Blood Pressure", "description": "Measure and record morning BP", "category": "vitals", "estimated_duration": 5, "points": 10, "priority": TaskPriority.HIGH},
    {"title": "30-Minute Walk", "description": "Take a moderate walk for cardiovascular health", "category": "exercise", "estimated_duration": 30, "points": 20, "priority": TaskPriority.MEDIUM},
    {"title": "Log Meals", "description": "Record breakfast, lunch, and dinner", "category": "diet", "estimated_duration": 10, "points": 15, "priority": TaskPriority.MEDIUM},
    {"title": "Hydration Check", "description": "Drink 7–8 glasses of water today", "category": "wellness", "estimated_duration": 0, "points": 5, "priority": TaskPriority.LOW},
    {"title": "Sleep Log", "description": "Record hours slept last night", "category": "vitals", "estimated_duration": 2, "points": 8, "priority": TaskPriority.LOW},
]


class DynamicTaskGenerator:
    """
    Generates today's task list: static daily habits + dynamic tasks
    derived from real vitals, alerts, and habit consistency.
    """

    def __init__(self, db: Session, preventive_engine: PreventiveAnalysisEngine, trend_analyzer: VitalTrendAnalyzer):
        self.db = db
        self.preventive_engine = preventive_engine
        self.trend_analyzer = trend_analyzer

    def generate_daily_tasks(self, user_id: int) -> List[Dict]:
        consistency = self._habit_consistency(user_id)

        # Scale standard tasks to engagement level
        cap = 3 if consistency < 0.3 else (5 if consistency < 0.5 else len(STANDARD_TASKS))
        standard = [dict(t) for t in STANDARD_TASKS[:cap]]

        health_status = self.preventive_engine.generate_body_status(user_id)
        alerts = health_status.get("alerts", [])

        dynamic = self._alert_tasks(alerts)
        trend_tasks = self._trend_tasks(user_id)
        habit_tasks = self._habit_tasks(consistency)

        all_tasks = standard + dynamic + trend_tasks + habit_tasks
        all_tasks = self._deduplicate_and_sort(all_tasks)
        top_tasks = all_tasks[:8]

        self._persist(user_id, top_tasks)
        return top_tasks

    # ── task builders ────────────────────────────────────────────────────────

    def _alert_tasks(self, alerts: List[Dict]) -> List[Dict]:
        tasks = []
        for alert in alerts:
            if alert.get("type") == "bp_alert" and alert.get("severity") in (AlertSeverity.HIGH, AlertSeverity.CRITICAL):
                tasks.append({
                    "title": "⚠️ Check Blood Pressure",
                    "description": f"URGENT: {alert['message']}. Measure and log your BP now.",
                    "category": "vitals", "estimated_duration": 5, "points": 50,
                    "priority": TaskPriority.URGENT, "triggered_by": "bp_alert",
                })
            elif alert.get("type") == "glucose_alert":
                tasks.append({
                    "title": "🩺 Log Blood Glucose",
                    "description": f"URGENT: {alert['message']}. Check your glucose level.",
                    "category": "vitals", "estimated_duration": 3, "points": 40,
                    "priority": TaskPriority.URGENT, "triggered_by": "glucose_alert",
                })
            elif alert.get("type") == "bp_trend_warning":
                tasks.append({
                    "title": "📊 Monitor BP Trend",
                    "description": "Your BP is trending upward. Increase monitoring frequency.",
                    "category": "vitals", "estimated_duration": 5, "points": 25,
                    "priority": TaskPriority.HIGH, "triggered_by": "bp_trend_warning",
                })
        return tasks

    def _trend_tasks(self, user_id: int) -> List[Dict]:
        tasks = []
        trends = self.trend_analyzer.calculate_bp_trends(user_id)
        if isinstance(trends.get("systolic"), dict) and trends["systolic"].get("trend") == "increasing":
            tasks.append({
                "title": "💊 Lifestyle Intervention",
                "description": "Your BP is rising. Reduce sodium and increase physical activity.",
                "category": "wellness", "estimated_duration": 30, "points": 30,
                "priority": TaskPriority.HIGH, "triggered_by": "bp_trend",
            })
        return tasks

    def _habit_tasks(self, consistency: float) -> List[Dict]:
        if consistency < 0.5:
            return [{
                "title": "🎯 Consistency Booster",
                "description": "You've missed some days. Complete 3 vitals entries to get back on track.",
                "category": "wellness", "estimated_duration": 10, "points": 15,
                "priority": TaskPriority.MEDIUM, "triggered_by": "low_consistency",
            }]
        return []

    # ── helpers ──────────────────────────────────────────────────────────────

    def _deduplicate_and_sort(self, tasks: List[Dict]) -> List[Dict]:
        seen, unique = set(), []
        for t in tasks:
            if t["title"] not in seen:
                seen.add(t["title"])
                unique.append(t)
        unique.sort(key=lambda t: (_PRIORITY_RANK.get(t.get("priority"), 99), -t.get("points", 0)))
        return unique

    def _persist(self, user_id: int, tasks: List[Dict]):
        for t in tasks:
            record = Task(
                user_id=user_id,
                title=t["title"],
                description=t.get("description", ""),
                category=t["category"],
                priority=t.get("priority", TaskPriority.MEDIUM),
                points=t.get("points", 10),
                is_dynamic=bool(t.get("triggered_by")),
                triggered_by=t.get("triggered_by"),
                expires_at=datetime.utcnow() + timedelta(days=1),
            )
            self.db.add(record)
        self.db.commit()

    def _habit_consistency(self, user_id: int) -> float:
        logins = (
            self.db.query(LoginEvent)
            .filter(
                LoginEvent.user_id == user_id,
                LoginEvent.login_time >= datetime.utcnow() - timedelta(days=7),
            )
            .count()
        )
        return min(logins / 7, 1.0)
