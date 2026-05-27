import React, { useState, useEffect } from "react";
import "./Settings.css";

const API_URL  = process.env.REACT_APP_API_URL  || "http://localhost:8000";
const API_BASE = process.env.REACT_APP_API_BASE || "/api/v1";

function Settings() {
  const [form, setForm] = useState({ url: "", user: "", password: "" });
  const [showPass, setShowPass] = useState(false);
  const [current, setCurrent] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [saveStatus, setSaveStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [testLoading, setTestLoading] = useState(false);

  useEffect(() => {
    fetchCurrent();
  }, []);

  const fetchCurrent = async () => {
    try {
      const r = await fetch(`${API_URL}${API_BASE}/settings/zabbix`);
      const d = await r.json();
      setCurrent(d);
      setForm(f => ({ ...f, url: d.url, user: d.user }));
    } catch (e) {
      console.error(e);
    }
  };

  const handleTest = async () => {
    if (!form.url || !form.user || !form.password) {
      setTestResult({ status: "error", message: "Fill in URL, user, and password first." });
      return;
    }
    setTestLoading(true);
    setTestResult(null);
    try {
      const r = await fetch(`${API_URL}${API_BASE}/settings/zabbix/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const d = await r.json();
      setTestResult(d);
    } catch (e) {
      setTestResult({ status: "error", message: e.message });
    } finally {
      setTestLoading(false);
    }
  };

  const handleSave = async () => {
    if (!form.url || !form.user || !form.password) {
      setSaveStatus({ ok: false, msg: "All fields are required." });
      return;
    }
    setLoading(true);
    setSaveStatus(null);
    try {
      const r = await fetch(`${API_URL}${API_BASE}/settings/zabbix`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const d = await r.json();
      if (d.status === "saved") {
        setSaveStatus({ ok: true, msg: `Settings saved — ${d.url}` });
        await fetchCurrent();
      } else {
        setSaveStatus({ ok: false, msg: "Save failed." });
      }
    } catch (e) {
      setSaveStatus({ ok: false, msg: e.message });
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    setLoading(true);
    try {
      await fetch(`${API_URL}${API_BASE}/settings/zabbix`, { method: "DELETE" });
      setSaveStatus({ ok: true, msg: "Reset to environment defaults." });
      setForm({ url: "", user: "", password: "" });
      setTestResult(null);
      await fetchCurrent();
    } finally {
      setLoading(false);
    }
  };

  const field = (key, label, type = "text", placeholder = "") => (
    <div className="sf-group">
      <label className="sf-label">{label}</label>
      <div className="sf-input-wrap">
        <input
          className="sf-input"
          type={key === "password" ? (showPass ? "text" : "password") : type}
          placeholder={placeholder}
          value={form[key]}
          onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
          autoComplete={key === "password" ? "new-password" : "off"}
        />
        {key === "password" && (
          <button
            className="sf-eye"
            type="button"
            onClick={() => setShowPass(s => !s)}
            tabIndex={-1}
          >
            {showPass ? "🙈" : "👁"}
          </button>
        )}
      </div>
    </div>
  );

  return (
    <div className="settings-page">

      {/* ── Page Header ── */}
      <div className="settings-page-header">
        <div>
          <h2 className="settings-title">Integration Settings</h2>
          <p className="settings-sub">Configure external monitoring sources</p>
        </div>
      </div>

      {/* ── Active Config Banner ── */}
      {current && (
        <div className={`active-banner ${current.is_custom ? "custom" : "env"}`}>
          <span className="banner-dot" />
          <div>
            <strong>{current.is_custom ? "Custom configuration active" : "Using environment defaults"}</strong>
            <span className="banner-detail">
              {current.url} · user: <code>{current.user}</code>
            </span>
          </div>
          {current.is_custom && (
            <button className="button button-secondary btn-sm" onClick={handleReset} disabled={loading}>
              Reset to defaults
            </button>
          )}
        </div>
      )}

      {/* ── Zabbix Card ── */}
      <div className="card settings-card">
        <div className="settings-card-header">
          <div className="settings-card-icon">🔗</div>
          <div>
            <h3 className="settings-card-title">Zabbix API Connection</h3>
            <p className="settings-card-sub">
              Connect to any Zabbix instance to pull real alert data. Changes take effect immediately — no restart needed.
            </p>
          </div>
        </div>

        <div className="sf-grid">
          {field("url", "Zabbix URL", "url", "http://your-zabbix.example.com")}
          {field("user", "Username", "text", "Admin")}
          {field("password", "Password", "password", "••••••••")}
        </div>

        {/* Test result */}
        {testResult && (
          <div className={`test-result ${testResult.status}`}>
            <span className="test-icon">
              {testResult.connected ? "✅" : "❌"}
            </span>
            <span>{testResult.message}</span>
          </div>
        )}

        {/* Save status */}
        {saveStatus && (
          <div className={saveStatus.ok ? "success" : "error"} style={{ marginTop: "0.75rem" }}>
            {saveStatus.msg}
          </div>
        )}

        {/* Actions */}
        <div className="sf-actions">
          <button
            className="button button-secondary"
            onClick={handleTest}
            disabled={testLoading || loading}
          >
            {testLoading ? <><span className="spinner" /> Testing…</> : "🔌 Test Connection"}
          </button>
          <button
            className="button button-primary"
            onClick={handleSave}
            disabled={loading || testLoading}
          >
            {loading ? <><span className="spinner" /> Saving…</> : "💾 Save & Apply"}
          </button>
        </div>
      </div>

      {/* ── Ollama Info Card ── */}
      <div className="card settings-card">
        <div className="settings-card-header">
          <div className="settings-card-icon">🤖</div>
          <div>
            <h3 className="settings-card-title">Ollama LLM Engine</h3>
            <p className="settings-card-sub">
              AI analysis engine — configured via environment variable <code>OLLAMA_URL</code>.
              Currently running with the <strong>Mistral</strong> model.
            </p>
          </div>
        </div>
        <div className="ollama-info">
          <div className="info-row">
            <span className="info-label">Endpoint</span>
            <code className="info-val">OLLAMA_URL (env)</code>
          </div>
          <div className="info-row">
            <span className="info-label">Model</span>
            <code className="info-val">mistral:latest</code>
          </div>
          <div className="info-row">
            <span className="info-label">Fallback</span>
            <span className="info-val" style={{ color: "#22c55e" }}>Rule-based engine (always available)</span>
          </div>
          <div className="info-row">
            <span className="info-label">Timeout</span>
            <code className="info-val">8s → fallback</code>
          </div>
        </div>
      </div>

      {/* ── Tips ── */}
      <div className="card settings-card tips-card">
        <div className="settings-card-header">
          <div className="settings-card-icon">💡</div>
          <div>
            <h3 className="settings-card-title">Usage Tips</h3>
          </div>
        </div>
        <ul className="tips-list">
          <li>Test the connection before saving to avoid applying bad credentials.</li>
          <li>Settings are stored in memory — they reset if the backend restarts. For permanent config, set <code>ZABBIX_URL</code>, <code>ZABBIX_USER</code>, <code>ZABBIX_PASSWORD</code> in your <code>.env</code> or Docker environment.</li>
          <li>When Zabbix is offline, the system automatically uses simulated data for analysis and PDF reports.</li>
          <li>Supports Zabbix API v5.x, v6.x, and v7.x.</li>
        </ul>
      </div>

    </div>
  );
}

export default Settings;
