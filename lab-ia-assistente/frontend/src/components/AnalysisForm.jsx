import React, { useState } from "react";
import { analysisService } from "../services/api";
import "./AnalysisForm.css";

const PRESETS = [
  { label: "1h",    hours: 1 },
  { label: "6h",    hours: 6 },
  { label: "24h",   hours: 24 },
  { label: "3 days", hours: 72 },
  { label: "1 week", hours: 168 },
];

function AnalysisForm({ onAnalysis }) {
  const [hours, setHours] = useState(24);
  const [analysisType, setAnalysisType] = useState("daily");
  const [loading, setLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await analysisService.analyze(hours);
      if (result.status === "success") {
        onAnalysis(result.data);
      } else {
        setError(result.detail || "Analysis failed");
      }
    } catch (err) {
      setError(err.message || "Error during analysis");
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePDF = async () => {
    setPdfLoading(true);
    setError(null);
    try {
      const API_URL  = process.env.REACT_APP_API_URL  || "http://localhost:8000";
      const API_BASE = process.env.REACT_APP_API_BASE || "/api/v1";
      const response = await fetch(`${API_URL}${API_BASE}/analysis/generate-pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hours }),
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "PDF generation failed");
      }
      const blob = await response.blob();
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement("a");
      a.href     = url;
      a.download = `carlos-ia-report-${new Date().toISOString().slice(0, 10)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message || "Error generating PDF");
    } finally {
      setPdfLoading(false);
    }
  };

  return (
    <div className="analysis-form card">
      <h2>Alert Analysis Configuration</h2>

      {error && <div className="error">{error}</div>}

      <div className="form-group">
        <label>Time Range</label>
        <div className="range-inputs">
          <input
            type="number"
            min="1"
            max="168"
            value={hours}
            onChange={e => setHours(parseInt(e.target.value))}
            disabled={loading || pdfLoading}
          />
          <span>hours</span>
        </div>
        <div className="quick-presets">
          {PRESETS.map(p => (
            <button
              key={p.hours}
              className="preset-btn"
              onClick={() => setHours(p.hours)}
              disabled={loading || pdfLoading}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label>Analysis Type</label>
        <select
          value={analysisType}
          onChange={e => setAnalysisType(e.target.value)}
          disabled={loading || pdfLoading}
        >
          <option value="daily">Daily Analysis</option>
          <option value="custom">Custom Period</option>
          <option value="emergency">Emergency Response</option>
        </select>
      </div>

      <div className="form-actions">
        <button
          className="button button-primary"
          onClick={handleAnalyze}
          disabled={loading || pdfLoading}
        >
          {loading
            ? <><span className="spinner" /> Analyzing…</>
            : "▶ Run Analysis"}
        </button>

        <button
          className="button button-secondary"
          onClick={handleGeneratePDF}
          disabled={loading || pdfLoading}
        >
          {pdfLoading
            ? <><span className="spinner" /> Generating…</>
            : "📄 Generate PDF Report"}
        </button>
      </div>

      <div className="info" style={{ marginTop: "1.5rem" }}>
        <strong>Tip:</strong> Use quick presets above or type a custom number of hours.
        The AI will identify patterns and provide actionable recommendations.
      </div>
    </div>
  );
}

export default AnalysisForm;
