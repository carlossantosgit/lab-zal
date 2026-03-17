# 🚀 Sincronização Prometheus → Zabbix - Produção

Script para sincronizar regras Prometheus com Zabbix em ambiente de produção.

**Versão:** 1.0
**Status:** Pronto para QUA e Produção
**Data:** Março 2026

---

## 📋 O que Faz

Sincroniza automaticamente as **alerting rules** do Prometheus com Zabbix criando:
- ✅ **Items** - um por cada rule Prometheus
- ✅ **Triggers** - com severidades mapeadas corretamente

**Fluxo:**
```
Prometheus Rules (32+ regras)
        ↓
Webhook ou Script de Sync
        ↓
Zabbix Items + Triggers criadas
```

---

## 🔧 Instalação

### Pré-requisitos

- Python 3.7+
- Acesso ao Zabbix API
- Acesso ao Prometheus API
- `pip` (gerenciador de pacotes Python)

### Passo 1: Copiar arquivos para servidor

```bash
# No servidor QUA/Prod
mkdir -p /opt/prometheus-zabbix-sync
cd /opt/prometheus-zabbix-sync

# Copiar os arquivos
scp -r production/* usuario@qua-server:/opt/prometheus-zabbix-sync/
```

### Passo 2: Instalar dependências

```bash
cd /opt/prometheus-zabbix-sync

# Criar ambiente virtual (recomendado)
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### Passo 3: Configurar variáveis de ambiente

```bash
# Abrir config.py e ajustar URLs e credenciais
# Ou usar variáveis de ambiente:

export ZABBIX_API_URL="http://zabbix-server:8080/api_jsonrpc.php"
export ZABBIX_USER="Admin"
export ZABBIX_PASSWORD="sua-senha"
export PROMETHEUS_API_URL="http://prometheus:9090"
```

---

## 🎯 Uso

### 1️⃣ Validar Configuração

```bash
python3 validate.py
```

**Saída esperada:**
```
✅ Prometheus OK
✅ Zabbix OK
✅ 32 alerting rules encontradas
✅ 10 hosts encontrados em Zabbix
✅ VALIDAÇÃO OK - Sistema pronto!
```

### 2️⃣ Sincronizar Hosts

```bash
# Ver todos os hosts
python3 sync_prometheus.py --list

# Sincronizar um host específico
python3 sync_prometheus.py --host prod-db-01

# Sincronizar todos os hosts
python3 sync_prometheus.py --all

# Modo verbose (mais detalhes)
python3 sync_prometheus.py --all --verbose
```

**Saída esperada:**
```
✅ Login Zabbix bem-sucedido
✅ Obtidas 32 regras do Prometheus

📋 10 hosts encontrados:
  • prod-db-01 (ID: 10451)
  • api-server-01 (ID: 10452)
  ...

🔄 Sincronizando...
✅ prod-db-01: 32 items, 32 triggers
✅ api-server-01: 32 items, 32 triggers
...

✅ Total: 320 items, 320 triggers
```

---

## ⏰ Automação com Cron

### Adicionar sincronização automática

```bash
# Abrir crontab
crontab -e

# Sincronizar a cada hora
0 * * * * cd /opt/prometheus-zabbix-sync && python3 sync_prometheus.py --all >> /var/log/prometheus-sync.log 2>&1

# Validar a cada 6 horas
0 */6 * * * python3 /opt/prometheus-zabbix-sync/validate.py >> /var/log/prometheus-validate.log 2>&1
```

---

## 🔍 Troubleshooting

### Erro: "Connection refused"

```bash
# Testar Zabbix
curl http://zabbix-server:8080

# Testar Prometheus
curl http://prometheus:9090/-/healthy
```

### Erro: "Invalid credentials"

```bash
# Verificar usuário/senha em config.py
# Testar manualmente:
curl -X POST http://zabbix-server:8080/api_jsonrpc.php \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"user.login","params":{"user":"Admin","password":"zabbix"},"id":1}'
```

### Erro: "Item already exists"

```bash
# Normal! Não cria duplicatas (idempotente)
# Continua sincronizando outros items
```

---

## 📊 Configuração em Production

### Arquivo de Configuração

Editar `config.py`:

```python
# URLs
ZABBIX_API_URL = "http://zabbix-prod:8080/api_jsonrpc.php"
PROMETHEUS_API_URL = "http://prometheus-prod:9090"

# Credenciais
ZABBIX_USER = "seu-usuario"
ZABBIX_PASSWORD = "sua-senha"

# Severidades (não mudar, padrão Zabbix)
SEVERITY_MAP = {
    "info": 0,
    "warning": 2,
    "critical": 4,
}
```

### Systemd Service (Opcional)

```bash
# Criar arquivo /etc/systemd/system/prometheus-sync.service

[Unit]
Description=Prometheus → Zabbix Sync
After=network.target

[Service]
Type=oneshot
User=prometheus-sync
ExecStart=/opt/prometheus-zabbix-sync/venv/bin/python3 /opt/prometheus-zabbix-sync/sync_prometheus.py --all
StandardOutput=append:/var/log/prometheus-sync.log
StandardError=append:/var/log/prometheus-sync.log

[Install]
WantedBy=multi-user.target

# Ativar
sudo systemctl daemon-reload
sudo systemctl enable prometheus-sync.service
```

---

## 📈 Monitoramento

### Ver logs

```bash
# Logs em tempo real
tail -f /var/log/prometheus-sync.log

# Procurar erros
grep "ERROR" /var/log/prometheus-sync.log

# Última execução
tail -20 /var/log/prometheus-sync.log
```

### Verificar items criados

```bash
# Contar items no Zabbix
curl -s http://zabbix-server:8080/api_jsonrpc.php \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"item.get","params":{"search":{"key_":"prometheus.%"}},"auth":"<token>","id":1}' \
  | jq '.result | length'
```

---

## 🔐 Segurança

### Recomendações

1. **Use variáveis de ambiente** para credenciais:
   ```bash
   export ZABBIX_PASSWORD=$(cat /etc/secrets/zabbix-password)
   ```

2. **Proteja permissões dos arquivos:**
   ```bash
   chmod 600 config.py
   chmod 700 sync_prometheus.py
   ```

3. **Use SSH para comunicação:**
   ```python
   # Em production, considere usar SSH tunnels
   # ou VPN para conectar a Zabbix/Prometheus
   ```

4. **Auditar execuções:**
   ```bash
   # Logs com usuário/timestamp
   # Armazenar em local seguro
   ```

---

## 📝 Referência de Comandos

```bash
# Instalação
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Uso
python3 validate.py                    # Validar config
python3 sync_prometheus.py --list      # Ver hosts
python3 sync_prometheus.py --all       # Sincronizar tudo
python3 sync_prometheus.py --host <name>  # Host específico

# Cron
0 * * * * cd /path && python3 sync_prometheus.py --all
```

---

## ✅ Checklist de Deployment

- [ ] Python 3.7+ instalado
- [ ] `requests` instalado (`pip install -r requirements.txt`)
- [ ] URLs de Zabbix/Prometheus configuradas em `config.py`
- [ ] Credenciais Zabbix configuradas
- [ ] `python3 validate.py` retorna OK
- [ ] Primeira sincronização testada: `python3 sync_prometheus.py --all --verbose`
- [ ] Items criados verificados no Zabbix
- [ ] Cron job configurado (se automação desejada)
- [ ] Logs configurados e testados
- [ ] Backups registrados

---

## 🚀 Próximos Passos

1. ✅ Instalar em QUA
2. ✅ Testar com hosts de teste
3. ✅ Ajustar conforme necessário
4. ✅ Ir para Produção

---

## 📞 Suporte

- **Docs completas:** Veja `PRODUCTION_README.md`
- **Erros comuns:** Ver seção Troubleshooting
- **Git repo:** https://github.com/carlossantosgit/lab-zal

---

**Desenvolvido:** Março 2026
**Versão:** 1.0 - Production Ready
