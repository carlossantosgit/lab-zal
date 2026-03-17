# 📚 Índice de Documentação - Lab ZAL

Guia rápido para navegar toda a documentação do projeto.

---

## 🎯 Começar Aqui

### Para Iniciantes (Primeiros 10-15 min)
1. 📖 [QUICKSTART.md](./QUICKSTART.md) - **COMECE AQUI!**
   - Instalação rápida (5 min)
   - Sincronizar regras (2 min)
   - Validação end-to-end (2 min, opcional)
   - Abrir no navegador (1 min)

---

## 📋 Documentação Por Tipo

### 🚀 Para Apresentações
1. **[APRESENTACAO.md](./APRESENTACAO.md)** ⭐
   - 10 slides com timing (24 min total)
   - Script completo de apresentação
   - 3 opções de demo (completa, rápida, webhook)
   - Checklist pré-apresentação

### ✅ Para Validação & Testes
1. **[E2E_VALIDATION_REPORT.md](./E2E_VALIDATION_REPORT.md)** ⭐
   - Relatório de validação end-to-end
   - Fluxo visual completo com diagramas
   - Execução prática com resultados reais
   - 🚀 **Executar:** `python3 scripts/validate_e2e.py`

2. **[VALIDACAO_SYNC.md](./VALIDACAO_SYNC.md)**
   - 4 métodos diferentes de validação
   - Troubleshooting guide
   - Teste com novas regras
   - Checklist para apresentações

3. **[scripts/validate_e2e.py](./scripts/validate_e2e.py)**
   - Script interativo com 6 etapas
   - Demonstração prática de tudo funcionando
   - Output colorido e fácil de ler
   - 🚀 **Executar:** `python3 scripts/validate_e2e.py`

### 📖 Para Entender o Projeto
1. **[README.md](./README.md)**
   - Overview do projeto
   - Arquitetura visual
   - 32 regras sincronizadas (listadas por categoria)
   - Quickstart básico
   - Manutenção e troubleshooting

2. **[POC_PROMETHEUS_SYNC.md](./POC_PROMETHEUS_SYNC.md)**
   - Documentação técnica detalhada do POC
   - Design de sincronização
   - Mapeamento de severity
   - Estrutura de dados

### 🔧 Para Scripts e Ferramentas
1. **[scripts/README.md](./scripts/README.md)**
   - Guia de todos os scripts disponíveis
   - Como usar cada script
   - Exemplos de execução

2. **Scripts principais:**
   - `sync_prometheus_rules.py` - Sincronizar regras (CLI)
   - `validate_e2e.py` - Validação end-to-end
   - `populate_demo_data.py` - Popular com dados demo
   - `setup_hosts.py` - Criar hosts manualmente
   - `fix_all_items.py` - Corrigir interfaces

---

## 🔄 Fluxo de Documentação Recomendado

### Opção 1: Demo Rápida (15 min)
```
1. QUICKSTART.md (Passos 1-2)
2. python3 scripts/validate_e2e.py
3. Abrir http://localhost:8080 e ver resultados
```

### Opção 2: Entender Tudo (30-45 min)
```
1. README.md (visão geral)
2. POC_PROMETHEUS_SYNC.md (técnico)
3. QUICKSTART.md (hands-on)
4. VALIDACAO_SYNC.md (validar)
5. python3 scripts/validate_e2e.py
```

### Opção 3: Apresentar ao Cliente (60 min prep + 30 min apresentação)
```
Prep (60 min antes):
  1. APRESENTACAO.md (familiarizar-se)
  2. python3 scripts/validate_e2e.py (testar)
  3. VALIDACAO_SYNC.md (troubleshooting)

Apresentação (30 min):
  1. Slides 1-3 (Problema, Solução, Arquitetura)
  2. Executar demo ao vivo (Slides 4+)
  3. Mostrar no Zabbix UI
  4. Call to action (próximos passos)
```

---

## 📊 Structure do Repositório

```
lab-zal/
├── 📚 DOCUMENTACAO_INDEX.md      ← Você está aqui!
├── README.md                     ← Overview + troubleshooting
├── QUICKSTART.md                 ← Comece rápido
├── APRESENTACAO.md               ← 10 slides para apresentação
├── POC_PROMETHEUS_SYNC.md         ← Documentação técnica
├── E2E_VALIDATION_REPORT.md      ← Validação com resultados reais
├── VALIDACAO_SYNC.md            ← 4 métodos de validação
│
├── scripts/                      ← Ferramentas de CLI
│   ├── README.md
│   ├── validate_e2e.py          ← ✅ Validação interativa
│   ├── sync_prometheus_rules.py  ← Sincronizar regras
│   └── ...
│
├── docker-compose.yml            ← Orquestração (8 containers)
├── prometheus/                   ← Coleta de métricas
├── alertmanager/                 ← Roteamento de alertas
├── webhook/                      ← 🔄 Sync de regras
│   ├── prometheus_sync.py        ← Módulo de sincronização
│   ├── receiver.py               ← Flask app
│   └── fake_prometheus_rules.json ← 32 regras para demo
└── zal/                          ← Zabbix Alert Manager
```

---

## 🎯 Mapa de Conteúdo Por Objetivo

### "Quero rodar localmente rapidinho"
→ [QUICKSTART.md](./QUICKSTART.md)

### "Quero validar que tudo funciona"
→ `python3 scripts/validate_e2e.py` + [E2E_VALIDATION_REPORT.md](./E2E_VALIDATION_REPORT.md)

### "Preciso apresentar ao cliente"
→ [APRESENTACAO.md](./APRESENTACAO.md) + [VALIDACAO_SYNC.md](./VALIDACAO_SYNC.md)

### "Entendo técnico, explica a arquitetura"
→ [POC_PROMETHEUS_SYNC.md](./POC_PROMETHEUS_SYNC.md) + [README.md](./README.md)

### "Como faço se algo dá erro?"
→ [README.md](./README.md#-troubleshooting) + [VALIDACAO_SYNC.md](./VALIDACAO_SYNC.md#troubleshooting)

### "Quero entender os scripts"
→ [scripts/README.md](./scripts/README.md)

---

## ✅ Recursos Principais

| O que | Onde | Tempo |
|------|------|-------|
| **Conhecer o projeto** | README.md | 5 min |
| **Demo rápida** | QUICKSTART.md | 10 min |
| **Validar tudo** | python3 scripts/validate_e2e.py | 2 min |
| **Entender técnico** | POC_PROMETHEUS_SYNC.md | 10 min |
| **Apresentar** | APRESENTACAO.md | 5 min (prep) + 24 min (demo) |
| **Troubleshoot** | README.md / VALIDACAO_SYNC.md | varies |

---

## 🚀 Execução Rápida

### Ver Tudo Funcionando (2 min)
```bash
python3 scripts/validate_e2e.py
```
Output colorido mostrando pipeline completa!

### Sincronizar Manualmente (1 min)
```bash
python3 scripts/sync_prometheus_rules.py --all --demo
```

### Listar Hosts e Status (10 seg)
```bash
python3 scripts/sync_prometheus_rules.py --list
```

---

## 📞 Dúvidas Comuns

**P: Por onde começo?**
R: [QUICKSTART.md](./QUICKSTART.md)

**P: Como valido que funciona?**
R: Execute `python3 scripts/validate_e2e.py`

**P: Como apresento ao cliente?**
R: Siga [APRESENTACAO.md](./APRESENTACAO.md)

**P: Algo deu erro, o que faço?**
R: Veja [README.md - Troubleshooting](./README.md#-troubleshooting)

**P: Como sincronizo regras novas?**
R: Veja [VALIDACAO_SYNC.md - Adicionar Nova Regra](./VALIDACAO_SYNC.md#validação-3-adicionar-nova-regra-no-prometheus-e-validar-sync)

**P: Quero entender a arquitetura**
R: Leia [README.md - Arquitetura](./README.md#-arquitetura) + [POC_PROMETHEUS_SYNC.md](./POC_PROMETHEUS_SYNC.md)

---

## 📈 Documentação Organizada Por Estágio

### 🌱 Estágio 1: Aprender
- README.md
- POC_PROMETHEUS_SYNC.md
- QUICKSTART.md

### 🔧 Estágio 2: Experimentar
- python3 scripts/validate_e2e.py
- VALIDACAO_SYNC.md
- Todos os scripts em scripts/

### 🎯 Estágio 3: Apresentar
- APRESENTACAO.md
- E2E_VALIDATION_REPORT.md
- Live demo com validate_e2e.py

### 🚀 Estágio 4: Produção
- POC_PROMETHEUS_SYNC.md (phase PRD section)
- Documentação de deployment
- Plano de manutenção

---

## 🎓 Recursos de Aprendizado

| Documento | Tipo | Tempo | Objetivo |
|-----------|------|-------|----------|
| QUICKSTART.md | Hands-on | 10 min | Rodar localmente |
| E2E_VALIDATION_REPORT.md | Técnico | 15 min | Validar pipeline |
| APRESENTACAO.md | Comercial | 30 min | Convencer cliente |
| POC_PROMETHEUS_SYNC.md | Referência | 20 min | Entender design |
| README.md | Geral | 10 min | Overview |
| VALIDACAO_SYNC.md | Troubleshooting | varies | Resolver problemas |

---

## 🔗 Links Rápidos

- **GitHub:** https://github.com/carlossantosgit/lab-zal
- **Zabbix UI:** http://localhost:8080 (Admin/zabbix)
- **Prometheus:** http://localhost:9090
- **Alert Manager:** http://localhost:9093
- **Webhook:** http://localhost:5001

---

**Última atualização:** Março 2026
**Status:** ✅ Completo e Pronto para Produção
**Próximos Passos:** Phase PRD (Production Ready Deployment)
