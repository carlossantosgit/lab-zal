# Guia Operacional: Sincronização Prometheus → Zabbix

---

## Arquitetura (Novo Modelo)

O sistema usa um **host único** no Zabbix chamado `prometheus` para representar todos os alertas do Prometheus.

### Items parametrizados

Para cada par `(alertname, instance)` são criados 4 items:

```
prom.alert.status[alertname,instance]    ← Valor numérico do threshold de severidade
prom.alert.severity[alertname,instance]  ← Prioridade numérica (1-5)
prom.alert.summary[alertname,instance]   ← Texto do summary (max 255 chars)
prom.alert.payload[alertname,instance]   ← JSON com todos os labels do alerta
```

Exemplo para o alerta `HighCPU` na instância `10.0.0.1:9100`:
```
prom.alert.status[highcpu,10.0.0.1_9100]
prom.alert.severity[highcpu,10.0.0.1_9100]
prom.alert.summary[highcpu,10.0.0.1_9100]
prom.alert.payload[highcpu,10.0.0.1_9100]
```

### Mapeamento de severidade

| Prometheus severity | Zabbix priority | Threshold |
|---|---|---|
| info / none | 1 (Information) | 1 |
| warning | 2 (Warning) | 2 |
| average | 3 (Average) | 3 |
| high | 4 (High) | 4 |
| critical / emergency / page | 5 (Disaster) | 5/6 |

### Triggers

Cada trigger é criada com:
- **Nome:** summary do alerta (com macros substituídas)
- **Expressão:** `{prometheus:prom.alert.status[alertname,instance].last()}>=threshold`
- **Tags:** labels do Prometheus (exceto meta-labels)
- **Prioridade:** baseada na severidade do alerta

### Envio de dados

Os valores são enviados via **Zabbix Trapper** (protocolo TCP nativo do Zabbix):
- Conexão direta TCP ao servidor Zabbix na porta do trapper (padrão: 10151)
- Protocolo binário `ZBXD` com payload JSON
- Não requer `zabbix_sender` instalado no servidor

---

## Comandos Disponíveis

### `--all` — Sincronizar estrutura

Cria (ou garante que existe) o host único `prometheus`, os items parametrizados e as triggers para todos os alertas ativos no Prometheus.

```bash
python3 sync_prometheus.py --all
```

**Quando usar:** na primeira execução e periodicamente para registar novos alertas.
Este comando é **idempotente** — seguro de executar várias vezes.

### `--push` — Enviar valores

Consulta os alertas ativos no Prometheus e envia os valores atuais para os items via Zabbix Trapper.

```bash
python3 sync_prometheus.py --push
```

**Quando usar:** frequentemente (ex: a cada 5 minutos via cron) para manter os dados atualizados no Zabbix.

### `--verbose` — Modo detalhado

Pode ser combinado com qualquer comando:

```bash
python3 sync_prometheus.py --all --verbose
python3 sync_prometheus.py --push --verbose
```

---

## Workflow Recomendado

```bash
cd /home/seu-usuario/prometheus-zabbix
source venv/bin/activate

# 1. Validar conectividade
python3 validate.py

# 2. Sincronizar estrutura (cria host, items e triggers)
python3 sync_prometheus.py --all

# 3. Enviar valores atuais dos alertas
python3 sync_prometheus.py --push

# 4. Verificar logs
tail -100 /var/log/prometheus-zabbix-sync.log
```

---

## Automação com Cron

```bash
crontab -e
```

```bash
# Sincronizar estrutura a cada hora (garante novos alertas registados)
0 * * * * cd /home/seu-usuario/prometheus-zabbix && source venv/bin/activate && python3 sync_prometheus.py --all >> /var/log/prometheus-zabbix-sync.log 2>&1

# Enviar valores a cada 5 minutos
*/5 * * * * cd /home/seu-usuario/prometheus-zabbix && source venv/bin/activate && python3 sync_prometheus.py --push >> /var/log/prometheus-zabbix-sync.log 2>&1
```

---

## O que é Criado no Zabbix

### Host

```
Nome:   prometheus
Grupo:  Prometheus
IP:     127.0.0.1 (interface fictícia — dados chegam via Trapper)
```

### Items (por alerta × instância)

Para cada alerta ativo no Prometheus:

| Key | Tipo Zabbix | Descrição |
|---|---|---|
| `prom.alert.status[alert,inst]` | Numeric unsigned | Threshold de severidade |
| `prom.alert.severity[alert,inst]` | Numeric unsigned | Prioridade numérica |
| `prom.alert.summary[alert,inst]` | Character (255) | Texto do summary |
| `prom.alert.payload[alert,inst]` | Text | JSON com todos os labels |

### Triggers

Uma trigger por combinação `(alertname, instance, severity)` com:
- Nome = summary do alerta
- Expressão = `{prometheus:prom.alert.status[alert,inst].last()}>=N`
- Tags = labels do Prometheus (namespace, cluster, job, etc.)

---

## Verificar no Zabbix UI

### Ver o host

```
Monitoring → Hosts
Filtrar por grupo: Prometheus
```

Esperado: host `prometheus` / `Prometheus Alerts`

### Ver items

```
Monitoring → Hosts → prometheus → Items
Filtrar por key: prom.alert
```

Esperado: grupos de 4 items por alerta/instância com tipo Trapper.

### Ver triggers

```
Monitoring → Triggers
Filtrar por host: prometheus
```

Esperado: triggers com nomes dos summaries dos alertas, severidade colorida.

### Testar manualmente via Zabbix Sender

```bash
zabbix_sender -z IP-zabbix -p 10151 -s prometheus -k prom.alert.status[highcpu,10.0.0.1_9100] -o 5
```

---

## Logs e Diagnóstico

Localização do log:
```
/var/log/prometheus-zabbix-sync.log
```
(Se não tiver permissão de escrita em `/var/log`, o log é criado na pasta do script.)

```bash
# Ver logs em tempo real
tail -f /var/log/prometheus-zabbix-sync.log

# Ver as últimas 100 linhas
tail -100 /var/log/prometheus-zabbix-sync.log

# Filtrar erros
grep -i error /var/log/prometheus-zabbix-sync.log
```

---

## Troubleshooting

### "Sem alertas activos no Prometheus"

O Prometheus não tem alertas em estado `firing` neste momento.

Verificar no browser: `https://seu-prometheus/api/v1/alerts`

### Items criados mas sem dados no Zabbix

Verificar se o `--push` está a correr via cron. Os items são do tipo Trapper e só recebem dados quando o `--push` é executado.

```bash
python3 sync_prometheus.py --push --verbose
```

### Trigger não dispara

1. Verificar se o item `prom.alert.status[alert,inst]` tem dados recentes
2. Verificar se o valor enviado é maior ou igual ao threshold da trigger
3. Ver expressão da trigger no Zabbix UI

### "Erro com Zabbix Trapper: Connection refused"

- Verificar `ZABBIX_SERVER` e `ZABBIX_TRAPPER_PORT` em `sync_prometheus.py`
- Confirmar que a porta está aberta: `nc -zv IP-zabbix 10151`
- Verificar regras de firewall

### SSL Certificate Errors

Certificados self-signed estão configurados para ser ignorados (`VERIFY_SSL = False`).

Se mesmo assim falhar:
```bash
curl -k https://seu-zabbix:4443/api_jsonrpc.php
curl -k -u user:pass https://seu-prometheus/-/healthy
```

---

## Suporte

- Prometheus Admin: [preencher]
- Zabbix Admin: [preencher]
- On-Call: [preencher]
