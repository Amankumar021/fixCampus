
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from semantic.predictor import predict_category

app = FastAPI(
    title="CampusFix Semantic AI Service",
    description="AI-powered campus complaint classification",
    version="1.0.0"
)


class ComplaintRequest(BaseModel):
    complaint: str = Field(
        min_length=5,
        max_length=2000
    )


@app.get("/")
def home():
    return {
        "message": "CampusFix Semantic AI is running",
        "status": "healthy"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model": "all-MiniLM-L6-v2"
    }


@app.post("/predict")
def predict(request: ComplaintRequest):

    try:
        result = predict_category(request.complaint)

        return {
            "success": True,
            **result
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Prediction service failed"
        )
