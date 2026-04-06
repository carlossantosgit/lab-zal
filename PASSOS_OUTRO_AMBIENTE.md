# 🚀 Passos para Rodar em Outro Ambiente

## 📋 RESUMO RÁPIDO (10 minutos)

```bash
# 1. SETUP
git clone https://github.com/carlossantosgit/lab-zal.git
cd lab-zal/production
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. CONFIGURAR (EDITAR CREDENCIAIS)
nano config.py
# Alterar: PROMETHEUS_URL, PROMETHEUS_USER, PROMETHEUS_PASS, ZABBIX_API_URL, ZABBIX_USER, ZABBIX_PASSWORD

# 3. VALIDAR
python3 validate.py
# Deve retornar: ✅ VALIDAÇÃO OK

# 4. SINCRONIZAR
python3 sync_prometheus.py --all

# 5. AUTOMAÇÃO (OPCIONAL)
crontab -e
# Adicionar: 0 * * * * cd /home/usuario/lab-zal/production && source venv/bin/activate && python3 sync_prometheus.py --all >> /var/log/prometheus-zabbix-sync.log 2>&1
```

---

## 📍 PASSO A PASSO DETALHADO

### 1️⃣ PRÉ-REQUISITOS

```bash
# Verificar Python (precisa de ≥3.8)
python3 --version

# Se não tiver git
apt-get install git  # Debian/Ubuntu
yum install git      # CentOS/RHEL
```

**Verificar acesso aos servidores:**
```bash
# Testar Prometheus
curl -k -u prometheus:SENHA https://prometheus-prod-srv01.spms.min-saude.pt/-/healthy

# Testar Zabbix
curl http://seu-zabbix:8080
```

---

### 2️⃣ CLONAR REPOSITÓRIO

```bash
cd /home/seu-usuario
git clone https://github.com/carlossantosgit/lab-zal.git
cd lab-zal/production

# Verificar arquivos
ls -la
# Deve ter: config.py, validate.py, sync_prometheus.py, requirements.txt, README.md, DEPLOYMENT.md
```

---

### 3️⃣ CRIAR AMBIENTE VIRTUAL

```bash
# Criar venv
python3 -m venv venv

# Ativar (SEMPRE FAZER ISTO ANTES DE RODAR QUALQUER SCRIPT)
source venv/bin/activate

# Você deve ver "(venv)" no início da linha do terminal
```

---

### 4️⃣ INSTALAR DEPENDÊNCIAS

```bash
# Com venv ativado
pip install --upgrade pip
pip install -r requirements.txt

# Verificar instalação
python3 -c "import requests; print('✅ OK')"
```

---

### 5️⃣ EDITAR CONFIGURAÇÃO ⚠️ CRÍTICO

```bash
nano config.py
```

**Alterar estas 6 linhas com valores REAIS:**

```python
# Linha 11
PROMETHEUS_URL = "https://seu-prometheus-aqui"

# Linha 15
PROMETHEUS_USER = "seu-usuario"

# Linha 16
PROMETHEUS_PASS = "sua-senha"

# Linha 22
ZABBIX_API_URL = "http://seu-zabbix:8080/api_jsonrpc.php"

# Linha 25
ZABBIX_USER = "Admin"

# Linha 26
ZABBIX_PASSWORD = "sua-senha-zabbix"
```

**Salvar:** `Ctrl+O` → `Enter` → `Ctrl+X`

---

### 6️⃣ VALIDAR CONEXÃO (OBRIGATÓRIO)

```bash
# Com venv ativado
python3 validate.py
```

**SUCESSO (esperado):**
```
🔍 Validando infraestrutura de sincronização...

1️⃣  Testando Prometheus...
   ✅ Prometheus OK

2️⃣  Testando Zabbix...
   ✅ Zabbix OK (login bem-sucedido)

3️⃣  Contando regras Prometheus...
   ✅ 32 alerting rules encontradas

4️⃣  Contando hosts Zabbix...
   ✅ 5 hosts encontrados em Zabbix

============================================================
✅ VALIDAÇÃO OK - Sistema pronto para sincronização!
============================================================
```

**SE FALHAR:** volte ao passo 5 e revise as credenciais

---

### 7️⃣ SINCRONIZAR (PRIMEIRA VEZ)

**Opção A: Ver hosts disponíveis**
```bash
python3 sync_prometheus.py --list
```

**Opção B: Testar em 1 host**
```bash
python3 sync_prometheus.py --host seu-host-test
```

**Opção C: Sincronizar TODOS (PRODUÇÃO)**
```bash
python3 sync_prometheus.py --all
```

**Opção D: Com detalhes**
```bash
python3 sync_prometheus.py --all --verbose
```

---

### 8️⃣ AUTOMAÇÃO COM CRON (OPCIONAL)

```bash
# Abrir editor de cron
crontab -e

# Adicionar esta linha (sincroniza cada hora):
0 * * * * cd /home/seu-usuario/lab-zal/production && source venv/bin/activate && python3 sync_prometheus.py --all >> /var/log/prometheus-zabbix-sync.log 2>&1
```

**Verificar se cron está configurado:**
```bash
crontab -l
```

---

## 📊 COMANDOS ÚTEIS

```bash
# Ativar venv (sempre fazer isto)
source venv/bin/activate

# Validar
python3 validate.py

# Listar hosts
python3 sync_prometheus.py --list

# Sincronizar tudo
python3 sync_prometheus.py --all

# Sincronizar com detalhes
python3 sync_prometheus.py --all --verbose

# Sincronizar 1 host
python3 sync_prometheus.py --host seu-host

# Ver logs
tail -f /var/log/prometheus-zabbix-sync.log

# Sair do venv (quando terminar)
deactivate
```

---

## 🔍 TROUBLESHOOTING

### ❌ "Prometheus não acessível"
```bash
# Testar conectividade
curl -k -u prometheus:SENHA https://prometheus-prod-srv01.spms.min-saude.pt/-/healthy

# Verificar firewall
telnet prometheus-prod-srv01.spms.min-saude.pt 443

# Verificar DNS
nslookup prometheus-prod-srv01.spms.min-saude.pt
```

### ❌ "Zabbix não acessível"
```bash
# Testar
curl http://seu-zabbix:8080

# Verificar firewall
telnet seu-zabbix 8080
```

### ❌ "Login Zabbix falhou"
```bash
# Revisar config.py:
# - ZABBIX_API_URL correto?
# - ZABBIX_USER correto?
# - ZABBIX_PASSWORD correto?

# Testar login manualmente com jq:
curl -X POST http://seu-zabbix:8080/api_jsonrpc.php \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"user.login","params":{"user":"Admin","password":"sua-senha"},"id":1}'
```

### ❌ "requests não instalado"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### ❌ "Permissão negada em /var/log"
```bash
# Criar log com permissão
sudo touch /var/log/prometheus-zabbix-sync.log
sudo chmod 666 /var/log/prometheus-zabbix-sync.log
```

---

## ✅ CHECKLIST FINAL

- [ ] Python ≥3.8 instalado
- [ ] Git clone feito
- [ ] venv criado e ativado
- [ ] pip install -r requirements.txt OK
- [ ] config.py editado com credenciais reais
- [ ] python3 validate.py passou
- [ ] python3 sync_prometheus.py --all OK
- [ ] Logs em /var/log/prometheus-zabbix-sync.log
- [ ] Cron configurado (opcional)
- [ ] Monitoramento ativo

---

## 📞 RESUMO FINAL

**O que foi feito:**
✅ Clonado repo
✅ Setup Python
✅ Configurado credenciais
✅ Validado conexão
✅ Sincronizado alerts
✅ Configurado automation

**Próximo passo:**
Monitorar logs em `/var/log/prometheus-zabbix-sync.log`

**Para parar:**
Remover linha do crontab: `crontab -e`

---

**Dúvidas?** Verificar `/var/log/prometheus-zabbix-sync.log` 📝
