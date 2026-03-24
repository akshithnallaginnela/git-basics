"""
FUTURE PREVENTIVE CARE ENGINE
==============================
This engine does NOT describe the current situation.
It looks at current BP + sugar trends + blood report values
and predicts what COULD go wrong in the future if habits don't change,
then gives specific precautions to prevent that future outcome.

Logic:
  current data → risk trajectory → future risk prediction → preventive actions
"""
from typing import Dict, List, Optional
from datetime import datetime


# ── Reference ranges ──────────────────────────────────────────────────────────
NORMAL = {
    "systolic":         (90, 120),
    "diastolic":        (60, 80),
    "blood_glucose":    (70, 100),
    "hemoglobin":       (12.0, 17.5),
    "platelets":        (1.5, 4.0),      # lakhs/µL
    "wbc":              (4.0, 11.0),
    "total_cholesterol":(0, 200),
    "ldl":              (0, 100),
    "hdl":              (40, 999),
    "triglycerides":    (0, 150),
    "creatinine":       (0.6, 1.2),
    "hba1c":            (0, 5.7),
    "tsh":              (0.4, 4.0),
    "vitamin_d":        (30, 100),
    "vitamin_b12":      (200, 900),
}


class FuturePreventiveEngine:
    """
    Generates future-focused preventive care cards.
    Each card = one predicted future risk + precautions to avoid it.
    """

    def generate(self, vitals_trend: Dict, latest_vitals: Dict, blood_report: Optional[Dict]) -> Dict:
        """
        Main entry point.
        Returns: { predictions: [...], overall_future_risk, generated_at }
        """
        predictions = []

        # 1. BP-based future predictions
        predictions += self._bp_future(vitals_trend, latest_vitals)

        # 2. Sugar-based future predictions
        predictions += self._sugar_future(vitals_trend, latest_vitals)

        # 3. Blood report-based future predictions
        if blood_report:
            predictions += self._report_future(blood_report, latest_vitals)

        # 4. Combined risk (e.g. BP + sugar together = higher CVD risk)
        predictions += self._combined_future(latest_vitals, blood_report)

        # Sort by urgency
        predictions.sort(key=lambda x: x["urgency_score"], reverse=True)

        return {
            "predictions": predictions[:6],  # top 6 future risks
            "overall_future_risk": self._overall_risk(predictions),
            "generated_at": datetime.utcnow().isoformat(),
        }

    # ── BP future predictions ─────────────────────────────────────────────────

    def _bp_future(self, trend: Dict, vitals: Dict) -> List[Dict]:
        results = []
        sys = vitals.get("systolic_bp")
        dia = vitals.get("diastolic_bp")
        if not sys:
            return results

        bp_trend = trend.get("bp", {}).get("systolic", {})
        velocity = bp_trend.get("velocity", 0) if isinstance(bp_trend, dict) else 0

        # Normal BP but trending up → future hypertension risk
        if 110 <= sys <= 125 and velocity > 0.5:
            results.append({
                "future_condition": "Hypertension",
                "timeframe": "3–6 months",
                "current_signal": f"BP is {sys}/{dia} — normal now, but rising at {velocity:.1f} pts/reading",
                "future_risk": "If this trend continues, BP could reach Stage 1 Hypertension (130+) within months",
                "urgency_score": 55,
                "precautions": [
                    "Reduce daily sodium intake to under 2g",
                    "Walk 30 minutes every day — even a slow walk counts",
                    "Avoid processed and packaged foods",
                    "Practice 5 minutes of deep breathing daily to reduce vascular stress",
                    "Re-check BP every 3 days and track the trend",
                ],
                "why_this_matters": "Hypertension is called the silent killer — it damages arteries slowly before symptoms appear",
            })

        # Elevated BP → future stroke / kidney risk
        if sys >= 130:
            results.append({
                "future_condition": "Stroke / Kidney Damage",
                "timeframe": "1–3 years if unmanaged",
                "current_signal": f"BP is {sys}/{dia} — consistently elevated",
                "future_risk": "Sustained high BP damages arterial walls and kidney filtration over time",
                "urgency_score": 75,
                "precautions": [
                    "Consult a doctor for BP management plan",
                    "DASH diet: more fruits, vegetables, low-fat dairy",
                    "Limit alcohol completely",
                    "Reduce stress — chronic stress directly raises BP",
                    "Monitor BP daily at the same time each morning",
                ],
                "why_this_matters": "Every 20 mmHg rise in systolic BP doubles the risk of cardiovascular events",
            })

        return results

    # ── Sugar future predictions ──────────────────────────────────────────────

    def _sugar_future(self, trend: Dict, vitals: Dict) -> List[Dict]:
        results = []
        glucose = vitals.get("blood_glucose")
        if not glucose:
            return results

        glucose_trend = trend.get("glucose", {})
        velocity = glucose_trend.get("velocity", 0) if isinstance(glucose_trend, dict) else 0

        # Normal glucose but trending up → prediabetes risk
        if 90 <= glucose <= 105 and velocity > 0.3:
            results.append({
                "future_condition": "Prediabetes",
                "timeframe": "6–12 months",
                "current_signal": f"Blood sugar is {glucose} mg/dL — acceptable now, but creeping up",
                "future_risk": "At this rate, glucose could enter prediabetic range (100–125) within months",
                "urgency_score": 50,
                "precautions": [
                    "Cut out sugary drinks and fruit juices completely",
                    "Replace white rice/bread with whole grains",
                    "Walk 10,000 steps daily — this alone reduces diabetes risk by 30%",
                    "Eat smaller meals more frequently to avoid glucose spikes",
                    "Avoid sweet fruits like mango, banana, grapes in large quantities",
                ],
                "why_this_matters": "Prediabetes is reversible — but only if caught and acted on early",
            })

        # Prediabetic range → Type 2 Diabetes risk
        if 100 <= glucose <= 125:
            results.append({
                "future_condition": "Type 2 Diabetes",
                "timeframe": "1–2 years if habits don't change",
                "current_signal": f"Blood sugar is {glucose} mg/dL — in prediabetic range",
                "future_risk": "Without lifestyle changes, 15–30% of prediabetics develop Type 2 Diabetes within 5 years",
                "urgency_score": 70,
                "precautions": [
                    "Get HbA1c tested — it shows your 3-month sugar average",
                    "Strictly avoid refined carbohydrates and sweets",
                    "Exercise 150 minutes per week minimum",
                    "Lose 5–7% of body weight if overweight — this is clinically proven to prevent diabetes",
                    "Eat more fiber: vegetables, legumes, oats",
                    "Check fasting glucose every month",
                ],
                "why_this_matters": "Type 2 Diabetes is largely preventable — your window to act is now",
            })

        # High glucose → complications risk
        if glucose > 125:
            results.append({
                "future_condition": "Diabetic Complications (Neuropathy / Retinopathy)",
                "timeframe": "5–10 years if uncontrolled",
                "current_signal": f"Blood sugar is {glucose} mg/dL — above diabetic threshold",
                "future_risk": "Chronic high glucose damages nerves, eyes, and kidneys over years",
                "urgency_score": 85,
                "precautions": [
                    "Consult an endocrinologist immediately",
                    "Get HbA1c, kidney function, and eye exam done",
                    "Strict carbohydrate counting — aim for <45g carbs per meal",
                    "Daily foot inspection for numbness or wounds",
                    "Blood sugar monitoring twice daily",
                ],
                "why_this_matters": "Diabetic complications are irreversible — prevention is the only cure",
            })

        return results

    # ── Blood report future predictions ──────────────────────────────────────

    def _report_future(self, report: Dict, vitals: Dict) -> List[Dict]:
        results = []

        # Low platelets → bleeding risk
        platelets = report.get("platelets")
        if platelets and platelets < 1.5:
            results.append({
                "future_condition": "Bleeding Disorder / Dengue Vulnerability",
                "timeframe": "Immediate risk — monitor closely",
                "current_signal": f"Platelets: {platelets} lakhs/µL — below normal (1.5–4.0)",
                "future_risk": "Low platelets increase risk of internal bleeding, slow wound healing, and severe dengue complications",
                "urgency_score": 90,
                "precautions": [
                    "Avoid aspirin, ibuprofen, and blood thinners completely",
                    "Eat papaya leaf extract — clinically shown to raise platelet count",
                    "Include pomegranate, pumpkin, and leafy greens in diet",
                    "Avoid contact sports or activities with injury risk",
                    "Re-test CBC in 1 week",
                    "Consult a hematologist if platelets drop below 1.0",
                ],
                "why_this_matters": "Platelet count below 1.0 lakh is a medical emergency",
            })

        # Low hemoglobin → anemia → heart strain
        hb = report.get("hemoglobin")
        if hb and hb < 12.0:
            results.append({
                "future_condition": "Severe Anemia / Heart Strain",
                "timeframe": "2–4 months if untreated",
                "current_signal": f"Hemoglobin: {hb} g/dL — below normal",
                "future_risk": "Chronic anemia forces the heart to pump harder, increasing long-term cardiac risk",
                "urgency_score": 72,
                "precautions": [
                    "Increase iron-rich foods: spinach, lentils, red meat, tofu",
                    "Take iron supplements with Vitamin C for better absorption",
                    "Avoid tea/coffee with meals — they block iron absorption",
                    "Get iron, ferritin, and B12 levels tested",
                    "If vegetarian, consider B12 supplementation",
                ],
                "why_this_matters": "Untreated anemia leads to fatigue, poor immunity, and cardiac complications",
            })

        # High cholesterol → future atherosclerosis
        chol = report.get("total_cholesterol")
        ldl = report.get("ldl")
        if (chol and chol > 200) or (ldl and ldl > 100):
            results.append({
                "future_condition": "Atherosclerosis / Heart Attack",
                "timeframe": "5–15 years if unmanaged",
                "current_signal": f"Cholesterol: {chol or '—'} mg/dL, LDL: {ldl or '—'} mg/dL",
                "future_risk": "High LDL slowly builds plaque in arteries, narrowing them over years until a blockage causes a heart attack",
                "urgency_score": 68,
                "precautions": [
                    "Eliminate trans fats: no fried food, margarine, or packaged snacks",
                    "Eat oats daily — beta-glucan in oats actively lowers LDL",
                    "Add omega-3: fish, flaxseed, walnuts",
                    "Exercise 30 minutes 5 days a week",
                    "Recheck lipid panel in 3 months",
                ],
                "why_this_matters": "Atherosclerosis is silent for decades — by the time symptoms appear, damage is severe",
            })

        # High creatinine → future kidney failure
        creat = report.get("creatinine")
        if creat and creat > 1.2:
            results.append({
                "future_condition": "Chronic Kidney Disease",
                "timeframe": "3–10 years if BP and sugar uncontrolled",
                "current_signal": f"Creatinine: {creat} mg/dL — above normal (0.6–1.2)",
                "future_risk": "Elevated creatinine signals reduced kidney filtration. Combined with high BP or sugar, this accelerates kidney damage",
                "urgency_score": 78,
                "precautions": [
                    "Drink 2.5–3 litres of water daily",
                    "Strictly control BP — it is the #1 cause of kidney damage",
                    "Reduce protein intake slightly — excess protein strains kidneys",
                    "Avoid NSAIDs (ibuprofen, diclofenac) — they damage kidneys",
                    "Get eGFR and urine microalbumin tested",
                ],
                "why_this_matters": "Kidney damage is irreversible — prevention is the only option",
            })

        # Low Vitamin D → future bone / immune risk
        vit_d = report.get("vitamin_d")
        if vit_d and vit_d < 30:
            results.append({
                "future_condition": "Osteoporosis / Immune Weakness",
                "timeframe": "5–10 years",
                "current_signal": f"Vitamin D: {vit_d} ng/mL — deficient (normal: 30–100)",
                "future_risk": "Chronic Vitamin D deficiency leads to bone density loss and weakened immunity",
                "urgency_score": 45,
                "precautions": [
                    "Get 20 minutes of morning sunlight daily",
                    "Take Vitamin D3 + K2 supplement (consult doctor for dosage)",
                    "Eat fatty fish, egg yolks, fortified milk",
                    "Retest Vitamin D in 3 months after supplementation",
                ],
                "why_this_matters": "Over 70% of Indians are Vitamin D deficient — it affects bone, heart, and immune health",
            })

        # High TSH → future hypothyroidism
        tsh = report.get("tsh")
        if tsh and tsh > 4.0:
            results.append({
                "future_condition": "Hypothyroidism",
                "timeframe": "1–3 years",
                "current_signal": f"TSH: {tsh} µIU/mL — above normal (0.4–4.0)",
                "future_risk": "Elevated TSH indicates the thyroid is struggling. Left untreated, it leads to weight gain, fatigue, and depression",
                "urgency_score": 60,
                "precautions": [
                    "Get Free T3, Free T4 tested along with TSH",
                    "Consult an endocrinologist",
                    "Eat selenium-rich foods: Brazil nuts, sunflower seeds",
                    "Avoid raw cruciferous vegetables in excess (broccoli, cabbage)",
                    "Retest TSH in 6 weeks",
                ],
                "why_this_matters": "Subclinical hypothyroidism is easily managed if caught early",
            })

        return results

    # ── Combined risk predictions ─────────────────────────────────────────────

    def _combined_future(self, vitals: Dict, report: Optional[Dict]) -> List[Dict]:
        results = []
        sys = vitals.get("systolic_bp", 0) or 0
        glucose = vitals.get("blood_glucose", 0) or 0
        chol = (report or {}).get("total_cholesterol", 0) or 0

        # BP + Sugar together → high CVD risk
        if sys >= 125 and glucose >= 100:
            results.append({
                "future_condition": "Cardiovascular Disease (Heart Attack / Stroke)",
                "timeframe": "5–10 years",
                "current_signal": f"BP {sys} + Glucose {glucose} — both elevated simultaneously",
                "future_risk": "Having both high BP and high sugar together multiplies cardiovascular risk by 4x compared to either alone",
                "urgency_score": 88,
                "precautions": [
                    "This combination requires a doctor's review — book an appointment",
                    "Mediterranean diet: olive oil, fish, vegetables, whole grains",
                    "Zero tolerance for smoking",
                    "Daily 30-minute brisk walk — the single most effective intervention",
                    "Annual ECG and stress test after age 40",
                    "Track both BP and sugar daily",
                ],
                "why_this_matters": "The combination of hypertension and diabetes is the leading cause of heart attacks in India",
            })

        return results

    # ── Overall risk summary ──────────────────────────────────────────────────

    def _overall_risk(self, predictions: List[Dict]) -> Dict:
        if not predictions:
            return {
                "level": "low",
                "message": "Your current readings look good. Keep your habits consistent to stay this way.",
                "score": 15,
            }

        max_score = max(p["urgency_score"] for p in predictions)
        count = len(predictions)

        if max_score >= 85 or count >= 4:
            level, msg = "high", "Multiple future risks detected. Preventive action needed now."
        elif max_score >= 60 or count >= 2:
            level, msg = "moderate", "Some future risks identified. Small habit changes now prevent big problems later."
        else:
            level, msg = "low", "Minor future risks. Stay consistent with healthy habits."

        return {"level": level, "message": msg, "score": max_score}
