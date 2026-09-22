// Set VITE_API_URL in a .env file (frontend/.env) — points at your
// Render/Railway-deployed backend, e.g. https://text-to-sql-agent-api.onrender.com
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function askQuestion(question) {
  const res = await fetch(`${API_URL}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export async function getSchema() {
  const res = await fetch(`${API_URL}/api/schema`);
  if (!res.ok) throw new Error("Failed to load schema");
  return res.json();
}

export async function uploadDataset(files) {
  const formData = new FormData();
  files.forEach(file => {
    formData.append("files", file);
  });

  const res = await fetch(`${API_URL}/api/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Upload failed (${res.status})`);
  }
  return res.json();
}
