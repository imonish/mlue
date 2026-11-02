from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from backend.orchestration.graph import MLUEOrchestrator


orchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator

    print("Starting MLUE API...")
    orchestrator = MLUEOrchestrator()

    yield

    print("Shutting down MLUE API...")
    if orchestrator:
        orchestrator.close()


app = FastAPI(
    title="MLUE Multi-Agent Business Analytics",
    description="Ask questions about datasets using SQL, analytics, and forecasting agents.",
    version="1.0.0",
    lifespan=lifespan,
)


# Allow the React/Vite frontend to connect during development
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


class QuestionRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="A question about the loaded dataset",
    )


@app.get("/")
def home():
    return {
        "app": "MLUE",
        "status": "running",
        "message": "MLUE API is ready",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "orchestrator_loaded": orchestrator is not None,
    }


@app.post("/ask")
def ask_question(request: QuestionRequest):
    if orchestrator is None:
        raise HTTPException(
            status_code=503,
            detail="MLUE is still initializing. Try again shortly.",
        )

    try:
        result = orchestrator.run(request.question)

        # Convert pandas Timestamps and NumPy values to JSON-compatible values
        return jsonable_encoder(result)

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"MLUE processing failed: {str(error)}",
        )