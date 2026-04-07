# 🔄 Guia: Sincronização Prometheus → Zabbix

## 📋 Antes de Começar

### Verificar Conectividade

```bash
cd /production

# Validar config
python validate.py
```

**Esperado:**
```
✅ Prometheus: https://prometheus-prod-srv01.spms.min-saude.pt (healthcheck OK)
✅ Zabbix: https://zabbix-dev.spms.min-saude.pt:4443 (login OK)
✅ VALIDAÇÃO OK - Sistema pronto!
```

---

## 🚀 Sincronização

### **Opção 1: Sincronizar TODOS os hosts** (Recomendado)

Sincroniza todos os targets Prometheus e seus alertas para Zabbix:

```bash
python sync_all_hosts.py --all
```

**Output esperado:**
```
======================================================================
🔄 SINCRONIZACAO PROMETHEUS → ZABBIX
======================================================================
✅ Zabbix: login OK
📡 Prometheus: 250 targets, 15 jobs
📋 Regras: 32 total | 45 base + 120 instancia | triggers: 45
Zabbix: 250 hosts existentes

[  1/250] hostname1                   :  12 regras → +5i +2t
[  2/250] hostname2                   :   8 regras → +3i +1t
...
[250/250] hostname250                 :  10 regras → +4i +2t

======================================================================
✅ CONCLUIDO: +0 hosts, +125 items, +45 triggers (0 saltados)
======================================================================

📊 SUMARIO:
  Hosts processados: 250
  Items criados:     125
  Triggers criadas:  45
```

### **Opção 2: Sincronizar Host Específico**

```bash
python sync_all_hosts.py --host=hostname1
```

**Output:**
```
Host hostname1: 12 regras, +5 items, +2 triggers
```

### **Opção 3: Modo Verbose (Debug)**

```bash
python sync_all_hosts.py --all --verbose
```

Mostra informações detalhadas de cada criação de item/trigger.

---

## 📊 Gerar Relatórios

### **JSON** (Para integração com sistemas)

```bash
python sync_all_hosts.py --all --report=json > sync_report.json
```

**Formato:**
```json
{
  "timestamp": "2026-04-06T10:30:00Z",
  "status": "success",
  "summary": {
    "hosts_processed": 250,
    "items_created": 125,
    "triggers_created": 45,
    "errors": 0
  },
  "per_host": [
    {
      "hostname": "hostname1",
      "items_created": 5,
      "triggers_created": 2,
      "total_rules": 12
    }
  ]
}
```

### **CSV** (Para análise em Excel)

```bash
python sync_all_hosts.py --all --report=csv > sync_report.csv
```

**Formato:**
```
hostname,items_created,triggers_created,total_rules
hostname1,5,2,12
hostname2,3,1,8
...
```

---

## ✅ Validação Pós-Sincronização

Após sincronizar, sempre validar o resultado:

### **Validar TODOS os hosts**

```bash
python validate_sync.py --all
```

**Output esperado:**
```
======================================================================
🔍 VALIDACAO GLOBAL
======================================================================
Hosts a validar: 250

✅ hostname1                             | items: 5 | triggers: 2 | issues: 0
✅ hostname2                             | items: 3 | triggers: 1 | issues: 0
...

📈 TOTALS:
  Hosts verificados:     250
  Hosts OK:              250
  Items total OK:        125
  Triggers total OK:     45
  Total de problemas:    0
```

### **Validar Host Específico**

```bash
python validate_sync.py --host=hostname1
```

**Output:**
```
======================================================================
🔍 VALIDACAO: hostname1
======================================================================

📋 Items (12 total):
  Prometheus items: 12
  ✅ Status: OK

⚡ Triggers (2 total):
  Prometheus triggers: 2
  ✅ Status: OK

✏️  RESUMO:
  Items OK:      12
  Triggers OK:   2
  ✅ Status:      OK
```

---

## 📈 O que É Criado

### **Items (Por Host)**

**Base Items** - Um por alerta+severity:
```
prometheus.cpuusage.warning         ← CPUUsage severa warning
prometheus.cpuusage.critical        ← CPUUsage severa critical
prometheus.diskusage.warning.a1b2c3 ← DiskUsage em /var (mountpoint-específico)
prometheus.diskusage.critical.c3d4e5← DiskUsage em /home (critical)
```

**Instance Items** - Apenas para alertas ativos com detalhes:
- Extraem: mountpoint, device, interface, filesystem, name, service
- Permitem monitorização granular (e.g., distinguir /var vs /home)

### **Triggers (Por Host)**

**Regra de Severidade:**
- Por host, por alerta: apenas a **severidade MAIS ALTA** gera trigger
- Outras severidades: items apenas (coleta de dados, sem alertar)
- Exemplo: Se alerta tem [warning, critical]:
  - Warning → item criado, sem trigger (dados)
  - Critical → item criado COM trigger (alerta)

**Expressão:**
```
{hostname:prometheus.alertname.severity.last()}>0
```

---

## 🔍 Como Verificar no Zabbix

### 1. **Ver Hosts**

```
Monitoring → Hosts
Procurar por: "prometheus"
```

Esperado: 250+ hosts com group "Prometheus"

### 2. **Ver Items de um Host**

```
Monitoring → Hosts
Clicar: hostname1 → "Items"
Procurar por: "prometheus."
```

Esperado:
- ~32 items com prefixo `prometheus.`
- Cada um com interface válida (não órfão)
- Chave exemplo: `prometheus.cpuusage.warning`

### 3. **Ver Triggers**

```
Monitoring → Triggers
Procurar por: hostname
```

Esperado:
- ~10-15 triggers por host
- Severidade colorida (red=critical, orange=warning, etc)
- Expressão: `{hostname:prometheus.xxx.last()}>0`

### 4. **Ver em Ação (Mock)**

Enviar valor via Zabbix Sender para teste:
```bash
zabbix_sender -z zabbix-server -s hostname1 -k prometheus.cpuusage.warning -o 1
```

Resultado: Trigger firewall em Zabbix!

---

## ⚠️ Troubleshooting

### **Items criados mas "Sem Dados" em Zabbix**

Causa: Items órfãos (sem interface)

Solução:
```bash
python validate_sync.py --host=hostname1
```

Se mostra "Órfão", executar:
```bash
# Fix de interface (ainda não implementado, manual no Zabbix UI)
# Ou recriar items com: sync_all_hosts.py --host=hostname1
```

### **Triggers não aparecem em Zabbix**

Causa provável: Expressão inválida ou item sem dados

Verificar:
```bash
python validate_sync.py --all --verbose
```

### **SSL Certificate Errors**

O script já trata self-signed certs (ZABBIX_VERIFY_SSL=False em config.py).

Se ainda falhar:
```bash
# Verificar conectividade direta
curl -k https://zabbix-dev.spms.min-saude.pt:4443/api_jsonrpc.php
curl -k https://prometheus-prod-srv01.spms.min-saude.pt/-/healthy
```

---

## 📋 Workflow Completo

```bash
# 1. Preparar
cd /production
python validate.py                    # Verificar tudo OK

# 2. Sincronizar
python sync_all_hosts.py --all       # Criar items/triggers

# 3. Validar
python validate_sync.py --all        # Verificar integridade

# 4. Relatório
python sync_all_hosts.py --all --report=json > sync_report.json

# 5. Verificar manualmente em Zabbix UI
# Monitoring → Hosts → hostname1 → Items
# Monitoring → Triggers → procurar "prometheus"

# ✅ Pronto para usar Zabbix como fonte de tickets!
```

---

## 📝 Logs e Auditoria

Todos os comandos geram logs em:
```
/var/log/prometheus-zabbix-sync.log
```

Ver logs em tempo real:
```bash
tail -f /var/log/prometheus-zabbix-sync.log
```

---

## 🆘 Suporte

Manter este guia atualizado e compartilhar com equipe de operações.

**Contatos:**
- Prometheus Admin: [...]
- Zabbix Admin: [...]
- On-Call: [...]
