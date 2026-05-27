from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
import logging
import random

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["alerts"])

# Fake alerts data
FAKE_ALERTS = [
    {"severity": "critical", "message": "CPU usage above 95%", "host": "web-server-01"},
    {"severity": "critical", "message": "Database connection pool exhausted", "host": "db-primary-01"},
    {"severity": "critical", "message": "Service restart required - pending updates", "host": "web-server-03"},
    {"severity": "critical", "message": "OOM killer triggered - process killed", "host": "api-gateway-02"},
    {"severity": "critical", "message": "RAID array degraded - disk failure", "host": "storage-02"},
    {"severity": "critical", "message": "Load balancer health check failing", "host": "lb-primary-01"},
    {"severity": "critical", "message": "Database replication lag > 60s", "host": "db-replica-01"},
    {"severity": "critical", "message": "SSL certificate expired", "host": "web-server-04"},
    {"severity": "critical", "message": "Firewall rules misconfiguration detected", "host": "fw-edge-01"},
    {"severity": "critical", "message": "Application crash loop detected", "host": "app-server-02"},
    {"severity": "high", "message": "Memory utilization at 85%", "host": "api-gateway-01"},
    {"severity": "high", "message": "Network packet loss detected (5%)", "host": "network-switch-01"},
    {"severity": "high", "message": "Disk I/O latency above threshold (>200ms)", "host": "storage-01"},
    {"severity": "high", "message": "Too many open file descriptors", "host": "app-server-01"},
    {"severity": "high", "message": "Redis memory usage at 90%", "host": "cache-server-01"},
    {"severity": "high", "message": "Elasticsearch cluster status yellow", "host": "search-01"},
    {"severity": "high", "message": "API response time > 5s", "host": "api-gateway-03"},
    {"severity": "high", "message": "Failed login attempts spike (>100/min)", "host": "auth-server-01"},
    {"severity": "high", "message": "Kubernetes pod crash loop backoff", "host": "k8s-node-02"},
    {"severity": "high", "message": "RabbitMQ queue depth > 10000", "host": "mq-server-01"},
    {"severity": "high", "message": "Network bandwidth saturation at 95%", "host": "network-switch-02"},
    {"severity": "high", "message": "Database deadlock detected", "host": "db-primary-01"},
    {"severity": "high", "message": "Swap usage above 80%", "host": "web-server-02"},
    {"severity": "high", "message": "NFS mount point unavailable", "host": "file-server-01"},
    {"severity": "high", "message": "Docker daemon unresponsive", "host": "docker-host-03"},
    {"severity": "medium", "message": "Disk space below 10% on /var", "host": "storage-01"},
    {"severity": "medium", "message": "Backup job failed - retry scheduled", "host": "backup-server"},
    {"severity": "medium", "message": "High I/O wait detected", "host": "cache-server-01"},
    {"severity": "medium", "message": "Cron job execution delayed > 30min", "host": "scheduler-01"},
    {"severity": "medium", "message": "Log rotation failed - disk filling up", "host": "log-server-01"},
    {"severity": "medium", "message": "SNMP trap received from network device", "host": "network-switch-03"},
    {"severity": "medium", "message": "SSH brute force attempt detected", "host": "bastion-host-01"},
    {"severity": "medium", "message": "MySQL slow queries > 50/min", "host": "db-secondary-01"},
    {"severity": "medium", "message": "CPU temperature above 70°C", "host": "compute-node-04"},
    {"severity": "medium", "message": "Puppet agent not reporting", "host": "app-server-03"},
    {"severity": "medium", "message": "DNS resolution latency elevated", "host": "dns-server-01"},
    {"severity": "medium", "message": "NTP drift > 100ms", "host": "web-server-05"},
    {"severity": "medium", "message": "Tomcat thread pool exhaustion warning", "host": "app-server-04"},
    {"severity": "medium", "message": "Kafka consumer lag increasing", "host": "kafka-broker-01"},
    {"severity": "medium", "message": "PHP-FPM worker pool at 80% capacity", "host": "web-server-06"},
    {"severity": "medium", "message": "Logstash pipeline backpressure detected", "host": "log-server-02"},
    {"severity": "medium", "message": "Nginx 5xx error rate > 2%", "host": "web-server-07"},
    {"severity": "medium", "message": "HAProxy backend server down", "host": "lb-secondary-01"},
    {"severity": "medium", "message": "Vault seal status check failed", "host": "vault-server-01"},
    {"severity": "medium", "message": "PostgreSQL checkpoint taking too long", "host": "db-primary-02"},
    {"severity": "low", "message": "Certificate expiration warning (30 days)", "host": "web-server-02"},
    {"severity": "low", "message": "Slow query detected in logs", "host": "db-secondary-01"},
    {"severity": "low", "message": "Disk space below 20% on /home", "host": "file-server-02"},
    {"severity": "low", "message": "Outdated OS packages available", "host": "app-server-05"},
    {"severity": "low", "message": "Systemd service restart count > 3", "host": "web-server-08"},
    {"severity": "low", "message": "Old log files not archived", "host": "log-server-03"},
    {"severity": "low", "message": "Clamav signatures outdated", "host": "mail-server-01"},
    {"severity": "low", "message": "SMART disk warning (reallocated sectors)", "host": "storage-03"},
    {"severity": "low", "message": "Unused scheduled task detected", "host": "scheduler-02"},
    {"severity": "low", "message": "DNS zone transfer enabled", "host": "dns-server-02"},
]


@router.get("/")
async def list_alerts(hours: int = 24):
    """Get alerts from last N hours"""
    try:
        # Generate fake alerts with timestamps
        now = datetime.now()
        alerts = []

        for i, alert_template in enumerate(FAKE_ALERTS[:100]):  # Generate up to 100 alerts
            timestamp = now - timedelta(hours=random.randint(0, hours))
            alert = {
                "id": i + 1,
                "severity": alert_template["severity"],
                "message": alert_template["message"],
                "host": alert_template["host"],
                "timestamp": timestamp.isoformat(),
                "acknowledged": random.choice([True, False]),
            }
            alerts.append(alert)

        return {
            "status": "success",
            "message": f"Retrieved {len(alerts)} alerts from last {hours} hours",
            "data": alerts,
        }
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{alert_id}")
async def get_alert(alert_id: int):
    """Get specific alert details"""
    try:
        if alert_id <= len(FAKE_ALERTS):
            alert = FAKE_ALERTS[alert_id - 1]
            return {
                "status": "success",
                "data": {
                    "id": alert_id,
                    "severity": alert["severity"],
                    "message": alert["message"],
                    "host": alert["host"],
                    "timestamp": datetime.now().isoformat(),
                    "details": f"Alert details for {alert['host']}: {alert['message']}",
                },
            }
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
    except Exception as e:
        logger.error(f"Error getting alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seed-fake")
async def seed_fake_alerts():
    """Generate fake alerts for testing"""
    try:
        alerts = []
        now = datetime.now()

        for i, alert_template in enumerate(FAKE_ALERTS):
            timestamp = now - timedelta(hours=random.randint(0, 24))
            alert = {
                "id": i + 1,
                "severity": alert_template["severity"],
                "message": alert_template["message"],
                "host": alert_template["host"],
                "timestamp": timestamp.isoformat(),
                "acknowledged": random.choice([True, False]) if i > 5 else False,
            }
            alerts.append(alert)

        logger.info(f"✅ Generated {len(alerts)} fake alerts for testing")

        return {
            "status": "success",
            "message": f"Generated {len(alerts)} fake alerts",
            "data": alerts,
        }
    except Exception as e:
        logger.error(f"Error seeding alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
