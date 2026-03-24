from typing import Dict, List, Optional

BASE_TASKS = [
    {"title": "Log morning BP", "description": "Measure blood pressure right after waking up, before eating.", "category": "vitals", "points": 10, "priority": "high", "duration_min": 3, "trigger": "base"},
    {"title": "Log blood sugar", "description": "Record fasting glucose before breakfast.", "category": "vitals", "points": 10, "priority": "high", "duration_min": 3, "trigger": "base"},
    {"title": "Drink 8 glasses of water", "description": "Hydration supports kidney function, BP regulation, and blood sugar control.", "category": "wellness", "points": 5, "priority": "medium", "duration_min": 0, "trigger": "base"},
]


class TaskEngine:
    def generate(self, latest_vitals: Optional[Dict], vitals_trend: Optional[Dict], blood_report: Optional[Dict], bmi: Optional[float]) -> List[Dict]:
        tasks = list(BASE_TASKS)
        v = latest_vitals or {}
        r = blood_report or {}
        sys_bp = v.get("systolic_bp") or 0
        glucose = v.get("blood_glucose") or 0
        bp_trend = (vitals_trend or {}).get("bp", {}).get("systolic", {})
        bp_velocity = bp_trend.get("velocity", 0) if isinstance(bp_trend, dict) else 0

        if sys_bp >= 130:
            tasks += [
                {"title": "Reduce sodium today", "description": "Skip pickles, papad, packaged snacks. BP is elevated.", "category": "diet", "points": 15, "priority": "high", "duration_min": 0, "trigger": "bp_high"},
                {"title": "30-minute brisk walk", "description": "Walking lowers systolic BP by 4-9 mmHg.", "category": "exercise", "points": 20, "priority": "high", "duration_min": 30, "trigger": "bp_high"},
                {"title": "5-minute deep breathing", "description": "4-7-8 breathing reduces BP within minutes.", "category": "wellness", "points": 10, "priority": "medium", "duration_min": 5, "trigger": "bp_high"},
            ]
        elif sys_bp >= 120 or bp_velocity > 0.5:
            tasks += [
                {"title": "Watch salt intake today", "description": "BP is borderline or trending up. Avoid high-sodium foods.", "category": "diet", "points": 10, "priority": "medium", "duration_min": 0, "trigger": "bp_borderline"},
                {"title": "20-minute walk", "description": "Light activity helps keep BP in check.", "category": "exercise", "points": 15, "priority": "medium", "duration_min": 20, "trigger": "bp_borderline"},
            ]
        else:
            tasks.append({"title": "Maintain your BP routine", "description": "BP is normal. Keep up your current habits.", "category": "wellness", "points": 5, "priority": "low", "duration_min": 0, "trigger": "bp_normal"})

        if glucose >= 126:
            tasks += [
                {"title": "Strict carb control today", "description": "No white rice, bread, or sweets. Vegetables, protein, whole grains only.", "category": "diet", "points": 20, "priority": "urgent", "duration_min": 0, "trigger": "glucose_high"},
                {"title": "10,000 steps today", "description": "Walking after meals reduces post-meal glucose spikes.", "category": "exercise", "points": 25, "priority": "high", "duration_min": 90, "trigger": "glucose_high"},
                {"title": "Log all meals today", "description": "Track every meal to identify what spikes your sugar.", "category": "diet", "points": 15, "priority": "high", "duration_min": 5, "trigger": "glucose_high"},
            ]
        elif glucose >= 100:
            tasks += [
                {"title": "Avoid sweet fruits today", "description": "Mango, banana, grapes raise sugar quickly. Choose papaya or guava.", "category": "diet", "points": 10, "priority": "medium", "duration_min": 0, "trigger": "glucose_borderline"},
                {"title": "Post-meal 15-minute walk", "description": "Short walk after lunch and dinner reduces glucose spikes by 22%.", "category": "exercise", "points": 15, "priority": "medium", "duration_min": 15, "trigger": "glucose_borderline"},
            ]
        else:
            tasks.append({"title": "Keep up your sugar habits", "description": "Blood sugar is normal. Maintain current diet and activity.", "category": "wellness", "points": 5, "priority": "low", "duration_min": 0, "trigger": "glucose_normal"})

        platelets = r.get("platelets")
        if platelets and platelets < 1.5:
            tasks += [
                {"title": "Eat papaya leaf extract", "description": f"Platelets low ({platelets} lakhs). Papaya leaf raises platelet count.", "category": "diet", "points": 20, "priority": "urgent", "duration_min": 5, "trigger": "low_platelets"},
                {"title": "Avoid aspirin and ibuprofen", "description": "These thin blood further. Use paracetamol only if needed.", "category": "wellness", "points": 15, "priority": "urgent", "duration_min": 0, "trigger": "low_platelets"},
                {"title": "Eat pomegranate and pumpkin", "description": "Both support platelet production.", "category": "diet", "points": 10, "priority": "high", "duration_min": 0, "trigger": "low_platelets"},
            ]

        hb = r.get("hemoglobin")
        if hb and hb < 12.0:
            tasks += [
                {"title": "Iron-rich meal today", "description": f"Hemoglobin low ({hb} g/dL). Eat spinach, lentils, or red meat with Vitamin C.", "category": "diet", "points": 15, "priority": "high", "duration_min": 0, "trigger": "low_hemoglobin"},
                {"title": "Avoid tea/coffee with meals", "description": "Tannins block iron absorption. Wait 1 hour after eating.", "category": "wellness", "points": 10, "priority": "medium", "duration_min": 0, "trigger": "low_hemoglobin"},
            ]

        chol = r.get("total_cholesterol")
        ldl = r.get("ldl")
        if (chol and chol > 200) or (ldl and ldl > 100):
            tasks += [
                {"title": "No fried food today", "description": "Cholesterol elevated. Avoid all fried and processed food.", "category": "diet", "points": 15, "priority": "high", "duration_min": 0, "trigger": "high_cholesterol"},
                {"title": "Eat a bowl of oats", "description": "Beta-glucan in oats actively lowers LDL. Make it breakfast.", "category": "diet", "points": 10, "priority": "medium", "duration_min": 10, "trigger": "high_cholesterol"},
            ]

        vit_d = r.get("vitamin_d")
        if vit_d and vit_d < 30:
            tasks.append({"title": "20 min morning sunlight", "description": f"Vitamin D deficient ({vit_d} ng/mL). Morning sun before 10am is best.", "category": "wellness", "points": 10, "priority": "medium", "duration_min": 20, "trigger": "low_vitamin_d"})

        if bmi and bmi >= 25:
            tasks.append({"title": "Portion control at every meal", "description": f"BMI is {bmi:.1f}. Use a smaller plate, stop at 80% full.", "category": "diet", "points": 10, "priority": "medium", "duration_min": 0, "trigger": "high_bmi"})

        rank = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
        seen, unique = set(), []
        for t in tasks:
            if t["title"] not in seen:
                seen.add(t["title"])
                unique.append(t)
        unique.sort(key=lambda t: (rank.get(t["priority"], 9), -t["points"]))
        return unique[:10]
