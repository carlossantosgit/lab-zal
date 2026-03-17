# 🔄 Lab ZAL - Prometheus + Alert Manager + Zabbix

Integração completa com **Auto-Create de Hosts** - quando alerta chega, host é criado automaticamente em Zabbix! ✨

## ✨ Feature Principal: Auto-Create de Hosts

**Webhook detecta hosts desconhecidos e cria automaticamente:**

```
Prometheus Alert (novo host)
         ↓
Webhook verifica
         ↓
Host não existe?
         ↓
CRIA automaticamente:
  ✅ Host com interface Zabbix Agent
  ✅ 3 items padrão (CPU, Memory, Watchdog)
  ✅ Pronto para receber dados!
```

**Benefícios:**
- ✅ Zero manual - sem criar hosts em Zabbix manualmente
- ✅ Escalável - adicione quantos hosts quiser em Prometheus
- ✅ Automático - tudo acontece quando alerta chega
- ✅ Robusto - API Zabbix valida tudo

## 🏗️ Arquitetura

```
┌─────────────┐      ┌──────────────┐      ┌──────────┐      ┌────────────┐
│ Prometheus  │ ───→ │ Alert Manager│ ───→ │ Webhook  │ ───→ │   Zabbix   │
│  (Coleta)   │      │ (Roteamento) │      │(Auto-Cria)      │  (Storage) │
└─────────────┘      └──────────────┘      └──────────┘      └────────────┘
     9090                  9093              ✨ AUTO-CREATE    10051/8080
```

**8 Containers Docker:**
- Prometheus (coleta métricas)
- Alert Manager (roteia alertas)
- Zabbix Server (armazena dados)
- Zabbix Web UI (interface)
- PostgreSQL (banco de dados)
- Node Exporter (exporta métricas)
- Webhook (auto-create, Python Flask)
- ZAL (Zabbix Alert Manager)

## 📊 Fluxo de Dados

```
1. Prometheus escruta exportadores
   └─ Cada scrape job tem label: zabbix_host=nome-do-host

2. Se métrica ultrapassa threshold, alerta dispara
   └─ CPU > 50%, RAM < 20%, etc

3. Alert Manager recebe e envia webhook POST /alerts
   └─ Preserva label zabbix_host

4. Webhook processa AUTOMATICAMENTE ✨
   ├─ Verifica se host existe em Zabbix via API
   ├─ Se não existe:
   │  ├─ Cria host com interface configurada
   │  ├─ Cria 3 items padrão
   │  └─ Loga: "✅ Created host in Zabbix: node-01"
   └─ Envia métrica via zabbix_sender

5. Zabbix Server processa dados
   └─ Host: node-01 → Item: prometheus.highcpu → Value: 1

6. Zabbix UI exibe dados em Monitoring → Latest Data
   └─ Host já criado com items configurados!
```

## 🚀 Quick Start (5 Minutos)

### 1️⃣ Iniciar

```bash
docker-compose up -d
```

### 2️⃣ Verificar Status

```bash
docker-compose ps
# Deve mostrar 8/8 containers UP
```

### 3️⃣ Popular Dados de Demo (OPCIONAL - para apresentação)

```bash
python3 scripts/populate_demo_data.py
```

Isso cria 4 hosts de exemplo com dados realistas:
- prod-db-01 (Production Database)
- api-server-01 (API Server)
- cache-redis-01 (Redis Cache)
- app-web-01 (Web Application)

Cada host com:
- ✅ 6 items (CPU, Memory, Requests, Latency, Error Rate, Watchdog)
- ✅ 3 triggers (High CPU, Low Memory, High Error Rate)
- ✅ Dados de teste realistas

### 4️⃣ Acessar Zabbix

```
http://localhost:8080
User: Admin
Password: zabbix
```

Navegar: **Monitoring → Latest Data** para ver hosts com dados!

## 📋 URLs de Acesso

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| **Zabbix Web** | http://localhost:8080 | Admin / zabbix |
| **Prometheus** | http://localhost:9090 | - |
| **Alert Manager** | http://localhost:9093 | - |
| **Webhook Health** | http://localhost:5001/health | - |

## 🧪 Testar Auto-Create

### Teste 1: Enviar Alerta Manual (Criar Host Novo)

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "alerts": [
      {
        "status": "firing",
        "labels": {
          "alertname": "TestAlert",
          "zabbix_host": "novo-servidor",
          "severity": "critical"
        }
      }
    ]
  }' \
  http://localhost:5001/alerts
```

**Resultado:** Host `novo-servidor` será criado automaticamente em Zabbix com 3 items! ✨

### Teste 2: Ver nos Logs

```bash
docker-compose logs webhook -f

# Verá mensagens tipo:
# INFO:root:📬 Received 1 alerts
# INFO:root:🆕 Host 'novo-servidor' not found - creating...
# INFO:root:✅ Created host in Zabbix: novo-servidor (ID: 10441)
# INFO:root:✅ Created item: prometheus.deadmansswitch
# INFO:root:✅ Created item: prometheus.highcpu
# INFO:root:✅ Created item: prometheus.lowmemory
```

### Teste 3: Verificar em Zabbix

```bash
# Abrir Zabbix Web UI
http://localhost:8080

# Monitoring → Latest Data
# Filtrar por: novo-servidor
# ✅ Host aparecerá com 3 items já configurados!
```

## 📁 Estrutura do Projeto

```
lab-zal/
├── docker-compose.yml          ← Orquestração (CRÍTICO)
├── README.md                   ← Este ficheiro
├── QUICKSTART.md               ← Guia rápido
├── APRESENTACAO.md             ← Guia para apresentação
│
├── prometheus/                 ← Coleta de métricas
│   ├── prometheus.yml          ← Scrape jobs com labels zabbix_host
│   └── rules/
│       └── alerts.yml          ← Regras com label zabbix_host
│
├── alertmanager/               ← Roteamento de alertas
│   └── alertmanager.yml        ← Route: webhook endpoint
│
├── webhook/                    ← ✨ Auto-create de hosts
│   ├── receiver.py             ← Flask app com auto-create
│   └── Dockerfile
│
├── zal/                        ← Zabbix Alert Manager
│   ├── hosts.yml
│   ├── zal-config.yaml
│   └── Dockerfile
│
└── scripts/                    ← Ferramentas
    ├── populate_demo_data.py   ← ✨ Popula dados para demo
    ├── setup_hosts.py          ← Criar hosts manualmente (opcional)
    ├── fix_all_items.py        ← Corrigir interfaces (opcional)
    └── README.md               ← Guia de scripts
```

## 🔧 Manutenção

### Adicionar Novo Host (Automático!)

1. **Editar `prometheus/prometheus.yml`:**

```yaml
- job_name: 'novo-servico'
  static_configs:
    - targets: ['novo-servico.example.com:9100']
      labels:
        zabbix_host: novo-servico
```

2. **Recarregar Prometheus:**

```bash
docker-compose restart prometheus
```

3. **Pronto!** Quando Prometheus scraper e enviar alerta, webhook cria host em Zabbix automaticamente ✨

### Verificar Logs do Webhook

```bash
docker-compose logs webhook -f

# Procure por:
# "✅ Created host" = sucesso
# "❌ Failed to create" = erro
# "🆕 Host ... not found - creating" = detectou host novo
```

### Corrigir Interfaces (Se Necessário)

Se items tiverem erro de interface:

```bash
cd scripts
python3 fix_all_items.py
```

### Setup Manual (Se Quiser)

Criar hosts pré-existentes manualmente:

```bash
cd scripts
python3 setup_hosts.py
```

**Nota:** Agora é OPCIONAL! Webhook cria automaticamente quando alerta chega.

## 📊 Troubleshooting

### Host não aparece em Zabbix depois do alerta

```bash
# 1. Ver logs do webhook
docker-compose logs webhook

# 2. Procurar por erro (❌ Failed to create host)

# 3. Testar conexão Zabbix API
curl http://localhost:8080/api_jsonrpc.php \
  -d '{"jsonrpc":"2.0","method":"user.login","params":{"user":"Admin","password":"zabbix"},"id":1}' \
  -H "Content-Type: application/json"
```

### Webhook não envia para Zabbix

```bash
# Verificar conexão
docker-compose exec webhook zabbix_sender \
  -z zabbix-server \
  -s "node-01" \
  -k "prometheus.test" \
  -o "1"

# Esperado: processed: 1; failed: 0
```

### Alertas não disparam em Prometheus

```bash
# Ver regras
curl http://localhost:9090/api/v1/rules | jq '.data.groups'

# Ver alertas
curl http://localhost:9090/api/v1/alerts | jq '.data[] | {alertname, state}'
```

### Alert Manager não encaminha

```bash
# Verificar config
curl http://localhost:9093/api/v2/status | jq '.config'

# Deve conter: route → receiver: webhook
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

## 🎓 Para Apresentação

Ver: **[APRESENTACAO.md](./APRESENTACAO.md)** para guia completo de apresentação!

**Quick Demo (5 min):**
```bash
docker-compose up -d
python3 scripts/populate_demo_data.py
open http://localhost:8080
# Login: Admin / zabbix
# Navegar: Monitoring → Latest Data
# Ver 4 hosts com dados realistas!
```

## 🎯 Próximas Melhorias

- [ ] Customizar items criados automaticamente
- [ ] Criar Triggers mais inteligentes
- [ ] Integrar com Slack/Email
- [ ] Dashboard interativo no Zabbix
- [ ] Backup automático
- [ ] Template automático para novo hosts

## 📞 Suporte

Ver logs em tempo real:

```bash
docker-compose logs -f

# Serviços individuais:
docker-compose logs prometheus
docker-compose logs alertmanager
docker-compose logs webhook        # Ver auto-create aqui!
docker-compose logs zabbix-server
```

## ✅ Status

- ✅ Prometheus coleta métricas
- ✅ Alert Manager roteia alertas
- ✅ Webhook mapeia hosts e cria automaticamente ✨
- ✅ Zabbix recebe dados em hosts corretos
- ✅ Mapeamento de labels automático
- ✅ Items criados automaticamente
- ✅ Interface configurada automaticamente
- ✅ Triggers criadas automaticamente
- ✅ Documentação completa
- ✅ Pronto para produção

---

**Desenvolvido com ❤️ para Prometheus + Zabbix**

Para apresentação: veja [APRESENTACAO.md](./APRESENTACAO.md)
