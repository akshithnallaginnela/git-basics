import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional


class TrainedHealthPredictor:
    """
    Loads pre-trained joblib models from backend/ml/weights/realistic/.
    Falls back gracefully if models are not yet trained.
    """

    MODEL_DIR = Path(__file__).parent / "weights" / "realistic"

    def __init__(self):
        self.risk_model = self._load("risk_model.joblib")
        self.metadata: Dict = self._load_json("metadata.json")

    # ── public API ───────────────────────────────────────────────────────────

    def predict_health_risk(self, user_vitals: Dict) -> Dict:
        if self.risk_model is None:
            return {"error": "Model not loaded — run training pipeline first"}

        features = self._features(user_vitals)
        proba = self.risk_model.predict_proba(features.reshape(1, -1))
        score = float(proba[0][1])

        return {
            "risk_score": round(score, 3),
            "risk_level": self._risk_level(score),
            "risk_factors": self._risk_factors(user_vitals),
            "interventions": self._interventions(user_vitals, score),
        }

    def recommend_diet(self, user_vitals: Dict, diet_history: List = None) -> Dict:
        recs: Dict = {
            "daily_calories": self._daily_calories(user_vitals),
            "macro_balance": self._macros(user_vitals),
            "foods_to_increase": [],
            "foods_to_avoid": [],
            "hydration": "2–3 litres water daily",
            "meal_timing": "Spread meals 4–5 hours apart",
        }

        if user_vitals.get("blood_glucose", 100) > 100:
            recs["foods_to_avoid"] += ["Refined sugars", "White bread", "Sugary drinks"]
            recs["foods_to_increase"] += ["Whole grains", "Leafy greens", "Fibre-rich foods"]

        if user_vitals.get("systolic_bp", 120) > 130:
            recs["sodium_limit"] = "< 2300 mg/day"
            recs["foods_to_increase"] += ["Potassium-rich foods (banana, spinach)", "Low-sodium options"]

        return recs

    # ── private helpers ──────────────────────────────────────────────────────

    def _features(self, v: Dict) -> np.ndarray:
        return np.array([
            v.get("systolic_bp", 120),
            v.get("diastolic_bp", 80),
            v.get("blood_glucose", 100),
            v.get("weight", 70),
            v.get("age", 40),
            v.get("activity_level", 2),
        ])

    def _risk_level(self, score: float) -> str:
        if score >= 0.8: return "Critical"
        if score >= 0.6: return "High"
        if score >= 0.4: return "Moderate"
        return "Low"

    def _risk_factors(self, v: Dict) -> List[str]:
        factors = []
        if v.get("systolic_bp", 120) > 140: factors.append("High Blood Pressure")
        if v.get("blood_glucose", 100) > 200: factors.append("Severe Hyperglycemia")
        if v.get("weight", 70) > 90: factors.append("Elevated Weight")
        return factors

    def _interventions(self, v: Dict, score: float) -> List[str]:
        items = []
        if score > 0.7:
            items += ["Daily BP monitoring", "Consult healthcare provider"]
        if v.get("blood_glucose", 100) > 150:
            items.append("Glucose monitoring twice daily")
        if v.get("activity_level", 2) < 2:
            items.append("Increase physical activity to 150 min/week")
        return items

    def _daily_calories(self, v: Dict) -> int:
        weight = v.get("weight", 70)
        activity = v.get("activity_level", 2)
        return int(weight * 24 * (0.8 + activity * 0.2))

    def _macros(self, v: Dict) -> Dict:
        cal = self._daily_calories(v)
        return {
            "protein_grams": int(cal * 0.25 / 4),
            "carbs_grams": int(cal * 0.45 / 4),
            "fats_grams": int(cal * 0.30 / 9),
        }

    def _load(self, filename: str):
        try:
            import joblib
            path = self.MODEL_DIR / filename
            return joblib.load(path) if path.exists() else None
        except Exception as e:
            print(f"[TrainedHealthPredictor] Could not load {filename}: {e}")
            return None

    def _load_json(self, filename: str) -> Dict:
        try:
            path = self.MODEL_DIR / filename
            if path.exists():
                with open(path) as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
