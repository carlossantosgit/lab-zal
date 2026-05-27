import React from "react";
import "./StatusBar.css";

function StatusBar({ status }) {
  if (!status) return null;

  const zabbixOk = status.services?.zabbix === "✅";
  const ollamaOk = status.services?.ollama === "✅";

  return (
    <div className="status-bar">
      <div className={`status-item ${zabbixOk ? "ok" : "err"}`}>
        <span className="status-dot" />
        Zabbix {zabbixOk ? "Online" : "Offline"}
      </div>
      <div className={`status-item ${ollamaOk ? "ok" : "err"}`}>
        <span className="status-dot" />
        Ollama {ollamaOk ? "Online" : "Offline"}
      </div>
    </div>
  );
}

export default StatusBar;
