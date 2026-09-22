import { useState } from "react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { askQuestion } from "./api/client";
import UploadPanel from "./components/UploadPanel";
import LandingPage from "./components/LandingPage";
import { LeftPanel, RightPanel } from "./components/SidePanels";

export default function App() {
  const [currentView, setCurrentView] = useState("landing");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]); // {role, content, steps?}
  const [loadedDatasets, setLoadedDatasets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    const q = question.trim();
    if (!q || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setQuestion("");
    setLoading(true);
    setError(null);

    try {
      const result = await askQuestion(q);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: result.answer, steps: result.steps },
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (currentView === "landing") {
    return <LandingPage onLaunch={() => setCurrentView("app")} />;
  }

  const suggestedQuestions = [
    "Which product generated the most revenue?",
    "Show me total sales by region.",
    "List the top 5 customers by order volume."
  ];

  return (
    <div className="app-layout">
      <LeftPanel />
      <div className="app">
        <header className="app-header">
          <div className="header-top">
            <button className="back-btn" onClick={() => setCurrentView("landing")} title="Back to Home">
              <svg viewBox="0 0 24 24" stroke="currentColor" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="19" y1="12" x2="5" y2="12"></line>
                <polyline points="12 19 5 12 12 5"></polyline>
              </svg>
            </button>
            <div className="nav-logo" onClick={() => setCurrentView("landing")} style={{cursor: "pointer"}}>
              <span className="logo-icon">✦</span> TextQL
            </div>
          </div>
          <p>Ask a question about the database in plain English.</p>
        </header>

        <UploadPanel
          onUploaded={(results) => {
            const summaries = results.map(r => `"${r.table_name}" (${r.row_count} rows, columns: ${r.columns.join(", ")})`);
            setLoadedDatasets(prev => {
              const newNames = results.map(r => r.table_name);
              return [...new Set([...prev, ...newNames])];
            });
            setMessages((prev) => [
              ...prev,
              {
                role: "assistant",
                content: `Loaded ${results.length} dataset(s):\n${summaries.join("\n")}\nYou can ask questions about them now.`,
              },
            ]);
          }}
        />

        {loadedDatasets.length > 0 && (
          <div className="loaded-datasets-row">
            <span className="loaded-label">Loaded Datasets:</span>
            <div className="loaded-chips">
              {loadedDatasets.map(name => (
                <span key={name} className="loaded-chip">
                  {name}
                  <button 
                    className="chip-remove"
                    onClick={() => setLoadedDatasets(prev => prev.filter(d => d !== name))}
                    title={`Remove ${name}`}
                  >
                    &times;
                  </button>
                </span>
              ))}
            </div>
          </div>
        )}

        {messages.length === 0 ? (
          <div className="empty-state">
            <div className="empty-orb"></div>
            <h2>Ask anything about your data</h2>
            <div className="empty-chips">
              {suggestedQuestions.map((q, idx) => (
                <button 
                  key={idx} 
                  type="button"
                  className="empty-chip"
                  onClick={() => setQuestion(q)}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="chat">
            {messages.map((m, i) => (
              <div key={i} className={`bubble-wrapper ${m.role}`}>
                {m.role === 'assistant' && (
                  <div className="bubble-avatar assistant">&gt;_</div>
                )}
                <div className={`bubble ${m.role}`}>
                  <div className="bubble-content markdown-body">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {m.content}
                    </ReactMarkdown>
                  </div>
                  {m.steps && m.steps.length > 0 && (
                    <details className="steps-card">
                      <summary>Show agent steps ({m.steps.length})</summary>
                      <div className="steps-content">
                        <ul>
                          {m.steps.map((s, j) => (
                            <li key={j}>
                              <code>{s.tool}</code>
                              {s.args && <pre>{JSON.stringify(s.args, null, 2)}</pre>}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </details>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="bubble-wrapper assistant">
                <div className="bubble-avatar assistant">&gt;_</div>
                <div className="bubble assistant loading">
                  <div className="typing-indicator">
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {error && <div className="error">⚠ {error}</div>}

        <div className="composer-wrapper">
          <form onSubmit={handleSubmit} className="composer">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask TextQL a question about your data..."
              disabled={loading}
            />
            <button type="submit" disabled={loading || !question.trim()}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            </button>
          </form>
        </div>
      </div>
      <RightPanel />
    </div>
  );
}
