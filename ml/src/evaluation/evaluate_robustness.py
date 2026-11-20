"""Small diagnostic suite for typos, paraphrases, and unknown complaints."""
from __future__ import annotations

import json
from pathlib import Path

from sklearn.metrics import accuracy_score, classification_report, f1_score

from ml.src.training.train_classifier import ROOT

CASES = [
    ("The wifi keeps disconnecting in the library", "IT"),
    ("WiFi is not conecting in our library", "IT"),
    ("No network access in the computer lab", "IT"),
    ("Water is leaking under the sink", "Plumbing"),
    ("The basin tap drips all night", "Plumbing"),
    ("The bathroom toilet is blocked", "Sanitation"),
    ("Washroom has an unpleasant sewage smell", "Sanitation"),
    ("The classroom fan stopped working", "Electrical"),
    ("The air conditioner blows warm air", "Electrical"),
    ("Several chairs have broken legs", "Furniture"),
    ("A desk is unstable and wobbles", "Furniture"),
    ("There is a crack in the classroom ceiling", "Civil Maintenance"),
    ("The corridor wall plaster is falling", "Civil Maintenance"),
    ("Trash bins have not been emptied", "Cleanliness"),
    ("Classroom floor is dusty and dirty", "Cleanliness"),
    ("The gate has no security guard", "Security"),
    ("Someone stole a bicycle from campus", "Security"),
    ("The canteen food was stale", "Cafeteria"),
    ("Cafeteria service is too slow", "Cafeteria"),
    ("Need help choosing classes for next term", "Other"),
    ("I forgot my personal email password", "Other"),
    ("Please tell me the exam timetable", "Other"),
]


def main():
    model_path = Path(__import__("app.core.config", fromlist=["settings"]).settings.ML_MODEL_PATH)
    if not model_path.is_absolute():
        model_path = ROOT / model_path
    import joblib
    if model_path.suffix.lower() == ".json":
        manifest = json.loads(model_path.read_text(encoding="utf-8"))
        model_path = model_path.parent / manifest["artifact"]
    model = joblib.load(model_path)
    actual = [expected for _, expected in CASES]
    import numpy as np
    predicted, confidence = [], []
    for text, _ in CASES:
        label = str(model.predict([text])[0])
        score = 1.0
        if hasattr(model, "decision_function"):
            ordered = np.sort(np.atleast_1d(model.decision_function([text])[0]))
            margin = float(ordered[-1] - ordered[-2]) if len(ordered) > 1 else 0.0
            score = float(1.0 / (1.0 + np.exp(-min(max(margin, -20.0), 20.0))))
            if margin < 0.45:
                label = "Other"
        predicted.append(label)
        confidence.append(score)
    known = [(truth, pred) for truth, pred in zip(actual, predicted) if truth != "Other"]
    report = {
        "cases": len(CASES),
        "known_category_cases": len(known),
        "known_category_accuracy": float(accuracy_score(*zip(*known))),
        "known_category_macro_f1": float(f1_score(
            [truth for truth, _ in known], [pred for _, pred in known], average="macro"
        )),
        "unknown_case_predictions": [pred for pred, truth in zip(predicted, actual) if truth == "Other"],
        "classification_report": classification_report(actual, predicted, output_dict=True, zero_division=0),
        "predictions": [
            {"complaint": text, "expected": truth, "predicted": pred, "confidence_signal": round(score, 4), "correct": truth == pred}
            for (text, truth), pred, score in zip(CASES, predicted, confidence)
        ],
        "limitations": "Small manually written diagnostic set; not a real-world accuracy estimate.",
    }
    output = ROOT / "ml/reports/robustness-results.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("cases", "known_category_accuracy", "known_category_macro_f1", "unknown_case_predictions", "limitations")}, indent=2))
    print(f"Detailed results: {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
