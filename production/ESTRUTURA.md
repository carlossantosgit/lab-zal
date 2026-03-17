# 📁 Estrutura da Pasta Production

```
production/
├── 📄 README.md                 ← 🎯 COMECE AQUI! Guia completo
├── 📄 requirements.txt          ← Dependências Python
│
├── 🐍 SCRIPTS PRINCIPAIS:
├── sync_prometheus.py           ← ⭐ Sincronizar regras (MAIN)
├── validate.py                  ← Validar configuração
├── quickstart.py                ← Quick start automático
│
├── 🔧 CONFIGURAÇÃO:
├── config.py                    ← Editar URLs e credenciais
│
└── 📦 DEPLOYMENT:
    ├── install.sh               ← Instalação no servidor
    └── deploy.sh                ← Deploy automático
```

---

## 🚀 Uso Rápido (3 passos)

### Passo 1: Instalar
```bash
cd production
bash install.sh
```

### Passo 2: Configurar (editar)
```bash
# Abrir config.py e ajustar:
# - ZABBIX_API_URL
# - PROMETHEUS_API_URL
# - Credenciais

nano config.py
```

### Passo 3: Sincronizar
```bash
# Validar
python3 validate.py

# Sincronizar todos
python3 sync_prometheus.py --all
```

---

## 📊 Scripts

| Script | Função | Uso |
|--------|--------|-----|
| **sync_prometheus.py** | Sincronizar regras | `python3 sync_prometheus.py --all` |
| **validate.py** | Validar config | `python3 validate.py` |
| **config.py** | Configuração | Editar URLs/credenciais |
| **install.sh** | Instalação | `bash install.sh` |
| **deploy.sh** | Fazer deploy | `bash deploy.sh` |
| **quickstart.py** | Setup automático | `python3 quickstart.py` |

---

## 🎯 Fluxo Production

```
1. Copiar pasta production/ para QUA/Prod
2. bash install.sh
3. Editar config.py (URLs e credenciais)
4. python3 validate.py (verificar)
5. python3 sync_prometheus.py --all (sincronizar)
6. Configurar cron para automação
```

---

## ⚙️ Automação com Cron

```bash
# Sincronizar a cada hora
0 * * * * cd /opt/prometheus-zabbix-sync && python3 sync_prometheus.py --all

# Validar a cada 6 horas
0 */6 * * * python3 /opt/prometheus-zabbix-sync/validate.py
```

---

## 📖 Referências

- [README.md](./README.md) - Guia completo
- GitHub: https://github.com/carlossantosgit/lab-zal
- POC: https://github.com/carlossantosgit/lab-zal (pasta principal)
