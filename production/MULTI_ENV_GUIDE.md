# Deploy Manual — Multi-Ambiente (DEV / QUA / PRD)

O Prometheus é sempre o mesmo (produção). Só o Zabbix muda entre ambientes.

---

## Ficheiros necessários

| Ficheiro | Descrição |
|---|---|
| `sync_prometheus.py` | Script principal de sincronização |
| `config.py` | Lê credenciais de variáveis de ambiente |
| `requirements.txt` | Dependências Python |
| `.env.<ambiente>` | Credenciais do ambiente específico |

---

## Ambientes disponíveis

| Ficheiro | Ambiente |
|---|---|
| `.env.dev` | DEV — já preenchido |
| `.env.qua` | QUA — preencher com dados reais |
| `.env.prd` | PRD — preencher com dados reais |

### Variáveis a preencher (QUA e PRD)

```bash
ZABBIX_API_URL=https://<url-do-zabbix>/api_jsonrpc.php
ZABBIX_USER=api
ZABBIX_PASSWORD=<password>
ZABBIX_VERIFY_SSL=false
ZABBIX_SERVER=<ip-do-servidor-zabbix>
ZABBIX_TRAPPER_PORT=10051
```

---

## Como fazer deploy num servidor

### 1. Copiar os ficheiros

```bash
scp sync_prometheus.py config.py requirements.txt .env.qua user@servidor-qua:/opt/prometheus-sync/
```

### 2. No servidor, instalar dependências (só uma vez)

```bash
pip install -r requirements.txt
```

### 3. Carregar as variáveis do ambiente

```bash
source .env.qua
```

### 4. Correr

```bash
# Criar/actualizar estrutura no Zabbix (hosts, items, triggers)
python sync_prometheus.py --all

# Enviar valores dos alertas activos para o Zabbix
python sync_prometheus.py --push
```

---

## Comandos disponíveis

| Comando | O que faz |
|---|---|
| `python sync_prometheus.py --all` | Cria host, items e triggers no Zabbix |
| `python sync_prometheus.py --push` | Envia valores dos alertas activos via Trapper |
| `python sync_prometheus.py --verbose` | Modo debug com mais detalhe nos logs |

---

## Notas

- O `--all` deve correr primeiro para criar a estrutura antes do `--push`.
- Para automatizar, basta colocar ambos em cron ou usar o `scheduler.py`.
- Os logs ficam em `/var/log/prometheus-zabbix-sync.log` (se o servidor tiver permissão) e no terminal.
