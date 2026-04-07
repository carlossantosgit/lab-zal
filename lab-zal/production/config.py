"""
Configuração de Produção
Ajuste estes valores conforme seu ambiente
"""

import logging
import os
from pathlib import Path
import urllib3

# ============================================================================
# SETUP LOGGING AUTOMÁTICO
# ============================================================================

LOG_FILE = "/var/log/prometheus-zabbix-sync.log"
LOG_LEVEL = "INFO"

# Tentar criar log em /var/log/, se falhar usa pasta local
try:
    log_dir = "/var/log"
    if not os.access(log_dir, os.W_OK):
        log_dir = os.path.dirname(os.path.abspath(__file__))
        LOG_FILE = os.path.join(log_dir, "prometheus-zabbix-sync.log")
except Exception:
    LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prometheus-zabbix-sync.log")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Suprimir avisos SSL de urllib3 (quando VERIFY_SSL = False)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Log de inicialização
logger.info("=" * 60)
logger.info("🚀 Configuração carregada - Production")
logger.info(f"📝 Log file: {LOG_FILE}")
logger.info("=" * 60)

# ============================================================================
# ZABBIX
# ============================================================================

# URL da API Zabbix
ZABBIX_API_URL = "https://zabbix-dev.spms.min-saude.pt:4443/api_jsonrpc.php"

# Credenciais Zabbix
ZABBIX_USER = "api"
ZABBIX_PASSWORD = "12345678"

# Flag para ignorar verificação de SSL (se usar HTTPS sem certificado válido)
ZABBIX_VERIFY_SSL = False

# ============================================================================
# PROMETHEUS
# ============================================================================

# URL da API Prometheus (PRODUÇÃO)
PROMETHEUS_URL = "https://prometheus-prod-srv01.spms.min-saude.pt"

# Credenciais Prometheus (HTTPS com autenticação básica)
PROMETHEUS_USER = "prometheus"
PROMETHEUS_PASS = "5FapePt9erAhCNdylnii8s6zr2957pRx1fNGTUUR"

# Flag para verificação de SSL (em produção, deixar True)
PROMETHEUS_VERIFY_SSL = False

# ============================================================================
# MAPEAMENTO DE SEVERIDADE
# ============================================================================

# Prometheus severity → Zabbix priority
SEVERITY_MAP = {
    "info": 0,        # Not classified
    "warning": 2,     # Average
    "critical": 4,    # High
}

# ============================================================================
# VALIDAÇÃO DE CONFIGURAÇÃO
# ============================================================================

def validate_config():
    """Valida se a configuração está ok"""
    import requests

    logger.info("🔍 Iniciando validação de configuração...")

    try:
        # Testar Prometheus
        logger.info(f"📡 Testando Prometheus: {PROMETHEUS_URL}")
        auth = (PROMETHEUS_USER, PROMETHEUS_PASS) if PROMETHEUS_PASS else None
        resp = requests.get(
            f"{PROMETHEUS_URL}/-/healthy",
            auth=auth,
            verify=PROMETHEUS_VERIFY_SSL,
            timeout=5
        )
        if resp.status_code == 200:
            logger.info("✅ Prometheus OK")
            print(f"✅ Prometheus: {PROMETHEUS_URL}")
        else:
            logger.error(f"❌ Prometheus respondeu com {resp.status_code}")
            print(f"❌ Prometheus respondeu com {resp.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Prometheus não acessível: {str(e)}")
        print(f"❌ Prometheus não acessível: {str(e)}")
        return False

    try:
        # Testar Zabbix
        logger.info(f"🔐 Testando Zabbix: {ZABBIX_API_URL}")
        payload = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {"user": ZABBIX_USER, "password": ZABBIX_PASSWORD},
            "id": 1
        }
        resp = requests.post(ZABBIX_API_URL, json=payload, timeout=5)
        result = resp.json()

        if "result" in result:
            logger.info("✅ Zabbix OK (login bem-sucedido)")
            print(f"✅ Zabbix: {ZABBIX_API_URL}")
        else:
            logger.error(f"❌ Login Zabbix falhou: {result.get('error')}")
            print(f"❌ Login Zabbix falhou: {result.get('error')}")
            return False
    except Exception as e:
        logger.error(f"❌ Zabbix não acessível: {str(e)}")
        print(f"❌ Zabbix não acessível: {str(e)}")
        return False

    logger.info("✅ VALIDAÇÃO OK - Sistema pronto!")
    return True
