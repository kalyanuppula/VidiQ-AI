
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import json

from pydantic import BaseModel
from app.services.video_processing.video_pipeline import process_video
from app.services.multimodal.visual_pipeline import analyze_video_frames
from app.services.rag.evidence_builder import build_evidence
from app.services.rag.vector_store import index_evidence
from app.services.rag.retrieval import search_evidence
from app.services.rag.rag_service import generate_grounded_answer

class QuestionRequest(BaseModel):
    question: str
    video_id: str
    top_k: int = 5



app = FastAPI(
    title="VidiQ AI",
    description="Multimodal Video Intelligence & Temporal Retrieval Platform",
    version="1.0.0",
)

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

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = PROJECT_ROOT / "data" / "raw_videos"

ALLOWED_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".mkv",
    ".webm",
    ".avi",
}


@app.get("/")
def home():
    return {
        "project": "VidiQ AI",
        "status": "running",
        "message": "Welcome to VidiQ AI",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "VidiQ AI Backend",
    }


@app.post("/api/videos/upload")
async def upload_video(file: UploadFile = File(...)):
    extension = Path(file.filename or "").suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported video format.",
        )

    video_id = uuid.uuid4().hex
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    saved_path = UPLOAD_DIR / f"{video_id}{extension}"

    try:
        with saved_path.open("wb") as destination:
            while chunk := await file.read(1024 * 1024):
                destination.write(chunk)

    except Exception:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail="Could not save uploaded video.",
        )

    finally:
        await file.close()

    return {
        "status": "uploaded",
        "video_id": video_id,
        "filename": file.filename,
        "saved_path": str(saved_path),
        "message": "Video uploaded successfully.",
    }

@app.post("/api/videos/{video_id}/process")
def process_uploaded_video(video_id: str):
    video_files = list(UPLOAD_DIR.glob(f"{video_id}.*"))

    if not video_files:
        raise HTTPException(
            status_code=404,
            detail="Uploaded video not found.",
        )

    video_path = video_files[0]
    data_dir = PROJECT_ROOT / "data"

    try:
        # 1. Extract metadata, audio, transcript and frames
        processing_result = process_video(
            video_path=str(video_path),
            data_dir=str(data_dir),
            model_size="base",
            interval_seconds=5,
        )

        # 2. Analyze extracted video frames
        frames_manifest = processing_result["frames"]["manifest"]

        visual_output_path = (
            data_dir
            / "visual_descriptions"
            / f"{video_id}_visual_analysis.json"
        )

        visual_result = analyze_video_frames(
            manifest_path=frames_manifest,
            output_path=visual_output_path,
            video_id=video_id,
        )

        # 3. Handle videos without audio
        transcript_path = (
            data_dir
            / "transcripts"
            / f"{video_path.stem}_transcript.json"
        )

        if not transcript_path.exists():
            transcript_path.parent.mkdir(parents=True, exist_ok=True)

            with transcript_path.open("w", encoding="utf-8") as file:
                json.dump({"segments": []}, file)

        # 4. Build timestamped evidence
        evidence_output_path = (
            data_dir
            / "evidence"
            / f"{video_id}_evidence.json"
        )

        evidence_result = build_evidence(
            transcript_path=transcript_path,
            visual_analysis_path=visual_output_path,
            output_path=evidence_output_path,
            video_id=video_id,
        )

        # 5. Index evidence in ChromaDB
        if not evidence_result.get("evidence"):
            return {
                "status": "partial",
                "video_id": video_id,
                "processing": processing_result,
                "visual_analysis": visual_result,
                "evidence_count": 0,
                "message": "Processing finished, but no evidence was available to index.",
            }

        indexing_result = index_evidence(
            evidence_path=evidence_output_path
        )

        return {
            "status": "completed",
            "video_id": video_id,
            "video_metadata": processing_result["video"],
            "transcription": processing_result["transcription"],
            "frames_extracted": processing_result["frames"]["total_frames"],
            "visual_analysis_status": visual_result["status"],
            "visual_descriptions": len(
                visual_result.get("visual_descriptions", [])
            ),
            "evidence_count": evidence_result["total_evidence"],
            "indexing": indexing_result,
            "message": "Video processing and indexing completed successfully.",
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Video processing failed: {str(error)}",
        ) from error

@app.post("/api/videos/ask")
def ask_video_question(request: QuestionRequest):
    try:
        # 1. Validate the question
        question = request.question.strip()

        if not question:
            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty.",
            )

        # 2. Retrieve relevant timestamped evidence
        evidence = search_evidence(
            query=question,
            top_k=request.top_k,
            video_id=request.video_id,
        )

        if not evidence:
            return {
                "status": "insufficient_evidence",
                "video_id": request.video_id,
                "question": question,
                "answer": "I could not find relevant evidence in this video.",
                "sources": [],
            }

        # 3. Generate an answer grounded in retrieved evidence
        answer_result = generate_grounded_answer(
            query=question,
            evidence=evidence,
        )

        return {
            "status": answer_result["status"],
            "video_id": request.video_id,
            "question": question,
            "answer": answer_result.get("answer"),
            "sources": answer_result.get("sources", []),
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Question answering failed: {str(error)}",
        ) from error