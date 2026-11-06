# VidiQ AI
### Multimodal Video Intelligence & Temporal Retrieval Platform

<p align="center">
  <strong>Turn long training and operational videos into searchable, timestamped knowledge.</strong>
</p>

<p align="center">
  <a href="https://vidi-q-ai.vercel.app/">Live UI Preview</a> ·
  <a href="#demo">Watch the Demo</a> ·
  <a href="#run-locally-with-docker">Run Locally</a>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white">
  <img alt="React" src="https://img.shields.io/badge/React-Frontend-61DAFB?logo=react&logoColor=black">
  <img alt="Docker" src="https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker&logoColor=white">
  <img alt="Status" src="https://img.shields.io/badge/Status-Local%20Demo%20Ready-success">
</p>

---

## Overview

Organizations create hours of employee-training, workplace-safety, and operational videos. However, finding one specific instruction or event inside a long recording can be slow and frustrating.

**VidiQ AI** is a multimodal video intelligence platform that makes video content searchable using natural language. It processes speech and visual information, organizes evidence with timestamps, and answers questions using relevant moments from the video.

Instead of returning only a generic summary, VidiQ AI is designed to help users find **what happened, where it happened, and the video moment that supports the answer**.

## Demo

> **The best way to evaluate VidiQ AI is to watch the complete workflow.** The demonstration video will show a video being uploaded and processed, questions being asked, evidence being returned, and timestamp controls navigating to the relevant moments.

<!-- Replace the URL below after publishing your LinkedIn demo. -->
**Full project walkthrough:** [Watch the VidiQ AI demonstration on LinkedIn]

### Screenshots

Add real screenshots from your running application to `docs/assets/` and update the filenames below.

<p align="center">
  <img src="docs/assets/dashboard.png" alt="VidiQ AI dashboard" width="90%">
  <br>
  <em>VidiQ AI dashboard — video upload and analysis workspace</em>
</p>

<p align="center">
  <img src="docs/assets/processing-results.png" alt="Video processing results" width="90%">
  <br>
  <em>Video processing results and extracted evidence</em>
</p>

<p align="center">
  <img src="docs/assets/question-answering.png" alt="Grounded question answering with timestamps" width="90%">
  <br>
  <em>Question answering with timestamp-based evidence</em>
</p>

## Key Features

- **Video upload and processing:** Upload supported video files for analysis.
- **Audio transcription:** Extract speech and generate timestamped transcript segments using Faster-Whisper.
- **Visual understanding:** Extract video frames with FFmpeg and analyze them using a vision-capable Gemini model.
- **Timestamp-aware evidence:** Combine transcript and visual descriptions into timestamped evidence records.
- **Hybrid retrieval:** Retrieve relevant evidence using semantic similarity and BM25 keyword search, combined with Reciprocal Rank Fusion (RRF).
- **Grounded question answering:** Ask natural-language questions and generate answers based on retrieved video evidence.
- **Evidence references:** Responses include timestamps and evidence references to help users inspect the source.
- **Video timestamp navigation:** Select a timestamp in the results to jump to the corresponding point in the video.
- **Insufficient-evidence handling:** The system can indicate when the available video evidence does not support an answer.

## How It Works

```text
                 Video Upload
                      |
                      v
          Video Metadata and Validation
                      |
             +--------+--------+
             |                 |
             v                 v
        Audio Extraction   Frame Extraction
             |                 |
             v                 v
       Whisper Speech      Gemini Visual
       Transcription        Understanding
             |                 |
             +--------+--------+
                      |
                      v
           Timestamped Evidence Builder
                      |
                      v
             Embeddings + BM25
                      |
                      v
             Hybrid Retrieval (RRF)
                      |
                      v
           Grounded Gemini Answering
                      |
                      v
        Answer + Evidence Timestamps
                      |
                      v
           Frontend Video Navigation
```

## Technology Stack

| Area | Technologies |
|---|---|
| Backend API | Python, FastAPI |
| Video and audio processing | FFmpeg, FFprobe |
| Speech transcription | Faster-Whisper |
| Visual understanding and answer generation | Google Gemini API |
| Embeddings | Sentence Transformers (`all-MiniLM-L6-v2`) |
| Vector storage | ChromaDB |
| Keyword retrieval | BM25 (`rank-bm25`) |
| Hybrid ranking | Reciprocal Rank Fusion (RRF) |
| Frontend | React, Vite, JavaScript |
| Containerization | Docker |
| Testing | Pytest |
| Version control | Git, GitHub |
| Frontend hosting | Vercel |
| Backend hosting | Render |

## Architecture and Engineering Notes

- **Separate processing stages:** Metadata extraction, audio transcription, frame extraction, visual analysis, evidence construction, retrieval, and answer generation are organized into backend services.
- **Multimodal evidence:** Transcript segments and visual descriptions are represented as timestamped evidence.
- **Hybrid search:** Semantic retrieval helps find conceptually related content, while BM25 supports exact terms and keyword matching. RRF combines the rankings.
- **Grounded responses:** The answer-generation stage receives retrieved evidence and validates timestamp/evidence references. It is designed to avoid inventing details when the video does not provide enough support.
- **Local and containerized execution:** The complete processing workflow has been tested locally, including through the project's Docker image.

**Important:** A transcript segment associated with a nearby frame is a time-based association, not proof that the frame visually confirms the spoken statement.

## Run Locally with Docker

The complete application is intended to be run locally for video processing. The Docker image contains the backend and FFmpeg; run the React frontend separately during local development.

### Prerequisites

- Docker Desktop
- Node.js and npm
- A Google Gemini API key

### 1. Clone the repository

```bash
git clone https://github.com/kalyanuppula/VidiQ-AI.git
cd VidiQ-AI
```

### 2. Configure the Gemini API key

Create or obtain a Gemini API key from [Google AI Studio](https://aistudio.google.com/).

Keep the key private. Do not commit it to GitHub or place it in frontend code.

### 3. Build the backend Docker image

Run this command from the repository root:

```bash
docker build -t vidiq-ai-backend .
```

### 4. Start the backend container

```bash
docker run --rm -p 8000:8000 \
  -e GEMINI_API_KEY="YOUR_GEMINI_API_KEY" \
  vidiq-ai-backend
```

The backend API should now be available at:

- API: `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`

### 5. Start the frontend

Open a second terminal:

```bash
cd frontend
npm install
```

Create `frontend/.env.local` with:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Then start the frontend:

```bash
npm run dev
```

Open the local URL printed by Vite (normally `http://localhost:5173`).

> **Note:** Never commit `.env`, `.env.local`, API keys, uploaded private videos, or generated data to the repository.

## Hosted Preview and Processing Limitation

The project has a hosted frontend preview and a deployed backend:

- **Frontend preview:** https://vidi-q-ai.vercel.app/
- **Backend service:** https://vidiq-ai-backend.onrender.com

The hosted frontend is provided to demonstrate the interface. **Full video processing is not currently available on the free hosted backend.** The Render Free service has a 512 MB memory limit, which is insufficient for the current processing pipeline and its machine-learning dependencies. Processing attempts can cause the service to run out of memory and restart.

For that reason:

- Use the hosted link to view the interface.
- Use the local Docker setup to run the complete application.
- Watch the linked demonstration video to see the full upload-to-answer workflow.

This is a hosting-resource limitation, not a claim that the application has been fully deployed for production use. The complete local workflow has been tested; the free hosted environment has not been able to support the full processing workload.

## Testing and Verification

The project has been tested locally through the main user workflow:

- Video upload and processing
- Audio transcription
- Visual frame analysis
- Timestamped evidence creation
- Transcript-based question answering
- Visual-only question answering for a silent video
- Handling questions that are not supported by the available evidence
- Timestamp selection and video navigation
- Backend execution inside Docker

**Automated test result:** 20 passed, 4 skipped. The skipped tests are optional Gemini integration tests and require explicit opt-in.

These results describe the tested development setup; they should not be interpreted as a production-scale accuracy or performance benchmark.

## Project Structure

```text
VidiQ-AI/
├── backend/
│   └── app/
│       ├── main.py
│       └── services/
│           ├── video_processing/
│           ├── multimodal/
│           └── rag/
├── frontend/
│   └── src/
├── data/                 # Local video and generated data (not committed)
├── Dockerfile
├── pyproject.toml
├── uv.lock
└── README.md
```

## Current Project Status

| Component | Status |
|---|---|
| Video and audio processing | Implemented and locally tested |
| Speech transcription | Implemented and locally tested |
| Visual frame analysis | Implemented and locally tested |
| Timestamped evidence construction | Implemented and locally tested |
| Hybrid retrieval and RAG | Implemented and locally tested |
| React dashboard and video navigation | Implemented and locally tested |
| Automated tests | 20 passed, 4 skipped |
| Docker backend image | Built and locally tested |
| Frontend hosting | Deployed as a preview |
| Full processing on Render Free | Limited by available memory |
| Complete local demonstration | Ready to record |

## Roadmap

- [x] Research and project design
- [x] Environment and project setup
- [x] Video and audio processing
- [x] Multimodal intelligence
- [x] Temporal retrieval and RAG
- [x] Backend and frontend development
- [x] Testing and local Docker verification
- [x] Deployment attempt and hosting limitation documented
- [ ] Publish the complete project walkthrough
- [ ] Add final application screenshots and demo link

## Responsible Use

- Use public, synthetic, or otherwise authorized videos when testing external AI services.
- Do not upload confidential company training footage or personal information unless the relevant data-processing terms and permissions have been reviewed.
- Keep API credentials in environment variables and out of source control.
- Treat generated answers as AI-assisted retrieval, and verify important operational or safety instructions against the original video.

## Author

**Kalyan Uppula**

VidiQ AI was developed as a portfolio project exploring multimodal GenAI, video intelligence, retrieval-augmented generation, and practical full-stack AI engineering.

---

<p align="center">
  <strong>VidiQ AI — Find the moment. Understand the context. Retrieve the evidence.</strong>
</p>
