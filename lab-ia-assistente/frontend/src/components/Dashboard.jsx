import React from "react";
import "./Dashboard.css";

const SEVERITY_CONFIG = {
  critical: { label: "Critical", color: "#ef4444", glow: "rgba(239,68,68,0.3)", icon: "🔴" },
  high:     { label: "High",     color: "#f97316", glow: "rgba(249,115,22,0.3)", icon: "🟠" },
  medium:   { label: "Medium",   color: "#eab308", glow: "rgba(234,179,8,0.3)",  icon: "🟡" },
  low:      { label: "Low",      color: "#22c55e", glow: "rgba(34,197,94,0.3)",  icon: "🟢" },
};

function SeverityBar({ label, value, total, color }) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0;
  return (
    <div className="sev-bar-row">
      <span className="sev-bar-label">{label}</span>
      <div className="sev-bar-track">
        <div
          className="sev-bar-fill"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <span className="sev-bar-pct">{pct}%</span>
      <span className="sev-bar-count">{value}</span>
    </div>
  );
}

function RiskBadge({ level }) {
  const map = {
    Critical: { bg: "#ef4444", shadow: "rgba(239,68,68,0.4)" },
    High:     { bg: "#f97316", shadow: "rgba(249,115,22,0.4)" },
    Medium:   { bg: "#eab308", shadow: "rgba(234,179,8,0.4)" },
    Low:      { bg: "#22c55e", shadow: "rgba(34,197,94,0.4)" },
  };
  const cfg = map[level] || map.Medium;
  return (
    <span
      className="risk-badge"
      style={{ background: cfg.bg, boxShadow: `0 0 16px ${cfg.shadow}` }}
    >
      {level === "Critical" && "⚠ "}
      {level} Risk
    </span>
  );
}

function StatCard({ severity, value }) {
  const cfg = SEVERITY_CONFIG[severity];
  return (
    <div className="stat-card" style={{ "--accent-color": cfg.color, "--glow": cfg.glow }}>
      <div className="stat-icon">{cfg.icon}</div>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{cfg.label}</div>
      <div className="stat-bar" style={{ background: cfg.color }} />
    </div>
  );
}

function HostBar({ host, count, max, rank }) {
  const pct = max > 0 ? (count / max) * 100 : 0;
  return (
    <div className="host-row">
      <span className="host-rank">#{rank}</span>
      <span className="host-name">{host}</span>
      <div className="host-track">
        <div className="host-fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="host-count">{count}</span>
    </div>
  );
}

function Dashboard({ analysisResult }) {
  if (!analysisResult) {
    return (
      <div className="dashboard-empty card">
        <div className="empty-glow" />
        <div className="empty-icon">⚡</div>
        <h2>Welcome to Carlos-IA</h2>
        <p>Your intelligent infrastructure observability platform.</p>
        <p className="hint">Go to <strong>AI Analysis</strong> and click <strong>Run Analysis</strong> to begin.</p>
        <div className="empty-features">
          <div className="feature-pill">🤖 AI-Powered Analysis</div>
          <div className="feature-pill">📊 Real-time Metrics</div>
          <div className="feature-pill">📄 PDF Reports</div>
          <div className="feature-pill">🔍 Pattern Detection</div>
        </div>
      </div>
    );
  }

  const alerts = analysisResult.alerts_summary || {};
  const analysis = analysisResult.analysis || {};
  const total = alerts.total || 0;
  const riskLevel = analysis.risk_level || "Medium";

  const topHosts = Object.entries(alerts.top_hosts || {})
    .sort(([, a], [, b]) => b - a)
    .slice(0, 8);
  const maxHostCount = topHosts[0]?.[1] || 1;

  return (
    <div className="dashboard">

      {/* ─── Header row ─── */}
      <div className="dashboard-header">
        <div>
          <h2 className="dashboard-title">Infrastructure Status</h2>
          <p className="dashboard-sub">
            {total} alerts analysed
            {analysisResult.timestamp
              ? ` · last event ${new Date(Number(analysisResult.timestamp) * 1000).toLocaleTimeString()}`
              : ""}
          </p>
        </div>
        <RiskBadge level={riskLevel} />
      </div>

      {/* ─── KPI row ─── */}
      <div className="stats-grid">
        <StatCard severity="critical" value={alerts.critical || 0} />
        <StatCard severity="high"     value={alerts.high     || 0} />
        <StatCard severity="medium"   value={alerts.medium   || 0} />
        <StatCard severity="low"      value={alerts.low      || 0} />
      </div>

      {/* ─── Two-column ─── */}
      <div className="dashboard-cols">

        {/* Left: severity distribution */}
        <div className="card panel">
          <div className="panel-heading">
            <span className="panel-icon">📊</span> Severity Distribution
          </div>
          <div className="sev-bars">
            {Object.entries(SEVERITY_CONFIG).map(([key, cfg]) => (
              <SeverityBar
                key={key}
                label={cfg.label}
                value={alerts[key] || 0}
                total={total}
                color={cfg.color}
              />
            ))}
          </div>
          <div className="total-pill">Total: <strong>{total}</strong> alerts</div>
        </div>

        {/* Right: AI Summary */}
        {analysis.summary && (
          <div className="card panel">
            <div className="panel-heading">
              <span className="panel-icon">🤖</span> AI Analysis Summary
            </div>
            <p className="ai-summary">{analysis.summary}</p>
          </div>
        )}
      </div>

      {/* ─── Patterns & Recommendations ─── */}
      <div className="dashboard-cols">
        {analysis.patterns && analysis.patterns.length > 0 && (
          <div className="card panel">
            <div className="panel-heading">
              <span className="panel-icon">🔍</span> Identified Patterns
            </div>
            <ul className="insight-list">
              {analysis.patterns.map((p, i) => (
                <li key={i}>
                  <span className="insight-dot" style={{ background: "#3b82f6" }} />
                  {p.replace(/^[-•]\s*/, "")}
                </li>
              ))}
            </ul>
          </div>
        )}

        {analysis.recommendations && analysis.recommendations.length > 0 && (
          <div className="card panel">
            <div className="panel-heading">
              <span className="panel-icon">💡</span> Recommendations
            </div>
            <ol className="rec-list">
              {analysis.recommendations.map((r, i) => (
                <li key={i}>
                  <span className="rec-num"
                    style={{ background: i === 0 ? "#ef4444" : i === 1 ? "#f97316" : "#3b82f6" }}>
                    {i + 1}
                  </span>
                  {r.replace(/^[-•]\s*/, "")}
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>

      {/* ─── Top Hosts ─── */}
      {topHosts.length > 0 && (
        <div className="card panel">
          <div className="panel-heading">
            <span className="panel-icon">🏢</span> Top Affected Hosts
          </div>
          <div className="hosts-grid">
            {topHosts.map(([host, count], i) => (
              <HostBar key={host} host={host} count={count} max={maxHostCount} rank={i + 1} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
