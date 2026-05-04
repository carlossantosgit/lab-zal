# Container Guide — Prometheus → Zabbix Sync

## Visão Geral

O container executa o sincronizador `sync_prometheus.py` em modo contínuo através de um scheduler Python interno, sem depender de cron do sistema operativo.

```
[Container]
  scheduler.py
    ├── cada 5 min → sync_prometheus.py --all   (cria/actualiza items e triggers)
    └── cada 1 min → sync_prometheus.py --push  (envia valores dos alertas activos)
```

---

## Ficheiros

```
production/
├── Dockerfile            imagem base python:3.11-slim
├── docker-compose.yml    definição do serviço
├── scheduler.py          loop interno com intervalos configuráveis
├── config.py             credenciais via env vars (com defaults para Dev)
├── sync_prometheus.py    lógica principal
├── validate.py           validação de conectividade (Prometheus + Zabbix)
├── requirements.txt      dependências Python
└── .env.example          template para sobrepor configuração
```

---

## Pré-requisitos

- Docker >= 20.10
- Docker Compose >= 2.0

```bash
docker --version
docker compose version
```

---

## Arranque Rápido (ambiente Dev)

Os defaults no `config.py` já apontam para o ambiente Dev — **não é necessário criar nenhum `.env`**.

```bash
cd production

# Build da imagem e arranque em background
docker compose up -d --build

# Verificar que o container está a correr
docker compose ps

# Ver logs em tempo real
docker compose logs -f
```

---

## Outro Ambiente (Prod, Staging, etc.)

Para sobrepor credenciais ou intervalos, exporta as variáveis antes de arrancar:

```bash
export ZABBIX_API_URL=https://zabbix-prod.empresa.pt/api_jsonrpc.php
export ZABBIX_PASSWORD=password_producao
export PROMETHEUS_URL=https://prometheus-prod.empresa.pt
export PROMETHEUS_PASS=password_producao

docker compose up -d --build
```

Ou cria um `.env` na pasta `production/` e o docker compose carrega-o automaticamente:

```env
ZABBIX_API_URL=https://zabbix-prod.empresa.pt/api_jsonrpc.php
ZABBIX_PASSWORD=password_producao
PROMETHEUS_URL=https://prometheus-prod.empresa.pt
PROMETHEUS_PASS=password_producao
```

```bash
docker compose up -d --build
```

---

## Variáveis de Configuração

| Variável | Default (Dev) | Descrição |
|---|---|---|
| `ZABBIX_API_URL` | `https://zabbix-dev.../api_jsonrpc.php` | URL da API Zabbix |
| `ZABBIX_USER` | `api` | Utilizador Zabbix |
| `ZABBIX_PASSWORD` | *(valor dev)* | Password Zabbix |
| `ZABBIX_VERIFY_SSL` | `false` | Verificar certificado SSL |
| `PROMETHEUS_URL` | `https://prometheus-prod-srv01...` | URL do Prometheus |
| `PROMETHEUS_USER` | `prometheus` | Utilizador Prometheus |
| `PROMETHEUS_PASS` | *(valor dev)* | Password Prometheus |
| `PROMETHEUS_VERIFY_SSL` | `false` | Verificar certificado SSL |
| `SYNC_INTERVAL_MINUTES` | `5` | Intervalo do `--all` em minutos |
| `PUSH_INTERVAL_MINUTES` | `1` | Intervalo do `--push` em minutos |
| `LOG_LEVEL` | `INFO` | Nível de log (`DEBUG`, `INFO`, `WARNING`) |

---

## Comandos Úteis

```bash
# Ver estado do container
docker compose ps

# Logs em tempo real
docker compose logs -f

# Últimas 100 linhas de log
docker compose logs --tail=100

# Parar o container
docker compose down

# Reiniciar
docker compose restart

# Rebuild da imagem (após alterações de código)
docker compose up -d --build

# Entrar no container para debug
docker compose exec prometheus-zabbix-sync sh

# Correr o sync manualmente dentro do container
docker compose exec prometheus-zabbix-sync python sync_prometheus.py --all
docker compose exec prometheus-zabbix-sync python sync_prometheus.py --push

# Validar conectividade (Prometheus + Zabbix)
docker compose exec prometheus-zabbix-sync python validate.py
```

---

## Logs

Os logs saem para `stdout` e são geridos pelo Docker com rotação automática:

- Tamanho máximo por ficheiro: **10 MB**
- Número de ficheiros retidos: **3**

Para ver os ficheiros de log físicos no host:

```bash
# Localizar os logs do container
docker inspect prometheus-zabbix-sync | grep LogPath
```

---

## Conectividade de Rede

O container precisa de acesso de rede a dois endpoints externos:

| Destino | Porta | Utilização |
|---|---|---|
| Zabbix API | 4443 (HTTPS) | Criar items, triggers, actualizar tags |
| Zabbix Trapper | 10151 (TCP) | Enviar valores dos alertas (`--push`) |
| Prometheus API | 443 (HTTPS) | Ler alertas activos e regras |

Para verificar conectividade antes de arrancar:

```bash
# Teste rápido de rede a partir de um container temporário
docker run --rm python:3.11-slim python -c "
import socket
for host, port in [('10.43.69.137', 4443), ('10.43.69.137', 10151)]:
    try:
        socket.create_connection((host, port), timeout=3).close()
        print('OK  %s:%s' % (host, port))
    except Exception as e:
        print('FAIL %s:%s — %s' % (host, port, e))
"
```

---

## Troubleshooting

**Container sai imediatamente**
```bash
docker compose logs
# Verificar erros de credenciais ou conectividade
```

**Triggers não estão a ser criadas**
```bash
# Correr o --all manualmente e observar output
docker compose exec prometheus-zabbix-sync python sync_prometheus.py --all
```

**Valores não chegam ao Zabbix**
```bash
# Correr o --push manualmente
docker compose exec prometheus-zabbix-sync python sync_prometheus.py --push
# Verificar linha "Trapper resposta: processed: X"
```

**Ver configuração activa no container**
```bash
docker compose exec prometheus-zabbix-sync python -c "
import config
print('Zabbix:', config.ZABBIX_API_URL)
print('Prometheus:', config.PROMETHEUS_URL)
"
```
