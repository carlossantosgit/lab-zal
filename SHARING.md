# 📤 Como Compartilhar o Projeto

Instruções para enviar o Lab ZAL a alguém e eles conseguirem rodar.

## 🎯 Resumo Executivo

**Se precisa de enviar para alguém rodar:**

1. ✅ Use **Git** (melhor opção)
2. ✅ Ou **ZIP** se não tiverem Git
3. ✅ Envie este ficheiro como guia

---

## 📨 Opção 1: Via Git (Recomendado)

### Você (repositório)

```bash
# 1. Criar repositório no GitHub/GitLab
# 2. Inicializar git (se ainda não estiver)
cd lab-zal
git init
git remote add origin https://github.com/your-org/lab-zal.git

# 3. Fazer push
git add .
git commit -m "Initial Lab ZAL setup"
git push -u origin main

# 4. Enviar link para a pessoa
# https://github.com/your-org/lab-zal
```

### A Pessoa (recebe o código)

```bash
# 1. Clonar projeto
git clone https://github.com/your-org/lab-zal.git
cd lab-zal

# 2. Verificar requisitos
./check-prerequisites.sh

# 3. Iniciar
docker-compose up -d

# 4. Pronto!
```

**⏱️ Tempo: ~2 minutos**

---

## 📦 Opção 2: Via ZIP

### Você (preparar)

```bash
# 1. Criar ZIP da pasta
cd ..
zip -r lab-zal-v1.0.zip lab-zal \
  --exclude "lab-zal/.git/*" \
  --exclude "lab-zal/.env" \
  --exclude "lab-zal/__pycache__/*"

# 2. Enviar por email/drive/etc
```

### A Pessoa (recebe)

```bash
# 1. Descompactar
unzip lab-zal-v1.0.zip
cd lab-zal

# 2. Verificar requisitos
chmod +x check-prerequisites.sh
./check-prerequisites.sh

# 3. Iniciar
docker-compose up -d

# 4. Pronto!
```

**⏱️ Tempo: ~2 minutos**

---

## 📝 Ficheiros Essenciais a Incluir

Certifique-se que está contido:

```
✅ QUICKSTART.md           ← ENVIE ISTO PRIMEIRO
✅ INSTALLATION.md         ← Requisitos detalhados
✅ README.md               ← Documentação completa
✅ check-prerequisites.sh  ← Script verificação
✅ docker-compose.yml      ← Configuração
├─ prometheus/
├─ alertmanager/
├─ webhook/
├─ zal/
└─ scripts/

❌ NÃO INCLUIR:
  ❌ .git/                 (ser recriado)
  ❌ .env                  (contem senhas)
  ❌ venv/                 (Python env)
  ❌ __pycache__/
```

**Boa notícia:** `.gitignore` já cobre isto!

---

## 📧 Email Template

Copiar e colar:

```
Assunto: Lab ZAL - Prometheus + Zabbix Setup

Olá!

Segue em anexo o Lab ZAL - integração Prometheus + Alert Manager + Zabbix.

INÍCIO RÁPIDO:
1. Descompactar: unzip lab-zal-main.zip && cd lab-zal
2. Verificar: ./check-prerequisites.sh
3. Iniciar: docker-compose up -d
4. Zabbix: http://localhost:8080 (Admin/zabbix)
5. Prometheus: http://localhost:9090

Documentação:
- QUICKSTART.md - Início rápido
- INSTALLATION.md - Requisitos detalhados
- README.md - Documentação completa

Requisitos:
- Docker 20.10+
- Docker Compose 1.29+
- 4GB RAM mínimo
- 10GB disco livre

Dúvidas? Consulte QUICKSTART.md ou README.md

Abraços!
```

---

## 🔗 Opção 3: Via Google Drive / GitHub Releases

### GitHub Releases (Profissional)

```bash
# 1. Criar tag
git tag v1.0.0
git push origin v1.0.0

# 2. GitHub cria release automática
# 3. Enviar link da release
# https://github.com/your-org/lab-zal/releases/tag/v1.0.0
```

### Google Drive

```bash
# 1. Criar ZIP
zip -r lab-zal-v1.0.zip lab-zal

# 2. Upload para Google Drive
# 3. Compartilhar link
# https://drive.google.com/file/d/...
```

---

## ✅ Checklist para Enviar

### Documentação
- [ ] QUICKSTART.md (guia início rápido)
- [ ] INSTALLATION.md (requisitos detalhados)
- [ ] README.md (documentação completa)
- [ ] scripts/README.md (guia de scripts)

### Code
- [ ] docker-compose.yml
- [ ] prometheus/ (configs)
- [ ] alertmanager/ (configs)
- [ ] webhook/ (receiver.py + Dockerfile)
- [ ] zal/ (configs + Dockerfile)
- [ ] scripts/ (setup scripts)

### Tools
- [ ] check-prerequisites.sh (script verificação)
- [ ] .gitignore (para Git)

### Excluir
- [ ] .git/ (pode ser recriado)
- [ ] .env (contem dados sensíveis)
- [ ] __pycache__/
- [ ] venv/
- [ ] *.pyc

---

## 🧪 Testar Antes de Enviar

Execute isto para garantir que tudo funciona:

```bash
# 1. Parar tudo
docker-compose down -v

# 2. Simular novo setup
docker-compose up -d

# 3. Esperar 2-3 minutos
sleep 180

# 4. Verificar
docker-compose ps
# Deve ter 8/8 containers UP

# 5. Testar Zabbix
curl -s http://localhost:8080 | head -5

# 6. Testar Prometheus
curl -s http://localhost:9090/api/v1/targets | jq .result[0]

# 7. Documentação
cat QUICKSTART.md | head -20
```

---

## 📊 Fluxo Recomendado para A Pessoa

```
1. Recebe projeto (Git ou ZIP)
      ↓
2. Descompactar / Clonar
      ↓
3. Ler QUICKSTART.md         ← 2 min
      ↓
4. Executar check-prerequisites.sh  ← 30 seg
      ↓
5. docker-compose up -d      ← 3 min
      ↓
6. Esperar (init dos containers)   ← 2 min
      ↓
7. Aceder: http://localhost:8080   ← PRONTO!
```

**Tempo Total: ~10 minutos**

---

## 🆘 Se Algo Correr Mal

Diga à pessoa para:

1. **Ver logs:**
   ```bash
   docker-compose logs -f
   ```

2. **Executar check:**
   ```bash
   ./check-prerequisites.sh
   ```

3. **Verificar requisitos:**
   ```bash
   cat INSTALLATION.md
   ```

4. **Parar e recomeçar:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

---

## 💡 Dicas de Sharing

### Melhor
✅ **Git Push** → Mais simples, versionado, fácil atualizar

### Bom
✅ **ZIP + Email** → Para não-técnicos

### Alternativas
✅ **GitHub Releases** → Profissional
✅ **Docker Hub** → Se quiser distribuir imagens pré-built
✅ **Internal git repo** → Se for equipa interna

---

## 🎯 Responda a FAQs da Pessoa

### "Preciso de instalar algo?"
Sim, Docker e Docker Compose. Ver INSTALLATION.md

### "Quanto tempo leva?"
~10 minutos (5 min setup + 3 min boot Docker + 2 min espera)

### "Posso correr no Windows?"
Sim, com WSL2. Ver INSTALLATION.md

### "Posso correr no Mac M1/M2?"
Sim, Docker Desktop suporta ARM64

### "Uso as mesmas credenciais?"
Sim, padrão: Admin/zabbix (editável em docker-compose.yml)

### "Posso customizar?"
Sim, editar docker-compose.yml antes de rodar

---

## 📋 Exemplo Completo de Envio

```bash
#!/bin/bash
# Script para preparar projeto para envio

cd lab-zal
git checkout main
git pull origin main

# Limpar caches
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name ".DS_Store" -delete 2>/dev/null

# Gerar ZIP
zip -r ../lab-zal-ready.zip . \
  --exclude ".git/*" \
  --exclude ".env" \
  --exclude "venv/*" \
  --exclude "__pycache__/*" \
  --exclude "*.pyc"

echo "✅ Pronto: ../lab-zal-ready.zip"
echo "   Enviar para: person@example.com"
echo "   Instruções: Ver QUICKSTART.md dentro do ZIP"
```

---

## ✨ Resumo

- **Melhor opção:** Git (mais simples, fácil atualizar)
- **Alternativa:** ZIP + QUICKSTART.md
- **Tempo para a pessoa:** ~10 minutos
- **Documentação:** QUICKSTART.md + INSTALLATION.md
- **Verificação:** check-prerequisites.sh automático

**Bom envio! 🚀**
