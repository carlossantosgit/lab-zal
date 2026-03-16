# 🛠️ Scripts de Setup e Maintenance

Scripts auxiliares para setup inicial e manutenção do Lab ZAL.

## 📋 Setup Initial (One-Time)

### `setup_hosts.py` - USE ESTE

Cria hosts e items no Zabbix automaticamente.

```bash
python3 setup_hosts.py
```

**O que faz:**
- ✅ Cria grupo "Prometheus" no Zabbix
- ✅ Cria hosts: node-01, prometheus-server
- ✅ Cria 3 items por host (prometheus.highcpu, lowmemory, deadmansswitch)

**Output:**
```
✅ Logged in
Using group: 18
✅ Created host: prometheus-server (ID: 10439)
  ✅ Created item: prometheus.deadmansswitch
  ✅ Created item: prometheus.highcpu
  ✅ Created item: prometheus.lowmemory
✅ Setup completed!
```

### `setup_zabbix.py` - DEPRECATED

Versão antiga. Mantido para referência historicamente. Use `setup_hosts.py` em vez disso.

## 🔧 Maintenance Scripts

### `fix_all_items.py` - USAR PARA MANUTENÇÃO

Corrige interfaces de items após criar novos hosts.

```bash
python3 fix_all_items.py
```

**O que faz:**
- ✅ Encontra todos os hosts (node-01, prometheus-server, etc)
- ✅ Carrega a interface correta de cada host
- ✅ Atualiza todos os items com a interface

**Quando usar:**
- Após adicionar novo host com `setup_hosts.py`
- Se items mostram "failed to fulfill the requests"

**Output:**
```
Found 2 target hosts

🔧 Host: prometheus-server
   Interface ID: 3
   Found 3 items
   ✅ prometheus.deadmansswitch
   ✅ prometheus.highcpu
   ✅ prometheus.lowmemory

✅ Done!
```

### `fix_items.py` - OBSOLETO

Versão antiga de correção. Mantido para backup histórico. Use `fix_all_items.py`.

## 📖 Como Adicionar Novo Host

### Passo 1: Modificar Prometheus

Editar `prometheus/prometheus.yml`:

```yaml
- job_name: 'node-exporter-prod'
  static_configs:
    - targets: ['prod-server.example.com:9100']
      labels:
        zabbix_host: srv-prod
```

### Passo 2: Recarregar Prometheus

```bash
docker-compose restart prometheus
```

### Passo 3: Executar Setup

```bash
cd scripts
python3 setup_hosts.py
```

Irá:
1. ✅ Detectar novo host "srv-prod"
2. ✅ Criar no Zabbix (ID gerado automaticamente)
3. ✅ Criar os 3 items
4. ✅ Configurar interface

### Passo 4: Corrigir Interfaces (se necessário)

```bash
python3 fix_all_items.py
```

## 🧪 Testes

### Testar se item funciona

```bash
docker-compose exec webhook zabbix_sender \
  -z zabbix-server \
  -s "srv-prod" \
  -k "prometheus.test" \
  -o "999"
```

Esperado: `processed: 1; failed: 0`

## 📋 Referência Rápida

| Tarefa | Comando |
|--------|---------|
| Setup inicial | `python3 setup_hosts.py` |
| Corrigir interfaces | `python3 fix_all_items.py` |
| Ver logs Zabbix | `docker-compose logs zabbix-server` |
| Ver logs Webhook | `docker-compose logs webhook` |
| Testar zabbix_sender | `docker-compose exec webhook zabbix_sender ...` |

## ⚙️ Dependências

```bash
pip install requests
```

## 📝 Notas

- Scripts conectam a `http://localhost:8080/api_jsonrpc.php`
- Credenciais: Admin / zabbix
- Todos os scripts suportam dry-run (verificação sem fazer mudanças)
