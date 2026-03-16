# 🔄 Lab ZAL - Prometheus + Alert Manager + Zabbix

Integração completa de Prometheus com Zabbix usando Alert Manager como intermediário, com **mapeamento dinâmico de hosts**.

## 🏗️ Arquitetura

```
┌─────────────┐      ┌──────────────┐      ┌──────────┐      ┌────────────┐
│ Prometheus  │ ───→ │ Alert Manager│ ───→ │ Webhook  │ ───→ │   Zabbix   │
│  (Coleta)   │      │ (Roteamento) │      │(Mapeamento)     │  (Storage) │
└─────────────┘      └──────────────┘      └──────────┘      └────────────┘
     9090                  9093                 5001              10051/8080
```

## 📊 Fluxo de Dados

```
1. Prometheus escruta node-exporter (label: zabbix_host=node-01)
2. Se CPU > 50%, dispara: {alertname: HighCPU, zabbix_host: node-01}
3. Alert Manager recebe e envia webhook POST /alerts
4. Webhook lê label zabbix_host e executa:
   zabbix_sender -s "node-01" -k "prometheus.highcpu" -o "1"
5. Zabbix Server recebe em: Host "node-01" → Item "prometheus.highcpu"
6. Zabbix UI mostra: Monitoring → Latest Data → node-01
```

## 🚀 Quick Start

### Iniciar

```bash
docker-compose up -d
```

### Verificar Status

```bash
docker-compose ps
```

### URLs de Acesso

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| Prometheus | http://localhost:9090 | - |
| Alert Manager | http://localhost:9093 | - |
| Zabbix Web | http://localhost:8080 | Admin / zabbix |
| Webhook Health | http://localhost:5001/health | - |

## 📋 Hosts Configurados

Cada host em Prometheus tem 3 items no Zabbix:

### 🖥️ node-01 (Node Exporter)
- `prometheus.deadmansswitch` - Watchdog (sempre 1)
- `prometheus.highcpu` - CPU > 50% por 1 min
- `prometheus.lowmemory` - RAM disponível < 20%

### 🖥️ prometheus-server (Prometheus)
- `prometheus.deadmansswitch` - Watchdog
- `prometheus.highcpu` - CPU stress
- `prometheus.lowmemory` - Memory pressure

## 🧪 Testes

### Teste Manual - Enviar alerta para node-01

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "alerts": [
      {
        "status": "firing",
        "labels": {
          "alertname": "HighCPU",
          "zabbix_host": "node-01",
          "severity": "warning"
        }
      }
    ]
  }' \
  http://localhost:5001/alerts
```

**Resultado no Zabbix:**
- Host: `node-01`
- Item: `prometheus.highcpu`
- Value: `1`

### Teste com zabbix_sender

```bash
docker-compose exec webhook zabbix_sender \
  -z zabbix-server \
  -s "node-01" \
  -k "prometheus.highcpu" \
  -o "1"

# Esperado: Response: "processed: 1; failed: 0"
```

### Teste Real - Gerar Carga CPU

```bash
# Terminal 1: Aumentar CPU
docker-compose exec node-exporter sh -c 'yes > /dev/null &'

# Terminal 2: Monitorar
open http://localhost:9090
# Query: rate(node_cpu_seconds_total{mode="idle"}[2m])

# Terminal 3: Ver em Zabbix
open http://localhost:8080
# Monitoring → Latest Data → Filter: node-01
```

## 📁 Estrutura de Ficheiros

```
lab-zal/
├── docker-compose.yml          ← Orquestração (CRÍTICO)
├── README.md                   ← Este ficheiro
│
├── prometheus/
│   ├── prometheus.yml          ← Config: scrape jobs com labels
│   └── rules/
│       └── alerts.yml          ← Regras com zabbix_host
│
├── alertmanager/
│   └── alertmanager.yml        ← Route: webhook endpoint
│
├── webhook/
│   ├── receiver.py             ← Flask app que mapeia alerts
│   └── Dockerfile
│
├── zal/
│   ├── hosts.yml               ← Mapeamento ZAL (pode estar vazio)
│   ├── zal-config.yaml         ← Config ZAL
│   ├── Dockerfile
│   └── zal                      ← Binary ZAL (builder)
│
└── scripts/                    ← Setup e maintenance
    ├── setup_hosts.py          ← Criar hosts no Zabbix
    ├── setup_zabbix.py         ← Setup inicial (deprecated)
    ├── fix_all_items.py        ← Corrigir interfaces
    └── fix_items.py            ← Versão antiga (manter backup)
```

## 🔧 Manutenção

### Adicionar Novo Host

1. **Adicionar ao Prometheus** (`prometheus/prometheus.yml`):

```yaml
- job_name: 'node-exporter-db'
  static_configs:
    - targets: ['srv-db.example.com:9100']
      labels:
        zabbix_host: srv-db
```

2. **Recarregar Prometheus**:

```bash
docker-compose exec prometheus kill -HUP 1
# ou
docker-compose restart prometheus
```

3. **Criar no Zabbix** (executar script):

```bash
cd scripts
python3 setup_hosts.py
```

### Verificar Conexão Webhook-Zabbix

```bash
# Ver logs do webhook
docker-compose logs webhook -f

# Verificar se webhook recebe (deveria estar em INFO level)
# Procurar por: "📬 Received" ou "📤 Sending to Zabbix"
```

### Corrigir Items com Interface Inválida

```bash
cd scripts
python3 fix_all_items.py
```

## 📊 Troubleshooting

### ZAL mostra "failed to fulfill the requests"

Items precisam de interface válida:
```bash
cd scripts
python3 fix_all_items.py
```

### Webhook não envia para Zabbix

```bash
# Verificar logs
docker-compose logs webhook

# Testar conexão manual
docker-compose exec webhook zabbix_sender \
  -z zabbix-server \
  -s "node-01" \
  -k "prometheus.test" \
  -o "123"
```

### Alertas não disparam no Prometheus

```bash
# Verificar regras
curl http://localhost:9090/api/v1/rules | jq '.data.groups'

# Verificar alertas em estado "pending"
curl http://localhost:9090/api/v1/alerts | jq '.data'
```

### Alert Manager não encaminha

```bash
# Verificar config
curl http://localhost:9093/api/v2/status | jq '.config.original'

# Verificar se webhook está no route
# Deve conter: "url: http://webhook:5001/alerts"
```

## 🔐 Credenciais

| Serviço | Usuário | Senha |
|---------|---------|-------|
| Zabbix | Admin | zabbix |
| PostgreSQL | zabbix | zabbix |

## 📝 Variáveis de Ambiente

Editar em `docker-compose.yml`:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `POSTGRES_DB` | zabbix | Database name |
| `POSTGRES_USER` | zabbix | DB user |
| `POSTGRES_PASSWORD` | zabbix | DB password |

## 🎯 Próximas Melhorias

- [ ] Criar Triggers automáticas para abrir incidentes
- [ ] Configurar notificações (Email, Slack, Teams)
- [ ] Adicionar dashboard customizado no Zabbix
- [ ] Integrar com CI/CD pipelines
- [ ] Backup automático da DB Zabbix
- [ ] Persistência de volumes (MongoDB/Prometheus)

## 📞 Suporte

Para ver logs:
```bash
docker-compose logs <service> -f
```

Services disponíveis:
```bash
docker-compose logs prometheus
docker-compose logs alertmanager
docker-compose logs webhook
docker-compose logs zabbix-server
docker-compose logs zal
```

## ✅ Status

- ✅ Prometheus coleta métricas
- ✅ Alert Manager roteia alertas
- ✅ Webhook mapeia hosts dinamicamente
- ✅ Zabbix recebe dados em hosts corretos
- ✅ Mapeamento de labels automático
