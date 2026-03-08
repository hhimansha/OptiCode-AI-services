from fastapi import APIRouter
from app.services.IT22601360.llm_service import extract_concepts

router = APIRouter(prefix="/concepts", tags=["Concept Extraction"])

@router.post("/extract")
def extract(data: dict):
    code = data["code"]
    return extract_concepts(code)
