from fastapi import FastAPI
from app.routers.IT22601360 import concepts

app = FastAPI()
app.include_router(concepts.router)

@app.get("/")
def root():
    return {"status": "AI service running"}
