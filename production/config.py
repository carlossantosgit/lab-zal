"""
Configuração de Produção
Ajuste estes valores conforme seu ambiente
"""

import os

# ============================================================================
# ZABBIX
# ============================================================================

# URL da API Zabbix
ZABBIX_API_URL = os.getenv("ZABBIX_API_URL", "http://zabbix-server:8080/api_jsonrpc.php")

# Credenciais Zabbix
ZABBIX_USER = os.getenv("ZABBIX_USER", "Admin")
ZABBIX_PASSWORD = os.getenv("ZABBIX_PASSWORD", "zabbix")

# ============================================================================
# PROMETHEUS
# ============================================================================

# URL da API Prometheus
PROMETHEUS_API_URL = os.getenv("PROMETHEUS_API_URL", "http://prometheus:9090")

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
# LOGGING
# ============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "/var/log/prometheus-zabbix-sync.log")

# ============================================================================
# VALIDAÇÃO DE CONFIGURAÇÃO
# ============================================================================

def validate_config():
    """Valida se a configuração está ok"""
    import requests

    try:
        # Testar Zabbix
        resp = requests.get(ZABBIX_API_URL.replace("/api_jsonrpc.php", ""), timeout=5)
        print(f"✅ Zabbix: {ZABBIX_API_URL}")
    except Exception as e:
        print(f"❌ Zabbix não acessível: {str(e)}")
        return False

    try:
        # Testar Prometheus
        resp = requests.get(f"{PROMETHEUS_API_URL}/-/healthy", timeout=5)
        print(f"✅ Prometheus: {PROMETHEUS_API_URL}")
    except Exception as e:
        print(f"❌ Prometheus não acessível: {str(e)}")
        return False

    return True
