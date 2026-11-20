from fastapi import APIRouter
from app.schemas.schemas import MLPredictRequest, MLPredictResponse
from app.ml.inference import predict_complaint_category

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


@router.post("/predict", response_model=MLPredictResponse)
def predict_category_endpoint(payload: MLPredictRequest):
    result = predict_complaint_category(payload.description)
    return MLPredictResponse(
        predicted_category=result["predicted_category"],
        confidence=result["confidence"],
        is_confident=result["is_confident"],
        method=result["method"],
    )
