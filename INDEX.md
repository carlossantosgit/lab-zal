# 📚 Lab ZAL - Documentação Index

Guia rápido para saber qual ficheiro ler.

## 🎯 Para Iniciantes (Start Here!)

### 1️⃣ Primeira Vez Rodando?
👉 **[QUICKSTART.md](QUICKSTART.md)**
- ⏱️ 2 minutos para ler
- ✅ Começar em 5 minutos
- 🎯 Tudo que precisa para iniciar

### 2️⃣ Precisa de Instalar Docker?
👉 **[INSTALLATION.md](INSTALLATION.md)**
- 📋 Requisitos por SO
- 🛠️ Passo a passo instalação
- 🔧 Troubleshooting instalação

### 3️⃣ Problema ao Iniciar?
👉 **[QUICKSTART.md - Troubleshooting](QUICKSTART.md#-troubleshooting)**
- 🔍 Checklist diagnóstico
- ❌ Problemas comuns
- ✅ Soluções rápidas

---

## 📖 Para Usuários Finais

### Quer Saber Tudo?
👉 **[README.md](README.md)**
- 📊 Arquitetura completa
- 🔌 Como funciona
- 📈 Testes e verificação
- 🎯 Próximas melhorias

### Quer Usar o Webhook?
👉 **[README.md - Testes](README.md#-testes)**
- 🧪 Teste Manual
- 🎯 Teste Real
- 📈 Verificação em Zabbix

### Quer Adicionar Novo Host?
👉 **[README.md - Manutenção](README.md#-manutenção)**
- ➕ Adicionar novo host
- 🔧 Fixar interfaces
- 🧪 Testar conectividade

---

## 🛠️ Para Developers/Admins

### Setup Inicial (One-Time)
👉 **[scripts/README.md](scripts/README.md)**
- 📋 Scripts disponíveis
- ⚙️ `setup_hosts.py`
- 🔧 `fix_all_items.py`
- 📖 Como usar

### Adicionar Novo Host
**Passo a passo:**
1. Editar `prometheus/prometheus.yml`
2. `docker-compose restart prometheus`
3. `cd scripts && python3 setup_hosts.py`
4. Na dúvida: [scripts/README.md](scripts/README.md)

### Troubleshooting Avançado
👉 **[README.md - Troubleshooting](README.md#-troubleshooting)**
- 🔍 Diagnóstico completo
- 🐛 Problemas conhecidos
- 📊 Verificação de status

---

## 📤 Para Compartilhar

### Quer Enviar para Alguém Rodar?
👉 **[SHARING.md](SHARING.md)**
- 📨 Como enviar (Git, ZIP, etc)
- 📋 Checklist de ficheiros
- 📧 Email template
- ✅ Fluxo recomendado

### Enviar por Email?
**Copie este template:**
```
Olá!

Projeto Lab ZAL em anexo/link.

Para começar:
1. Ler: QUICKSTART.md
2. Rodar: ./check-prerequisites.sh
3. Iniciar: docker-compose up -d

Pronto em ~10 minutos!

Ver SHARING.md para mais detalhes.
```

---

## 📁 Estrutura de Ficheiros

```
📚 DOCUMENTAÇÃO (Leia Primeiro!)
├─ ⭐ QUICKSTART.md          ← Início rápido (2 min)
├─ 📋 INSTALLATION.md        ← Requisitos e install
├─ 📖 README.md              ← Documentação completa
├─ 📤 SHARING.md             ← Como compartilhar
├─ 📚 INDEX.md               ← Este ficheiro
└─ 🔗 check-prerequisites.sh ← Script verificação

🔧 CONFIGURAÇÃO
├─ docker-compose.yml
├─ prometheus/
│  ├─ prometheus.yml
│  └─ rules/alerts.yml
├─ alertmanager/
│  └─ alertmanager.yml
├─ webhook/
│  ├─ receiver.py
│  └─ Dockerfile
└─ zal/
   ├─ hosts.yml
   ├─ zal-config.yaml
   └─ Dockerfile

🛠️  SCRIPTS E FERRAMENTAS
└─ scripts/
   ├─ README.md             ← Guia scripts
   ├─ setup_hosts.py        ← Criar hosts
   ├─ fix_all_items.py      ← Corrigir interfaces
   ├─ setup_zabbix.py       ← Deprecated
   └─ fix_items.py          ← Backup
```

---

## 🎓 Fluxos de Aprendizagem

### Fluxo 1: "Só Quer Rodar"
1. QUICKSTART.md
2. `./check-prerequisites.sh`
3. `docker-compose up -d`
4. ✅ Pronto!

**Tempo: 10 minutos**

### Fluxo 2: "Quer Entender"
1. QUICKSTART.md
2. README.md (arquitetura)
3. README.md (como funciona)
4. Explorar configs
5. ✅ Entendido!

**Tempo: 30 minutos**

### Fluxo 3: "Quer Customizar"
1. QUICKSTART.md (setup)
2. README.md (manutenção)
3. scripts/README.md
4. Editar configs
5. `docker-compose restart`
6. ✅ Customizado!

**Tempo: 1 hora**

### Fluxo 4: "Quer Partilhar"
1. Verificar tudo funciona
2. SHARING.md (preparar envio)
3. `zip -r lab-zal.zip .`
4. Enviar + QUICKSTART.md link
5. ✅ Pronto para usar!

**Tempo: 15 minutos**

---

## 🔍 Busca Rápida

### Procura de Tópico

| Tópico | Ficheiro | Secção |
|--------|----------|--------|
| Início rápido | QUICKSTART.md | - |
| Instalar Docker | INSTALLATION.md | 🛠️ Instalação por SO |
| Rodar projeto | QUICKSTART.md | 🚀 Iniciar |
| Zabbix URL | QUICKSTART.md | 🌐 Aceder |
| Testar conectividade | README.md | 🧪 Testes |
| Adicionar host | README.md | 🔧 Manutenção |
| Error/problema | QUICKSTART.md | ❌ Troubleshooting |
| Scripts uso | scripts/README.md | - |
| Compartilhar projeto | SHARING.md | - |
| Requisitos | INSTALLATION.md | ✅ Requisitos |
| Architecture | README.md | 📊 Fluxo de Dados |
| Code changes | README.md | 📝 Ficheiros |

---

## ✅ Checklist Rápido

### Setup Inicial
- [ ] Ler QUICKSTART.md?
- [ ] Docker instalado?
- [ ] `./check-prerequisites.sh` passou?
- [ ] `docker-compose up -d` rodou?
- [ ] Esperar 3 minutos?
- [ ] `http://localhost:8080` acessível?

### Primeiro Uso
- [ ] Fazer login Zabbix (Admin/zabbix)?
- [ ] Ver containers todos UP?
- [ ] Rodar setup_hosts.py?
- [ ] Testar zabbix_sender?

### Antes de Compartilhar
- [ ] Tudo funciona localmente?
- [ ] QUICKSTART.md presente?
- [ ] check-prerequisites.sh executável?
- [ ] SHARING.md incluído?
- [ ] .gitignore aplicado?

---

## 🆘 Precisa de Ajuda?

### Não Sabe por Onde Começar?
👉 **[QUICKSTART.md](QUICKSTART.md)** (2 minutos de leitura)

### Problema com Instalação?
👉 **[INSTALLATION.md](INSTALLATION.md)**

### Problema ao Rodar?
👉 **[QUICKSTART.md - Troubleshooting](QUICKSTART.md#-troubleshooting)**

### Quer Saber Tudo?
👉 **[README.md](README.md)**

### Problema Avançado?
👉 **[README.md - Troubleshooting](README.md#-troubleshooting)**

---

## 🎯 Resumo Final

| Situação | Ficheiro | Tempo |
|----------|----------|-------|
| Primeira vez | QUICKSTART.md | 2 min |
| Sem Docker | INSTALLATION.md | 15 min |
| Tudo pronto | docker-compose up -d | 5 min |
| Problema? | Troubleshooting | 5-10 min |
| Quer compartilhar | SHARING.md | 15 min |
| Quer aprender tudo | README.md | 30 min |

---

**Happy Learning! 📚✨**

*Última atualização: 2026-03-16*
