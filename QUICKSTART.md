# 🚀 Quick Start - Lab ZAL (5-10 Minutos)

Para colocar Lab ZAL rodando em sua máquina do zero.

## ⚙️ Pré-requisitos

```bash
# Docker
docker --version
# Esperado: Docker version 20.10+ ou superior

# Docker Compose
docker-compose --version
# Esperado: Docker Compose version 1.29+ ou superior
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

### Git (recomendado)

```bash
git clone https://github.com/carlossantosgit/lab-zal.git
cd lab-zal
```

### ZIP

```bash
# Descarregar de: https://github.com/carlossantosgit/lab-zal/archive/refs/heads/main.zip
unzip lab-zal-main.zip
cd lab-zal-main
```

## 🚀 Iniciar (3 Passos)

### Passo 1: Verificar Docker

```bash
docker-compose ps
# Deve estar funcionando
```

### Passo 2: Iniciar Containers

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

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| **Zabbix Web** | http://localhost:8080 | Admin / zabbix |
| **Prometheus** | http://localhost:9090 | - |
| **Alert Manager** | http://localhost:9093 | - |
| **Webhook** | http://localhost:5001/health | - |

## ✨ Feature Principal: Auto-Create de Hosts

Quando um alerta chega do Prometheus com um host desconhecido, o webhook **cria automaticamente**:

```
Prometheus Alert com label: zabbix_host=novo-host
        ↓
Webhook recebe
        ↓
Verifica em Zabbix API: Host existe?
        ↓
NÃO? CRIA automaticamente:
  ✅ Host com interface configurada
  ✅ 3 items padrão (CPU, Memory, Watchdog)
  ✅ Pronto para receber dados!
```

### Teste Auto-Create

Enviar alerta via curl para testar:

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

**Resultado esperado:**
```
ok
```

**Verificar no Zabbix:**
1. Abrir http://localhost:8080
2. Login: Admin / zabbix
3. Monitoring → Latest Data
4. Filtrar por: "servidor-novo"
5. ✅ Host aparecerá com 3 items já criados!

**Verificar nos logs:**
```bash
docker-compose logs webhook -f

# Verá:
# INFO:root:🆕 Host 'servidor-novo' not found - creating...
# INFO:root:✅ Created host in Zabbix: servidor-novo
# INFO:root:✅ Created item: prometheus.deadmansswitch
# INFO:root:✅ Created item: prometheus.highcpu
# INFO:root:✅ Created item: prometheus.lowmemory
```

## 📊 Popular Dados de Demo (Para Apresentação)

Para ter dados realistas prontos para demonstração:

```bash
python3 scripts/populate_demo_data.py
```

Isso cria:
- ✅ 4 hosts: prod-db-01, api-server-01, cache-redis-01, app-web-01
- ✅ 24 items (6 por host): CPU, Memory, Requests, Latency, Error Rate, Watchdog
- ✅ 9 triggers (3 por host): High CPU, Low Memory, High Error Rate
- ✅ Dados de teste realistas

**Ver em Zabbix:**
```
http://localhost:8080
Monitoring → Latest Data
```

Você verá 4 hosts com dados realistas prontos para apresentação!

## ✅ Testar Tudo Funciona

### Teste 1: Conexão Zabbix

```bash
docker-compose exec webhook zabbix_sender \
  -z zabbix-server \
  -s "node-01" \
  -k "prometheus.test" \
  -o "999"

# Esperado:
# Response from "zabbix-server:10051": "processed: 1; failed: 0"
```

### Teste 2: Logs em Tempo Real

```bash
docker-compose logs webhook -f

# Verá logs do webhook processando
```

### Teste 3: Dados Realistas

```bash
python3 scripts/populate_demo_data.py

# Verá output com 4 hosts criados + items + triggers
```

## 📖 Próximos Passos

1. **Ler documentação completa:**
   ```bash
   cat README.md
   ```

2. **Ver guia de apresentação:**
   ```bash
   cat APRESENTACAO.md
   ```

3. **Ver logs em tempo real:**
   ```bash
   docker-compose logs -f
   ```

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
services:
  zabbix-web:
    ports:
      - "8081:8080"  # Usar 8081 em vez de 8080
```

### "Cannot connect to Zabbix"

```bash
# Ver se container está UP
docker-compose ps zabbix-server

# Ver logs
docker-compose logs zabbix-server

# Zabbix precisa de 30-60 segundos para inicializar
sleep 60
```

### "Auto-create não está funcionando"

```bash
# Ver logs do webhook
docker-compose logs webhook -f

# Procurar por:
# "✅ Created host" = funcionando
# "❌ Failed" = erro

# Testar conexão webhook-zabbix
docker-compose exec webhook zabbix_sender \
  -z zabbix-server -s "test" -k "test" -o "1"
```

## 🏗️ Arquitetura Rápida

```
Prometheus (9090)
    ↓ (coleta com label zabbix_host=...)
Alert Manager (9093)
    ↓ (webhook POST)
Webhook (5001) ✨ Auto-Create
    ↓
Zabbix Server (10051)
    ↓
Zabbix Web UI (8080)
    ↓
Você vê dados em tempo real!
```

## 💡 Dicas

- **Primeiro acesso Zabbix**: Esperar 2-3 minutos para DB inicializar
- **Ver métricas Prometheus**: Abrir http://localhost:9090/targets
- **Ver alertas**:http://localhost:9093/api/v2/alerts
- **Auto-create em ação**: `docker-compose logs webhook -f | grep "Created"`
- **Para apresentação**: `python3 scripts/populate_demo_data.py`

## 🎯 Para Apresentação

Guia completo de apresentação: **[APRESENTACAO.md](./APRESENTACAO.md)**

**Quick Demo (5-10 min):**
```bash
# Terminal 1
docker-compose up -d

# Terminal 2 (depois de 1-2 min)
python3 scripts/populate_demo_data.py

# Browser
open http://localhost:8080
# Login: Admin / zabbix
# Navegar: Monitoring → Latest Data
```

Pronto para impressionar! 🚀

## 📞 Precisa de Ajuda?

Verifique a documentação completa:
```bash
cat README.md          # Documentação completa
cat APRESENTACAO.md   # Guia de apresentação
```

Ver logs dos serviços:
```bash
docker-compose logs <service> -f

# Exemplos:
docker-compose logs prometheus
docker-compose logs zabbix-server
docker-compose logs webhook
docker-compose logs alertmanager
```

---

**Bom uso! 🎊**
