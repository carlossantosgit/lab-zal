# 🚀 Sincronização Prometheus → Zabbix

Sistema Python para sincronizar alerting rules do Prometheus com Zabbix.

**Arquitetura:**
```
Prometheus (PRODUÇÃO)  →  Python Scripts (QUA)  →  Zabbix (QUA)
```

---

## ⚡ Quick Start

### 1️⃣ Instalar dependências

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2️⃣ Configurar URLs

Editar `config.py`:
```python
# Prometheus em PRODUÇÃO
PROMETHEUS_API_URL = "http://seu-prometheus-prod:9090"

# Zabbix em QUA
ZABBIX_API_URL = "http://seu-zabbix-qua:8080/api_jsonrpc.php"

# Credenciais Zabbix
ZABBIX_USER = "Admin"
ZABBIX_PASSWORD = "sua-senha"
```

### 3️⃣ Validar conexão

```bash
python3 validate.py
```

Retorna:
```
✅ Prometheus OK
✅ Zabbix OK
✅ 32 alerting rules encontradas
✅ VALIDAÇÃO OK!
```

### 4️⃣ Sincronizar

```bash
# Ver hosts em Zabbix
python3 sync_prometheus.py --list

# Sincronizar todos
python3 sync_prometheus.py --all

# Sincronizar um host específico
python3 sync_prometheus.py --host seu-host
```

---

## 📋 Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `sync_prometheus.py` | ⭐ Script principal de sincronização |
| `validate.py` | Valida conectividade |
| `config.py` | Configuração (editar URLs/credenciais) |
| `requirements.txt` | Dependências Python |

---

## 🎯 O que faz

- ✅ Lê alerting rules do Prometheus
- ✅ Sincroniza como items em Zabbix
- ✅ Cria triggers com severidades corretas
- ✅ Idempotente (sem duplicatas)

---

## ⏰ Automação (Cron)

Adicionar ao crontab para sincronizar a cada hora:

```bash
crontab -e

# Sincronizar a cada hora
0 * * * * cd /home/seu-usuario/prometheus-sync && source venv/bin/activate && python3 sync_prometheus.py --all >> /var/log/prometheus-sync.log 2>&1
```

---

## 🔍 Troubleshooting

**Erro de conexão:**
```bash
# Testar Prometheus
curl http://seu-prometheus-prod:9090/-/healthy

# Testar Zabbix
curl http://seu-zabbix-qua:8080
```

**Erro de autenticação:**
```bash
# Verificar credenciais em config.py
```

**Items já existem:**
```bash
# Normal! Sincronização é idempotente
# Continua sincronizando outros items
```

---

## 📱 Comandos Principais

```bash
python3 validate.py                    # Validar config
python3 sync_prometheus.py --list      # Ver hosts
python3 sync_prometheus.py --all       # Sincronizar tudo
python3 sync_prometheus.py --host X    # Sincronizar host X
```

---

**GitHub:** https://github.com/carlossantosgit/lab-zal | **Status:** Production Ready
