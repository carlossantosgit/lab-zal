from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import logging
import tempfile
import random
from pathlib import Path
from datetime import datetime, timedelta

from ..services.zabbix_client import ZabbixClient
from ..services.llm_analyzer import OllamaAnalyzer
from ..services.pdf_generator import PDFGenerator
from ..config import settings
from .settings import get_effective_zabbix

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])


class AnalysisRequest(BaseModel):
    hours: int = 24
    analysis_type: str = "daily"  # daily, custom, emergency


@router.post("/analyze")
async def analyze(request: AnalysisRequest):
    """Run AI analysis on recent alerts"""
    try:
        logger.info(f"📊 Starting analysis for last {request.hours} hours")

        # Initialize clients (use runtime config if set via UI)
        zabbix_cfg = get_effective_zabbix()
        zabbix = ZabbixClient(
            zabbix_cfg["url"],
            zabbix_cfg["user"],
            zabbix_cfg["password"],
        )
        analyzer = OllamaAnalyzer(settings.ollama_url, settings.ollama_model)

        # Authenticate and get alerts (fallback to fake data if Zabbix unavailable)
        zabbix_ok = await zabbix.authenticate()
        if zabbix_ok:
            problems = await zabbix.get_problems(request.hours)
            logger.info(f"📥 Retrieved {len(problems)} problems from Zabbix")
        else:
            logger.warning("⚠️ Zabbix unavailable - using simulated data for analysis")
            problems = _generate_fake_problems(request.hours)

        if not problems:
            return {
                "status": "success",
                "message": "No alerts found for analysis",
                "data": {"total_alerts": 0},
            }

        # Analyze with LLM
        logger.info("🤖 Starting LLM analysis")
        analysis = await analyzer.analyze_alerts(problems)

        # Prepare data for report
        alerts_summary = _summarize_alerts(problems)

        logger.info("✅ Analysis completed")

        return {
            "status": "success",
            "data": {
                "alerts_summary": alerts_summary,
                "analysis": analysis,
                "timestamp": problems[-1].get("clock", "") if problems else "",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-pdf")
async def generate_pdf(request: AnalysisRequest):
    """Generate PDF report with analysis and charts"""
    try:
        logger.info("📄 Starting PDF generation")

        # Initialize clients (use runtime config if set via UI)
        zabbix_cfg = get_effective_zabbix()
        zabbix = ZabbixClient(
            zabbix_cfg["url"],
            zabbix_cfg["user"],
            zabbix_cfg["password"],
        )
        analyzer = OllamaAnalyzer(settings.ollama_url, settings.ollama_model)
        pdf_gen = PDFGenerator("IA Analyzer - Alert Intelligence Report")

        # Get alerts (fallback to fake data if Zabbix unavailable)
        zabbix_ok = await zabbix.authenticate()
        if zabbix_ok:
            problems = await zabbix.get_problems(request.hours)
        else:
            logger.warning("⚠️ Zabbix unavailable - using simulated data for PDF")
            problems = _generate_fake_problems(request.hours)
        if not problems:
            raise HTTPException(status_code=404, detail="No alerts found")

        # Analyze
        analysis = await analyzer.analyze_alerts(problems)
        alerts_summary = _summarize_alerts(problems)
        alerts_summary["hours"] = request.hours

        # Generate PDF
        temp_dir = Path(tempfile.gettempdir())
        pdf_path = temp_dir / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        success = pdf_gen.create_report(
            alerts_summary, analysis, str(pdf_path), problems=problems
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to generate PDF")

        logger.info(f"✅ PDF generated: {pdf_path}")

        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename=f"ia-analyzer-report-{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ PDF generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """Check system status"""
    try:
        # Test Zabbix connection (use runtime config if set)
        zabbix_cfg = get_effective_zabbix()
        zabbix = ZabbixClient(
            zabbix_cfg["url"],
            zabbix_cfg["user"],
            zabbix_cfg["password"],
        )
        zabbix_ok = await zabbix.authenticate()

        # Test Ollama connection
        analyzer = OllamaAnalyzer(settings.ollama_url, settings.ollama_model)
        ollama_ok = await analyzer.ensure_model_loaded()

        return {
            "status": "ok" if (zabbix_ok and ollama_ok) else "degraded",
            "services": {
                "zabbix": "✅" if zabbix_ok else "❌",
                "ollama": "✅" if ollama_ok else "❌",
            },
        }

    except Exception as e:
        logger.error(f"Status check error: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


def _generate_fake_problems(hours: int) -> list:
    """Generate fake Zabbix-like problems for demo/testing when Zabbix is unavailable"""
    templates = [
        {"severity": "4", "name": "CPU usage above 95%", "host": "web-server-01"},
        {"severity": "4", "name": "Database connection pool exhausted", "host": "db-primary-01"},
        {"severity": "4", "name": "OOM killer triggered", "host": "api-gateway-02"},
        {"severity": "4", "name": "RAID array degraded - disk failure", "host": "storage-02"},
        {"severity": "4", "name": "Load balancer health check failing", "host": "lb-primary-01"},
        {"severity": "3", "name": "Memory utilization at 85%", "host": "api-gateway-01"},
        {"severity": "3", "name": "Network packet loss detected (5%)", "host": "network-switch-01"},
        {"severity": "3", "name": "Redis memory usage at 90%", "host": "cache-server-01"},
        {"severity": "3", "name": "Kubernetes pod crash loop backoff", "host": "k8s-node-02"},
        {"severity": "3", "name": "Database deadlock detected", "host": "db-primary-01"},
        {"severity": "2", "name": "Disk space below 10% on /var", "host": "storage-01"},
        {"severity": "2", "name": "Backup job failed - retry scheduled", "host": "backup-server"},
        {"severity": "2", "name": "High I/O wait detected", "host": "cache-server-01"},
        {"severity": "2", "name": "SSH brute force attempt detected", "host": "bastion-host-01"},
        {"severity": "2", "name": "Nginx 5xx error rate > 2%", "host": "web-server-07"},
        {"severity": "1", "name": "Certificate expiration warning (30 days)", "host": "web-server-02"},
        {"severity": "1", "name": "Slow query detected in logs", "host": "db-secondary-01"},
        {"severity": "1", "name": "Outdated OS packages available", "host": "app-server-05"},
        {"severity": "1", "name": "SMART disk warning", "host": "storage-03"},
        {"severity": "1", "name": "DNS zone transfer enabled", "host": "dns-server-02"},
    ]
    now = datetime.now()
    problems = []
    for i, t in enumerate(templates):
        ts = now - timedelta(hours=random.uniform(0, hours))
        problems.append({
            "problemid": str(i + 1),
            "name": t["name"],
            "severity": t["severity"],
            "clock": str(int(ts.timestamp())),
            "hosts": [{"host": t["host"]}],
        })
    return problems


def _summarize_alerts(problems: list) -> dict:
    """Summarize alert counts by severity"""
    summary = {
        "total": len(problems),
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "top_hosts": {},
    }

    severity_map = {
        "0": "low",
        "1": "medium",
        "2": "high",
        "3": "high",
        "4": "critical",
        "5": "critical",
    }

    for problem in problems:
        severity = severity_map.get(str(problem.get("severity", 0)), "low")
        summary[severity] += 1

        # Track top hosts
        hosts = problem.get("hosts", [])
        if hosts:
            host_name = hosts[0].get("host", "Unknown")
            summary["top_hosts"][host_name] = (
                summary["top_hosts"].get(host_name, 0) + 1
            )

    return summary

