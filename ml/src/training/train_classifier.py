"""Compare and train versioned TF-IDF classifiers without replacing the baseline."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET = ROOT / "ml" / "data" / "campusfix_complaints_large.csv"


def load_dataset(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {"complaint", "category", "issue_template"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    frame = frame.dropna(subset=list(required)).copy()
    for column in required:
        frame[column] = frame[column].astype(str).str.strip()
    frame = frame[frame.complaint.ne("")].drop_duplicates(subset="complaint").reset_index(drop=True)
    if frame.category.nunique() < 2:
        raise ValueError("At least two distinct categories are required")
    return frame


def build_candidates():
    def word_vectorizer():
        return TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.98,
                               strip_accents="unicode", sublinear_tf=True)

    return {
        "linear_svc_word": Pipeline([
            ("tfidf", word_vectorizer()),
            ("classifier", LinearSVC(C=1.0, class_weight="balanced")),
        ]),
        "linear_svc_char": Pipeline([
            ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5),
                                       min_df=2, max_features=400_000, sublinear_tf=True)),
            ("classifier", LinearSVC(C=1.0, class_weight="balanced")),
        ]),
        "logistic_regression": Pipeline([
            ("tfidf", word_vectorizer()),
            ("classifier", LogisticRegression(C=4.0, max_iter=2000, class_weight="balanced")),
        ]),
        "multinomial_nb": Pipeline([
            ("tfidf", word_vectorizer()),
            ("classifier", MultinomialNB(alpha=0.1)),
        ]),
    }


def train(dataset: Path = DEFAULT_DATASET, test_size: float = 0.2, random_state: int = 42):
    frame = load_dataset(dataset)
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, test_idx = next(splitter.split(
        frame.complaint, frame.category, groups=frame.issue_template
    ))
    x_train, x_test = frame.iloc[train_idx].complaint, frame.iloc[test_idx].complaint
    y_train, y_test = frame.iloc[train_idx].category, frame.iloc[test_idx].category
    results = {}
    for name, model in build_candidates().items():
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        results[name] = {
            "accuracy": float(accuracy_score(y_test, predictions)),
            "macro_f1": float(f1_score(y_test, predictions, average="macro")),
            "weighted_f1": float(f1_score(y_test, predictions, average="weighted")),
            "classification_report": classification_report(y_test, predictions, output_dict=True, zero_division=0),
        }
    best_name = max(results, key=lambda name: results[name]["macro_f1"])
    best = build_candidates()[best_name]
    best.fit(frame.complaint, frame.category)
    version = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = sha256(dataset.read_bytes()).hexdigest()
    model_dir, report_dir = ROOT / "ml/models", ROOT / "ml/reports"
    model_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    artifact = model_dir / f"campusfix-{best_name}-{version}.joblib"
    joblib.dump(best, artifact)
    active_manifest = {
        "model_version": version,
        "artifact": artifact.name,
        "sha256": sha256(artifact.read_bytes()).hexdigest(),
        "selected_model": best_name,
        "evaluation_report": f"evaluation-{version}.json",
    }
    report = {
        "model_version": version,
        "selected_model": best_name,
        "dataset": str(dataset.relative_to(ROOT)),
        "dataset_sha256": digest,
        "rows_after_exact_deduplication": int(len(frame)),
        "classes": sorted(frame.category.unique().tolist()),
        "train_rows": int(len(train_idx)),
        "test_rows": int(len(test_idx)),
        "split_strategy": "GroupShuffleSplit grouped by issue_template",
        "random_state": random_state,
        "metrics": results,
        "artifact": str(artifact.relative_to(ROOT)),
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "limitations": [
            "The source dataset may contain synthetic templated examples; this score is not a real-world performance estimate.",
            "Collect a human-labeled campus dataset for deployment acceptance and ongoing monitoring.",
        ],
    }
    report_path = report_dir / f"evaluation-{version}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    (model_dir / "active-model.json").write_text(json.dumps(active_manifest, indent=2), encoding="utf-8")
    return report, report_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()
    evaluation, report_path = train(args.dataset, args.test_size, args.random_state)
    print(json.dumps({
        "selected_model": evaluation["selected_model"],
        "candidate_metrics": {
            name: {metric: round(values[metric], 4) for metric in ("accuracy", "macro_f1", "weighted_f1")}
            for name, values in evaluation["metrics"].items()
        },
        "artifact": evaluation["artifact"],
        "active_model_manifest": "ml/models/active-model.json",
        "report": str(report_path.relative_to(ROOT)),
    }, indent=2))
