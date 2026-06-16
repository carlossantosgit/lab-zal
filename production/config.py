"""
Configuração de Produção
Lê de variáveis de ambiente; usa os valores hardcoded como default.
Para sobrepor num ambiente diferente basta criar um .env ou exportar as vars.
"""

import logging
import os
import urllib3

# ============================================================================
# LOGGING
# ============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

_handlers = [logging.StreamHandler()]
try:
    if os.access("/var/log", os.W_OK):
        _handlers.append(logging.FileHandler("/var/log/prometheus-zabbix-sync.log"))
except Exception:
    pass

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=_handlers,
)
logger = logging.getLogger(__name__)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger.info("=" * 60)
logger.info("Configuracao carregada - Production")
logger.info("=" * 60)

# ============================================================================
# ZABBIX
# ============================================================================

ZABBIX_API_URL       = os.getenv("ZABBIX_API_URL",       "https://zabbix-dev.spms.min-saude.pt:4443/api_jsonrpc.php")
ZABBIX_USER          = os.getenv("ZABBIX_USER",          "api")
ZABBIX_PASSWORD      = os.getenv("ZABBIX_PASSWORD",      "12345678")
ZABBIX_VERIFY_SSL    = os.getenv("ZABBIX_VERIFY_SSL",    "false").lower() == "true"
ZABBIX_SERVER        = os.getenv("ZABBIX_SERVER",        "10.43.69.137")
ZABBIX_TRAPPER_PORT  = os.getenv("ZABBIX_TRAPPER_PORT",  "10151")

# ============================================================================
# PROMETHEUS
# ============================================================================

PROMETHEUS_URL        = os.getenv("PROMETHEUS_URL",        "https://prometheus-prod-srv01.spms.min-saude.pt")
PROMETHEUS_USER       = os.getenv("PROMETHEUS_USER",       "prometheus")
PROMETHEUS_PASS       = os.getenv("PROMETHEUS_PASS",       "5FapePt9erAhCNdylnii8s6zr2957pRx1fNGTUUR")
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
# VALIDAÇÃO
# ============================================================================

def validate_config():
    import requests

    logger.info("Iniciando validacao de configuracao...")

    try:
        auth = (PROMETHEUS_USER, PROMETHEUS_PASS) if PROMETHEUS_PASS else None
        resp = requests.get(
            "%s/-/healthy" % PROMETHEUS_URL,
            auth=auth, verify=PROMETHEUS_VERIFY_SSL, timeout=5,
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
        resp = requests.post(ZABBIX_API_URL, timeout=5, verify=ZABBIX_VERIFY_SSL,
                             json={"jsonrpc": "2.0", "method": "user.login",
                                   "params": {"user": ZABBIX_USER,
                                              "password": ZABBIX_PASSWORD},
                                   "id": 1})
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
