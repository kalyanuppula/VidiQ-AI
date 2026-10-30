import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [backendStatus, setBackendStatus] = useState("Checking...");
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/health")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Backend returned an error");
        }
        return response.json();
      })
      .then((data) => {
        setBackendStatus(data.status);
        setError("");
      })
      .catch(() => {
        setBackendStatus("Disconnected");
        setError("Could not connect to the VidiQ AI backend.");
      });
  }, []);

  return (
    <div className="app">
      <h1>VidiQ AI</h1>
      <h2>Multimodal Video Intelligence & Temporal Retrieval Platform</h2>

      <div className="status">
        <h3>Backend Connection</h3>
        <p>Status: {backendStatus}</p>
        {error && <p>{error}</p>}
      </div>
    </div>
  );
}

export default App;