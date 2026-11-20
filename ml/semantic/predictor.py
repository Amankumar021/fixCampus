
from sklearn.metrics.pairwise import cosine_similarity

try:
    from semantic.categories import CATEGORIES
except ModuleNotFoundError:
    from ml.semantic.categories import CATEGORIES

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

model = None
category_embeddings = {}


def _load_model_and_embeddings():
    global model, category_embeddings

    if model is not None and category_embeddings:
        return model, category_embeddings

    if SentenceTransformer is None:
        raise ImportError(
            "sentence-transformers is required to run CampusFix semantic prediction."
        )

    print("Loading semantic AI model...")
    model = SentenceTransformer(MODEL_NAME)

    print("Generating category embeddings...")
    category_embeddings = {}

    for category, descriptions in CATEGORIES.items():
        embeddings = model.encode(
            descriptions,
            normalize_embeddings=True
        )
        category_embeddings[category] = embeddings

    print("CampusFix Semantic AI is ready!")
    return model, category_embeddings


def predict_category(complaint):

    if not complaint or not complaint.strip():
        raise ValueError("Complaint cannot be empty")

    model, category_embeddings = _load_model_and_embeddings()

    complaint_embedding = model.encode(
        [complaint],
        normalize_embeddings=True
    )

    scores = {}

    for category, embeddings in category_embeddings.items():

        similarities = cosine_similarity(
            complaint_embedding,
            embeddings
        )[0]

        # Average the two strongest matching descriptions
        top_scores = sorted(similarities, reverse=True)[:2]

        scores[category] = float(sum(top_scores) / len(top_scores))

    ranked = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True
    )

    best_category, best_score = ranked[0]

    second_score = ranked[1][1]

    return {
        "complaint": complaint,
        "predicted_category": best_category,
        "similarity_score": round(best_score, 4),
        "margin": round(best_score - second_score, 4),
        "alternatives": [
            {
                "category": category,
                "similarity": round(score, 4)
            }
            for category, score in ranked[:3]
        ]
    }


if __name__ == "__main__":

    while True:

        complaint = input("\nEnter complaint (or exit): ")

        if complaint.lower() == "exit":
            break

        try:
            result = predict_category(complaint)

            print("\nPrediction:", result["predicted_category"])
            print("Similarity:", result["similarity_score"])
            print("Margin:", result["margin"])

            print("\nAlternative categories:")

            for item in result["alternatives"]:
                print(item)

        except ValueError as error:
            print(error)
