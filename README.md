# OptiCode-AI-services

# Python AI Services (FastAPI)

## Run locally
pip install -r requirements.txt
uvicorn app.main:app --reload

## API Endpoint
POST /concepts/extract
{
   "code": "print('Hello')"
}

## Environment
Copy .env.example → .env and add your API keys
