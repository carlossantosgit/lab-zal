# Deployment — Cópia Manual

Setup sem git clone. Copiar arquivos manualmente para o servidor de produção.

---

## Pré-requisitos

- Python 3.8 ou superior
- Acesso de rede ao Zabbix API (porta 4443 ou 443)
- Acesso de rede ao Prometheus (porta 443)
- Acesso TCP ao Zabbix Trapper (porta 10151 por padrão)

---

## PASSO 1: Copiar Arquivos

```bash
mkdir -p /home/seu-usuario/prometheus-zabbix
cd /home/seu-usuario/prometheus-zabbix

# Copiar via scp, rsync, wget ou manualmente:
# config.py, validate.py, sync_prometheus.py, requirements.txt
```

Arquivos necessários (mínimo):
```
config.py
validate.py
sync_prometheus.py
requirements.txt
```

---

## PASSO 2: Editar config.py

```bash
nano config.py
```

Alterar os seguintes valores:

```python
# --- Zabbix ---
ZABBIX_API_URL  = "https://seu-zabbix:4443/api_jsonrpc.php"
ZABBIX_USER     = "api"
ZABBIX_PASSWORD = "sua-senha-zabbix"
ZABBIX_VERIFY_SSL = False  # True se tiver certificado válido

# --- Prometheus ---
PROMETHEUS_URL  = "https://seu-prometheus"
PROMETHEUS_USER = "prometheus"
PROMETHEUS_PASS = "sua-senha-prometheus"
PROMETHEUS_VERIFY_SSL = False  # True se tiver certificado válido
```

Também editar em `sync_prometheus.py` (linhas 30-31):

```python
ZABBIX_SERVER        = "IP-do-servidor-zabbix"
ZABBIX_TRAPPER_PORT  = "10151"
```

---

## PASSO 3: Setup Python

```bash
# Verificar versão (necessário >= 3.8)
python3 --version

# Criar ambiente virtual
python3 -m venv venv

# Ativar
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

---

## PASSO 4: Validar Conectividade

```bash
python3 validate.py
```

Saída esperada:
```
✅ Prometheus OK
✅ Zabbix OK (login bem-sucedido)
✅ XX alerting rules encontradas
✅ X hosts encontrados em Zabbix
✅ VALIDAÇÃO OK - Sistema pronto para sincronização!
```

Se falhar: revisar URLs e credenciais em `config.py`.

---

## PASSO 5: Primeiro Sync

```bash
# Cria o host único "prometheus" + items parametrizados + triggers
python3 sync_prometheus.py --all
```

Saída esperada:
```
======================================================================
SYNC ALL (NOVO MODELO)
======================================================================
Host existente encontrado: prometheus (id=XXX)
Prometheus alertas activos: N instancias
Prometheus rules: N regras unicas
Host: X items, Y triggers existentes
Build plan: N items unicas
Build plan: N triggers
Items criados: N
Triggers criadas: N
======================================================================
SYNC COMPLETO
  Items: N (novos: +N)
  Triggers: N (novas: +N)
======================================================================
```

---

## PASSO 6: Enviar Valores (Push)

```bash
# Envia valores dos alertas ativos via Zabbix Trapper
python3 sync_prometheus.py --push
```

Este comando deve ser executado periodicamente (ver Passo 7).

---

## PASSO 7: Automação com Cron

```bash
crontab -e
```

Adicionar:

```bash
# Sincronizar estrutura (host, items, triggers) a cada hora
0 * * * * cd /home/seu-usuario/prometheus-zabbix && source venv/bin/activate && python3 sync_prometheus.py --all >> /var/log/prometheus-zabbix-sync.log 2>&1

# Enviar valores dos alertas a cada 5 minutos
*/5 * * * * cd /home/seu-usuario/prometheus-zabbix && source venv/bin/activate && python3 sync_prometheus.py --push >> /var/log/prometheus-zabbix-sync.log 2>&1
```

> **Nota:** `--all` cria a estrutura (idempotente, seguro repetir). `--push` envia os valores atuais dos alertas.

---

## Comandos de Referência

```bash
# Ativar venv
source venv/bin/activate

# Validar
python3 validate.py

# Sincronizar estrutura
python3 sync_prometheus.py --all

# Enviar alertas ativos
python3 sync_prometheus.py --push

# Modo verbose
python3 sync_prometheus.py --all --verbose

# Ver logs
tail -f /var/log/prometheus-zabbix-sync.log
```

---

## Troubleshooting

### "Prometheus não acessível"
- Verificar `PROMETHEUS_URL` em `config.py`
- Testar: `curl -k -u user:pass https://url/-/healthy`

### "Zabbix não acessível"
- Verificar `ZABBIX_API_URL` em `config.py`
- Testar: `curl -k https://seu-zabbix:4443/api_jsonrpc.php`

### "Login Zabbix falhou"
- Revisar `ZABBIX_USER` e `ZABBIX_PASSWORD` em `config.py`

### "Trapper não consegue enviar"
- Verificar `ZABBIX_SERVER` e `ZABBIX_TRAPPER_PORT` em `sync_prometheus.py`
- Testar: `nc -zv IP-zabbix 10151`

### "requests não instalado"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Sem alertas ativos
- O Prometheus pode não ter alertas firing neste momento
- Verificar: `curl -k -u user:pass https://prometheus/-/api/v1/alerts`
