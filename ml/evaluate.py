
from pathlib import Path

import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

try:
    from semantic.predictor import predict_category
except ModuleNotFoundError:
    from ml.semantic.predictor import predict_category


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def main():
    # Load evaluation dataset
    df = pd.read_csv(DATA_DIR / "semantic_test.csv")

    y_true = []
    y_pred = []

    print("\nCAMPUSFIX SEMANTIC AI EVALUATION")
    print("=" * 55)

    for _, row in df.iterrows():

        complaint = row["complaint"]
        actual = row["actual_category"]

        result = predict_category(complaint)

        predicted = result["predicted_category"]

        y_true.append(actual)
        y_pred.append(predicted)

        status = "PASS" if actual == predicted else "FAIL"

        print(f"\nComplaint: {complaint}")
        print(f"Actual: {actual}")
        print(f"Predicted: {predicted}")
        print(f"Similarity: {result['similarity_score']}")
        print(f"Result: {status}")

    # Evaluation metrics
    accuracy = accuracy_score(y_true, y_pred)

    print("\n" + "=" * 55)
    print("FINAL EVALUATION")
    print("=" * 55)

    print(f"\nAccuracy: {accuracy * 100:.2f}%")

    print("\nClassification Report:")

    print(
        classification_report(
            y_true,
            y_pred,
            zero_division=0
        )
    )

    labels = sorted(df["actual_category"].unique())

    print("\nConfusion Matrix:")

    print(
        confusion_matrix(
            y_true,
            y_pred,
            labels=labels
        )
    )

    # Save predictions
    df["predicted_category"] = y_pred
    df["correct"] = df["actual_category"] == df["predicted_category"]

    output_path = DATA_DIR / "evaluation_results.csv"
    df.to_csv(output_path, index=False)

    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
