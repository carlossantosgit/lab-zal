# 📊 Explicação do analise_mapeamento.py

Script que **conecta em dois servidores** e extrai informações para criar **mapeamento**

---

## 🎯 O QUE ELE FAZ (Simples)

```
Conecta aqui          ←→          Conecta aqui
Zabbix (QUA)                   Prometheus (PROD)
   ↓                              ↓
Lista grupos:              Lista labels "app":
- Linux servers            - app=database
- Databases                - app=api
- API Servers              - app=cache
- Web Servers              - app=web
   ↓                              ↓
   └──────→ CRIA MAPEAMENTO ←────┘
```

**Resultado:** Tabela que você completa manualmente

---

## 📋 PASSO A PASSO

### PASSO 1️⃣: CONFIGURAÇÃO (editar no topo do arquivo)

```python
# Linha 22-26 - EDITE AQUI:

ZABBIX_API_URL = "http://seu-zabbix-qua:8080/api_jsonrpc.php"  ← URL de QUA
ZABBIX_USER = "Admin"
ZABBIX_PASSWORD = "zabbix"

PROMETHEUS_API_URL = "http://seu-prometheus-prod:9090"  ← URL de PRODUÇÃO
```

**É só você colocar suas URLs!**

---

### PASSO 2️⃣: EXECUÇÃO

```bash
python3 analise_mapeamento.py
```

Vai fazer **5 coisas em sequência:**

#### 1. CONECTAR em Zabbix (QUA)
```python
def get_zabbix_token():
    # Envia login + password
    # Retorna token para usar a API
    print("✅ Zabbix: Login bem-sucedido")
    return token
```

**Saída:**
```
✅ Zabbix: Login bem-sucedido
```

---

#### 2. LISTAR grupos em Zabbix
```python
def get_zabbix_hostgroups(token):
    # Usa token para pedir lista de grupos
    # Retorna: ID do grupo + Nome
    print(f"✅ Zabbix: 10 Host Groups encontrados")
    return [
        {"groupid": "10", "name": "Linux servers"},
        {"groupid": "11", "name": "Databases"},
        {"groupid": "12", "name": "API Servers"},
        ...
    ]
```

**Saída:**
```
✅ Zabbix: 10 Host Groups encontrados
```

---

#### 3. CONECTAR em Prometheus (PROD)
```python
def get_prometheus_targets():
    # Faz HTTP GET em Prometheus
    # Pede lista de targets (máquinas sendo monitoradas)
    print(f"✅ Prometheus: 50 targets encontrados")
    return [targets]
```

**Saída:**
```
✅ Prometheus: 50 targets encontrados
```

---

#### 4. EXTRAIR labels "app"
```python
def analyze_prometheus_labels(targets, rules):
    # Varre todos os targets
    # Encontra label "app" em cada um
    # AGRUPA por valor de "app"

    app_labels = {
        "database": ["prod-db-01", "prod-db-02", "prod-db-03"],
        "api": ["prod-api-01", "prod-api-02"],
        "cache": ["prod-redis-01"],
        "web": ["prod-web-01"]
    }
```

**Saída visual:**
```
📋 Labels 'app' encontrados em Prometheus:

  app='database'
    Quantidade: 3 targets
    Exemplos:
      - prod-db-01:5432
      - prod-db-02:5432
      - prod-db-03:5432

  app='api'
    Quantidade: 2 targets
    Exemplos:
      - prod-api-01:8080
      - prod-api-02:8080

  app='cache'
    Quantidade: 1 targets
    Exemplos:
      - prod-redis-01:6379

  app='web'
    Quantidade: 1 targets
    Exemplos:
      - prod-web-01:80
```

---

#### 5. GERA TABELAS

**Tabela 1: Grupos Zabbix existentes**
```
| Group ID | Group Name | Descrição |
|----------|-----------|-----------|
| 10       | Linux servers | |
| 11       | Databases     | |
| 12       | API Servers   | |
| 13       | Web Servers   | |
```

**Tabela 2: Mapeamento recomendado (para você completar)**
```
| Prometheus 'app' | Zabbix Group | Group ID | Targets |
|------------------|--------------|----------|---------|
| database         | [DEFINIR]    | [??]     |       3 |
| api              | [DEFINIR]    | [??]     |       2 |
| cache            | [DEFINIR]    | [??]     |       1 |
| web              | [DEFINIR]    | [??]     |       1 |
```

---

### PASSO 3️⃣: VOCÊ COMPLETA

O script mostra template YAML:

```yaml
mapping:
  database:
    zabbix_group: "[DEFINIR - qual grupo?]"
    group_id: "[DEFINIR - qual ID?]"
    prometheus_app_label: "app=database"
    hosts:
      - [liste hosts que usam app=database]
    alerting_rules:
      - [liste rules que monitoram app=database]

  api:
    zabbix_group: "[DEFINIR - qual grupo?]"
    group_id: "[DEFINIR - qual ID?]"
    prometheus_app_label: "app=api"
    hosts:
      - [liste hosts que usam app=api]
    alerting_rules:
      - [liste rules que monitoram app=api]
```

**Você preenche com:**
```yaml
mapping:
  database:
    zabbix_group: "Databases"      ← Você escolhe qual grupo
    group_id: "11"                  ← ID do grupo
    prometheus_app_label: "app=database"
    hosts:
      - prod-db-01
      - prod-db-02
      - prod-db-03
    alerting_rules:
      - DatabaseSlowQueries
      - DatabaseConnectionPoolExhausted

  api:
    zabbix_group: "API Servers"    ← Você escolhe qual grupo
    group_id: "12"                  ← ID do grupo
    prometheus_app_label: "app=api"
    hosts:
      - prod-api-01
      - prod-api-02
    alerting_rules:
      - HTTPErrorRateHigh
      - HTTPSlowResponse

  # ... etc para cache, web, etc
```

---

### PASSO 4️⃣: SALVA RESULTADO

O script cria arquivo: `analise_mapeamento_resultado.txt`

Com conteúdo:
```
# RESULTADO DA ANÁLISE DE MAPEAMENTO

## Zabbix Host Groups (10)

- Linux servers (ID: 10)
- Databases (ID: 11)
- API Servers (ID: 12)
- Web Servers (ID: 13)
- etc...

## Prometheus App Labels (4)

- app=database (3 targets)
- app=api (2 targets)
- app=cache (1 targets)
- app=web (1 targets)

## YAML Template

mapping:
  database:
    zabbix_group: "[DEFINIR - qual grupo?]"
    ...
```

---

## 🎯 RESUMO - O QUE VOCÊ PRECISA FAZER

```
1. Editar analise_mapeamento.py (linhas 22-26):
   ZABBIX_API_URL = "sua-qua-aqui"
   PROMETHEUS_API_URL = "sua-prod-aqui"

2. Executar:
   python3 analise_mapeamento.py

3. Ver saída na tela com:
   ✓ Seus grupos Zabbix
   ✓ Seus labels "app" do Prometheus
   ✓ Tabela de mapeamento vazia para preencher
   ✓ Template YAML

4. Copiar YAML da tela e completar
   Salvar em arquivo: MAPPING_PROMETHEUS_ZABBIX.md

5. PRONTO! Você tem mapeamento documentado
```

---

## 💡 EXEMPLO REAL

### SE você executar e receber:

```
✅ Zabbix: 12 Host Groups encontrados
✅ Prometheus: 45 targets encontrados

📋 Labels 'app' encontrados em Prometheus:

  app='postgres'
    Quantidade: 5 targets
    Exemplos:
      - db01:5432
      - db02:5432

  app='redis'
    Quantidade: 2 targets
    Exemplos:
      - cache01:6379

  app='api'
    Quantidade: 8 targets
    Exemplos:
      - api01:8080
      - api02:8080

  app='web'
    Quantidade: 5 targets
    Exemplos:
      - web01:80
      - web02:80
```

### VOCÊ FAZ:

```yaml
mapping:
  postgres:
    zabbix_group: "Databases"          ← Você escolhe
    group_id: "5"                        ← Viu na lista acima
    hosts:
      - db01
      - db02
      - db03
      - db04
      - db05

  redis:
    zabbix_group: "Cache Servers"      ← Você escolhe
    group_id: "8"                        ← Viu na lista acima
    hosts:
      - cache01
      - cache02

  api:
    zabbix_group: "API Servers"        ← Você escolhe
    group_id: "3"                        ← Viu na lista acima
    hosts:
      - api01
      - api02
      - api03
      - api04
      - api05
      - api06
      - api07
      - api08

  web:
    zabbix_group: "Web Servers"        ← Você escolhe
    group_id: "7"                        ← Viu na lista acima
    hosts:
      - web01
      - web02
      - web03
      - web04
      - web05
```

---

## ✅ RESULTADO FINAL

Arquivo `MAPPING_PROMETHEUS_ZABBIX.md` cria "dicionário" que diz:

```
"Quanto você vir um alerta com app=postgres,
 crie o host no grupo 'Databases' (ID: 5)"

"Quanto você vir um alerta com app=redis,
 crie o host no grupo 'Cache Servers' (ID: 8)"

etc...
```

Depois disso, `sync_prometheus.py` usa este mapeamento para:
- Ler label "app" do alerta
- Procurar grupo correto no mapeamento
- Criar host naquele grupo
- Sincronizar regras para aquele host

---

## 📊 FLUXO COMPLETO

```
1. python3 analise_mapeamento.py
        ↓
2. [Você preenche YAML]
        ↓
3. MAPPING_PROMETHEUS_ZABBIX.md criado
        ↓
4. python3 sync_prometheus.py --all
   (usará mapeamento para criar hosts nos grupos certos)
        ↓
5. ✅ Hosts em Zabbix nos grupos corretos!
```

---

**É basicamente:**
1. Script **vê** o que existe (grupos + labels)
2. **Mostra pra você** em tabelas
3. **Você completa** o mapeamento (qual app → qual grupo)
4. **Depois** o script de sync usa esse mapeamento

**Simples assim!** 👍
