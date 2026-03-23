# 🚀 Sincronização Prometheus → Zabbix (PRODUÇÃO)

Sistema Python para sincronizar alerting rules do Prometheus em produção com Zabbix em qualidade.

**Arquitetura:**
```
Prometheus PRODUÇÃO (HTTPS)  →  Python Scripts (QUA)  →  Zabbix (QUA)
prometheus-prod-srv01.spms.min-saude.pt      |      zabbix-server
                                        Autenticação Básica
```

---

## ⚡ Quick Start

### 1️⃣ Instalar dependências

```bash
cd ~/lab-zal/production
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2️⃣ Configurar credenciais (Variáveis de Ambiente)

Criar arquivo `.env` na pasta production:

```bash
# Prometheus PRD (HTTPS com autenticação básica)
PROMETHEUS_URL=https://prometheus-prod-srv01.spms.min-saude.pt
PROMETHEUS_USER=prometheus
PROMETHEUS_PASS=5FapePt9erAhCNdylnii8s6zr2957pRx1fNGTUUR
PROMETHEUS_VERIFY_SSL=False  # False se usar cert auto-assinado

# Zabbix QUA
ZABBIX_API_URL=http://seu-zabbix-qua:8080/api_jsonrpc.php
ZABBIX_USER=Admin
ZABBIX_PASSWORD=sua-senha-zabbix
```

**Ou editar `config.py` diretamente:**

```python
# Prometheus em PRODUÇÃO (com autenticação)
PROMETHEUS_URL = "https://prometheus-prod-srv01.spms.min-saude.pt"
PROMETHEUS_USER = "prometheus"
PROMETHEUS_PASS = "5FapePt9erAhCNdylnii8s6zr2957pRx1fNGTUUR"
PROMETHEUS_VERIFY_SSL = False  # True para validar certificado

# Zabbix em QUA
ZABBIX_API_URL = "http://seu-zabbix-qua:8080/api_jsonrpc.php"
ZABBIX_USER = "Admin"
ZABBIX_PASSWORD = "sua-senha"
```

### 3️⃣ Exemplo de Chamada com Autenticação Básica

```python
import requests

PROMETHEUS_URL = "https://prometheus-prod-srv01.spms.min-saude.pt"
PROMETHEUS_USER = "prometheus"
PROMETHEUS_PASS = "5FapePt9erAhCNdylnii8s6zr2957pRx1fNGTUUR"

# Obter alerting rules
response = requests.get(
    f"{PROMETHEUS_URL}/api/v1/rules",
    auth=(PROMETHEUS_USER, PROMETHEUS_PASS),
    verify=False  # ou apontar para o cert da CA interna
)

# Obter status de saúde
response = requests.get(
    f"{PROMETHEUS_URL}/-/healthy",
    auth=(PROMETHEUS_USER, PROMETHEUS_PASS),
    verify=False
)

# Obter alertas ativos
response = requests.get(
    f"{PROMETHEUS_URL}/api/v1/alerts",
    auth=(PROMETHEUS_USER, PROMETHEUS_PASS),
    verify=False
)
```

### 4️⃣ Validar conexão

```bash
source venv/bin/activate
python3 validate.py
```

Retorna:
```
✅ Prometheus OK
✅ Zabbix OK
✅ 32 alerting rules encontradas
✅ 5 hosts encontrados em Zabbix
✅ VALIDAÇÃO OK - Sistema pronto para sincronização!
```

### 5️⃣ Análise de Mapeamento (IMPORTANTE!)

```bash
source venv/bin/activate
python3 analise_mapeamento.py
```

Isso gera:
- Lista de Zabbix Host Groups
- Lista de Prometheus "app" labels
- Tabela de mapeamento recomendado

Criar arquivo: `MAPPING_PROMETHEUS_ZABBIX.md` com mapeamento

### 6️⃣ Sincronizar Regras

```bash
source venv/bin/activate

# Ver hosts disponíveis
python3 sync_prometheus.py --list

# Sincronizar todos os hosts
python3 sync_prometheus.py --all

# Sincronizar um host específico
python3 sync_prometheus.py --host seu-host

# Modo verbose (com mais detalhes)
python3 sync_prometheus.py --all --verbose
```

---

## 📋 Arquivos de Configuração

| Arquivo | Descrição |
|---------|-----------|
| `config.py` | ⚙️ Configuração (URLs, credenciais, environment vars) |
| `sync_prometheus.py` | ⭐ Script principal de sincronização |
| `validate.py` | ✅ Validação de conectividade |
| `analise_mapeamento.py` | 🔍 Análise de mapeamento (labels → groups) |
| `requirements.txt` | 📦 Dependências Python |

---

## 🔐 Autenticação Prometheus (HTTPS)

O Prometheus em produção usa:
- **URL:** `https://prometheus-prod-srv01.spms.min-saude.pt`
- **Método:** Autenticação básica HTTP
- **Usuário:** `prometheus`
- **Senha:** `5FapePt9erAhCNdylnii8s6zr2957pRx1fNGTUUR`

**Nota sobre SSL:**
- Se usar certificado auto-assinado: `PROMETHEUS_VERIFY_SSL = False`
- Se usar certificado válido: `PROMETHEUS_VERIFY_SSL = True`
- Ou apontar arquivo CA: `verify="/path/to/ca-bundle.crt"`

---

## 🎯 O que o Script Faz

- ✅ Conecta ao Prometheus com autenticação básica (HTTPS)
- ✅ Lê alerting rules do Prometheus
- ✅ Sincroniza como items em Zabbix
- ✅ Cria triggers com severidades corretas
- ✅ Idempotente (sem duplicatas)
- ✅ Mapeia hosts em grupos corretos

---

## 🔍 Análise de Mapeamento (Prometheus → Zabbix)

Antes de sincronizar em produção:

```bash
# 1. Executar análise
python3 analise_mapeamento.py

# 2. Criar arquivo: MAPPING_PROMETHEUS_ZABBIX.md
# Com o mapeamento:
# {
#   "database": {
#     "zabbix_group": "Databases",
#     "group_id": "11",
#     "hosts": ["prod-db-01", "prod-db-02"]
#   },
#   "api": {
#     "zabbix_group": "API Servers",
#     "group_id": "12",
#     "hosts": ["prod-api-01"]
#   }
# }
```

---

## ⏰ Automação (Cron)

Para sincronizar a cada hora em produção:

```bash
crontab -e

# Adicionar:
0 * * * * cd /home/seu-usuario/lab-zal/production && source venv/bin/activate && python3 sync_prometheus.py --all >> /var/log/prometheus-zabbix-sync.log 2>&1
```

---

## 🔍 Troubleshooting

### Erro de autenticação Prometheus

```bash
# Testar conexão manualmente
curl -u prometheus:5FapePt9erAhCNdylnii8s6zr2957pRx1fNGTUUR \
  https://prometheus-prod-srv01.spms.min-saude.pt/-/healthy

# Se tiver erro de SSL:
curl -k -u prometheus:5FapePt9erAhCNdylnii8s6zr2957pRx1fNGTUUR \
  https://prometheus-prod-srv01.spms.min-saude.pt/-/healthy
```

### Erro de conexão Zabbix

```bash
# Testar Zabbix
curl http://seu-zabbix-qua:8080

# Verificar credenciais em config.py
```

### Items ou triggers já existem

```bash
# Normal! Sincronização é idempotente
# Continua sincronizando novos items
# Não cria duplicatas
```

---

## 📱 Comandos Principais

```bash
# Validar configuração
python3 validate.py

# Analisar mapeamento
python3 analise_mapeamento.py

# Listar hosts
python3 sync_prometheus.py --list

# Sincronizar tudo
python3 sync_prometheus.py --all

# Sincronizar host específico
python3 sync_prometheus.py --host seu-host

# Com detalhes
python3 sync_prometheus.py --all --verbose
```

---

## ✅ Checklist de Deployment

- [ ] Criar `.env` com credenciais (ou editar `config.py`)
- [ ] Instalar dependências: `pip install -r requirements.txt`
- [ ] Executar validação: `python3 validate.py` ✅
- [ ] Analisar mapeamento: `python3 analise_mapeamento.py`
- [ ] Criar `MAPPING_PROMETHEUS_ZABBIX.md`
- [ ] Testar sincronização em um host: `python3 sync_prometheus.py --host test-host`
- [ ] Se OK, sincronizar todos: `python3 sync_prometheus.py --all`
- [ ] Configurar cron para automação
- [ ] Monitorar logs: `tail -f /var/log/prometheus-zabbix-sync.log`

---

**GitHub:** https://github.com/carlossantosgit/lab-zal | **Status:** Production Ready ✅
