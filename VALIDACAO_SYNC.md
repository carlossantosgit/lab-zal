# 🧪 Guia de Validação - Sincronização Prometheus → Zabbix

Documento prático para validar que **novas regras do Prometheus sincronizam automaticamente com Zabbix**.

---

## ✅ Validação 1: Sincronização Manual (Rápida)

**Objetivo:** Testar se novas regras do Prometheus são sincronizadas corretamente quando o script é executado.

### Passo 1: Ver hosts e regras sincronizadas
```bash
cd /Users/carlossantos/lab-zal
python3 scripts/sync_prometheus_rules.py --list --demo
```

**Saída esperada:**
```
✓ Conectado ao Zabbix em http://localhost:8080
📊 Hosts disponíveis:
1. prod-node-01 (hostid: 1001)
2. prod-node-02 (hostid: 1002)
3. prometheus-server (hostid: 1003)
...

📋 Regras Prometheus (32):
1. HighCPUUsage (warning)
2. CriticalCPUUsage (critical)
3. LowMemoryAvailable (warning)
...
```

### Passo 2: Sincronizar um host específico
```bash
python3 scripts/sync_prometheus_rules.py --host prod-node-01 --demo
```

**Saída esperada:**
```
🔄 Sincronizando prod-node-01...
✅ Itens criados: 32
✅ Triggers criados: 32
✨ Sincronização concluída com sucesso!
```

### Passo 3: Validar no Zabbix UI
1. Abrir: http://localhost:8080
2. Login: `Admin` / `zabbix`
3. Ir em: **Configuration → Hosts**
4. Selecionar host: `prod-node-01`
5. Aba **Items** → Deve ter 32 items com nomes como:
   - `prometheus.HighCPUUsage`
   - `prometheus.LowMemoryAvailable`
   - `prometheus.CriticalMemoryUsage`
   - etc.
6. Aba **Triggers** → Deve ter 32 triggers correspondentes

---

## ✅ Validação 2: Sincronização via Webhook (Com Alerta Real)

**Objetivo:** Testar que quando um alerta chega, o webhook **cria o host + sincroniza regras automaticamente**.

### Passo 1: Verificar que o webhook está rodando
```bash
docker-compose logs -f webhook | grep -E "Running on|listeando"
```

Saída esperada:
```
webhook_1  | Running on http://0.0.0.0:5001
```

### Passo 2: Verificar logs do webhook em tempo real
```bash
docker-compose logs -f webhook
```

### Passo 3: Simular um alerta chegando do Prometheus
```bash
curl -X POST http://localhost:5001/alert \
  -H "Content-Type: application/json" \
  -d '{
    "alerts": [{
      "status": "firing",
      "labels": {
        "alertname": "TestRule",
        "zabbix_host": "test-host-123"
      },
      "annotations": {
        "summary": "Test alert for validation"
      }
    }]
  }' \
  -v
```

### Passo 4: Validar que o WebHook fez seu trabalho
```bash
# Verificar se o host foi criado
python3 scripts/sync_prometheus_rules.py --list --demo | grep test-host-123

# Ou validar diretamente via Zabbix
curl -s http://localhost:8080/api_jsonrpc.php \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "host.get",
    "params": {"filter": {"name": "test-host-123"}},
    "auth": "<token>",
    "id": 1
  }' | python3 -m json.tool
```

**Deve retornar:** Um host com 32 items já criados.

---

## ✅ Validação 3: Adicionar Nova Regra no Prometheus e Validar Sync

**Objetivo:** Teste mais realista - editar rules Prometheus, recarregar, sincronizar, validar no Zabbix.

### Passo 1: Acessar arquivo de rules do Prometheus
```bash
cat /Users/carlossantos/lab-zal/prometheus/prometheus.yml
# Ou ver as rules fake:
cat /Users/carlossantos/lab-zal/webhook/fake_prometheus_rules.json | python3 -m json.tool | head -50
```

### Passo 2: Adicionar uma nova regra (para teste)

Opção A - **Editar arquivo fake rules:**
```bash
# Fazer backup
cp /Users/carlossantos/lab-zal/webhook/fake_prometheus_rules.json \
   /Users/carlossantos/lab-zal/webhook/fake_prometheus_rules.json.bak

# Adicionar nova regra ao array
# (Você pode editar manualmente e adicionar uma regra chamada "MyCustomRule")
```

Opção B - **Usar Prometheus real (se em produção):**
```bash
# SSH para servidor Prometheus
# Editar /etc/prometheus/rules/custom.rules
# Adicionar:
# groups:
#   - name: custom
#     rules:
#     - alert: MyNewCustomRule
#       expr: up == 0
#       severity: critical
```

### Passo 3: Recarregar regras
```bash
# Se for Prometheus em Docker local:
docker-compose exec prometheus kill -HUP 1

# Ou fazer restart:
docker-compose restart prometheus
```

### Passo 4: Sincronizar com a nova regra
```bash
python3 scripts/sync_prometheus_rules.py --all --demo
```

**Saída esperada:**
```
🔄 Sincronizando todos os hosts...
Host: prod-node-01
  ✅ Items criados: 33 (adicionou a nova "MyNewCustomRule")
  ✅ Triggers criados: 33
```

### Passo 5: Validar no Zabbix
```bash
# Ver items com "MyNewCustomRule"
python3 -c "
import sys
sys.path.insert(0, 'webhook')
from prometheus_sync import get_prometheus_rules
rules = get_prometheus_rules(use_fake=True)
custom = [r for r in rules if 'Custom' in r.get('alert', '')]
print(f'Encontradas {len(custom)} regras com Custom no nome')
for r in custom:
    print(f\"  - {r['alert']} ({r['labels'].get('severity', 'info')})\")
"
```

---

## ✅ Validação 4: Teste End-to-End Completo

**Objetivo:** Teste realista simulando toda a pipeline em sequência.

### Checklist para executar:

```bash
#!/bin/bash
set -e

echo "🧪 VALIDAÇÃO END-TO-END - PROMETHEUS SYNC"
echo "=========================================="

# 1. Verificar containers
echo "1️⃣ Verificando containers..."
docker-compose ps

# 2. Verificar conectividade
echo "2️⃣ Testando conectividade..."
curl -s http://localhost:9090/-/healthy && echo "✅ Prometheus OK"
curl -s http://localhost:8080/api_jsonrpc.php -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"apiinfo.version","id":1}' > /dev/null && echo "✅ Zabbix OK"

# 3. Listar hosts antes
echo "3️⃣ Hosts antes de sync:"
python3 scripts/sync_prometheus_rules.py --list --demo 2>&1 | head -10

# 4. Sincronizar tudo
echo "4️⃣ Sincroni Zando todos os hosts..."
python3 scripts/sync_prometheus_rules.py --all --demo

# 5. Verificar items criados
echo "5️⃣ Verificando items criados..."
curl -s http://localhost:8080/api_jsonrpc.php \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "item.get",
    "params": {"search": {"key_": "prometheus.%"}},
    "auth": "<token>",
    "id": 1
  }' | python3 -m json.tool | head -30

# 6. Verificar triggers
echo "6️⃣ Verificando triggers criados..."
curl -s http://localhost:8080/api_jsonrpc.php \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "trigger.get",
    "params": {"search": {"description": "Prometheus%"}},
    "auth": "<token>",
    "id": 1
  }' | python3 -m json.tool | head -30

echo "✅ VALIDAÇÃO CONCLUÍDA!"
```

Salve como `validate.sh` e execute:
```bash
chmod +x validate.sh
./validate.sh
```

---

## 📊 Resultados Esperados Resumo

| Validação | O que testar | Sucesso observável |
|-----------|-------------|-------------------|
| **Manual** | `--list` e `--host` | 32 items + 32 triggers por host |
| **Webhook** | POST /alert com novo host | Host criado + 32 items criados automaticamente |
| **Nova Regra** | Adicionar rule, sincronizar | Item + trigger criados para nova regra |
| **E2E** | Pipeline completa | Todos os hosts × 32 regras = itens/triggers criados |

---

## 🔍 Troubleshooting - Se algo não sincronizar

### Problema: "Items criados: 0"
```bash
# Causa: Regras já existem (idempotente é feature, não bug!)
# Solução: Testar com novo host ou deletar items do host e resync

# Verificar items existentes:
python3 -c "
import sys
sys.path.insert(0, 'webhook')
from prometheus_sync import PrometheusSync
ps = PrometheusSync()
rules = ps.get_prometheus_rules(use_fake=True)
print(f'Total de regras encontradas: {len(rules)}')
"
```

### Problema: "Connection refused - Zabbix"
```bash
# Verificar se Zabbix está rodando
docker-compose ps | grep zabbix

# Checar logs
docker-compose logs zabbix-server | tail -20
docker-compose logs zabbix-web | tail -20

# Reiniciar se necessário
docker-compose restart zabbix-server zabbix-web
```

### Problema: "Webhook não criou items"
```bash
# Ver logs do webhook
docker-compose logs webhook | tail -50

# Testar webhook manualmente
curl -X POST http://localhost:5001/alert -v \
  -H "Content-Type: application/json" \
  -d '{"alerts":[{"status":"firing","labels":{"zabbix_host":"debug-test"}}]}'
```

---

## 💡 Dicas para Apresentação

Quando apresentar para o cliente, execute nesta ordem:

```bash
# Apresentação LIVE
echo "1. Mostrar hosts e regras"
python3 scripts/sync_prometheus_rules.py --list --demo

echo "2. Sincronizar um host"
python3 scripts/sync_prometheus_rules.py --host prod-node-01 --demo

echo "3. Abrir Zabbix e mostrar items criados"
echo "Abrir: http://localhost:8080 → prod-node-01 → Items"

echo "4. Simular novo alerta (webhook)"
curl -X POST http://localhost:5001/alert -d '...'

echo "5. Mostrar novo host criado no Zabbix"
```

**Timing sugerido:** 5-7 minutos

---

## ✅ Conclusão

Se TODOS os passos acima funcionarem, você tem validado que:

✅ Prometheus rules → Items Zabbix (sincronização manual)
✅ Webhook → Auto-cria hosts + sincroniza regras
✅ Novas regras → Automáticamente sincronizadas
✅ Pipeline completa funcionando end-to-end

**Próximo passo:** Ir para fase PRD (Produção)!
