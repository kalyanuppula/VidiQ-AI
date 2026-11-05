import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000";



function App() {
  const videoRef = useRef(null);
  const [backendStatus, setBackendStatus] = useState("Checking...");
  const [selectedFile, setSelectedFile] = useState(null);
  const [videoUrl, setVideoUrl] = useState("");
  const [videoId, setVideoId] = useState("");
  const [processing, setProcessing] = useState(false);
  const [processingResult, setProcessingResult] = useState(null);
  const [question, setQuestion] = useState("");
  const [answerResult, setAnswerResult] = useState(null);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((response) => {
        if (!response.ok) throw new Error("Backend unavailable");
        return response.json();
      })
      .then((data) => setBackendStatus(data.status))
      .catch(() => setBackendStatus("Disconnected"));
  }, []);

  useEffect(() => {
    return () => {
      if (videoUrl) URL.revokeObjectURL(videoUrl);
    };
  }, [videoUrl]);

  function handleFileChange(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    const allowedExtensions = [".mp4", ".mov", ".mkv", ".webm", ".avi"];
    const extension = `.${file.name.split(".").pop().toLowerCase()}`;

    if (!allowedExtensions.includes(extension)) {
      setError("Please select a supported video file.");
      return;
    }

    setError("");
    setSelectedFile(file);
    setVideoId("");
    setProcessingResult(null);
    setAnswerResult(null);

    setVideoUrl(URL.createObjectURL(file));
  }

  async function uploadVideo() {
    if (!selectedFile) return;

    setError("");

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch(`${API_BASE}/api/videos/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Video upload failed.");
      }

      setVideoId(data.video_id);
      return data.video_id;
    } catch (err) {
      setError(err.message);
      return null;
    }
  }

  async function handleProcess() {
    if (!selectedFile || processing) return;

    setProcessing(true);
    setError("");
    setProcessingResult(null);
    setAnswerResult(null);

    try {
      const currentVideoId = videoId || (await uploadVideo());

      if (!currentVideoId) return;

      const response = await fetch(
        `${API_BASE}/api/videos/${currentVideoId}/process`,
        { method: "POST" }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Video processing failed.");
      }

      setProcessingResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setProcessing(false);
    }
  }

  async function handleAsk(event) {
    event.preventDefault();

    if (!question.trim() || !videoId || asking) return;

    setAsking(true);
    setError("");
    setAnswerResult(null);

    try {
      const response = await fetch(`${API_BASE}/api/videos/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: question.trim(),
          video_id: videoId,
          top_k: 5,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not answer the question.");
      }

      setAnswerResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setAsking(false);
    }
  }

  function jumpToTimestamp(timestamp) {
  if (!videoRef.current || !timestamp) return;

  const parts = timestamp.split(":").map(Number);

  const totalSeconds =
    parts.length === 3
      ? parts[0] * 3600 + parts[1] * 60 + parts[2]
      : parts.length === 2
        ? parts[0] * 60 + parts[1]
        : null;

  if (totalSeconds === null || !Number.isFinite(totalSeconds)) return;

  videoRef.current.currentTime = totalSeconds;
  videoRef.current.play();
}

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">V</div>
          <div>
            <h1>VidiQ AI</h1>
            <span>VIDEO INTELLIGENCE PLATFORM</span>
          </div>
         </div>
            <span className="creator-credit">
                Developed by Uppula Kalyan
            </span>
          <div className="connection">
          <span
            className={`status-dot ${
              backendStatus === "healthy" ? "online" : "offline"
            }`}
          />
          Backend {backendStatus}
        </div>
      </header>

      <main className="dashboard">
        <section className="page-heading">
          <div>
            <p className="eyebrow">ENTERPRISE VIDEO INTELLIGENCE</p>
            <h2>Understand every moment.</h2>
            <p className="subtitle">
              Upload, analyze and ask questions about your operational videos.
            </p>
          </div>
        </section>

        {error && <div className="error-message">{error}</div>}

        <section className="workspace">
          <div className="panel upload-panel">
            <div className="panel-heading">
              <div>
                <span className="step-label">01 / VIDEO SOURCE</span>
                <h3>Upload video</h3>
              </div>
              <span className="panel-icon">↑</span>
            </div>

            <label className="upload-area">
              <input
                type="file"
                accept="video/mp4,video/quicktime,video/x-matroska,video/webm,video/x-msvideo"
                onChange={handleFileChange}
              />
              <span className="upload-icon">⇧</span>
              <strong>Choose a video file</strong>
              <span>MP4, MOV, MKV, WEBM or AVI</span>
            </label>

            {selectedFile && (
              <div className="file-details">
                <div className="file-icon">VID</div>
                <div className="file-info">
                  <strong>{selectedFile.name}</strong>
                  <span>
                    {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                  </span>
                </div>
                <span className="file-check">✓</span>
              </div>
            )}

            <button
              className="primary-button"
              onClick={handleProcess}
              disabled={!selectedFile || processing || backendStatus !== "healthy"}
            >
              {processing
                ? "Processing video..."
                : processingResult
                  ? "Process again"
                  : "Upload & analyze video"}
            </button>

            {processing && (
              <p className="helper-text">
                Extracting audio, analyzing frames and indexing evidence.
                Please keep this page open.
              </p>
            )}

            {processingResult && (
              <div className="success-message">
                <strong>Processing finished</strong>
                <span>
                  {processingResult.status === "completed"
                    ? "Your video is ready for questions."
                    : "Processing finished with limited evidence."}
                </span>
              </div>
            )}
          </div>

          <div className="panel video-panel">
            <div className="panel-heading">
              <div>
                <span className="step-label">02 / VIDEO PREVIEW</span>
                <h3>Video player</h3>
              </div>
              {videoId && <span className="ready-label">VIDEO LOADED</span>}
            </div>

            {videoUrl ? (
              <video
                ref={videoRef}
                className="video-player"
                src={videoUrl}
                controls
              />
            ) : (
              <div className="video-placeholder">
                <span className="play-symbol">▶</span>
                <strong>Your video preview will appear here</strong>
                <span>Choose a video file to get started</span>
              </div>
            )}

            {processingResult && (
              <div className="metrics">
                <div>
                  <strong>
                    {processingResult.frames_extracted ?? 0}
                  </strong>
                  <span>Frames</span>
                </div>
                <div>
                  <strong>
                    {processingResult.visual_descriptions ?? 0}
                  </strong>
                  <span>Visual analyses</span>
                </div>
                <div>
                  <strong>
                    {processingResult.evidence_count ?? 0}
                  </strong>
                  <span>Evidence records</span>
                </div>
              </div>
            )}
          </div>
        </section>

        <section className="panel qa-panel">
          <div className="panel-heading">
            <div>
              <span className="step-label">03 / TEMPORAL RETRIEVAL</span>
              <h3>Ask your video</h3>
              <p className="panel-description">
                Ask questions and get answers grounded in video evidence.
              </p>
            </div>
            <span className="ai-label">AI POWERED</span>
          </div>

          <form className="question-form" onSubmit={handleAsk}>
            <input
              type="text"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="What safety risks are discussed in this video?"
              disabled={!processingResult || asking}
            />
            <button
              className="primary-button ask-button"
              type="submit"
              disabled={!processingResult || !question.trim() || asking}
            >
              {asking ? "Thinking..." : "Ask question"}
            </button>
          </form>

          {!processingResult && (
            <p className="helper-text">
              Upload and process a video before asking questions.
            </p>
          )}

          {answerResult && (
            <div className="answer-section">
              <div className="answer-heading">
                <span className="answer-icon">✦</span>
                <strong>VidiQ AI Answer</strong>
                <span className="answer-status">
                  {answerResult.status.replaceAll("_", " ")}
                </span>
              </div>

              <div className="answer-text">{answerResult.answer}</div>

              {answerResult.sources?.length > 0 && (
                <div className="sources-section">
                  <h4>Evidence sources</h4>
                  <div className="source-list">
                    {answerResult.sources.map((source) => (
                      <button
                        className="source-chip"
                        key={source.evidence_id}
                        onClick={() => jumpToTimestamp(source.timestamp)}
                        type="button"
                      >
                        <span>▶</span>
                        {source.timestamp}
                        <small>{source.evidence_type}</small>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </section>

        <footer className="footer">
          VidiQ AI · Multimodal Video Intelligence & Temporal Retrieval
        </footer>
      </main>
    </div>
  );
}

export default App;