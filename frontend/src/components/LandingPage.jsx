import React from 'react';

export default function LandingPage({ onLaunch }) {
  return (
    <div className="landing-page">
      <nav className="landing-nav">
        <div className="nav-logo">
            <span className="logo-icon">✦</span> TextQL
        </div>
        <div className="nav-links">
            <a href="#features">Features</a>
        </div>
        <button className="nav-cta" onClick={onLaunch}>Try TextQL</button>
      </nav>

      <header className="hero-section">
        <div className="hero-pill">Agentic Data Analysis</div>
        <h1 className="hero-title">
          Transform Plain English into <br/><span className="text-gradient">Production-Grade SQL</span>
        </h1>
        <p className="hero-subtitle">
          TextQL translates your natural language questions into highly optimized SQL queries, 
          executes them safely, and delivers instant, actionable answers.
        </p>
        <div className="hero-actions">
          <button className="btn-primary" onClick={onLaunch}>
            Launch Agent <span className="arrow">→</span>
          </button>
        </div>

        <div className="hero-mockup">
          <div className="mockup-header">
            <span className="dot red"></span>
            <span className="dot yellow"></span>
            <span className="dot green"></span>
          </div>
          <div className="mockup-body">
            <div className="mockup-user">
                "Which product generated the most revenue last quarter?"
            </div>
            <div className="mockup-code">
                <code>
                    <span className="kw">SELECT</span> p.name, <span className="fn">SUM</span>(s.revenue) <span className="kw">AS</span> total_revenue<br/>
                    <span className="kw">FROM</span> sales s<br/>
                    <span className="kw">JOIN</span> products p <span className="kw">ON</span> s.product_id = p.id<br/>
                    <span className="kw">WHERE</span> s.date &gt;= <span className="str">'2026-06-01'</span><br/>
                    <span className="kw">GROUP BY</span> p.name<br/>
                    <span className="kw">ORDER BY</span> total_revenue <span className="kw">DESC</span><br/>
                    <span className="kw">LIMIT</span> 1;
                </code>
            </div>
            <div className="mockup-agent">
                The product that generated the most revenue last quarter was <strong>Enterprise Plan</strong> with $1.4M.
            </div>
          </div>
        </div>
      </header>

      <section id="features" className="features-section">
        <h2 className="section-title">Designed for modern data teams</h2>
        <div className="bento-grid">
            <div className="bento-card col-span-2 glass-panel">
                <div className="bento-icon">⚡</div>
                <h3>Natural Language Translation</h3>
                <p>Stop writing complex joins. Describe what you want in simple English, and our agent translates it into flawless dialect-specific SQL instantly.</p>
            </div>
            <div className="bento-card glass-panel">
                <div className="bento-icon">🛡️</div>
                <h3>Enterprise Security</h3>
                <p>Read-only guardrails ensure your database cannot be modified or dropped, keeping your data perfectly safe.</p>
            </div>
            <div className="bento-card glass-panel">
                <div className="bento-icon">🚀</div>
                <h3>Blazing Fast Inference</h3>
                <p>Powered by the latest 120B parameter OSS models via Groq, achieving sub-second reasoning and code generation.</p>
            </div>
            <div className="bento-card col-span-2 glass-panel">
                <div className="bento-icon">📊</div>
                <h3>Instant Insights</h3>
                <p>Don't just get the SQL code. TextQL automatically executes the query and summarizes the raw rows into an easy-to-understand executive answer.</p>
            </div>
        </div>
      </section>
      
      <footer className="landing-footer">
        <h2>Ready to chat with your database?</h2>
        <button className="btn-primary" onClick={onLaunch}>
            Launch TextQL Now
        </button>
        <p>© 2026 TextQL Inc. Built with React and FastAPI.</p>
      </footer>

      <div className="terminal-widget">
        <div className="terminal-header">
          <div className="terminal-avatar">&gt;_</div>
          <div className="terminal-title">TextQL Terminal</div>
        </div>
        <div className="terminal-body">
          <p>
            Hi, I'm TextQL.<br />
            I turn your plain-English questions into SQL, run them safely, and give you real answers — instantly, on your own data.
          </p>
          <ul>
            <li>Ask me about your database.</li>
            <li>Upload your own dataset.</li>
            <li>Get answers in seconds — no SQL required.</li>
          </ul>
          <p>Let's talk! ➔</p>
        </div>
        <div className="terminal-footer">
          <input 
            type="text" 
            className="terminal-input" 
            placeholder="Ask TextQL a question about your data..."
          />
          <button className="terminal-btn" onClick={onLaunch}>SEND</button>
        </div>
      </div>
    </div>
  );
}
