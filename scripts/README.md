# 🛠️ Scripts de Setup e Maintenance

Scripts auxiliares para setup inicial e manutenção do Lab ZAL.

> ⚠️ **ATENÇÃO**: Com o novo **auto-create feature**, muitos destes scripts são **OPCIONAIS**!
> O webhook cria hosts automaticamente quando recebe alertas. Use estes scripts apenas se precisar de setup manual.

## ✨ Novo: Auto-Create Feature

O webhook agora cria hosts **automaticamente**:
- ✅ Detecta novo host via label `zabbix_host`
- ✅ Verifica se existe em Zabbix via API
- ✅ Se não existe, cria com interface e 3 items
- ✅ Não precisa rodar scripts manuais!

**Quando usar scripts:**
- Setup manual de hosts pré-existentes
- Corrigir interfaces se houver erro
- Manutenção avançada

---

## 📋 Setup Inicial - OPCIONALMENTE

### `setup_hosts.py` - OPCIONAL (Agora com Auto-Create)

Cria hosts e items no Zabbix **manualmente**.

```bash
python3 setup_hosts.py
```

**O que faz:**
- ✅ Cria grupo "Prometheus" no Zabbix
- ✅ Cria hosts: node-01, prometheus-server
- ✅ Cria 3 items por host
- ✅ Configura interfaces

**Quando usar:**
- Setup inicial de hosts pré-existentes (node-01, prometheus-server)
- Verificar que Zabbix API está funcionando
- Recriar hosts se deletados acidentalmente

**Output esperado:**
```
✅ Logged in
Using group: 18
✅ Created host: prometheus-server (ID: 10439)
  ✅ Created item: prometheus.deadmansswitch
  ✅ Created item: prometheus.highcpu
  ✅ Created item: prometheus.lowmemory
✅ Setup completed!
```

> **Nota**: Se rodar novamente, pulará hosts que já existem (não duplica)

---

## 🔧 Maintenance Scripts

### `fix_all_items.py` - USAR PARA MANUTENÇÃO

Corrige interfaces de items se houver erro.

```bash
python3 fix_all_items.py
```

**O que faz:**
- ✅ Encontra todos os hosts em Zabbix
- ✅ Carrega a interface correta de cada host
- ✅ Atualiza todos os items com a interface correta

**Quando usar:**
- Se items mostram erro "failed to fulfill the requests"
- Após criar hosts manualmente e precisar configurar interface
- Manutenção preventiva

**Output esperado:**
```
Found 4 target hosts

🔧 Host: prometheus-server
   Interface ID: 3
   Found 3 items
   ✅ prometheus.deadmansswitch
   ✅ prometheus.highcpu
   ✅ prometheus.lowmemory

🔧 Host: node-01
   Interface ID: 2
   Found 3 items
   ✅ prometheus.deadmansswitch
   ✅ prometheus.highcpu
   ✅ prometheus.lowmemory

✅ Done!
```

### Scripts Deprecated

- `setup_zabbix.py` - Versão antiga. Mantido para referência histórica.
- `fix_items.py` - Versão antiga de correção. Use `fix_all_items.py`.

---

## 📖 Fluxo Recomendado Agora

### Cenário 1: Adicionar Host Novo (Recomendado - AUTOMÁTICO)

**Nenhum script necessário!** O webhook cria tudo sozinho:

1. Adicionar ao `prometheus/prometheus.yml`:
```yaml
- job_name: 'node-exporter-db'
  static_configs:
    - targets: ['db-server.example.com:9100']
      labels:
        zabbix_host: srv-db
```

2. Recarregar Prometheus:
```bash
docker-compose restart prometheus
```

3. **Pronto!** Quando Prometheus scraper o host e enviar alerta, webhook cria automaticamente em Zabbix ✨

### Cenário 2: Setup Inicial (Se Necessário)

Se quiser criar hosts **antes** de receber alertas:

```bash
cd scripts
python3 setup_hosts.py
```

### Cenário 3: Corrigir Interface (Manutenção)

Se items tiverem erro de interface:

```bash
cd scripts
python3 fix_all_items.py
```

---

## 🧪 Testar Items

### Teste Manual com zabbix_sender

```bash
docker-compose exec webhook zabbix_sender \
  -z zabbix-server \
  -s "node-01" \
  -k "prometheus.highcpu" \
  -o "1"
```

Esperado: `processed: 1; failed: 0`

### Teste com Webhook (Auto-Create)

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

Resultado: Host `novo-servidor` será criado em Zabbix automaticamente!

---

## 📋 Referência Rápida

| Tarefa | Comando | Necessário? |
|--------|---------|-----------|
| Setup hosts pré-existentes | `python3 setup_hosts.py` | ❌ Opcional |
| Corrigir interfaces | `python3 fix_all_items.py` | ✅ Se erro |
| Auto-criar novo host | Enviar alerta via webhook | ✅ Recomendado |
| Ver logs Zabbix | `docker-compose logs zabbix-server` | ✅ Diagnóstico |
| Ver logs Webhook | `docker-compose logs webhook -f` | ✅ Ver auto-create |

---

## ⚙️ Dependências

```bash
pip install requests
```

Já incluído nos containers!

---

## 📝 Notas Técnicas

- Scripts conectam a `http://localhost:8080/api_jsonrpc.php`
- Credenciais: Admin / zabbix
- Todos suportam **dry-run** (sem fazer mudanças)
- Webhook usa mesma API para auto-create

---

## 🚀 Sumário

**Antes (Manual):**
1. Adicionar em prometheus.yml
2. Rodar `python3 setup_hosts.py` ← Passo necessário
3. Pode rodar `python3 fix_all_items.py` se erro

**Agora (Automático):**
1. Adicionar em prometheus.yml
2. ✨ Webhook faz o resto automaticamente
3. Scripts são só ferramentas opcionais de manutenção

Muito mais simples! 🎉

---

## ✅ Scripts Novos - POC Validação

### `validate_e2e.py` - VALIDAÇÃO END-TO-END ⭐

**Novo!** Demonstra pipeline completa de ponta a ponta.

```bash
python3 validate_e2e.py
```

**O que faz:**
- ETAPA 1: Valida conectividade (Zabbix, Prometheus, Webhook)
- ETAPA 2: Carrega 32 regras Prometheus atuais
- ETAPA 3: Cria nova regra customizada (DemoValidacaoE2E)
- ETAPA 4: Cria host de teste e sincroniza 33 regras
- ETAPA 5: Valida items e triggers no Zabbix API
- ETAPA 6: Mostra resumo completo

**Resultado:**
```
✅ 33 items criados (um por cada regra!)
✅ 33 triggers criadas (com severidades corretas)
✨ Prova visual que pipeline completa funciona!
```

**Quando usar:**
- Validar que tudo está funcionando
- Demonstração rápida (2 min)
- Testar integração Prometheus ↔ Zi Zabbix
- Apresentações ao cliente

**Tempo:** ~2-3 segundos

**Referência:** [E2E_VALIDATION_REPORT.md](../E2E_VALIDATION_REPORT.md)

### `sync_prometheus_rules.py` - SINCRONIZAR REGRAS ⭐

**Sincroniza manualmente as 32 regras Prometheus com Zabbix.**

```bash
# Ver todos os hosts
python3 sync_prometheus_rules.py --list

# Sincronizar um host
python3 sync_prometheus_rules.py --host prod-db-01 --demo

# Sincronizar todos
python3 sync_prometheus_rules.py --all --demo
```

**Resultado:**
```
✅ Host: prod-db-01
✅ Items criados: 32
✅ Triggers criadas: 32
```

**Quando usar:**
- Sincronizar regras manualmente
- Demo rápida do POC
- Testes de sincronização

**Tempo:** ~1-2 segundos por host

---

## 🎨 Scripts Antigos (Ainda Funcionam)

### `populate_demo_data.py` - PARA APRESENTAÇÃO

Popula dados realistas em Zabbix para demonstração.

```bash
python3 populate_demo_data.py
```

**O que faz:**
- ✅ Cria 4 hosts de demonstração:
  - prod-db-01 (Production Database)
  - api-server-01 (API Server)
  - cache-redis-01 (Redis Cache)
  - app-web-01 (Web Application)
- ✅ Cada host com 6 items (CPU, Memory, Requests, Latency, etc)
- ✅ Envia dados de teste via webhook
- ✅ Configura interfaces automaticamente

**Resultado:**
```
✅ 4 hosts criados
✅ 24 items criados (6 por host)
✅ Dados de teste populados

→ Abrir http://localhost:8080
→ Monitoring → Latest Data
→ Ver dados realistas de 4 hosts!
```

**Perfeito para:**
- Demonstrações ao vivo
- Apresentações
- Testes de alerts
- Screenshots para documentação

