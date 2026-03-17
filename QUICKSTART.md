# 🚀 Quick Start - Lab ZAL (10-15 Minutos)

Sincronização dinâmica de 32 regras Prometheus com Zabbix!

## ⚙️ Pré-requisitos

```bash
# Docker
docker --version
# Docker Compose
docker-compose --version
```

### Instalar Docker

**macOS:**
```bash
brew install docker docker-compose
# ou Docker Desktop: https://www.docker.com/products/docker-desktop
```

**Linux:**
```bash
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker $USER
newgrp docker
```

**Windows:**
- Descarregar Docker Desktop
- Executar no PowerShell/CMD

## 📥 Descarregar o Projeto

```bash
git clone https://github.com/carlossantosgit/lab-zal.git
cd lab-zal
```

## 🚀 Iniciar (3 Passos)

### Passo 1: Iniciar Containers (5 minutos)

```bash
docker-compose up -d
```

Esperar Zabbix inicializar...

### Passo 2: Sincronizar Regras Prometheus ⭐

```bash
# Option A: Sincronizar todos os hosts
python3 scripts/sync_prometheus_rules.py --all --demo

# Option B: Sincronizar um host específico
python3 scripts/sync_prometheus_rules.py --host prod-db-01 --demo

# Option C: Ver lista de hosts
python3 scripts/sync_prometheus_rules.py --list
```

**Resultado esperado:**
```
✅ Items criados:     32 (por host)
✅ Triggers criadas:  32 (por host)
```

### Passo 3: Abrir Zabbix

```
http://localhost:8080
User: Admin
Password: zabbix
```

**Navegar:** Monitoring → Latest Data

**Ver:** Hosts com 32 items cada! ✨

## ✨ O Que é Novo: Dynamic Prometheus Rules Sync

Quando um alerta chega do Prometheus:

```
1. Webhook detecta novo host
2. Cria host em Zabbix
3. ✨ SINCRONIZA 32 REGRAS PROMETHEUS
4. Cria 32 items + 32 triggers automaticamente!
```

**Resultados:**
```
Prometheus: 32 alerting rules
         ↓
Zabbix: 32 items + 32 triggers por host
         ↓
Sem hardcoding - totalmente dinâmico!
```

## 🧪 Testar Auto-Create + Sync

### Teste 1: Via Webhook (Auto-Create + Sync)

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

**Resultado:**
- Host `novo-servidor` criado
- 32 items + 32 triggers sincronizados automaticamente! ✨

**Ver em Zabbix:**
1. Monitoring → Latest Data
2. Filtrar: "novo-servidor"
3. Ver 32 items criados!

### Teste 2: Sincronização Manual

```bash
# Sincronizar UM host com 32 regras
python3 scripts/sync_prometheus_rules.py --host api-server-01 --demo

# Sincronizar TODOS os hosts
python3 scripts/sync_prometheus_rules.py --all --demo
```

### Teste 3: Ver Logs de Sincronização

```bash
docker-compose logs webhook -f

# Verá mensagens como:
# INFO:root:✅ Item criado: prometheus.highcpuusage
# INFO:root:✅ Trigger criada: High CPU Usage
# INFO:root:✨ Prometheus sync: 32 items, 32 triggers criados
```

## 📋 32 Regras Sincronizadas

```
✅ CPU (High, Critical)
✅ Memory (Low, Critical)
✅ Disk (High, Critical, I/O)
✅ Network (Packet Loss, Latency)
✅ HTTP (Errors, Slow Response)
✅ Database (Connections, Slow Queries, Replication)
✅ Cache (Hit Rate, Persistence)
✅ Kubernetes (Node, Pod)
✅ Docker (Container)
✅ Prometheus (Memory, Checkpoints)
✅ Alertmanager (Config)
✅ Zabbix (Down, Queue)
✅ Security (SSL, Auth, Suspicious Activity)
✅ System (Load, File Descriptors)

Total: 32 regras dinâmicas!
```

## 📊 URLs de Acesso

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| **Zabbix Web** | http://localhost:8080 | Admin / zabbix |
| **Prometheus** | http://localhost:9090 | - |
| **Alert Manager** | http://localhost:9093 | - |
| **Webhook** | http://localhost:5001/health | - |

## ✅ Verificações Rápidas

```bash
# Ver status dos containers
docker-compose ps

# Listar hosts em Zabbix
python3 scripts/sync_prometheus_rules.py --list

# Verificar webhook health
curl http://localhost:5001/health

# Ver logs
docker-compose logs webhook -f
```

## 🎯 Para Apresentação

```bash
# Setup completo em 3 comandos:
docker-compose up -d                              # Iniciar
python3 scripts/sync_prometheus_rules.py --all --demo  # Sincronizar
open http://localhost:8080                        # Ver resultado

# Resultado: 288 items + triggers criados! 🎊
```

## ❌ Troubleshooting

### Containers não iniciam

```bash
# Ver status
docker-compose ps

# Ver logs de erro
docker-compose logs

# Recriar containers
docker-compose down -v
docker-compose up -d
```

### Script não sincroniza

```bash
# Testar se Zabbix está respondendo
curl -s http://localhost:8080 | grep -i zabbix

# Verificar arquivo fake existe
ls webhook/fake_prometheus_rules.json

# Testar manualmente
python3 scripts/sync_prometheus_rules.py --list
```

### Items não aparecem em Zabbix

```bash
# Corrigir interfaces
cd scripts && python3 fix_all_items.py

# Sincronizar novamente
python3 sync_prometheus_rules.py --all --demo
```

## 📖 Próximos Passos

1. **Ler documentação completa:**
   ```bash
   cat README.md
   ```

2. **Ler POC detalhada:**
   ```bash
   cat POC_PROMETHEUS_SYNC.md
   ```

3. **Ver guia de apresentação:**
   ```bash
   cat APRESENTACAO.md
   ```

4. **Parar os serviços:**
   ```bash
   docker-compose down
   ```

5. **Remover tudo (dados inclusos):**
   ```bash
   docker-compose down -v
   ```

## 🎓 Conceitos-Chave

**Auto-Create (Fase 1):**
- Webhook detecta host novo via alerta
- Cria host em Zabbix automaticamente
- Configura interface Zabbix Agent

**Dynamic Rules Sync (Fase 2) ⭐:**
- Webhook lê 32+ regras do Prometheus
- Cria item para cada regra
- Cria trigger correspondente
- Mapeia severity (warning→Average, critical→High)
- Host fica pronto com 32 items + triggers

**Result:** Monitoramento completo automático! 🚀

## 🏗️ Arquitetura Simplificada

```
Prometheus
    ↓ (32 alerting rules)
Alert Manager
    ↓ (webhook POST)
Webhook ✨
    ├─ Cria host
    └─ Sincroniza 32 regras
    ↓
Zabbix
    └─ 32 items + 32 triggers prontos!
```

## 💡 Dicas

- **Primeira vez:** Esperar 5-10 min para Zabbix inicializar completamente
- **Demo:** Usar `--demo` para modo arquivo fake (não precisa Prometheus real)
- **Real:** Remover `--demo` para sincronizar com Prometheus real
- **Rápido:** Use `--all` para sincronizar todos os hosts de uma vez
- **Seguro:** Syncronização é idempotente (não duplica regras)

## 📞 Precisa de Ajuda?

Ver logs em tempo real:
```bash
docker-compose logs -f
```

Ver guias completos:
- [README.md](./README.md) - Documentação técnica
- [POC_PROMETHEUS_SYNC.md](./POC_PROMETHEUS_SYNC.md) - POC detalhada
- [APRESENTACAO.md](./APRESENTACAO.md) - Slides para apresentação
- [scripts/README.md](./scripts/README.md) - Guia de scripts

---

**Pronto para impressionar!** 🎊
