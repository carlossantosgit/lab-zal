"""
Configuração de Produção
Valores lidos de variáveis de ambiente (com fallback para desenvolvimento local).
"""

import logging
import os
from pathlib import Path
import urllib3

# ============================================================================
# SETUP LOGGING
# ============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Em container os logs vão para stdout; fora do container tenta /var/log/
_log_handlers = [logging.StreamHandler()]
try:
    log_dir = "/var/log"
    if os.access(log_dir, os.W_OK):
        LOG_FILE = os.path.join(log_dir, "prometheus-zabbix-sync.log")
        _log_handlers.append(logging.FileHandler(LOG_FILE))
except Exception:
    pass

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=_log_handlers,
)
logger = logging.getLogger(__name__)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger.info("=" * 60)
logger.info("Configuracao carregada - Production")
logger.info("=" * 60)

# ============================================================================
# ZABBIX
# ============================================================================

ZABBIX_API_URL  = os.getenv("ZABBIX_API_URL",  "https://zabbix-dev.spms.min-saude.pt:4443/api_jsonrpc.php")
ZABBIX_USER     = os.getenv("ZABBIX_USER",     "api")
ZABBIX_PASSWORD = os.getenv("ZABBIX_PASSWORD", "")
ZABBIX_VERIFY_SSL = os.getenv("ZABBIX_VERIFY_SSL", "false").lower() == "true"

# ============================================================================
# PROMETHEUS
# ============================================================================

PROMETHEUS_URL        = os.getenv("PROMETHEUS_URL",        "https://prometheus-prod-srv01.spms.min-saude.pt")
PROMETHEUS_USER       = os.getenv("PROMETHEUS_USER",       "prometheus")
PROMETHEUS_PASS       = os.getenv("PROMETHEUS_PASS",       "")
PROMETHEUS_VERIFY_SSL = os.getenv("PROMETHEUS_VERIFY_SSL", "false").lower() == "true"

# ============================================================================
# MAPEAMENTO DE SEVERIDADE
# ============================================================================

SEVERITY_MAP = {
    "info":     0,
    "warning":  2,
    "critical": 4,
}

# ============================================================================
# VALIDAÇÃO DE CONFIGURAÇÃO
# ============================================================================

def validate_config():
    import requests

    logger.info("Iniciando validacao de configuracao...")

    try:
        auth = (PROMETHEUS_USER, PROMETHEUS_PASS) if PROMETHEUS_PASS else None
        resp = requests.get(
            "%s/-/healthy" % PROMETHEUS_URL,
            auth=auth,
            verify=PROMETHEUS_VERIFY_SSL,
            timeout=5,
        )
        if resp.status_code == 200:
            logger.info("Prometheus OK")
        else:
            logger.error("Prometheus respondeu com %s", resp.status_code)
            return False
    except Exception as e:
        logger.error("Prometheus nao acessivel: %s", e)
        return False

    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {"user": ZABBIX_USER, "password": ZABBIX_PASSWORD},
            "id": 1,
        }
        resp = requests.post(ZABBIX_API_URL, json=payload, timeout=5,
                             verify=ZABBIX_VERIFY_SSL)
        result = resp.json()
        if "result" in result:
            logger.info("Zabbix OK")
        else:
            logger.error("Login Zabbix falhou: %s", result.get("error"))
            return False
    except Exception as e:
        logger.error("Zabbix nao acessivel: %s", e)
        return False

    logger.info("VALIDACAO OK - Sistema pronto!")
    return True
