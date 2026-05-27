import React, { useState, useEffect, useRef } from "react";
import "./Assistant.css";
import { sendChatMessage, getAssistantStatus } from "../services/assistantApi";

const QUICK_ACTIONS = [
  { label: "Problemas ativos",      message: "Quais os problemas ativos no Zabbix?" },
  { label: "🔨 Corrigir tudo",      message: "Arranja todos os problemas ativos" },
  { label: "Lista hosts",           message: "Lista todos os hosts do Zabbix" },
  { label: "Lista dashboards",      message: "Lista os dashboards do Grafana" },
  { label: "Dashboard overview",    message: "Cria um dashboard de overview geral no Grafana com título 'Infrastructure Overview'" },
  { label: "Dashboard CPU",         message: "Cria um dashboard de CPU no Grafana com título 'CPU Monitoring'" },
  { label: "Dashboard rede",        message: "Cria um dashboard de rede no Grafana com título 'Network Monitoring'" },
];

const ACTION_ICONS = {
  create_zabbix_item:      "🔧",
  create_zabbix_trigger:   "⚡",
  create_zabbix_template:  "📋",
  create_zabbix_host:      "🖥️",
  create_grafana_dashboard:"📊",
  create_grafana_folder:   "📁",
  get_active_problems:     "🚨",
  get_host_status:         "🩺",
  acknowledge_problem:     "✅",
  fix_problem:             "🔨",
  list_zabbix_hosts:       "🖥️",
  list_zabbix_templates:   "📋",
  list_grafana_dashboards: "📊",
  get_zabbix_items:        "🔍",
  get_zabbix_triggers:     "⚡",
  info:                    "💬",
  unknown:                 "❓",
};

function renderMarkdown(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>");
}

function ResultCard({ result }) {
  if (!result) return null;
  const { action, message, data, links, success } = result;
  const icon = ACTION_ICONS[action] || "✅";

  return (
    <div className={`result-card ${success ? "success" : "error"}`}>
      <div className="result-header">
        <span className="result-icon">{icon}</span>
        <span
          className="result-message"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(message || "") }}
        />
      </div>

      {data && (
        <div className="result-body">
          {/* List views */}
          {action === "list_zabbix_hosts" && data.hosts && (
            <div className="result-list">
              {data.hosts.slice(0, 20).map(h => (
                <div key={h.id} className="result-list-item">
                  <span className="item-icon">🖥️</span>
                  <span className="item-name">{h.name}</span>
                  <span className="item-id">#{h.id}</span>
                </div>
              ))}
              {data.count > 20 && <div className="result-more">+ {data.count - 20} mais…</div>}
            </div>
          )}

          {action === "list_zabbix_templates" && data.templates && (
            <div className="result-list">
              {data.templates.slice(0, 20).map(t => (
                <div key={t.id} className="result-list-item">
                  <span className="item-icon">📋</span>
                  <span className="item-name">{t.name}</span>
                  <span className="item-id">#{t.id}</span>
                </div>
              ))}
              {data.count > 20 && <div className="result-more">+ {data.count - 20} mais…</div>}
            </div>
          )}

          {action === "list_grafana_dashboards" && data.dashboards && (
            <div className="result-list">
              {data.dashboards.slice(0, 20).map(d => (
                <div key={d.uid} className="result-list-item">
                  <span className="item-icon">📊</span>
                  <span className="item-name">{d.title}</span>
                  {d.url && (
                    <a href={d.url} target="_blank" rel="noreferrer" className="item-link">Abrir</a>
                  )}
                </div>
              ))}
              {data.count > 20 && <div className="result-more">+ {data.count - 20} mais…</div>}
            </div>
          )}

          {action === "get_zabbix_items" && data.items && (
            <div className="result-list">
              {data.items.slice(0, 15).map(i => (
                <div key={i.id} className="result-list-item">
                  <span className="item-icon">🔧</span>
                  <span className="item-name">{i.name}</span>
                  <code className="item-key">{i.key}</code>
                </div>
              ))}
              {data.count > 15 && <div className="result-more">+ {data.count - 15} mais…</div>}
            </div>
          )}

          {action === "get_zabbix_triggers" && data.triggers && (
            <div className="result-list">
              {data.triggers.slice(0, 15).map(t => (
                <div key={t.id} className="result-list-item trigger-item">
                  <span className="item-icon">⚡</span>
                  <div className="trigger-info">
                    <span className="item-name">{t.description}</span>
                    <span className={`priority-badge priority-${t.priority?.toLowerCase()}`}>{t.priority}</span>
                  </div>
                </div>
              ))}
              {data.count > 15 && <div className="result-more">+ {data.count - 15} mais…</div>}
            </div>
          )}

          {action === "get_active_problems" && data.problems && (
            <div className="result-list">
              {data.problems.length === 0 ? (
                <div className="no-problems">Nenhum problema ativo</div>
              ) : data.problems.map((p, i) => (
                <div key={i} className="result-list-item problem-item">
                  <span className="item-icon">{p.emoji}</span>
                  <div className="problem-info">
                    <span className="item-name">{p.name}</span>
                    <div className="problem-meta">
                      {p.host && p.host !== data.host && <span className="problem-host">{p.host}</span>}
                      <span className="problem-duration">⏱ {p.duration}</span>
                      <span className={`priority-badge priority-${p.severity?.toLowerCase()}`}>{p.severity}</span>
                      {p.acknowledged && <span className="ack-badge">✓ ACK</span>}
                    </div>
                  </div>
                </div>
              ))}
              {data.count > 20 && <div className="result-more">+ {data.count - 20} mais…</div>}
            </div>
          )}

          {action === "get_host_status" && (
            <div className="host-status-card">
              <div className="status-row">
                <span className="status-label">Disponibilidade</span>
                <span className={`avail-badge ${data.available ? "avail-ok" : "avail-fail"}`}>
                  {data.available ? "✅" : "❌"} {data.availability}
                </span>
              </div>
              {data.agent_error && (
                <div className="status-row">
                  <span className="status-label">Erro</span>
                  <span className="status-error">{data.agent_error}</span>
                </div>
              )}
              <div className="status-row">
                <span className="status-label">Problemas ativos</span>
                <span className={`prob-count ${data.problem_count > 0 ? "has-problems" : "no-problems-count"}`}>
                  {data.problem_count}
                </span>
              </div>
              {data.problems && data.problems.length > 0 && (
                <div className="result-list" style={{marginTop: "0.5rem"}}>
                  {data.problems.map((p, i) => (
                    <div key={i} className="result-list-item problem-item">
                      <span className="item-icon">{p.emoji}</span>
                      <div className="problem-info">
                        <span className="item-name">{p.name}</span>
                        <div className="problem-meta">
                          <span className="problem-duration">⏱ {p.duration}</span>
                          <span className={`priority-badge priority-${p.severity?.toLowerCase()}`}>{p.severity}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {action === "acknowledge_problem" && data && (
            <div className="detail-grid">
              <div className="detail-row"><span>Problema</span><span>{data.problem}</span></div>
              <div className="detail-row"><span>Mensagem</span><code>{data.message}</code></div>
            </div>
          )}

          {action === "fix_problem" && data?.fixes && (
            <div className="result-list">
              {data.fixes.length === 0 ? (
                <div className="no-problems">Nenhum problema para corrigir</div>
              ) : data.fixes.map((f, i) => (
                <div key={i} className="result-list-item fix-item">
                  <span className="item-icon">{f.done ? "✅" : "❌"}</span>
                  <div className="fix-info">
                    <span className="item-name">{f.problem}</span>
                    <div className="fix-meta">
                      <span className="fix-strategy">{
                        f.strategy === "fix_agent"       ? "🔧 Monitorização interna" :
                        f.strategy === "disable_trigger" ? "🔇 Trigger desativado" :
                        f.strategy === "maintenance"     ? "🛠️ Manutenção 4h" :
                                                          "✅ Reconhecido"
                      }</span>
                      {f.host && <span className="problem-host">{f.host}</span>}
                    </div>
                    {f.detail && <span className="fix-detail">{f.detail}</span>}
                    {f.error  && <span className="status-error">{f.error}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Created object detail cards */}
          {action === "create_zabbix_trigger" && data.triggerid && (
            <div className="detail-grid">
              <div className="detail-row"><span>ID</span><code>{data.triggerid}</code></div>
              <div className="detail-row"><span>Expressão</span><code className="expr">{data.expression}</code></div>
              <div className="detail-row"><span>Severidade</span><span className={`priority-badge priority-${data.priority?.toLowerCase()}`}>{data.priority}</span></div>
            </div>
          )}

          {action === "create_zabbix_item" && data.itemid && (
            <div className="detail-grid">
              <div className="detail-row"><span>ID</span><code>{data.itemid}</code></div>
              <div className="detail-row"><span>Chave</span><code>{data.key_}</code></div>
              <div className="detail-row"><span>Intervalo</span><code>{data.delay}</code></div>
            </div>
          )}

          {action === "create_zabbix_host" && data.hostid && (
            <div className="detail-grid">
              <div className="detail-row"><span>ID</span><code>{data.hostid}</code></div>
              <div className="detail-row"><span>IP</span><code>{data.ip}</code></div>
              <div className="detail-row"><span>Grupo</span><span>{data.group}</span></div>
            </div>
          )}

          {action === "create_zabbix_template" && data.templateid && (
            <div className="detail-grid">
              <div className="detail-row"><span>ID</span><code>{data.templateid}</code></div>
            </div>
          )}

          {action === "create_grafana_dashboard" && data.uid && (
            <div className="detail-grid">
              <div className="detail-row"><span>UID</span><code>{data.uid}</code></div>
              <div className="detail-row"><span>Tipo</span><span>{data.type}</span></div>
              {data.instance_filter && (
                <div className="detail-row"><span>Filtro</span><code>{data.instance_filter}</code></div>
              )}
            </div>
          )}
        </div>
      )}

      {links && Object.keys(links).length > 0 && (
        <div className="result-links">
          {links.grafana && (
            <a href={links.grafana} target="_blank" rel="noreferrer" className="result-link grafana-link">
              <span>📊</span> Abrir no Grafana
            </a>
          )}
          {links.zabbix && (
            <a href={links.zabbix} target="_blank" rel="noreferrer" className="result-link zabbix-link">
              <span>🔗</span> Abrir no Zabbix
            </a>
          )}
        </div>
      )}
    </div>
  );
}

function Message({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div className={`message ${isUser ? "message-user" : "message-assistant"}`}>
      {!isUser && <div className="avatar assistant-avatar">🤖</div>}
      <div className="message-content">
        <div className="bubble">
          {msg.text}
        </div>
        {msg.result && msg.result.action !== "info" && msg.result.action !== "unknown" && <ResultCard result={msg.result} />}
        <div className="message-time">{msg.time}</div>
      </div>
      {isUser && <div className="avatar user-avatar">👤</div>}
    </div>
  );
}

function StatusDot({ ok, label }) {
  return (
    <span className={`status-dot-item ${ok ? "ok" : "fail"}`}>
      <span className="dot" /> {label}
    </span>
  );
}

export default function Assistant() {
  const [messages, setMessages] = useState([
    {
      id: 0,
      role: "assistant",
      text: "Olá! Sou o teu assistente de infraestrutura. Posso criar triggers, items, templates e hosts no Zabbix, e dashboards no Grafana. O que precisas?",
      time: new Date().toLocaleTimeString("pt-PT", { hour: "2-digit", minute: "2-digit" }),
      result: null,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [connStatus, setConnStatus] = useState(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    getAssistantStatus().then(setConnStatus).catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const now = () => new Date().toLocaleTimeString("pt-PT", { hour: "2-digit", minute: "2-digit" });

  const send = async (text) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    const userMsg = {
      id: Date.now(),
      role: "user",
      text: trimmed,
      time: now(),
      result: null,
    };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const data = await sendChatMessage(trimmed);
      const result = data.result;
      const LIST_ACTIONS    = new Set(["list_zabbix_hosts","list_zabbix_templates","list_grafana_dashboards"]);
      const DIAG_ACTIONS    = new Set(["get_active_problems","get_host_status","get_zabbix_items","get_zabbix_triggers"]);
      const CREATE_ACTIONS  = new Set(["create_zabbix_item","create_zabbix_trigger","create_zabbix_template","create_zabbix_host","create_grafana_dashboard","create_grafana_folder"]);

      let bubbleText;
      if (!result.success) {
        bubbleText = "Ocorreu um erro.";
      } else if (result.action === "info" || result.action === "unknown") {
        bubbleText = result.message;
      } else if (LIST_ACTIONS.has(result.action) || DIAG_ACTIONS.has(result.action) || result.action === "fix_problem" || result.action === "acknowledge_problem") {
        bubbleText = result.message;
      } else if (CREATE_ACTIONS.has(result.action)) {
        bubbleText = "Feito! " + result.message;
      } else {
        bubbleText = result.message || "Feito!";
      }

      const assistantMsg = {
        id: Date.now() + 2,
        role: "assistant",
        text: bubbleText,
        time: now(),
        result,
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err) {
      setMessages(prev => [...prev, {
        id: Date.now() + 3,
        role: "assistant",
        text: `Erro de ligação: ${err.message}`,
        time: now(),
        result: { success: false, action: "error", message: err.message, data: null, links: null },
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
  };

  return (
    <div className="assistant-page">
      {/* Header */}
      <div className="assistant-header card">
        <div className="assistant-header-left">
          <div className="assistant-icon">🤖</div>
          <div>
            <h2 className="assistant-title">AI Assistant</h2>
            <p className="assistant-sub">Cria recursos em Zabbix e Grafana por linguagem natural</p>
          </div>
        </div>
        {connStatus && (
          <div className="conn-status">
            <StatusDot ok={connStatus.zabbix?.ok} label="Zabbix" />
            <StatusDot ok={connStatus.grafana?.ok} label="Grafana" />
          </div>
        )}
      </div>

      {/* Quick actions */}
      <div className="quick-actions">
        {QUICK_ACTIONS.map(qa => (
          <button
            key={qa.label}
            className="quick-btn"
            onClick={() => send(qa.message)}
            disabled={loading}
          >
            {qa.label}
          </button>
        ))}
      </div>

      {/* Chat area */}
      <div className="chat-area card">
        <div className="messages">
          {messages.map(msg => (
            <Message key={msg.id} msg={msg} />
          ))}
          {loading && (
            <div className="message message-assistant">
              <div className="avatar assistant-avatar">🤖</div>
              <div className="message-content">
                <div className="bubble thinking">
                  <span className="dot-pulse" /><span className="dot-pulse" /><span className="dot-pulse" />
                  <span className="thinking-label">A processar</span>
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="chat-input-row">
          <textarea
            ref={inputRef}
            className="chat-input"
            placeholder="Ex: Cria um trigger de CPU > 90% no host web01 com severidade High…"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={2}
            disabled={loading}
          />
          <button
            className="send-btn"
            onClick={() => send(input)}
            disabled={loading || !input.trim()}
          >
            {loading ? <span className="spinner" /> : "Enviar"}
          </button>
        </div>
        <div className="chat-hint">Enter para enviar · Shift+Enter para nova linha</div>
      </div>
    </div>
  );
}
