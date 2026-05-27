-- Create tables for IA Analyzer

CREATE TABLE IF NOT EXISTS analyses (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    analysis_type VARCHAR(50),
    time_range_hours INTEGER DEFAULT 24,
    total_alerts INTEGER,
    alerts_critical INTEGER DEFAULT 0,
    alerts_high INTEGER DEFAULT 0,
    alerts_medium INTEGER DEFAULT 0,
    alerts_low INTEGER DEFAULT 0,
    ai_summary TEXT,
    ai_recommendations TEXT,
    top_hosts JSONB,
    alert_distribution JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    pdf_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_time_seconds FLOAT
);

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    zabbix_event_id VARCHAR(50),
    severity VARCHAR(20),
    host VARCHAR(255),
    item_name VARCHAR(255),
    problem_text TEXT,
    acknowledged INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_analyses_user_id ON analyses(user_id);
CREATE INDEX idx_analyses_created_at ON analyses(created_at);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_host ON alerts(host);
CREATE INDEX idx_alerts_created_at ON alerts(created_at);
