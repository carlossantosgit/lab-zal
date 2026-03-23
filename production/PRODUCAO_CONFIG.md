# 🔒 Configuração de Produção - Prometheus → Zabbix

Este documento detalha a configuração de autenticação e segurança para produção.

---

## 📋 Credenciais PRD

### Prometheus Produção

```
URL: https://prometheus-prod-srv01.spms.min-saude.pt
Usuário: prometheus
Senha: 5FapePt9erAhCNdylnii8s6zr2957pRx1fNGTUUR
Protocolo: HTTPS (com autenticação básica)
```

### Zabbix Qualidade

```
URL: http://seu-zabbix-qua:8080/api_jsonrpc.php
Usuário: Admin (ou seu usuário)
Senha: [sua-senha]
Protocolo: HTTP
```

---

## 🔐 Autenticação Básica HTTP

Acessar o Prometheus requer autenticação básica HTTP.

### Exemplo com requests (Python)

```python
import requests

PROMETHEUS_URL = "https://prometheus-prod-srv01.spms.min-saude.pt"
PROMETHEUS_USER = "prometheus"
PROMETHEUS_PASS = "5FapePt9erAhCNdylnii8s6zr2957pRx1fNGTUUR"

# Com verificação de SSL (se tiver certificado válido)
response = requests.get(
    f"{PROMETHEUS_URL}/api/v1/rules",
    auth=(PROMETHEUS_USER, PROMETHEUS_PASS),
    verify=True  # Validar certificado
)

# Sem verificação (se usar auto-assinado)
response = requests.get(
    f"{PROMETHEUS_URL}/api/v1/rules",
    auth=(PROMETHEUS_USER, PROMETHEUS_PASS),
    verify=False  # NÃO validar certificado
)

# Ou com arquivo de certificado
response = requests.get(
    f"{PROMETHEUS_URL}/api/v1/rules",
    auth=(PROMETHEUS_USER, PROMETHEUS_PASS),
    verify="/path/to/ca-bundle.crt"
)

print(response.json())
```

### Exemplo com curl

```bash
# Teste simples
curl -u prometheus:5FapePt9erAhCNdylnii8s6zr2957pRx1fNGTUUR \
  https://prometheus-prod-srv01.spms.min-saude.pt/-/healthy

# Se tiver erro SSL, usar -k para ignorar
curl -k -u prometheus:5FapePt9erAhCNdylnii8s6zr2957pRx1fNGTUUR \
  https://prometheus-prod-srv01.spms.min-saude.pt/-/healthy

# Obter regras
curl -u prometheus:5FapePt9erAhCNdylnii8s6zr2957pRx1fNGTUUR \
  https://prometheus-prod-srv01.spms.min-saude.pt/api/v1/rules

# Obter alertas
curl -u prometheus:5FapePt9erAhCNdylnii8s6zr2957pRx1fNGTUUR \
  https://prometheus-prod-srv01.spms.min-saude.pt/api/v1/alerts
```

---

## ⚙️ Configuração em `config.py`

```python
import os

# ============================================================================
# PROMETHEUS PRODUÇÃO (HTTPS com autenticação básica)
# ============================================================================

PROMETHEUS_URL = os.getenv(
    "PROMETHEUS_URL",
    "https://prometheus-prod-srv01.spms.min-saude.pt"
)

PROMETHEUS_USER = os.getenv("PROMETHEUS_USER", "prometheus")
PROMETHEUS_PASS = os.getenv("PROMETHEUS_PASS", "5FapePt9erAhCNdylnii8s6zr2957pRx1fNGTUUR")

# Verificação de SSL
# True = validar certificado (produção com cert válido)
# False = ignorar verificação (cert auto-assinado)
PROMETHEUS_VERIFY_SSL = os.getenv("PROMETHEUS_VERIFY_SSL", "False").lower() == "true"

# Alternativa: apontar para arquivo CA
# PROMETHEUS_VERIFY_SSL = "/etc/ssl/certs/ca-bundle.crt"

# ============================================================================
# ZABBIX QUALIDADE
# ============================================================================

ZABBIX_API_URL = os.getenv(
    "ZABBIX_API_URL",
    "http://seu-zabbix-qua:8080/api_jsonrpc.php"
)

ZABBIX_USER = os.getenv("ZABBIX_USER", "Admin")
ZABBIX_PASSWORD = os.getenv("ZABBIX_PASSWORD", "sua-senha")
```

---

## 🌍 Variáveis de Ambiente

Para manter credenciais seguras, usar variáveis de ambiente:

### Criar arquivo `.env`

```bash
# .env (nunca committar!)
PROMETHEUS_URL=https://prometheus-prod-srv01.spms.min-saude.pt
PROMETHEUS_USER=prometheus
PROMETHEUS_PASS=5FapePt9erAhCNdylnii8s6zr2957pRx1fNGTUUR
PROMETHEUS_VERIFY_SSL=False

ZABBIX_API_URL=http://seu-zabbix-qua:8080/api_jsonrpc.php
ZABBIX_USER=Admin
ZABBIX_PASSWORD=sua-senha-zabbix

LOG_LEVEL=INFO
```

### Carregar variáveis

```bash
# No bash
source .env

# Ou no Python
from dotenv import load_dotenv
load_dotenv()
```

---

## 🚀 Exemplo Completo: Sincronizar Regras

```python
#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

# Carregar .env
load_dotenv()

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL")
PROMETHEUS_USER = os.getenv("PROMETHEUS_USER")
PROMETHEUS_PASS = os.getenv("PROMETHEUS_PASS")
PROMETHEUS_VERIFY_SSL = os.getenv("PROMETHEUS_VERIFY_SSL", "False").lower() == "true"

ZABBIX_API_URL = os.getenv("ZABBIX_API_URL")
ZABBIX_USER = os.getenv("ZABBIX_USER")
ZABBIX_PASSWORD = os.getenv("ZABBIX_PASSWORD")

def get_prometheus_rules():
    """Obter alerting rules do Prometheus"""
    auth = (PROMETHEUS_USER, PROMETHEUS_PASS)

    response = requests.get(
        f"{PROMETHEUS_URL}/api/v1/rules",
        auth=auth,
        verify=PROMETHEUS_VERIFY_SSL,
        timeout=10
    )

    response.raise_for_status()
    data = response.json()

    rules = []
    for group in data.get("data", {}).get("groups", []):
        for rule in group.get("rules", []):
            if rule.get("type") == "alerting":
                rules.append({
                    "alert": rule.get("alert"),
                    "expr": rule.get("expr"),
                    "for": rule.get("for", "5m"),
                    "severity": rule.get("labels", {}).get("severity", "warning"),
                    "description": rule.get("annotations", {}).get("description", ""),
                    "summary": rule.get("annotations", {}).get("summary", "")
                })

    return rules

def login_zabbix():
    """Fazer login no Zabbix"""
    payload = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "user": ZABBIX_USER,
            "password": ZABBIX_PASSWORD
        },
        "id": 1
    }

    response = requests.post(ZABBIX_API_URL, json=payload, timeout=10)
    result = response.json()

    if "result" in result:
        return result["result"]
    else:
        raise Exception(f"Login Zabbix falhou: {result.get('error')}")

if __name__ == "__main__":
    print("🔍 Obtendo regras do Prometheus PRD...")
    rules = get_prometheus_rules()
    print(f"✅ {len(rules)} regras encontradas")

    for rule in rules[:5]:
        print(f"  • {rule['alert']} (severity: {rule['severity']})")

    print("\n🔐 Fazendo login no Zabbix QUA...")
    token = login_zabbix()
    print(f"✅ Login bem-sucedido (token: {token[:10]}...)")
```

---

## 📊 Endpoints Prometheus Disponíveis

### Healthcheck
```bash
GET /healthz
GET /-/healthy
GET /-/ready
```

### Regras (rules)
```bash
GET /api/v1/rules
```

### Alertas (alerts)
```bash
GET /api/v1/alerts
```

### Query (instant query)
```bash
GET /api/v1/query?query=<expr>
```

### Query Range
```bash
GET /api/v1/query_range?query=<expr>&start=<timestamp>&end=<timestamp>&step=<duration>
```

### Targets
```bash
GET /api/v1/targets
```

---

## ✅ Checklist de Configuração

- [ ] Credenciais Prometheus obtidas
- [ ] Credenciais Zabbix obtidas
- [ ] Arquivo `config.py` atualizado com URLs
- [ ] Arquivo `.env` criado com credenciais (não committar!)
- [ ] `.gitignore` contém `.env`
- [ ] Dependências instaladas: `pip install -r requirements.txt`
- [ ] Teste de conexão: `python3 validate.py` ✅
- [ ] Curl test: `curl -u user:pass https://prometheus-prod-srv01.spms.min-saude.pt/-/healthy` ✅
- [ ] Primeira sincronização: `python3 sync_prometheus.py --list` ✅
- [ ] Sincronizar tudo: `python3 sync_prometheus.py --all` ✅

---

## 🔒 Boas Práticas de Segurança

1. **Nunca committar `.env`** ✅
2. **Usar `os.getenv()`** para separar config de código
3. **Usar `verify_ssl`** em produção com certificado válido
4. **Rotar senhas** regularmente
5. **Usar firewall** para limitar acesso ao Prometheus
6. **Monitorar logs** de sincronização
7. **Usar HTTPS** sempre que possível

---

## 📝 Exemplo de Deploy

```bash
# 1. Clonar repo
git clone https://github.com/seu-user/lab-zal.git
cd lab-zal/production

# 2. Criar venv
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar .env com credenciais PRD
cat > .env << EOF
PROMETHEUS_URL=https://prometheus-prod-srv01.spms.min-saude.pt
PROMETHEUS_USER=prometheus
PROMETHEUS_PASS=5FapePt9erAhCNdylnii8s6zr2957pRx1fNGTUUR
PROMETHEUS_VERIFY_SSL=False
ZABBIX_API_URL=http://seu-zabbix-qua:8080/api_jsonrpc.php
ZABBIX_USER=Admin
ZABBIX_PASSWORD=sua-senha
EOF

# 5. Validar
python3 validate.py

# 6. Sincronizar
python3 sync_prometheus.py --all

# 7. Automatizar (cron)
crontab -e
# 0 * * * * cd ~/lab-zal/production && source venv/bin/activate && python3 sync_prometheus.py --all >> /var/log/sync.log 2>&1
```

---

**Versão:** 1.0 | **Data:** 2026-03-23 | **Status:** Production Ready ✅
