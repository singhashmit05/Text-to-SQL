import React, { useEffect, useState } from 'react';

export function LeftPanel() {
  const [logs, setLogs] = useState([
    "INITIALIZING TEXTQL AGENT...",
    "LOADING PROTOCOLS..."
  ]);

  useEffect(() => {
    const messages = [
      "SYSTEM: ONLINE",
      "ESTABLISHING CONNECTION...",
      "DATA STREAM: ACTIVE",
      "NEURAL NET: LOADED",
      "AWAITING INPUT...",
      "ANALYZING METADATA...",
      "OPTIMIZING PATHWAYS...",
      "SYSTEM STATUS: NOMINAL"
    ];

    let count = 0;
    const interval = setInterval(() => {
      setLogs(prev => {
        const newLogs = [...prev, messages[count % messages.length]];
        if (newLogs.length > 20) newLogs.shift();
        return newLogs;
      });
      count++;
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="side-panel left-panel">
      <div className="panel-header">
        <span className="panel-title">SYS_LOG</span>
        <span className="blinking-cursor">_</span>
      </div>
      <div className="data-stream">
        {logs.map((log, i) => (
          <div key={i} className="log-line">&gt; {log}</div>
        ))}
      </div>
      <div className="panel-footer">
        <div className="status-indicator">
          <div className="dot green-pulse"></div>
          <span>IDLE</span>
        </div>
      </div>
    </div>
  );
}

export function RightPanel() {
  return (
    <div className="side-panel right-panel">
      <div className="panel-header">
        <span className="panel-title">TELEMETRY</span>
      </div>
      
      <div className="visualizer-container">
        <div className="node-grid">
          {Array(9).fill(0).map((_, i) => (
            <div key={i} className={`node node-${i}`}></div>
          ))}
        </div>
      </div>

      <div className="metrics-bars">
        <div className="metric">
          <div className="metric-label">CPU</div>
          <div className="bar-bg"><div className="bar-fill pulse-bar-1"></div></div>
        </div>
        <div className="metric">
          <div className="metric-label">MEM</div>
          <div className="bar-bg"><div className="bar-fill pulse-bar-2"></div></div>
        </div>
        <div className="metric">
          <div className="metric-label">NET</div>
          <div className="bar-bg"><div className="bar-fill pulse-bar-3"></div></div>
        </div>
      </div>
    </div>
  );
}
