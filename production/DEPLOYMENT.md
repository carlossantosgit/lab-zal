# 📋 Guia de Deployment - Production Ready

**Tempo estimado:** 10 minutos

---

## 1️⃣ Pré-requisitos

```bash
# Verificar Python
python3 --version  # ≥3.8

# Server com acesso a:
# - Prometheus HTTPS: prometheus-prod-srv01.spms.min-saude.pt
# - Zabbix HTTP: seu-zabbix-qua:8080
```

---

## 2️⃣ Clonar e Setup

```bash
# Clonar repo
cd ~
git clone https://github.com/carlossantosgit/lab-zal.git
cd lab-zal/production

# Criar environment virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

---

## 3️⃣ Configurar (OBRIGATÓRIO)

```bash
nano config.py
```

**Alterar APENAS estes 6 valores:**

```python
# PROMETHEUS (seu servidor)
PROMETHEUS_URL = "https://prometheus-prod-srv01.spms.min-saude.pt"
PROMETHEUS_USER = "prometheus"
PROMETHEUS_PASS = "sua-senha-aqui"

# ZABBIX (seu servidor)
ZABBIX_API_URL = "http://seu-zabbix:8080/api_jsonrpc.php"
ZABBIX_USER = "Admin"
ZABBIX_PASSWORD = "sua-senha-aqui"
```

---

## 4️⃣ Validar (CRÍTICO)

```bash
python3 validate.py
```

**Se vir isto → SUCESSO ✅**

```
✅ Prometheus OK
✅ Zabbix OK (login bem-sucedido)
✅ XX alerting rules encontradas
✅ X hosts encontrados em Zabbix
✅ VALIDAÇÃO OK - Sistema pronto para sincronização!
```

**Se falhar:**
- Verificar URLs
- Verificar credenciais
- Verificar firewall/conectividade
- Verificar SSL (se HTTPS)

---

## 5️⃣ Analisar Mapeamento

```bash
python3 analise_mapeamento.py
```

Revisar a saída e confirmar que os hosts/labels estão corretos.

---

## 6️⃣ Sincronizar

### Opção A: Teste (1 host)

```bash
python3 sync_prometheus.py --host seu-host-teste
```

### Opção B: Produção (todos)

```bash
python3 sync_prometheus.py --all
```

---

## 7️⃣ Automação (Cron)

```bash
crontab -e
```

Adicionar (sincroniza cada hora):

```bash
0 * * * * cd /home/usuario/lab-zal/production && source venv/bin/activate && python3 sync_prometheus.py --all >> /var/log/prometheus-zabbix-sync.log 2>&1
```

---

## 📋 Comandos de Monitoramento

```bash
# Ver logs em tempo real
tail -f /var/log/prometheus-zabbix-sync.log

# Ver status de sincronização
python3 sync_prometheus.py --list

# Ver detalhes completos
python3 sync_prometheus.py --all --verbose
```

---

## ⚠️ Pontos Críticos

| ❌ ERRADO | ✅ CERTO |
|-----------|---------|
| Esquecer de validar | `python3 validate.py` primeiro |
| Usar .env | Editar `config.py` hardcoded |
| Editar `/api_jsonrpc` | Deixar URL completa |
| Esquecer venv | Sempre `source venv/bin/activate` |

---

## 🆘 Se Algo Falhar

1. **Validação falha** → Revisar `config.py` (credenciais/URLs)
2. **Sincronização falha** → Verificar logs, rodar `python3 validate.py` novamente
3. **Cron não funciona** → Testar comando manualmente primeiro

---

**Pronto para produção! 🚀**
