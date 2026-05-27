from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False)
    analysis_type = Column(String(50))  # 'daily', 'custom', 'emergency'
    time_range_hours = Column(Integer, default=24)
    total_alerts = Column(Integer)
    alerts_critical = Column(Integer, default=0)
    alerts_high = Column(Integer, default=0)
    alerts_medium = Column(Integer, default=0)
    alerts_low = Column(Integer, default=0)
    ai_summary = Column(Text)
    ai_recommendations = Column(Text)
    top_hosts = Column(JSON)
    alert_distribution = Column(JSON)
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    pdf_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processing_time_seconds = Column(Float, nullable=True)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    zabbix_event_id = Column(String(50))
    severity = Column(String(20))  # critical, high, medium, low, info
    host = Column(String(255))
    item_name = Column(String(255))
    problem_text = Column(Text)
    acknowledged = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
