"""
Run this once to train and save the risk model:
    python -m backend.ml.train_risk_model
"""
import json
import numpy as np
import joblib
from pathlib import Path
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report

WEIGHTS_DIR = Path(__file__).parent / "weights" / "realistic"
WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Synthetic realistic dataset ───────────────────────────────────────────────
# Features: [systolic, diastolic, glucose, weight, age, activity_level]
# Label: 1 = at-risk, 0 = healthy
rng = np.random.default_rng(42)
n = 2000

healthy = np.column_stack([
    rng.integers(90, 120, n // 2),    # systolic
    rng.integers(60, 80, n // 2),     # diastolic
    rng.uniform(70, 100, n // 2),     # glucose
    rng.uniform(50, 80, n // 2),      # weight
    rng.integers(20, 50, n // 2),     # age
    rng.integers(3, 5, n // 2),       # activity (high)
])

at_risk = np.column_stack([
    rng.integers(130, 180, n // 2),   # systolic high
    rng.integers(85, 110, n // 2),    # diastolic high
    rng.uniform(110, 250, n // 2),    # glucose high
    rng.uniform(80, 120, n // 2),     # weight high
    rng.integers(45, 75, n // 2),     # age higher
    rng.integers(1, 3, n // 2),       # activity low
])

X = np.vstack([healthy, at_risk])
y = np.array([0] * (n // 2) + [1] * (n // 2))

# ── Train ─────────────────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", GradientBoostingClassifier(n_estimators=100, max_depth=4, random_state=42)),
])

model.fit(X_train, y_train)

cv_scores = cross_val_score(model, X, y, cv=5, scoring="roc_auc")
print(f"CV AUC: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
print(classification_report(y_test, model.predict(X_test)))

# ── Save ──────────────────────────────────────────────────────────────────────
joblib.dump(model, WEIGHTS_DIR / "risk_model.joblib")

metadata = {
    "features": ["systolic_bp", "diastolic_bp", "blood_glucose", "weight", "age", "activity_level"],
    "classes": ["healthy", "at_risk"],
    "cv_auc_mean": round(float(cv_scores.mean()), 4),
    "cv_auc_std": round(float(cv_scores.std()), 4),
    "trained_on": str(n) + " synthetic samples",
}
with open(WEIGHTS_DIR / "metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print(f"Model saved to {WEIGHTS_DIR}")
