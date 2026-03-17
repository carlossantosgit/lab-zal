# 🎯 Lab ZAL - Guia de Apresentação

Pronto para apresentar! 🚀

## ⚡ Quick Demo (5 Minutos)

### 1️⃣ Iniciar (30 segundos)

```bash
docker-compose up -d
```

### 2️⃣ Popular Dados de Demo (2-3 minutos)

```bash
python3 scripts/populate_demo_data.py
```

**Isso cria:**
- ✅ 4 hosts de exemplo (prod-db, api-server, cache-redis, app-web)
- ✅ 24 items (6 por host: CPU, Memory, Requests, Latency, Error Rate, Watchdog)
- ✅ 9 triggers (3 por host: High CPU, Low Memory, High Error Rate)
- ✅ Dados de teste realistas

### 3️⃣ Abrir Zabbix (1-2 minutos)

```bash
# Abrir no navegador
open http://localhost:8080

# Login
User: Admin
Password: zabbix
```

### 4️⃣ Navegar & Mostrar

```
Monitoring → Latest Data
```

**Você verá:**
- 🖥️ 4 hosts com dados realistas
- 📊 Items com valores atualizados
- ⚠️ Triggers prontos para disparar
- 📈 Dados de teste enviados

---

## 🎓 Apresentação Completa (15-20 Minutos)

### Slide 1: O Problema

> "Prometheus coleta métricas, Alert Manager roteia alertas, mas Zabbix precisa de hosts criados manualmente. E se pudéssemos automatizar tudo?"

### Slide 2: A Solução - Arquitetura

```
Prometheus (Coleta) →  Alert Manager (Roteamento) →  Webhook (Auto-Cria)  →  Zabbix (Storage)
```

### Slide 3: O que é Auto-Create?

Quando um alerta chega do Prometheus com um host desconhecido:

```
Webhook recebe alerta
    ↓
Verifica: Host existe em Zabbix?
    ↓
NÃO existe?
    ↓
CRIA automaticamente:
  - Host com interface configurada
  - 3 items padrão (CPU, Memory, Watchdog)
  - Pronto para receber dados!
```

### Slide 4: Demo Ao Vivo

```bash
# Terminal aberto, rodar:
python3 scripts/populate_demo_data.py

# Mostrar output:
✅ Host criado: prod-db-01 (ID: 10457)
  ✅ Item: prometheus.deadmansswitch
  ✅ Item: prometheus.highcpu
  ✅ Item: prometheus.lowmemory
  ✅ Item: custom.requests
  ✅ Item: custom.latency
  ✅ Item: custom.errors
✅ Trigger: High CPU Usage on {HOST.NAME}
✅ Trigger: Low Memory on {HOST.NAME}
✅ Trigger: High Error Rate on {HOST.NAME}
```

### Slide 5: Zabbix com Dados

Abrir http://localhost:8080 e mostrar:
- Hosts criados
- Items com dados
- Triggers configuradas
- Dashboard com dados realistas

### Slide 6: Fluxo Automático

```
1. Prometheus escruta node-exporter (com label zabbix_host=prod-db-01)
2. Alert Manager recebe e envia webhook
3. Webhook verifica e cria em Zabbix
4. Zabbix mostra dados em tempo real
5. Triggers disparam automaticamente
```

### Slide 7: Benefícios

✅ **Zero Manual:** Sem criar hosts manualmente em Zabbix
✅ **Escalável:** Adiciona quantos hosts quiser em Prometheus
✅ **Automático:** Tudo acontece quando alerta chega
✅ **Robusto:** API Zabbix valida tudo
✅ **Produção:** Testado e funcionando

### Slide 8: Tecnologia Stack

- 🐳 **8 Containers Docker:**
  - Prometheus
  - Alert Manager
  - Zabbix Server
  - Zabbix Web UI
  - PostgreSQL
  - Node Exporter
  - Webhook (Python Flask)
  - ZAL (Zabbix Alert Manager)

### Slide 9: Como Adicionar Novo Host

**Antes (Manual):**
1. Editar prometheus.yml
2. Restart Prometheus
3. Rodar setup_hosts.py
4. Possível rodar fix_all_items.py

**Agora (Automático):**
1. Editar prometheus.yml
2. Restart Prometheus
3. ✨ Webhook faz tudo quando alerta chega!

### Slide 10: Próximos Passos

- [ ] Customizar items criados automaticamente
- [ ] Criar Triggers mais inteligentes
- [ ] Integrar com Slack/Email
- [ ] Dashboard interativo no Zabbix
- [ ] Backup automático

---

## 🔑 Pontos-Chave para Mencionar

1. **Auto-Create Feature**
   - Detecta hosts desconhecidos via webhook
   - Cria automaticamente com 3 items padrão
   - Sem intervenção manual

2. **Escalabilidade**
   - Adicione quantos hosts quiser em Prometheus
   - Webhook cuida de tudo automaticamente
   - Suporta centenas de hosts

3. **Manutenção**
   - Scripts opcionais para gerenciamento
   - Fixar interfaces se necessário
   - Logs detalhados para debug

4. **Pronto para Produção**
   - Testado localmente
   - Documentação completa
   - GitHub privado

---

## 📱 Dicas de Apresentação

### Antes da Apresentação

1. ✅ Rodar `docker-compose up -d` (15 min antes)
2. ✅ Rodar `python3 scripts/populate_demo_data.py` (5 min antes)
3. ✅ Testar acesso: http://localhost:8080
4. ✅ Ter terminal aberto mostrando logs: `docker-compose logs webhook -f`

### Durante a Apresentação

1. **Mostrar Arquitetura:** 1-2 min
2. **Explicar Auto-Create:** 2-3 min
3. **Demo ao Vivo:** 5-10 min
   - Abrir Zabbix mostrando hosts/items
   - Mostrar triggers
   - Andar pelo dashboard
4. **Tecnologia:** 2-3 min
5. **Q&A:** 3-5 min

### Comandos Úteis

```bash
# Ver status de tudo
docker-compose ps

# Ver logs do webhook em tempo real
docker-compose logs webhook -f

# Testar alert manual
curl -X POST -H "Content-Type: application/json" \
  -d '{"alerts":[{"status":"firing","labels":{"alertname":"Test","zabbix_host":"novo-host"}}]}' \
  http://localhost:5001/alerts

# Ver hosts em Zabbix
python3 scripts/setup_hosts.py
```

---

## 📊 Dados de Demo Criados

**Hosts:**
- prod-db-01 (Production Database)
- api-server-01 (API Server)
- cache-redis-01 (Redis Cache)
- app-web-01 (Web Application)

**Items por Host (6 total):**
- prometheus.deadmansswitch (Watchdog - sempre 1)
- prometheus.highcpu (CPU > 50%)
- prometheus.lowmemory (RAM < 20%)
- custom.requests (HTTP Requests/sec)
- custom.latency (Response Time ms)
- custom.errors (Error Rate %)

**Triggers por Host (3 total):**
- High CPU Usage
- Low Memory
- High Error Rate

---

## ✅ Checklist Pré-Apresentação

- [ ] Docker rodando
- [ ] 8/8 containers UP
- [ ] Scripts populados
- [ ] Zabbix acessível (http://localhost:8080)
- [ ] Login Admin/zabbix funcionando
- [ ] 4 hosts visíveis em Latest Data
- [ ] Items com dados
- [ ] Triggers criadas
- [ ] Logs do webhook abertos
- [ ] Terminal pronto
- [ ] Apresentação salva/pronta
- [ ] Conexão de internet (se apresentar online)

---

## 🎬 Script da Apresentação

> "Boa noite! Hoje vou mostrar Lab ZAL - uma integração entre Prometheus, Alert Manager e Zabbix com uma feature especial: **auto-create de hosts**.
>
> **O Problema:** Prometheus coleta métricas, Alert Manager roteia alertas, mas Zabbix exigia criar cada host manualmente. Se você tem 100 hosts, era 100 vzes criando em Zabbix.
>
> **A Solução:** Nosso webhook agora **verifica se o host existe** quando um alerta chega, e se não existir, **cria automaticamente** com todos os items necessários. Zero manual!
>
> Vou mostrar isso funcionando agora..."

[Abrir navegador e mostrar Zabbix com dados]

"...Como podem ver, temos 4 hosts de produção aqui com dados realistas. Cada um tem items como CPU, Memory, Requests, Latency e Error Rate. E cada host tem triggers prontas para disparar.
>
> Tudo isso foi criado **automaticamente** quando o webhook recebeu alertas do Prometheus!
>
> Se eu adicione um novo host em Prometheus... [editar prometheus.yml rapidamente] ...em poucos minutos ele aparecerá aqui com todos os items já configurados!"

---

Bom uso na apresentação! 🎊
