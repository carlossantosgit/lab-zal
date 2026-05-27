# Lab IA Assistente — Zabbix + Grafana + AI

Assistente de infraestrutura por linguagem natural (português) que executa ações reais no Zabbix e Grafana.

## O que faz

- **Diagnóstico**: lista problemas ativos, verifica estado de hosts, mostra triggers/items
- **Remediação inteligente**: detecta o tipo de problema e aplica o fix correto (ativa monitorização interna, coloca em manutenção, reconhece alertas)
- **Criação**: triggers, items, templates, hosts no Zabbix; dashboards (overview, CPU, memory, disk, network, gerencial) no Grafana
- **Gestão**: elimina dashboards, desativa/ativa triggers, remove hosts

## Pré-requisitos

- Docker Desktop em execução
- Portas livres: `3000`, `3001`, `8001`, `8080`, `10050`, `10051`, `11434`

## Arranque rápido

```bash
cd lab-ia-assistente

# 1. Subir todos os serviços
docker compose up -d

# 2. Aguardar ~60s para o Zabbix inicializar, depois puxar o modelo LLM
docker compose exec ollama ollama pull mistral

# 3. Aceder à interface
#    Frontend AI:  http://localhost:3000  → aba "AI Assistant"
#    Zabbix:       http://localhost:8080  → Admin / zabbix
#    Grafana:      http://localhost:3001  → admin / admin
```

## Após o primeiro arranque — configurar interface do agente

O Zabbix server precisa de saber que o agente corre no container `zabbix-agent`.
Aceder a Zabbix → Configuration → Hosts → Zabbix server → Interfaces
e mudar de `127.0.0.1` para DNS: `zabbix-agent`.

**Ou via curl (automático):**
```bash
# Obter token
TOKEN=$(curl -s -X POST http://localhost:8080/api_jsonrpc.php \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"user.login","params":{"user":"Admin","password":"zabbix"},"id":1}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['result'])")

# Atualizar interface
curl -s -X POST http://localhost:8080/api_jsonrpc.php \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"hostinterface.update\",\"params\":{\"interfaceid\":\"1\",\"ip\":\"\",\"dns\":\"zabbix-agent\",\"useip\":0,\"port\":\"10050\"},\"auth\":\"$TOKEN\",\"id\":2}"
```

## Exemplos de comandos no chat

```
# Diagnóstico
"Quais os problemas ativos?"
"Pode ver se tem dashboard no Grafana?"
"Estado do host Zabbix server"

# Remediação
"Arranja todos os problemas ativos"
"Corrige o problema do Zabbix server"

# Criação
"Preciso de um dashboard padrão gerencial"
"Cria um dashboard de CPU"
"Cria um trigger de CPU > 90% no host Zabbix server com severidade High"
"Cria um host chamado web01 com IP 192.168.1.10"

# Gestão
"Lista os hosts do Zabbix"
"Mostra os triggers do host Zabbix server"
"Pode excluir os dashboards do Grafana?"
"Desativa o trigger de CPU no host Zabbix server"
```

## Serviços e portas

| Serviço        | URL                        | Credenciais       |
|----------------|----------------------------|-------------------|
| Frontend AI    | http://localhost:3000      | —                 |
| AI Backend API | http://localhost:8001/docs | —                 |
| Zabbix Web     | http://localhost:8080      | Admin / zabbix    |
| Grafana        | http://localhost:3001      | admin / admin     |
| Ollama         | http://localhost:11434     | —                 |

## Estrutura

```
lab-ia-assistente/
├── docker-compose.yml          ← todos os serviços num só ficheiro
├── backend/                    ← FastAPI + Python (engine de IA)
│   └── app/
│       ├── services/
│       │   ├── assistant_engine.py   ← classificador NLU + handlers
│       │   ├── zabbix_manager.py     ← cliente Zabbix API
│       │   └── grafana_client.py     ← cliente Grafana API
│       └── api/
│           └── assistant.py          ← endpoints REST
├── frontend/                   ← React (chat UI)
│   └── src/components/
│       ├── Assistant.jsx             ← componente principal
│       └── Assistant.css
├── db/                         ← schema SQL inicial
└── configs/
    ├── grafana/provisioning/   ← datasource Prometheus auto-provisionado
    └── zabbix-agent/           ← configuração do agente Zabbix
```

## Paragem e limpeza

```bash
# Parar sem apagar dados
docker compose stop

# Parar e remover containers (mantém volumes/dados)
docker compose down

# Apagar tudo incluindo dados
docker compose down -v
```
