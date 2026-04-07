# 🚀 Sincronização Prometheus → Zabbix

Setup manual - Copiar 6 arquivos e rodar.

**SEM git, SEM .env - Tudo hardcoded em config.py**

---

## 📦 Arquivos (6 apenas)

```
config.py              ← Editar credenciais aqui
validate.py            ← Validar conexão
sync_prometheus.py     ← Sincronizar
requirements.txt       ← Dependências
README.md              ← Este arquivo
DEPLOYMENT.md          ← Guia de deployment
```

---

## ⚡ Resumo (10 min)

```bash
# 1. Copiar os 6 arquivos para /home/usuario/prometheus-zabbix/

# 2. Editar config.py
cd /home/usuario/prometheus-zabbix
nano config.py
# Alterar: PROMETHEUS_URL, PROMETHEUS_USER, PROMETHEUS_PASS, ZABBIX_API_URL, ZABBIX_USER, ZABBIX_PASSWORD

# 3. Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Validar
python3 validate.py
# Esperado: ✅ VALIDAÇÃO OK

# 5. Sincronizar
python3 sync_prometheus.py --all

# 6. Automação (opcional)
crontab -e
# Adicionar: 0 * * * * cd /home/usuario/prometheus-zabbix && source venv/bin/activate && python3 sync_prometheus.py --all >> /var/log/prometheus-zabbix-sync.log 2>&1
```

---

## 🔧 Configuração (config.py)

**6 linhas para editar:**

```python
PROMETHEUS_URL = "https://seu-prometheus"   ← EDITAR
PROMETHEUS_USER = "usuario"                  ← EDITAR
PROMETHEUS_PASS = "senha"                    ← EDITAR

ZABBIX_API_URL = "http://seu-zabbix:8080/api_jsonrpc.php"  ← EDITAR
ZABBIX_USER = "Admin"                        ← EDITAR
ZABBIX_PASSWORD = "senha"                    ← EDITAR
```

---

## 📋 Comandos

```bash
# Ativar venv (sempre primeiro)
source venv/bin/activate

# Validar
python3 validate.py

# Listar hosts
python3 sync_prometheus.py --list

# Sincronizar tudo
python3 sync_prometheus.py --all

# Sincronizar 1 host
python3 sync_prometheus.py --host seu-host

# Com detalhes
python3 sync_prometheus.py --all --verbose

# Ver logs
tail -f /var/log/prometheus-zabbix-sync.log
```

---

## ⚠️ IMPORTANTE

| ❌ ERRADO | ✅ CERTO |
|-----------|---------|
| Usar .env | Editar config.py |
| Esquecer venv | `source venv/bin/activate` |
| Sem validar | `python3 validate.py` sempre |
| Valores de exemplo | Colocar valores REAIS |

---

**Para detalhes:** Ver `DEPLOYMENT.md`


