# Sincronização Prometheus → Zabbix

Sincroniza alertas ativos do Prometheus para o Zabbix usando um host único com items parametrizados, enviando valores via Zabbix Trapper.

---

## Ficheiros

```
production/
├── Dockerfile              imagem base python:3.11-slim
├── docker-compose.yml      definição do serviço
├── scheduler.py            loop interno (--all cada 5 min, --push cada 1 min)
├── config.py               credenciais via env vars (com defaults Dev)
├── sync_prometheus.py      lógica principal
├── validate.py             validação de conectividade
├── requirements.txt        dependências Python
├── .env.example            template para sobrepor configuração
├── CONTAINER_GUIDE.md      guia completo de Docker
└── SYNC_GUIDE.md           arquitetura e operação detalhada
```

---

## Arranque Rápido

Não é necessário criar nenhum ficheiro de configuração — as credenciais Dev já estão nos defaults do `config.py`.

```bash
cd production
docker compose up -d --build
docker compose logs -f
```

Para outros ambientes (Prod, Staging) ver [CONTAINER_GUIDE.md](CONTAINER_GUIDE.md).

---

## Comandos do Script

O `sync_prometheus.py` pode ser executado manualmente dentro do container:

```bash
# Sincronizar estrutura (cria host, items, triggers) — idempotente
docker compose exec prometheus-zabbix-sync python sync_prometheus.py --all

# Enviar valores dos alertas ativos via Zabbix Trapper
docker compose exec prometheus-zabbix-sync python sync_prometheus.py --push

# Validar conectividade
docker compose exec prometheus-zabbix-sync python validate.py
```

---

## Arquitetura

- **1 host único** chamado `prometheus` no Zabbix
- **Items parametrizados** por alerta e instância:
  ```
  prom.alert.status[alertname,instance]
  prom.alert.severity[alertname,instance]
  prom.alert.summary[alertname,instance]
  prom.alert.payload[alertname,instance]
  ```
- **Triggers** com expressão baseada no `status` e tags dos labels do Prometheus
- **Push** via protocolo Zabbix Trapper (TCP socket direto, sem `zabbix_sender`)

---

**Para detalhes:** ver [CONTAINER_GUIDE.md](CONTAINER_GUIDE.md) e [SYNC_GUIDE.md](SYNC_GUIDE.md)
