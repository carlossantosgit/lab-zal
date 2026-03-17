# config.example.py
# Exemplo de configuração para produção

# ============================================================================
# ZABBIX - Altere conforme seu ambiente
# ============================================================================

# URL OBRIGATÓRIA - Zabbix API endpoint
ZABBIX_API_URL = "http://zabbix.seudominio.com.br:8080/api_jsonrpc.php"

# Usuário Zabbix com permissão de API
ZABBIX_USER = "admin-api"

# Senha do usuário
ZABBIX_PASSWORD = "sua_senha_super_secreta"

# ============================================================================
# PROMETHEUS - Altere conforme seu ambiente
# ============================================================================

# URL OBRIGATÓRIA - Prometheus API endpoint
PROMETHEUS_API_URL = "http://prometheus.seudominio.com.br:9090"

# ============================================================================
# SEVERIDADES - Não alterar (padrão Zabbix)
# ============================================================================

SEVERITY_MAP = {
    "info": 0,          # Not classified
    "warning": 2,       # Average
    "critical": 4,      # High
}

# ============================================================================
# EXEMPLOS DE CONFIGURAÇÃO POR AMBIENTE
# ============================================================================

# QUA (Qualidade)
"""
ZABBIX_API_URL = "http://zabbix-qua.interno:8080/api_jsonrpc.php"
PROMETHEUS_API_URL = "http://prometheus-qua.interno:9090"
"""

# PRODUÇÃO
"""
ZABBIX_API_URL = "https://zabbix-prod.seudominio.com.br/api_jsonrpc.php"
PROMETHEUS_API_URL = "https://prometheus-prod.seudominio.com.br:9090"
"""

# SSH Tunnel (se necessário)
"""
ssh -L 8080:zabbix-server:8080 bastion-server.com
ssh -L 9090:prometheus-server:9090 bastion-server.com

ZABBIX_API_URL = "http://localhost:8080/api_jsonrpc.php"
PROMETHEUS_API_URL = "http://localhost:9090"
"""
