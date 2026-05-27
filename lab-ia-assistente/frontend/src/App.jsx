import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import Dashboard from "./components/Dashboard";
import AnalysisForm from "./components/AnalysisForm";
import AlertsList from "./components/AlertsList";
import StatusBar from "./components/StatusBar";
import Settings from "./components/Settings";
import Assistant from "./components/Assistant";

function Clock() {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  return (
    <span className="live-clock">
      {time.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
    </span>
  );
}

const TABS = [
  { id: "dashboard",  icon: "📊", label: "Dashboard" },
  { id: "assistant",  icon: "💬", label: "AI Assistant" },
  { id: "analysis",   icon: "🔎", label: "Analysis" },
  { id: "alerts",     icon: "🚨", label: "Alerts" },
  { id: "settings",   icon: "⚙️",  label: "Settings" },
];

function App() {
  const [activeTab, setActiveTab]       = useState("dashboard");
  const [analysisResult, setAnalysisResult] = useState(null);
  const [status, setStatus]             = useState(null);
  const [prevTab, setPrevTab]           = useState(null);
  const mainRef = useRef(null);

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadStatus = async () => {
    try {
      const { analysisService } = await import("./services/api");
      const result = await analysisService.getStatus();
      setStatus(result);
    } catch (error) {
      console.error("Status error:", error);
    }
  };

  const handleAnalysis = (result) => {
    setAnalysisResult(result);
    switchTab("dashboard");
  };

  const switchTab = (id) => {
    setPrevTab(activeTab);
    setActiveTab(id);
    // animate main content
    if (mainRef.current) {
      mainRef.current.classList.remove("tab-enter");
      void mainRef.current.offsetWidth; // reflow
      mainRef.current.classList.add("tab-enter");
    }
  };

  const alertCount = analysisResult?.alerts_summary?.critical || null;

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div className="logo-section">
            <div className="logo-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                <rect x="2" y="12" width="4" height="10" rx="1" fill="#60a5fa"/>
                <rect x="8" y="7"  width="4" height="15" rx="1" fill="#818cf8"/>
                <rect x="14" y="3" width="4" height="19" rx="1" fill="#a78bfa"/>
                <rect x="20" y="9" width="2" height="13" rx="1" fill="#c4b5fd"/>
              </svg>
            </div>
            <div className="logo-text">
              <h1>Carlos-IA</h1>
              <p>Intelligent Infrastructure Observability</p>
            </div>
          </div>

          <div className="header-right">
            <Clock />
            <StatusBar status={status} onRefresh={loadStatus} />
          </div>
        </div>
      </header>

      <div className="container">
        <nav className="tabs">
          {TABS.map(tab => (
            <button
              key={tab.id}
              className={`tab ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => switchTab(tab.id)}
            >
              <span className="tab-icon">{tab.icon}</span>
              <span>{tab.label}</span>
              {tab.id === "alerts" && alertCount > 0 && (
                <span className="tab-badge">{alertCount}</span>
              )}
            </button>
          ))}
        </nav>

        <main className="main-content tab-enter" ref={mainRef}>
          {activeTab === "dashboard"  && <Dashboard analysisResult={analysisResult} />}
          {activeTab === "assistant"  && <Assistant />}
          {activeTab === "analysis"   && <AnalysisForm onAnalysis={handleAnalysis} />}
          {activeTab === "alerts"     && <AlertsList />}
          {activeTab === "settings"   && <Settings onSaved={loadStatus} />}
        </main>
      </div>

      <footer className="footer">
        Carlos-IA v2.0.0 &nbsp;·&nbsp; Infrastructure Intelligence Platform &nbsp;·&nbsp; Zabbix · Grafana · Ollama
      </footer>
    </div>
  );
}

export default App;
