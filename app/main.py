from fastapi import FastAPI
from app.routers.IT22601360 import concepts, concept_extractor

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(concepts.router)
app.include_router(concept_extractor.router, prefix="/api/IT22601360", tags=["IT22601360"])

@app.get("/")
def root():
    return {"status": "AI service running"}
