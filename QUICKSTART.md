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
git clone https://github.com/your-org/lab-zal.git
cd lab-zal
```

### Opção 2: Descarregar ZIP

```bash
# Descarregar: https://github.com/your-org/lab-zal/archive/refs/heads/main.zip
unzip lab-zal-main.zip
cd lab-zal-main
```

## 🚀 Iniciar (3 passos)

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

# Esperado:
# NAME                      STATUS            PORTS
# lab-zal-alertmanager-1    Up 2 minutes      0.0.0.0:9093->9093/tcp
# lab-zal-node-exporter-1   Up 2 minutes      0.0.0.0:9100->9100/tcp
# lab-zal-postgres-1        Up 2 minutes      5432/tcp
# lab-zal-prometheus-1      Up 2 minutes      0.0.0.0:9090->9090/tcp
# lab-zal-webhook-1         Up 2 minutes      0.0.0.0:5001->5001/tcp
# lab-zal-zabbix-server-1   Up 2 minutes      0.0.0.0:10051->10051/tcp
# lab-zal-zabbix-web-1      Up 2 minutes      0.0.0.0:8080->8080/tcp (healthy)
# lab-zal-zal-1             Up 2 minutes      0.0.0.0:9095->9095/tcp
```

## 🌐 Aceder aos Serviços

Abrir no navegador:

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| **Zabbix Web** | http://localhost:8080 | Admin / zabbix |
| **Prometheus** | http://localhost:9090 | - |
| **Alert Manager** | http://localhost:9093 | - |
| **Webhook** | http://localhost:5001/health | - |

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

### Teste 2: Ver Logs

```bash
docker-compose logs webhook -f
```

**Você verá logs como:**
```
webhook-1 | 127.0.0.1 - - [16/Mar/2026 23:04:53] "GET /health HTTP/1.1" 200
```

## 🔧 Setup Inicial (One-Time)

Se for a primeira vez, precisa de criar os hosts no Zabbix:

```bash
cd scripts
python3 setup_hosts.py
```

**Esperado:**
```
✅ Logged in
✅ Created host: prometheus-server (ID: 10439)
  ✅ Created item: prometheus.deadmansswitch
  ✅ Created item: prometheus.highcpu
  ✅ Created item: prometheus.lowmemory
✅ Setup completed!
```

## 📖 Próximos Passos

1. **Ler documentação:**
   ```bash
   cat README.md
   ```

2. **Ver status em tempo real:**
   ```bash
   docker-compose logs -f
   ```

3. **Parar os serviços:**
   ```bash
   docker-compose down
   ```

4. **Remover tudo (incluindo dados):**
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

### "Webhook não conecta a Zabbix"

**Verificar:**
```bash
# Ver logs do webhook
docker-compose logs webhook

# Testar manualmente
docker-compose exec webhook zabbix_sender -z zabbix-server -s "test" -k "test" -o "1"
```

## 📊 Estrutura do Projeto

```
lab-zal/
├─ README.md              ← Documentação completa
├─ QUICKSTART.md          ← Este ficheiro
├─ docker-compose.yml     ← Configuração
├─ prometheus/            ← Coleta de métricas
├─ alertmanager/          ← Roteamento de alertas
├─ webhook/               ← Mapeamento dinâmico
├─ zal/                   ← Zabbix AlertManager
└─ scripts/               ← Setup & manutenção
```

## 🎯 Fluxo de Dados

```
Prometheus (coleta)
    ↓
Alert Manager (roteamento)
    ↓
Webhook (mapeamento)
    ↓
Zabbix (armazenamento)
    ↓
Zabbix UI (visualização)
```

## 💡 Dicas

- **Primeiro acesso Zabbix**: Esperar 2-3 minutos para DB inicializar
- **Ver métricas em tempo real**: `curl http://localhost:9090/api/v1/targets`
- **Ver alertas**: `curl http://localhost:9093/api/v2/alerts`
- **Logs em tempo real**: `docker-compose logs -f`

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

**Bom uso! 🚀**
