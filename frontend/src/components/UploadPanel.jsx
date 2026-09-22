import { useRef, useState } from "react";
import { uploadDataset } from "../api/client";

export default function UploadPanel({ onUploaded }) {
  const fileInputRef = useRef(null);
  const [status, setStatus] = useState("idle"); // idle | uploading | success | error
  const [message, setMessage] = useState("");

  async function handleFileChange(e) {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    if (files.length > 5) {
      setStatus("error");
      setMessage("Maximum 5 files allowed.");
      e.target.value = "";
      return;
    }

    setStatus("uploading");
    setMessage("");

    try {
      const response = await uploadDataset(files);
      const results = response.results || [];
      setStatus("success");
      
      const tableNames = results.map(r => r.table_name).join(", ");
      setMessage(`Loaded ${results.length} dataset(s): ${tableNames}.`);
      onUploaded?.(results);
    } catch (err) {
      setStatus("error");
      setMessage(err.message);
    } finally {
      e.target.value = ""; // allow re-uploading the same filename
    }
  }

  return (
    <div className="upload-panel">
      <button
        type="button"
        className="upload-btn"
        onClick={() => fileInputRef.current?.click()}
        disabled={status === "uploading"}
        title="Add your own datasets (up to 5 CSV/Excel)"
      >
        {status === "uploading" ? (
          <div className="typing-indicator" style={{ gap: 2, padding: 0 }}>
            <div className="typing-dot" style={{ width: 4, height: 4 }}></div>
            <div className="typing-dot" style={{ width: 4, height: 4 }}></div>
            <div className="typing-dot" style={{ width: 4, height: 4 }}></div>
          </div>
        ) : (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ fill: 'none' }}>
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
          </svg>
        )}
      </button>
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv,.xlsx,.xls"
        multiple
        onChange={handleFileChange}
        style={{ display: "none" }}
      />
      {message && (
        <div className={`upload-toast ${status}`}>
          {status === "success" ? "✓ " : status === "error" ? "⚠ " : ""}
          {message}
        </div>
      )}
    </div>
  );
}
