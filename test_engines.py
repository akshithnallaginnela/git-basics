from backend.ml.task_engine import TaskEngine
from backend.ml.future_preventive_engine import FuturePreventiveEngine

vitals = {"systolic_bp": 124, "diastolic_bp": 82, "blood_glucose": 118, "weight": 72, "height": 175}
report = {"platelets": 1.1, "hemoglobin": 11.2, "total_cholesterol": 210}
trend  = {"bp": {"systolic": {"velocity": 0.8, "trend": "increasing"}}, "glucose": {"velocity": 0.4, "trend": "increasing"}}
bmi    = round(72 / (1.75 ** 2), 1)

tasks     = TaskEngine().generate(vitals, trend, report, bmi)
preventive = FuturePreventiveEngine().generate(trend, vitals, report)

print("=== DAILY TASKS ===")
for t in tasks:
    print(f"  [{t['priority'].upper()}] {t['title']}")

print("\n=== FUTURE PREVENTIVE CARE ===")
for p in preventive["predictions"]:
    print(f"  [score {p['urgency_score']}] {p['future_condition']} -> {p['timeframe']}")

print("\nOverall risk:", preventive["overall_future_risk"]["level"])
print("Message:", preventive["overall_future_risk"]["message"])
