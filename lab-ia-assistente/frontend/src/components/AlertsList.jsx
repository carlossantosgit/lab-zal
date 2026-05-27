import React, { useState, useEffect, useCallback } from "react";
import { alertsService } from "../services/api";
import "./AlertsList.css";

const SEV_MAP = {
  critical: { label: "Critical", color: "#ef4444", bg: "rgba(239,68,68,0.1)", border: "rgba(239,68,68,0.3)" },
  high:     { label: "High",     color: "#f97316", bg: "rgba(249,115,22,0.1)", border: "rgba(249,115,22,0.3)" },
  medium:   { label: "Medium",   color: "#eab308", bg: "rgba(234,179,8,0.1)",  border: "rgba(234,179,8,0.3)" },
  low:      { label: "Low",      color: "#22c55e", bg: "rgba(34,197,94,0.1)",  border: "rgba(34,197,94,0.3)" },
};

function SeverityBadge({ severity }) {
  const cfg = SEV_MAP[severity] || SEV_MAP.low;
  return (
    <span
      className="sev-badge"
      style={{ color: cfg.color, background: cfg.bg, borderColor: cfg.border }}
    >
      {cfg.label}
    </span>
  );
}

function AlertsList() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hours, setHours] = useState(24);
  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [sortKey, setSortKey] = useState("timestamp");
  const [sortDir, setSortDir] = useState("desc");

  const loadAlerts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await alertsService.getAlerts(hours);
      if (result.status === "success") {
        setAlerts(result.data || []);
      } else {
        setError("Failed to load alerts");
      }
    } catch (err) {
      setError(err.message || "Error loading alerts");
    } finally {
      setLoading(false);
    }
  }, [hours]);

  useEffect(() => { loadAlerts(); }, [loadAlerts]);

  const handleSort = (key) => {
    if (sortKey === key) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortKey(key); setSortDir("desc"); }
  };

  const SortIcon = ({ col }) => {
    if (sortKey !== col) return <span className="sort-icon">⇅</span>;
    return <span className="sort-icon active">{sortDir === "asc" ? "↑" : "↓"}</span>;
  };

  const sevOrder = { critical: 0, high: 1, medium: 2, low: 3 };
  const filtered = alerts
    .filter(a => severityFilter === "all" || a.severity === severityFilter)
    .filter(a => {
      if (!search) return true;
      const q = search.toLowerCase();
      return (a.host || "").toLowerCase().includes(q) ||
             (a.message || "").toLowerCase().includes(q);
    })
    .sort((a, b) => {
      let diff = 0;
      if (sortKey === "severity")   diff = (sevOrder[a.severity] || 0) - (sevOrder[b.severity] || 0);
      if (sortKey === "host")       diff = (a.host || "").localeCompare(b.host || "");
      if (sortKey === "timestamp")  diff = new Date(a.timestamp) - new Date(b.timestamp);
      return sortDir === "asc" ? diff : -diff;
    });

  const counts = { critical: 0, high: 0, medium: 0, low: 0 };
  alerts.forEach(a => { if (counts[a.severity] !== undefined) counts[a.severity]++; });

  return (
    <div className="alerts-page">

      {/* Header */}
      <div className="alerts-header">
        <div>
          <h2 className="alerts-title">Alert Feed</h2>
          <p className="alerts-sub">{alerts.length} alerts · live view</p>
        </div>
        <button className="button button-secondary" onClick={loadAlerts} disabled={loading}>
          {loading ? <><span className="spinner" /> Refreshing…</> : "↻ Refresh"}
        </button>
      </div>

      {/* Severity summary pills */}
      <div className="sev-pills">
        {Object.entries(counts).map(([sev, cnt]) => {
          const cfg = SEV_MAP[sev];
          return (
            <button
              key={sev}
              className={`sev-pill ${severityFilter === sev ? "active" : ""}`}
              style={{
                "--pill-color": cfg.color,
                "--pill-bg": cfg.bg,
                "--pill-border": cfg.border,
              }}
              onClick={() => setSeverityFilter(s => s === sev ? "all" : sev)}
            >
              <span className="sev-pill-dot" style={{ background: cfg.color }} />
              {cfg.label}
              <span className="sev-pill-count">{cnt}</span>
            </button>
          );
        })}
        {severityFilter !== "all" && (
          <button className="sev-pill clear" onClick={() => setSeverityFilter("all")}>✕ Clear</button>
        )}
      </div>

      {/* Controls */}
      <div className="alerts-controls card">
        <div className="control-group">
          <label>Time Range</label>
          <select value={hours} onChange={e => setHours(parseInt(e.target.value))}>
            <option value="1">Last 1h</option>
            <option value="6">Last 6h</option>
            <option value="24">Last 24h</option>
            <option value="72">Last 3 days</option>
            <option value="168">Last week</option>
          </select>
        </div>
        <div className="control-group search-group">
          <label>Search</label>
          <div className="search-wrap">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              placeholder="Filter by host or message…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
            {search && (
              <button className="search-clear" onClick={() => setSearch("")}>✕</button>
            )}
          </div>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      {loading && (
        <div className="alerts-loading">
          <span className="spinner" style={{ width: 24, height: 24, borderWidth: 3 }} />
          <span>Loading alerts…</span>
        </div>
      )}

      {!loading && filtered.length === 0 && (
        <div className="card alerts-empty">
          <div>🔕</div>
          <p>No alerts match your filters.</p>
        </div>
      )}

      {!loading && filtered.length > 0 && (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div className="table-meta">
            <span>{filtered.length} result{filtered.length !== 1 ? "s" : ""}</span>
          </div>
          <div className="alerts-table-wrap">
            <table className="alerts-table">
              <thead>
                <tr>
                  <th onClick={() => handleSort("severity")} className="sortable">
                    Severity <SortIcon col="severity" />
                  </th>
                  <th onClick={() => handleSort("host")} className="sortable">
                    Host <SortIcon col="host" />
                  </th>
                  <th>Message</th>
                  <th onClick={() => handleSort("timestamp")} className="sortable">
                    Time <SortIcon col="timestamp" />
                  </th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((alert, idx) => (
                  <tr key={idx} className={`row-${alert.severity}`}>
                    <td><SeverityBadge severity={alert.severity} /></td>
                    <td className="host-cell">{alert.host}</td>
                    <td className="msg-cell">{alert.message}</td>
                    <td className="time-cell">
                      {new Date(alert.timestamp).toLocaleString("en-GB", {
                        month: "short", day: "2-digit",
                        hour: "2-digit", minute: "2-digit",
                      })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default AlertsList;
