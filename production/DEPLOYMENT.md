# Deployment — Container Docker

Deploy do sincronizador Prometheus → Zabbix via Docker Compose.  
Não requer Python, venv, nem ficheiro `.env` no ambiente Dev.

---

## Pré-requisitos

- Docker >= 20.10
- Docker Compose >= 2.0
- Acesso de rede ao Zabbix API (porta 4443)
- Acesso TCP ao Zabbix Trapper (porta 10151)
- Acesso de rede ao Prometheus (porta 443)

```bash
docker --version
docker compose version
```

---

## PASSO 1: Copiar Ficheiros para o Servidor

Copiar a pasta `production/` para o servidor via scp, rsync ou manualmente.

Ficheiros necessários:
```
Dockerfile
docker-compose.yml
scheduler.py
config.py
sync_prometheus.py
validate.py
requirements.txt
```

---

## PASSO 2: Build e Arranque

```bash
cd production

# Build da imagem e arranque em background
docker compose up -d --build

# Verificar que está a correr
docker compose ps

# Ver logs em tempo real
docker compose logs -f
```

O container arranca imediatamente com as credenciais Dev e executa:
- `--all` na inicialização e depois a cada **5 minutos**
- `--push` na inicialização e depois a cada **1 minuto**

---

## PASSO 3: Validar Conectividade (Opcional)

```bash
docker compose exec prometheus-zabbix-sync python validate.py
```

Saída esperada:
```
Prometheus OK
Zabbix OK (login bem-sucedido)
XX alerting rules encontradas
X hosts encontrados em Zabbix
VALIDAÇÃO OK - Sistema pronto para sincronização!
```

---

## Sobrepor Configuração (Outros Ambientes)

Para Prod, Staging ou qualquer ambiente diferente do Dev, exportar as variáveis antes de arrancar:

```bash
export ZABBIX_API_URL=https://zabbix-prod.empresa.pt/api_jsonrpc.php
export ZABBIX_PASSWORD=password_producao
export PROMETHEUS_URL=https://prometheus-prod.empresa.pt
export PROMETHEUS_PASS=password_producao

docker compose up -d --build
```

Ou criar um ficheiro `.env` na pasta `production/`:

```env
ZABBIX_API_URL=https://zabbix-prod.empresa.pt/api_jsonrpc.php
ZABBIX_PASSWORD=password_producao
PROMETHEUS_URL=https://prometheus-prod.empresa.pt
PROMETHEUS_PASS=password_producao
```

```bash
docker compose up -d --build
```

Ver `.env.example` para todas as variáveis disponíveis.

---

## Verificar Configuração Activa

```bash
docker compose exec prometheus-zabbix-sync python -c "
import config
print('Zabbix:', config.ZABBIX_API_URL)
print('Prometheus:', config.PROMETHEUS_URL)
"
```

---

## Comandos de Referência

```bash
# Estado do container
docker compose ps

# Logs em tempo real
docker compose logs -f

# Últimas 100 linhas
docker compose logs --tail=100

# Parar
docker compose down

# Reiniciar
docker compose restart

# Rebuild após alterações de código
docker compose up -d --build

# Sync manual
docker compose exec prometheus-zabbix-sync python sync_prometheus.py --all
docker compose exec prometheus-zabbix-sync python sync_prometheus.py --push

# Debug dentro do container
docker compose exec prometheus-zabbix-sync sh
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
docker compose exec prometheus-zabbix-sync python sync_prometheus.py --all
```

**Valores não chegam ao Zabbix**
```bash
docker compose exec prometheus-zabbix-sync python sync_prometheus.py --push
# Verificar linha "Trapper resposta: processed: X"
```

**Prometheus não acessível**
```bash
# Testar a partir de um container temporário
docker run --rm python:3.11-slim python -c "
import urllib.request
urllib.request.urlopen('https://prometheus-url/-/healthy', timeout=5)
print('OK')
"
```
