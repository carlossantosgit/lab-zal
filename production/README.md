# 🚀 Sincronização Prometheus → Zabbix (PRODUÇÃO)

Sistema Python para sincronizar alerting rules do Prometheus com Zabbix.

---

## 📦 Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `config.py` | ⚙️ Configuração (editar credenciais aqui) |
| `validate.py` | ✅ Validação de conectividade |
| `sync_prometheus.py` | ⭐ Script principal de sincronização |
| `requirements.txt` | 📦 Dependências Python |
| `README.md` | Este arquivo |
| `DEPLOYMENT.md` | 🚀 Guia de deployment |

---

## ⚡ Quick Start

### 1. Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar
```bash
nano config.py  # Editar credenciais
```

### 3. Validar
```bash
python3 validate.py
```

**Esperado:**
```
✅ Prometheus OK
✅ Zabbix OK
✅ XX alerting rules encontradas
✅ X hosts encontrados em Zabbix
✅ VALIDAÇÃO OK - Sistema pronto para sincronização!
```

### 4. Sincronizar
```bash
# Ver hosts
python3 sync_prometheus.py --list

# Sincronizar todos
python3 sync_prometheus.py --all

# Sincronizar host específico
python3 sync_prometheus.py --host seu-host
```

---

## 🔧 Configuração (config.py)

Editar apenas estes 6 valores:

```python
PROMETHEUS_URL = "https://seu-prometheus"
PROMETHEUS_USER = "usuario"
PROMETHEUS_PASS = "senha"

ZABBIX_API_URL = "http://seu-zabbix:8080/api_jsonrpc.php"
ZABBIX_USER = "Admin"
ZABBIX_PASSWORD = "senha"
```

---

## 📋 Comandos

```bash
python3 validate.py                    # Validar conectividade
python3 sync_prometheus.py --list      # Listar hosts
python3 sync_prometheus.py --all       # Sincronizar tudo
python3 sync_prometheus.py --host xxx  # Sincronizar host X
python3 sync_prometheus.py --all -v    # Com detalhes
```

---

## ⏰ Automação (Cron)

```bash
crontab -e

# Adicionar (sincroniza cada hora):
0 * * * * cd /home/usuario/production && source venv/bin/activate && python3 sync_prometheus.py --all >> /var/log/prometheus-zabbix-sync.log 2>&1
```

---

**Para deployment, ver: `DEPLOYMENT.md`**

