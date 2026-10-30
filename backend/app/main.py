from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="VidiQ AI",
    description="Multimodal Video Intelligence & Temporal Retrieval Platform",
    version="1.0.0"
)

# Allow the React frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "project": "VidiQ AI",
        "status": "running",
        "message": "Welcome to VidiQ AI"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "VidiQ AI Backend"
    }