"""
Configuração de Produção
Ajuste estes valores conforme seu ambiente
"""

# ============================================================================
# ZABBIX
# ============================================================================

# URL da API Zabbix
ZABBIX_API_URL = "http://zabbix-server:8080/api_jsonrpc.php"

# Credenciais Zabbix
ZABBIX_USER = "Admin"
ZABBIX_PASSWORD = "zabbix"

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
# LOGGING
# ============================================================================

LOG_LEVEL = "INFO"
LOG_FILE = "/var/log/prometheus-zabbix-sync.log"

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
        # Testar Prometheus com autenticação básica
        auth = (PROMETHEUS_USER, PROMETHEUS_PASS) if PROMETHEUS_PASS else None
        resp = requests.get(
            f"{PROMETHEUS_URL}/-/healthy",
            auth=auth,
            verify=PROMETHEUS_VERIFY_SSL,
            timeout=5
        )
        print(f"✅ Prometheus: {PROMETHEUS_URL}")
    except Exception as e:
        print(f"❌ Prometheus não acessível: {str(e)}")
        return False

    return True
