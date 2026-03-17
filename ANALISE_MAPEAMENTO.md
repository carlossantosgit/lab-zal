# 📊 Análise de Mapeamento: Prometheus Labels → Zabbix Host Groups

**Objetivo:** Mapear labels "app" do Prometheus com Host Groups do Zabbix para sincronização correta.

---

## 🔍 Fase 1: ANÁLISE (O que você precisa fazer)

### A. Listar Host Groups Zabbix Atuais

```bash
# Conectar no Zabbix via API
curl -s http://seu-zabbix-qua:8080/api_jsonrpc.php \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "user.login",
    "params": {"user": "Admin", "password": "zabbix"},
    "id": 1
  }'

# Resultado retorna token, depois:
curl -s http://seu-zabbix-qua:8080/api_jsonrpc.php \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "hostgroup.get",
    "params": {"output": ["groupid", "name"]},
    "auth": "TOKEN_AQUI",
    "id": 1
  }' | python3 -m json.tool
```

**Esperado:** Lista de grupos como:
```
{
  "groupid": "10",
  "name": "Linux servers"
}
{
  "groupid": "11",
  "name": "Databases"
}
{
  "groupid": "12",
  "name": "API Servers"
}
{
  "groupid": "13",
  "name": "Cache Servers"
}
```

**Registre aqui:**

| Group ID | Group Name | Descrição |
|----------|-----------|-----------|
| | | |
| | | |
| | | |

---

### B. Listar Labels "app" do Prometheus PRODUÇÃO

```bash
# Conectar no Prometheus
curl -s http://seu-prometheus-prod:9090/api/v1/targets \
  | python3 -m json.tool | grep -A 5 "app"
```

**Esperado:** Lista de targets com labels:
```json
{
  "labels": {
    "app": "database",
    "instance": "prod-db-01:5432",
    "job": "prometheus"
  }
}
{
  "labels": {
    "app": "api",
    "instance": "prod-api-01:8080",
    "job": "prometheus"
  }
}
```

**Ou consultar alerting rules:**
```bash
curl -s http://seu-prometheus-prod:9090/api/v1/rules \
  | python3 -m json.tool | grep -B 2 -A 2 "app"
```

**Registre aqui todos os valores "app" encontrados:**

```
Valores de label "app" encontrados em Prometheus:
- app=database
- app=api
- app=cache
- app=web
- app=...
```

---

## 🗺️ Fase 2: MAPEAMENTO (Tabela de Correlação)

Agora emparelar o que encontrou:

| Prometheus "app" | Zabbix Host Group | Group ID | Aplicações/Hosts Inclusos |
|------------------|-------------------|----------|--------------------------|
| database | Databases | 11 | prod-db-01, prod-db-02, ... |
| api | API Servers | 12 | prod-api-01, prod-api-02, ... |
| cache | Cache Servers | 13 | prod-redis-01, prod-memcached-01, ... |
| web | Web Servers | 14 | prod-web-01, prod-web-02, ... |
| monitoring | Monitoring | 15 | prometheus, alertmanager, ... |

---

## 📝 Fase 3: DOCUMENTO DE MAPEAMENTO

**Arquivo a criar:** `MAPPING_PROMETHEUS_ZABBIX.md`

```yaml
# Mapeamento Prometheus → Zabbix

mapping:
  database:
    zabbix_group: "Databases"
    group_id: "11"
    prometheus_app_label: "app=database"
    hosts:
      - prod-db-01
      - prod-db-02
      - prod-db-03
    alerting_rules:
      - DatabaseSlowQueries
      - DatabaseConnectionPoolExhausted
      - DatabaseReplicationLag

  api:
    zabbix_group: "API Servers"
    group_id: "12"
    prometheus_app_label: "app=api"
    hosts:
      - prod-api-01
      - prod-api-02
    alerting_rules:
      - HTTPErrorRateHigh
      - HTTPSlowResponse

  cache:
    zabbix_group: "Cache Servers"
    group_id: "13"
    prometheus_app_label: "app=cache"
    hosts:
      - prod-redis-01
      - prod-memcached-01
    alerting_rules:
      - CacheHitRateLow
      - RedisPersistenceFailure

  web:
    zabbix_group: "Web Servers"
    group_id: "14"
    prometheus_app_label: "app=web"
    hosts:
      - prod-web-01
      - prod-web-02
    alerting_rules:
      - HighNetworkLatency
      - HighDiskUsage
```

---

## 🔗 Fase 4: IMPLEMENTAÇÃO (Próxima etapa)

Com este mapeamento pronto, podemos:

1. **Atualizar `sync_prometheus.py`** para usar `app` label
2. **Criar hosts automaticamente** no grupo correto
3. **Sincronizar regras** por grupo

Exemplo futura implementação:
```python
# Em production/sync_prometheus.py (futuro)

def map_app_to_group(app_label):
    """Mapeia app label para group_id"""
    mapping = {
        "database": "11",
        "api": "12",
        "cache": "13",
        "web": "14"
    }
    return mapping.get(app_label, "2")  # Fallback: default group

# Criar host no grupo correto
group_id = map_app_to_group(prometheus_alert.labels.get("app"))
create_host(hostname, group_id)
```

---

## 🎯 Seu Trabalho Agora

### ✅ TODO - ANÁLISE

- [ ] **Listar Host Groups Zabbix**
  ```bash
  # Comando para executar no seu servidor QUA
  # Registrar grupos em tabela acima
  ```

- [ ] **Listar Labels "app" do Prometheus PROD**
  ```bash
  # Comando para executar no seu servidor PROD
  # Registrar valores em tabela acima
  ```

- [ ] **Criar mapeamento completo**
  - Alinhar quais "app" labels existem
  - Com quais Host Groups devem ir

- [ ] **Documentar mapeamento**
  - Criar arquivo `MAPPING_PROMETHEUS_ZABBIX.md`
  - Com tabela YAML de correlação

- [ ] **Validar mapeamento**
  - Confirmar com time: "Está correto?"
  - "Faltou algum app/group?"

### ⏳ DEPOIS (Implementação)

1. Atualizar production/sync_prometheus.py com mapping
2. Testar sincronização com grupos
3. Validar que hosts vão para grupos corretos
4. Documentar para produção

---

## 📋 Checklist de Análise

```
ZABBIX (QUA):
☐ Acessível? http://seu-zabbix-qua:8080
☐ User/pass corretos? Admin/zabbix
☐ API funciona? Consegue listar hostgroups
☐ Listou todos os grupos? [ ] Sim [ ] Não
☐ Quantos grupos existem? _____

PROMETHEUS (PROD):
☐ Acessível? http://seu-prometheus-prod:9090
☐ Tem targets? Quantos? _____
☐ Alerting rules têm labels? [ ] Sim [ ] Não
☐ Encontrou label "app"? [ ] Sim [ ] Não
☐ Valores de "app" encontrados:
   - app=_______
   - app=_______
   - app=_______
```

---

## 💡 Exemplo Caso Real

**Se você tiver:**

Zabbix Groups:
- 10 = Linux servers
- 11 = Databases
- 12 = Applications
- 13 = Monitoring

Prometheus Labels (app):
- app=postgres (database)
- app=mysql (database)
- app=redis (cache)
- app=api (application)
- app=web (application)
- app=prometheus (monitoring)

**Mapeamento seria:**
```
app=postgres     → Database Group (11)
app=mysql        → Database Group (11)
app=redis        → Cache Group (novo ou Applications 12)
app=api          → Applications Group (12)
app=web          → Applications Group (12)
app=prometheus   → Monitoring Group (13)
```

---

## 📞 O que você precisa fazer AGORA

1. ✅ **Conectar em Zabbix QUA** via API
2. ✅ **Listar Host Groups** existentes
3. ✅ **Conectar em Prometheus PROD** via API
4. ✅ **Listar Labels "app"** encontradas
5. ✅ **Criar mapeamento** em tabela
6. ✅ **Documentar** em arquivo MAPPING_PROMETHEUS_ZABBIX.md
7. ✅ **Confirmar** com time/gestor

**Depois que tiver isso pronto**, posso:
- Implementar mapeamento no script
- Testar full pipeline
- Sincronizar para produção

---

**Quer que eu crie um script para automatizar essa análise?** 🚀
