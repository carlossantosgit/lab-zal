# 🚀 Quick Start - Lab ZAL

Para rodar este projeto noutra máquina do zero.

## ⚙️ Pré-requisitos

Verifique se tem instalado:

```bash
# Docker
docker --version
# Esperado: Docker version 20.10+ (ou superior)

# Docker Compose
docker-compose --version
# Esperado: Docker Compose version 1.29+ (ou superior)
```

### Instalar Docker (se não tiver)

**macOS:**
```bash
brew install docker docker-compose
# ou descarregar Docker Desktop: https://www.docker.com/products/docker-desktop
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker $USER
newgrp docker
```

**Windows:**
- Descarregar Docker Desktop: https://www.docker.com/products/docker-desktop
- Executar no PowerShell/CMD

## 📥 Descarregar o Projeto

### Opção 1: Git (recomendado)

```bash
git clone https://github.com/carlossantosgit/lab-zal.git
cd lab-zal
```

### Opção 2: Descarregar ZIP

```bash
# Descarregar: https://github.com/carlossantosgit/lab-zal/archive/refs/heads/main.zip
unzip lab-zal-main.zip
cd lab-zal-main
```

## 🚀 Iniciar (3 passos simples)

### Passo 1: Verificar Docker

```bash
docker-compose ps
# Deve estar funcionando
```

### Passo 2: Iniciar os Serviços

```bash
docker-compose up -d
```

**Esperado (depois de ~30 segundos):**
```
✅ Creating network "lab-zal_lab" with driver "bridge"
✅ Container lab-zal-postgres-1 Created
✅ Container lab-zal-prometheus-1 Created
✅ Container lab-zal-alertmanager-1 Created
✅ Container lab-zal-webhook-1 Created
✅ Container lab-zal-zabbix-server-1 Created
✅ Container lab-zal-zabbix-web-1 Created
✅ Container lab-zal-node-exporter-1 Created
✅ Container lab-zal-zal-1 Created
```

### Passo 3: Verificar Status

```bash
docker-compose ps

# Esperado: 8/8 containers UP
```

## 🌐 Aceder aos Serviços

Abrir no navegador:

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| **Zabbix Web** | http://localhost:8080 | Admin / zabbix |
| **Prometheus** | http://localhost:9090 | - |
| **Alert Manager** | http://localhost:9093 | - |
| **Webhook** | http://localhost:5001/health | - |

## ✨ Recurso Principal: Auto-Create de Hosts

### O que é?

Quando um alerta chega do Prometheus, o webhook **cria automaticamente** o host em Zabbix:

```
Prometheus Alert → Webhook verifica → Host não existe?
→ Cria host + 3 items automaticamente ✨
```

**Sem necessidade de rodar scripts manuais!**

### Teste o Auto-Create

1. **Enviar alerta para host novo:**

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "alerts": [
      {
        "status": "firing",
        "labels": {
          "alertname": "TestAlert",
          "zabbix_host": "servidor-novo",
          "severity": "critical"
        }
      }
    ]
  }' \
  http://localhost:5001/alerts
```

2. **Ver em Zabbix** (http://localhost:8080):
   - Monitoring → Latest Data
   - Filtrar por: `servidor-novo`
   - ✅ Host aparecerá com 3 items já criados!

3. **Ver nos logs:**

```bash
docker-compose logs webhook | grep "servidor-novo"

# Verá mensagens como:
# "🆕 Host 'servidor-novo' not found - creating..."
# "✅ Created host in Zabbix: servidor-novo"
# "✅ Created item: prometheus.highcpu"
```

## ✅ Testar que Tudo Funciona

### Teste 1: Zabbix Conectado

```bash
docker-compose exec webhook zabbix_sender \
  -z zabbix-server \
  -s "node-01" \
  -k "prometheus.test" \
  -o "999"
```

**Esperado:**
```
Response from "zabbix-server:10051": "processed: 1; failed: 0; total: 1"
```

### Teste 2: Ver Logs em Tempo Real

```bash
docker-compose logs webhook -f

# Verá logs do webhook processando alertas
```

### Teste 3: Auto-Create em Ação

```bash
# Enviar alerta para 3 hosts novos
for host in "api-server" "db-prod" "cache-01"; do
  curl -s -X POST -H "Content-Type: application/json" \
    -d "{\"alerts\":[{\"status\":\"firing\",\"labels\":{\"alertname\":\"Test\",\"zabbix_host\":\"$host\"}}]}" \
    http://localhost:5001/alerts
done

# Esperar 2 segundos
sleep 2

# Verificar em Zabbix
docker-compose exec webhook zabbix_sender \
  -z zabbix-server \
  -s "api-server" \
  -k "prometheus.test" \
  -o "1"
```

## 🔧 Setup Inicial (OPCIONALMENTE)

Se quiser criar hosts **antes** de enviar alertas:

```bash
cd scripts
python3 setup_hosts.py
```

**Nota:** Isto é **OPCIONAL**! O webhook cria automaticamente quando recebe alertas.

## 📖 Próximos Passos

1. **Ler documentação completa:**
   ```bash
   cat README.md
   ```

2. **Ver logs em tempo real:**
   ```bash
   docker-compose logs -f
   ```

3. **Adicionar novo host em Prometheus:**
   - Editar `prometheus/prometheus.yml`
   - Adicionar scrape job com label `zabbix_host`
   - Recarregar: `docker-compose restart prometheus`
   - Esperar alerta → Host criado automaticamente em Zabbix! ✨

4. **Parar os serviços:**
   ```bash
   docker-compose down
   ```

5. **Remover tudo (incluindo dados):**
   ```bash
   docker-compose down -v
   ```

## ❌ Troubleshooting

### "Permission denied while trying to connect to Docker daemon"

**Solução (Linux):**
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### "Port 8080 already in use"

**Solução:** Mude a porta em `docker-compose.yml`:
```yaml
ports:
  - "8081:8080"  # Usar 8081 em vez de 8080
```

### "Cannot connect to Zabbix"

**Verificar:**
```bash
# Ver se container está UP
docker-compose ps zabbix-server

# Ver logs
docker-compose logs zabbix-server

# Esperar 30-60 segundos (init do Zabbix é lento)
```

### "Auto-create não está funcionando"

**Verificar:**
```bash
# Ver logs do webhook
docker-compose logs webhook -f

# Procurar por:
# "✅ Created host" (sucesso)
# "❌ Failed to create host" (erro)

# Se houver erro, pode tentar corrigir interfaces:
cd scripts
python3 fix_all_items.py
```

### "Host criado mas sem items"

```bash
cd scripts
python3 fix_all_items.py
```

## 📊 Arquitetura Rápida

```
┌─────────────┐      ┌──────────────┐      ┌──────────┐      ┌────────────┐
│ Prometheus  │ ───→ │ Alert Manager│ ───→ │ Webhook  │ ───→ │   Zabbix   │
│  (Coleta)   │      │ (Roteamento) │      │(Auto-Cria)      │  (Storage) │
└─────────────┘      └──────────────┘      └──────────┘      └────────────┘
     9090                  9093              ✨ AUTO-CREATE    10051/8080
```

## 💡 Dicas

- **Primeiro acesso Zabbix**: Esperar 2-3 minutos para DB inicializar
- **Ver métricas em tempo real**: `curl http://localhost:9090/api/v1/targets`
- **Ver alertas**: `curl http://localhost:9093/api/v2/alerts`
- **Logs em tempo real**: `docker-compose logs -f`
- **Auto-create em ação**: `docker-compose logs webhook -f | grep "Created host"`

## 📞 Precisa de Ajuda?

Verifique a documentação completa:
```bash
cat README.md
```

Ou check dos logs dos serviços:
```bash
docker-compose logs <service>
# Exemplos:
docker-compose logs prometheus
docker-compose logs zabbix-server
docker-compose logs webhook
docker-compose logs alertmanager
```

---

**Bom uso! 🚀✨**
