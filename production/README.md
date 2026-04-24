# Sincronização Prometheus → Zabbix

Sincroniza alertas ativos do Prometheus para o Zabbix usando um host único com items parametrizados, enviando valores via Zabbix Trapper.

**Sem git, sem .env — configuração hardcoded em `config.py`**

---

## Arquivos

```
config.py              ← Editar credenciais aqui
validate.py            ← Validar conectividade
sync_prometheus.py     ← Script principal
requirements.txt       ← Dependências Python
README.md              ← Este arquivo
DEPLOYMENT.md          ← Guia de deployment detalhado
SYNC_GUIDE.md          ← Guia operacional completo
sync_prometheus.py.bk  ← Backup do script
```

---

## Setup Rápido (10 min)

```bash
# 1. Copiar arquivos para /home/usuario/prometheus-zabbix/
cd /home/usuario/prometheus-zabbix

# 2. Editar credenciais
nano config.py

# 3. Criar ambiente virtual e instalar dependências
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Validar conectividade
python3 validate.py

# 5. Sincronizar (cria host + items + triggers)
python3 sync_prometheus.py --all

# 6. Enviar valores dos alertas ativos
python3 sync_prometheus.py --push
```

---

## Configuração (config.py)

```python
# Zabbix
ZABBIX_API_URL  = "https://seu-zabbix/api_jsonrpc.php"
ZABBIX_USER     = "api"
ZABBIX_PASSWORD = "sua-senha"

# Prometheus
PROMETHEUS_URL  = "https://seu-prometheus"
PROMETHEUS_USER = "usuario"
PROMETHEUS_PASS = "sua-senha"

# Zabbix Trapper (em sync_prometheus.py)
ZABBIX_SERVER        = "IP-do-servidor-zabbix"
ZABBIX_TRAPPER_PORT  = "10151"
```

---

## Comandos

```bash
# Ativar venv (sempre primeiro)
source venv/bin/activate

# Validar conectividade
python3 validate.py

# Sincronizar: cria host único + items + triggers
python3 sync_prometheus.py --all

# Enviar alertas ativos para items via Zabbix Trapper
python3 sync_prometheus.py --push

# Modo verbose
python3 sync_prometheus.py --all --verbose
python3 sync_prometheus.py --push --verbose

# Ver logs
tail -f /var/log/prometheus-zabbix-sync.log
```

---

## Arquitetura (Novo Modelo)

- **1 host único** chamado `prometheus` no Zabbix
- **Items parametrizados** por alerta e instância:
  ```
  prom.alert.status[alertname,instance]
  prom.alert.severity[alertname,instance]
  prom.alert.summary[alertname,instance]
  prom.alert.payload[alertname,instance]
  ```
- **Triggers** com expressão baseada no `status` e tags dos labels do Prometheus
- **Push** via protocolo Zabbix Trapper (TCP socket direto)

---

## Automação (Cron)

```bash
crontab -e
```

```
# Sincronizar estrutura a cada hora
0 * * * * cd /home/usuario/prometheus-zabbix && source venv/bin/activate && python3 sync_prometheus.py --all >> /var/log/prometheus-zabbix-sync.log 2>&1

# Enviar valores a cada 5 minutos
*/5 * * * * cd /home/usuario/prometheus-zabbix && source venv/bin/activate && python3 sync_prometheus.py --push >> /var/log/prometheus-zabbix-sync.log 2>&1
```

---

**Para detalhes:** ver `DEPLOYMENT.md` e `SYNC_GUIDE.md`
