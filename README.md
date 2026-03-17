# 🔄 Lab ZAL - Prometheus + Alert Manager + Zabbix

Integração completa de Prometheus com Zabbix usando Alert Manager como intermediário, com **criação automática de hosts**.

## ✨ Destaque Principal

**O webhook agora cria hosts automaticamente!** Quando um alerta chega do Prometheus, o webhook:
- ✅ Verifica se o host existe no Zabbix
- ✅ Se NÃO existe, cria automaticamente com interface configurada
- ✅ Adiciona 3 items padrão para coletar métricas
- ✅ Sem necessidade de scripts manuais ou intervenção!

## 🏗️ Arquitetura

```
┌─────────────┐      ┌──────────────┐      ┌──────────┐      ┌────────────┐
│ Prometheus  │ ───→ │ Alert Manager│ ───→ │ Webhook  │ ───→ │   Zabbix   │
│  (Coleta)   │      │ (Roteamento) │      │(Auto-Cria)      │  (Storage) │
└─────────────┘      └──────────────┘      └──────────┘      └────────────┘
     9090                  9093                 5001              10051/8080
```

## 📊 Fluxo de Dados Completo

```
1. Prometheus escruta exportadores (label: zabbix_host=node-01)
   └─ node-exporter, prometheus self-metrics, etc

2. Alerta dispara se métrica ultrapassa threshold
   └─ Ex: CPU > 50%, RAM < 20%
   └─ Alerta inclui: {alertname: HighCPU, zabbix_host: node-01}

3. Alert Manager recebe e envia webhook POST /alerts
   └─ Preserva label zabbix_host

4. Webhook processa AUTOMATICAMENTE:
   ✅ Verifica se host "node-01" existe em Zabbix
   ✅ Se NÃO existe:
      → Cria host com interface Zabbix Agent
      → Cria 3 items: deadmansswitch, highcpu, lowmemory
      → Loga: "✅ Created host in Zabbix: node-01"
   ✅ Envia métrica: zabbix_sender -s "node-01" -k "prometheus.highcpu" -o "1"

5. Zabbix Server recebe dados
   └─ Host: node-01 → Item: prometheus.highcpu → Value: 1

6. Zabbix UI exibe em Monitoring → Latest Data
   └─ Host criado AUTOMATICAMENTE com items já configurados!
```

## 🚀 Quick Start

### Iniciar

```bash
docker-compose up -d
```

### Verificar Status

```bash
docker-compose ps
# Deve mostrar 8/8 containers UP
```

### URLs de Acesso

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| Prometheus | http://localhost:9090 | - |
| Alert Manager | http://localhost:9093 | - |
| Zabbix Web | http://localhost:8080 | Admin / zabbix |
| Webhook Health | http://localhost:5001/health | - |

## 📋 Hosts Configurados

### Pré-existentes (já com items)

• **node-01** - Node Exporter (CPU, RAM, Disco)
• **prometheus-server** - Prometheus self-metrics

### Novos Hosts

Qualquer host que receber alerta será **auto-criado** com 3 items:
- `prometheus.deadmansswitch` - Watchdog (sempre 1)
- `prometheus.highcpu` - CPU > 50% por 1 min
- `prometheus.lowmemory` - RAM disponível < 20%

## 🧪 Testes

### Teste 1: Auto-Criar Host Novo

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "alerts": [
      {
        "status": "firing",
        "labels": {
          "alertname": "HighCPU",
          "zabbix_host": "servidor-novo",
          "severity": "warning"
        }
      }
    ]
  }' \
  http://localhost:5001/alerts
```

**Resultado:**
- Host `servidor-novo` será **criado automaticamente** em Zabbix
- Item `prometheus.highcpu` será povado com valor 1
- Ver em: Zabbix WebUI → Monitoring → Latest Data

### Teste 2: Testar com zabbix_sender

```bash
docker-compose exec webhook zabbix_sender \
  -z zabbix-server \
  -s "node-01" \
  -k "prometheus.highcpu" \
  -o "1"

# Esperado: Response: "processed: 1; failed: 0"
```

### Teste 3: Gerar Carga Real e Ver Alerta

```bash
# Terminal 1: Aumentar CPU
docker-compose exec node-exporter sh -c 'yes > /dev/null &'

# Terminal 2: Ver em Prometheus (http://localhost:9090)
# Query: rate(node_cpu_seconds_total{mode="idle"}[2m])

# Terminal 3: Ver em Zabbix (http://localhost:8080)
# Monitoring → Latest Data → Filter: node-01
# Item "prometheus.highcpu" deve mostrar valor 1
```

## 📁 Estrutura de Ficheiros

```
lab-zal/
├── docker-compose.yml          ← Orquestração (CRÍTICO)
├── README.md                   ← Este ficheiro
│
├── prometheus/
│   ├── prometheus.yml          ← Config: scrape jobs com labels zabbix_host
│   └── rules/
│       └── alerts.yml          ← Regras com label zabbix_host
│
├── alertmanager/
│   └── alertmanager.yml        ← Route: webhook endpoint
│
├── webhook/
│   ├── receiver.py             ← ✨ Flask app com auto-create
│   └── Dockerfile
│
├── zal/
│   ├── hosts.yml               ← Mapeamento ZAL (pode estar vazio)
│   ├── zal-config.yaml         ← Config ZAL
│   ├── Dockerfile
│   └── zal                      ← Binary ZAL (builder)
│
└── scripts/                    ← Ferramentas avançadas
    ├── setup_hosts.py          ← Criar hosts manualmente (opcional)
    ├── fix_all_items.py        ← Corrigir interfaces se necessário
    └── ...
```

## 🔧 Manutenção

### Adicionar Novo Host (AUTOMÁTICO!)

Agora é muito simples! O host é criado **automaticamente** quando receber primeiro alerta:

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
docker-compose restart prometheus
```

3. **Pronto!** Quando o alerta chegar, host será criado em Zabbix automaticamente ✨

> **Antes:** Precisava rodar `python3 setup_hosts.py`
> **Agora:** Webhook cria tudo sozinho quando alerta chega!

### Verificar Logs do Webhook

```bash
docker-compose logs webhook -f

# Procurar por estas mensagens de sucesso:
# "🆕 Host 'novo-host' not found - creating..."
# "✅ Created host in Zabbix: novo-host (ID: 10441)"
# "✅ Created item: prometheus.highcpu"
```

### Corrigir Interfaces (Se Necessário)

Se por algum motivo items tiverem interface inválida:

```bash
cd scripts
python3 fix_all_items.py
```

## 📊 Troubleshooting

### Host não aparece em Zabbix depois do alerta

```bash
# 1. Verificar logs do webhook
docker-compose logs webhook

# 2. Procurar por erro de criação (❌ Failed to create host)
# 3. Testar conexão Zabbix API
curl http://localhost:8080/api_jsonrpc.php -d '{"jsonrpc":"2.0","method":"user.login","params":{"user":"Admin","password":"zabbix"},"id":1}' | jq
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
  -o "1"
```

### Alertas não disparam no Prometheus

```bash
# Verificar regras
curl http://localhost:9090/api/v1/rules | jq '.data.groups'

# Ver alertas em "pending"
curl http://localhost:9090/api/v1/alerts | jq '.data[] | {alertname, state}'
```

### Alert Manager não encaminha para webhook

```bash
# Verificar config
curl http://localhost:9093/api/v2/status | jq '.config'

# Deve conter: "receivers": [...], "route": {"receiver": "webhook", ...}
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
- [ ] Customizar items criados automaticamente

## 📞 Suporte

Ver logs de qualquer serviço:

```bash
docker-compose logs <service> -f
```

Serviços:
```bash
docker-compose logs prometheus
docker-compose logs alertmanager
docker-compose logs webhook        # Ver auto-create aqui!
docker-compose logs zabbix-server
```

## ✅ Status

- ✅ Prometheus coleta métricas
- ✅ Alert Manager roteia alertas
- ✅ Webhook mapeia hosts e **cria automaticamente**
- ✅ Zabbix recebe dados em hosts corretos
- ✅ Mapeamento de labels automático
- ✅ Items criados automaticamente
- ✅ Interface configurada automaticamente
