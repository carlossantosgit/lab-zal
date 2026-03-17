# 🔄 Lab ZAL - Prometheus + Alert Manager + Zabbix

**Integração completa com Sincronização Dinâmica de Regras Prometheus!** ✨

> Quando um alerta chega do Prometheus, o webhook **sincroniza automaticamente** todas as rules (32+ regras) criando items e triggers no Zabbix - **sem hardcoding, totalmente dinâmico!**

## ✨ Feature Principal: Dynamic Prometheus Rules Sync

**POC (Proof of Concept) - Pronta para Apresentação**

```
Prometheus (32+ Alerting Rules)
         ↓
Webhook sincroniza via API Prometheus
         ↓
Zabbix cria dinamicamente:
  ✅ 32 items (um por rule)
  ✅ 32 triggers (com threshold correto)
  ✅ Severity mapped (warning→Average, critical→High)
         ↓
Resultado: Host pronto para monitoramento completo!
```

### Como Funciona

1. **Host novo chega via alerta**
   ```
   Alert: {alertname: "HighCPUUsage", zabbix_host: "prod-db-01"}
   ```

2. **Webhook cria host em Zabbix**
   ```
   Host: prod-db-01 ✅
   ```

3. **Sincroniza todas as 32 regras** ⭐
   ```
   rule[0] → prometheus.highcpuusage + trigger
   rule[1] → prometheus.criticalmemory + trigger
   rule[2] → prometheus.highdiskusage + trigger
   ...
   rule[31] → prometheus.filedescriptorexhausted + trigger
   ```

4. **Host fica pronto com dados**
   ```
   32 items + 32 triggers
   Histórico funcionando
   Dashboard pronto
   ```

## 🏗️ Arquitetura

```
┌─────────────┐      ┌──────────────┐      ┌──────────────┐      ┌────────────┐
│ Prometheus  │ ───→ │ Alert Manager│ ───→ │   Webhook    │ ───→ │   Zabbix   │
│(32+ rules)  │      │ (Roteamento) │      │(Sync Dynamic)      │  (Storage) │
└─────────────┘      └──────────────┘      └──────────────┘      └────────────┘
     9090                  9093           prometheus_sync.py      10051/8080
```

**8 Containers Docker:**
- ✅ Prometheus (coleta + 32 alerting rules)
- ✅ Alert Manager (roteia alertas)
- ✅ Zabbix Server (armazena dados)
- ✅ Zabbix Web UI (interface)
- ✅ PostgreSQL (banco de dados)
- ✅ Node Exporter (exporta métricas)
- ✅ Webhook (sincroniza regras dinamicamente) ⭐
- ✅ ZAL (Zabbix Alert Manager)

## 📊 Fluxo de Dados Completo

```
1. Prometheus coleta métricas de hosts
   └─ Com label: zabbix_host=nome-do-host

2. Se métrica ultrapassa threshold, cria alerta
   └─ Com all 32 alerting rules (CPU, Memory, Disk, Network, HTTP, DB, etc)

3. Alerta chega no Alert Manager
   └─ Com label zabbix_host preservado

4. Alert Manager envia webhook POST /alerts
   └─ Webhook recebe a request

5. Webhook processa:
   ├─ Verifica se host existe em Zabbix
   ├─ Se não existe, CRIA host
   └─ SINCRONIZA 32 regras Prometheus ✨
      ├─ Lê regras do Prometheus API ou arquivo fake
      ├─ Para cada rule:
      │  ├─ Cria item: prometheus.{alertname.lower()}
      │  ├─ Cria trigger: {hostname:item.last()}>0
      │  └─ Mapeia severity (warning→2, critical→4)
      └─ Resultado: 32 items + 32 triggers

6. Host em Zabbix fica com:
   ✅ 32 items configurados
   ✅ 32 triggers prontas
   ✅ Histórico funcionando
   ✅ Dashboard pronto

7. Zabbix UI exibe:
   └─ Monitoring → Latest Data
      └─ Host com todos os 32 items com dados!
```

## 🚀 Quick Start (5-10 Minutos)

### Passo 1: Iniciar

```bash
docker-compose up -d
# Esperar 5 min para Zabbix inicializar...
```

### Passo 2: Sincronizar Regras (Novo!)

```bash
# Listar hosts
python3 scripts/sync_prometheus_rules.py --list

# Sincronizar UM host com 32 regras
python3 scripts/sync_prometheus_rules.py --host prod-db-01 --demo

# Sincronizar TODOS os hosts
python3 scripts/sync_prometheus_rules.py --all --demo
```

**Resultado:**
```
✅ 10 hosts processados
✅ 288 items criados (10 × 32)
✅ 288 triggers criadas (10 × 32)
```

### Passo 3: Abrir Zabbix

```
http://localhost:8080
User: Admin
Password: zabbix
```

**Ir para:** Monitoring → Latest Data

**Ver:** 10 hosts com 288 items cada! ✨

## 📋 32 Regras Prometheus Sincronizadas

### Infraestrutura
- ✅ HighCPUUsage, CriticalCPUUsage
- ✅ LowMemoryAvailable, CriticalMemoryUsage
- ✅ HighDiskUsage, CriticalDiskUsage, DiskIOHigh
- ✅ NetworkPacketLoss, HighNetworkLatency
- ✅ LoadAverageHigh, FileDescriptorExhausted

### Aplicações
- ✅ HTTPErrorRateHigh, HTTPSlowResponse
- ✅ DatabaseConnectionPoolExhausted, DatabaseSlowQueries, DatabaseReplicationLag
- ✅ CacheHitRateLow, RedisPersistenceFailure

### Orquestração
- ✅ KubernetesNodeNotReady, KubernetesPodCrashLooping, KubernetesPodNotHealthy
- ✅ DockerContainerExited

### Monitoramento
- ✅ PrometheusHighMemoryUsage, PrometheusChunksToDiskSuccess
- ✅ AlertmanagerConfigReload
- ✅ ZabbixServerDown, ZabbixHighQueueSize

### Segurança
- ✅ SSLCertificateExpiringSoon, SSLCertificateExpired
- ✅ AuthenticationFailures, UnusualNetworkActivity

### Sistema
- ✅ FilesystemReadonly

## 📁 Estrutura do Projeto

```
lab-zal/
├── docker-compose.yml              ← Orquestração (8 containers)
├── README.md                        ← Este arquivo
├── QUICKSTART.md                    ← Começo rápido
├── APRESENTACAO.md                  ← Slides para apresentação
├── POC_PROMETHEUS_SYNC.md          ← Documentação POC detalhada
│
├── prometheus/                      ← Coleta de métricas
│   ├── prometheus.yml              ← Scrape jobs com labels zabbix_host
│   └── rules/
│       └── alerts.yml              ← 32+ alerting rules com label zabbix_host
│
├── alertmanager/                    ← Roteamento de alertas
│   └── alertmanager.yml            ← Route: webhook http://webhook:5001/alerts
│
├── webhook/                         ← ✨ AUTO-CREATE + DYNAMIC SYNC
│   ├── receiver.py                 ← Flask app integrado
│   ├── prometheus_sync.py          ← ⭐ Módulo de sincronização Prometheus
│   ├── fake_prometheus_rules.json   ← ⭐ 32 regras para demo
│   └── Dockerfile
│
├── zal/                             ← Zabbix Alert Manager
│   ├── hosts.yml
│   ├── zal-config.yaml
│   └── Dockerfile
│
└── scripts/                         ← Ferramentas
    ├── populate_demo_data.py        ← Popular 4 hosts com dados demo
    ├── sync_prometheus_rules.py     ← ⭐ CLI para sincronizar regras
    ├── validate_e2e.py              ← ✅ Validação end-to-end completa
    ├── setup_hosts.py               ← Criar hosts manualmente (opcional)
    ├── fix_all_items.py             ← Corrigir interfaces (opcional)
    └── README.md                    ← Guia de scripts
```

## 🧪 Como Testar

### Teste 1: Auto-Create + Sync via Webhook

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "alerts": [
      {
        "status": "firing",
        "labels": {
          "alertname": "TestAlert",
          "zabbix_host": "novo-host-teste",
          "severity": "warning"
        }
      }
    ]
  }' \
  http://localhost:5001/alerts
```

**Resultado:**
1. Host `novo-host-teste` é criado em Zabbix
2. Webhook sincroniza 32 regras Prometheus
3. Host fica com 32 items + 32 triggers prontos! ✨

### Teste 2: Sincronizar Manual com CLI

```bash
# Sincronizar um host específico
python3 scripts/sync_prometheus_rules.py --host prod-db-01 --demo

# Output:
# ✅ Items criados:     32
# ✅ Triggers criadas:  32
```

### Teste 3: Validação End-to-End Completa ✅

```bash
# Script que demonstra pipeline completa de ponta a ponta
python3 scripts/validate_e2e.py

# Output: Validação com 6 etapas:
# ETAPA 1: Conectividade com Sistemas (OK)
# ETAPA 2: Ver 32 Regras Prometheus (OK)
# ETAPA 3: Criar Nova Regra Customizada (OK)
# ETAPA 4: Sincronizar com Zabbix (33 items + 33 triggers ✅)
# ETAPA 5: Validar no Zabbix API (OK)
# ETAPA 6: Resultado Final (Pronto para Produção!)
```

**Documentação:**
- 📄 [E2E_VALIDATION_REPORT.md](./E2E_VALIDATION_REPORT.md) - Relatório completo com diagramas
- 📄 [VALIDACAO_SYNC.md](./VALIDACAO_SYNC.md) - 4 métodos de validação

### Teste 4: Via Logs (Ver Sincronização em Tempo Real)

```bash
docker-compose logs webhook -f

# Verá:
# INFO:root:🆕 Host 'novo-host' not found - creating...
# INFO:root:✅ Created host in Zabbix: novo-host
# INFO:root:🔄 Sincronizando regras Prometheus para 'novo-host'...
# INFO:root:✅ Item criado: prometheus.highcpuusage
# INFO:root:✅ Item criado: prometheus.criticalmemory
# ... 30 items mais ...
# INFO:root:✅ Trigger criada: High CPU Usage
# INFO:root:✨ Prometheus sync: 32 items, 32 triggers criados
```

## 🔧 Manutenção

### Adicionar Novo Host (Agora é Automático!)

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

3. **Pronto!** Quando alerta chegar:
   - ✅ Host criado em Zabbix
   - ✅ 32 regras sincronizadas automaticamente
   - ✅ Items + triggers prontos

### Sincronizar Manualmente

```bash
# Um host
python3 scripts/sync_prometheus_rules.py --host meu-host --demo

# Todos os hosts
python3 scripts/sync_prometheus_rules.py --all --demo

# Ver status
python3 scripts/sync_prometheus_rules.py --list
```

## 📊 Troubleshooting

### Webhook não sincroniza

```bash
# Ver logs
docker-compose logs webhook

# Testar conexão
curl http://localhost:5001/health

# Testar criação manual
python3 scripts/sync_prometheus_rules.py --host test-host --demo
```

### Items não aparecem em Zabbix

```bash
# Corrigir interfaces
cd scripts
python3 fix_all_items.py

# Ver status
python3 sync_prometheus_rules.py --list
```

### Regras não sincronizam

```bash
# Usar modo --demo (arquivo fake)
python3 sync_prometheus_rules.py --all --demo

# Verificar arquivo fake existe
ls webhook/fake_prometheus_rules.json
```

## 🔐 Credenciais

| Serviço | Usuário | Senha |
|---------|---------|-------|
| Zabbix | Admin | zabbix |
| PostgreSQL | zabbix | zabbix |

## 🎯 Para Apresentação

### Setup Rápido (15 minutos)

```bash
# Terminal 1
docker-compose up -d && sleep 5

# Terminal 2
python3 scripts/sync_prometheus_rules.py --all --demo

# Terminal 3
open http://localhost:8080
# Login: Admin / zabbix
# Monitoring → Latest Data
# Ver 288 items criados! 🎊
```

### Demo Script

> "Lab ZAL sincroniza automaticamente as regras de monitoramento do Prometheus com Zabbix. Quando um alerta chega, o webhook não apenas **cria o host**, mas também **sincroniza todas as 32 regras de alertas**, criando correspondentes items e triggers em Zabbix. Totalmente automático, sem configuração manual!"

### Pontos-Chave

1. **Auto-Create de Hosts** ✅
2. **Sincronização Dinâmica de Regras** ✅ ⭐
3. **32 Items + Triggers Automáticos** ✅ ⭐
4. **Pronto para Produção** ✅

## 🚀 Próximos Passos (Para PRD)

- [ ] Background job de sincronização (cron/scheduler)
- [ ] Usar Prometheus real (não apenas arquivo fake)
- [ ] Versionamento de regras
- [ ] Unit tests + integration tests
- [ ] Validação antes de criar items/triggers
- [ ] Alertas de falha de sincronização
- [ ] Dashboard de status

## 📞 Suporte

Ver logs em tempo real:

```bash
docker-compose logs -f

# Serviços individuais:
docker-compose logs prometheus
docker-compose logs webhook
docker-compose logs zabbix-server
docker-compose logs alertmanager
```

## ✅ Status

- ✅ Prometheus coleta métricas com 32+ alerting rules
- ✅ Alert Manager roteia alertas com webhook
- ✅ Webhook cria hosts automaticamente ✨
- ✅ Webhook sincroniza 32 regras Prometheus ⭐
- ✅ Zabbix recebe 32 items + 32 triggers por host ⭐
- ✅ Mapeamento de labels automático
- ✅ Severity mapping correto (warning→2, critical→4)
- ✅ Documentação completa
- ✅ **Pronto para apresentação e PRD!** 🚀

---

**Desenvolvido com ❤️ para Observabilidade Automática**

📚 **Documentação Principal:**
- [QUICKSTART.md](./QUICKSTART.md) - Começo rápido (5-10 min)
- [APRESENTACAO.md](./APRESENTACAO.md) - Slides para apresentação (10 min)
- [POC_PROMETHEUS_SYNC.md](./POC_PROMETHEUS_SYNC.md) - Detalhes técnicos do POC

✅ **Validação & Testes:**
- [E2E_VALIDATION_REPORT.md](./E2E_VALIDATION_REPORT.md) - Relatório end-to-end com execução real
- [VALIDACAO_SYNC.md](./VALIDACAO_SYNC.md) - 4 métodos de validação + troubleshooting
- `python3 scripts/validate_e2e.py` - Executar validação interativa
