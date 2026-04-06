# 📋 Deployment Production - Cópia Manual

**Setup sem git clone - Copiar arquivos manualmente**

---

## 📦 Arquivos para Copiar

**Total: 6 arquivos**

```
✅ config.py
✅ validate.py
✅ sync_prometheus.py
✅ requirements.txt
✅ README.md
✅ DEPLOYMENT.md
```

---

## 🚀 PASSO 1: Copiar Arquivos

**Para `/home/seu-usuario/prometheus-zabbix/`**

```bash
# Criar pasta
mkdir -p /home/seu-usuario/prometheus-zabbix
cd /home/seu-usuario/prometheus-zabbix

# Copiar os 6 arquivos aquela
# (scp, wget, cat > file, etc.)
```

---

## ⚙️ PASSO 2: Editar config.py (CRÍTICO)

```bash
nano config.py
```

**Alterar APENAS estes 6 valores:**

```python
PROMETHEUS_URL = "https://seu-prometheus"
PROMETHEUS_USER = "seu-usuario"
PROMETHEUS_PASS = "sua-senha"

ZABBIX_API_URL = "http://seu-zabbix:8080/api_jsonrpc.php"
ZABBIX_USER = "Admin"
ZABBIX_PASSWORD = "sua-senha"
```

**SEM .env - tudo hardcoded em config.py**

---

## 🐍 PASSO 3: Setup Python

```bash
# Verificar Python
python3 --version  # Precisa ≥3.8

# Criar venv
python3 -m venv venv

# Ativar
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

---

## ✅ PASSO 4: Validar

```bash
python3 validate.py
```

**Esperado:**
```
✅ Prometheus OK
✅ Zabbix OK (login bem-sucedido)
✅ XX alerting rules encontradas
✅ X hosts encontrados em Zabbix
✅ VALIDAÇÃO OK - Sistema pronto para sincronização!
```

**Se falhar:** revisar `config.py` (URLs e credenciais)

---

## 🔄 PASSO 5: Sincronizar

```bash
# Ver hosts
python3 sync_prometheus.py --list

# Sincronizar TODOS
python3 sync_prometheus.py --all

# Sincronizar 1 host
python3 sync_prometheus.py --host seu-host

# Com detalhes
python3 sync_prometheus.py --all --verbose
```

---

## ⏰ PASSO 6: Automação (Cron)

```bash
crontab -e
```

Adicionar:
```bash
0 * * * * cd /home/seu-usuario/prometheus-zabbix && source venv/bin/activate && python3 sync_prometheus.py --all >> /var/log/prometheus-zabbix-sync.log 2>&1
```

---

## 📋 Comandos Principais

```bash
# Sempre que abrir terminal
source venv/bin/activate

# Validar
python3 validate.py

# Listar hosts
python3 sync_prometheus.py --list

# Sincronizar
python3 sync_prometheus.py --all

# Ver logs
tail -f /var/log/prometheus-zabbix-sync.log
```

---

## ⚠️ Pontos Críticos

| ❌ ERRADO | ✅ CERTO |
|-----------|---------|
| Usar .env | Editar `config.py` |
| Esquecer venv | `source venv/bin/activate` |
| Sem validar | `python3 validate.py` primeiro |
| Credenciais de exemplo | Alterar config.py com valores REAIS |

---

## 🆘 Troubleshooting

### "Prometheus não acessível"
- Verificar `PROMETHEUS_URL` em config.py
- Testrar: `curl -k -u user:pass https://url/-/healthy`

### "Zabbix não acessível"
- Verificar `ZABBIX_API_URL` em config.py
- Testrar: `curl http://seu-zabbix:8080`

### "Login falhou"
- Revisar `ZABBIX_USER` e `ZABBIX_PASSWORD`

### "requests não instalado"
- `source venv/bin/activate`
- `pip install -r requirements.txt`

---

**Pronto!** 🚀

