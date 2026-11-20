from app.ml.inference import predict_complaint_category


def test_empty_complaint_is_not_confident():
    result = predict_complaint_category("   ")
    assert result["predicted_category"] == "Other"
    assert result["is_confident"] is False


def test_known_complaint_returns_valid_category_and_score():
    result = predict_complaint_category("The classroom fan has stopped working")
    assert result["predicted_category"] in {
        "Electrical", "Furniture", "Civil Maintenance", "Other"
    }
    assert 0.0 <= result["confidence"] <= 1.0
