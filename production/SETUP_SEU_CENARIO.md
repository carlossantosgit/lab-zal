# 🚀 Setup Production - Seu Cenário

**Configuração Real:**
```
Zabbix QUA (sua máquina)
        ↑
        │ sincronização
        ↓
Scripts Python (em QUA)
        ↑
        │ consulta regras
        ↓
Prometheus PRODUÇÃO (já rodando)
```

---

## 📋 Passo a Passo - SEU Cenário

### 1️⃣ Copiar scripts para QUA

```bash
# Na sua máquina QUA
scp -r production/ seu-usuario@qua:/home/seu-usuario/prometheus-sync/

# Ou manualmente:
# Copie arquivos de production/ via SCP/FTP/Git
```

### 2️⃣ Configurar URLs (AQUI É O IMPORTANTE!)

```bash
# No arquivo production/config.py

# ✅ ZABBIX - está em QUA (localhost?)
ZABBIX_API_URL = "http://localhost:8080/api_jsonrpc.php"
# ou
ZABBIX_API_URL = "http://seu-zabbix-qua:8080/api_jsonrpc.php"

# ✅ PROMETHEUS - está em PRODUÇÃO (remoto)
PROMETHEUS_API_URL = "http://seu-prometheus-prod.com.br:9090"
# ou
PROMETHEUS_API_URL = "http://10.0.1.50:9090"  # IP do servidor PROD

# Credenciais Zabbix
ZABBIX_USER = "Admin"
ZABBIX_PASSWORD = "zabbix"
```

### 3️⃣ Instalar Python + dependências em QUA

```bash
cd /home/seu-usuario/prometheus-sync

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar
pip install -r requirements.txt
```

### 4️⃣ Validar conexão

```bash
python3 validate.py
```

Deve retornar:
```
✅ Prometheus OK (conectou em PROD)
✅ Zabbix OK (conectou em QUA)
✅ 32+ alerting rules encontradas (em PROD)
✅ 10 hosts em Zabbix (em QUA)
✅ VALIDAÇÃO OK!
```

### 5️⃣ Sincronizar

```bash
# Ver hosts em Zabbix QUA
python3 sync_prometheus.py --list

# Sincronizar um host
python3 sync_prometheus.py --host seu-host-qua

# Sincronizar todos
python3 sync_prometheus.py --all
```

---

## 🔗 URLs Corretas - Ajuste Conforme

```python
# Se Zabbix está NA MESMA MÁQUINA QUA
ZABBIX_API_URL = "http://localhost:8080/api_jsonrpc.php"

# Se Zabbix está em outra máquina
ZABBIX_API_URL = "http://10.x.x.x:8080/api_jsonrpc.php"

# Se Prometheus está em servidor distante (PROD)
PROMETHEUS_API_URL = "http://prometheus.prod.interno:9090"

# Se Prometheus está noutra rede (SSH tunnel)
# veja config.example.py - SSH Tunnel section
```

---

## ⏰ Automação em QUA

```bash
# No servidor QUA, adicionar ao crontab para sincronizar a cada hora
0 * * * * cd /home/seu-usuario/prometheus-sync && source venv/bin/activate && python3 sync_prometheus.py --all
```

---

## ⚡ TL;DR - Rápido

```bash
# 1. Copiar
scp -r production/ seu-usuario@qua:/home/seu-usuario/prometheus-sync/

# 2. Configurar
cd /home/seu-usuario/prometheus-sync
nano config.py
# Editar: PROMETHEUS_API_URL e ZABBIX_API_URL

# 3. Validar
python3 -m venv venv && source venv/bin/activate && pip install requests
python3 validate.py

# 4. Sincronizar
python3 sync_prometheus.py --all

# ✅ Pronto!
```

---

## 🎯 Sua Situação Específica

É UMA CONEXÃO SIMPLES:

```
┌──────────────────────┐
│  Zabbix QUA          │
│  (sua máquina)       │
└──────────┬───────────┘
           │
     script Python
    (seu-usuario@qua)
           │
┌──────────▼───────────┐
│  Prometheus PROD     │
│  (já rodando)        │
└──────────────────────┘
```

**Scripts vão:**
1. Conectar no Prometheus PROD via HTTP
2. Ler as 32+ alerting rules
3. Sincronizar como items/triggers em Zabbix QUA

**Sem nenhum container novo!**

---

## ✅ Checklist

- [ ] Python 3 instalado em QUA
- [ ] `production/` copiado para QUA
- [ ] URLs corretas em `config.py`
  - [ ] Zabbix QUA está acessível
  - [ ] Prometheus PROD está acessível
- [ ] `python3 validate.py` retorna OK
- [ ] `python3 sync_prometheus.py --all` sincroniza
- [ ] Items criados em Zabbix QUA
- [ ] (Opcional) Cron configurado

---

**Está claro agora? Quer que eu ajuste algo na config.py?**
