# 📋 Installation & Requirements

Guia de requisitos e instalação do Lab ZAL.

## ✅ Requisitos Mínimos

### Sistema Operativo
- **macOS**: 10.14+
- **Linux**: Ubuntu 18.04+, CentOS 7+, Debian 10+
- **Windows**: 10 Pro/Enterprise (com WSL2)

### Recursos de Hardware
- **CPU**: 2+ cores (4 recomendado)
- **RAM**: 4GB mínimo (8GB recomendado)
- **Disk**: 10GB livre (para volumes Docker)
- **Rede**: Acesso à porta 8080, 9090, 9093, etc

### Software Obrigatório

| Software | Versão Mínima | Instalação |
|----------|---------------|-----------|
| **Docker** | 20.10+ | [docker.com](https://www.docker.com/products/docker-desktop) |
| **Docker Compose** | 1.29+ | [docs.docker.com](https://docs.docker.com/compose/install/) |
| **Git** (opcional) | - | `brew install git` ou `apt install git` |
| **Python** (se adicionar hosts) | 3.7+ | Incluído na maioria das distros |

### Python Packages (Opcional)
Se quiser rodar scripts de setup:
```bash
pip install requests
```

## 🛠️ Instalação por SO

### macOS

#### 1. Instalar Homebrew (se não tiver)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 2. Instalar Docker Desktop
```bash
# Opção 1: Via Homebrew
brew install docker docker-compose

# Opção 2: Descarregar
# https://www.docker.com/products/docker-desktop
```

#### 3. Verificar Instalação
```bash
docker --version
docker-compose --version
```

#### 4. Descarregar o Projeto
```bash
git clone https://github.com/your-org/lab-zal.git
cd lab-zal
```

#### 5. Executar Check
```bash
chmod +x check-prerequisites.sh
./check-prerequisites.sh
```

#### 6. Iniciar
```bash
docker-compose up -d
```

---

### Linux (Ubuntu/Debian)

#### 1. Atualizar Packages
```bash
sudo apt update
sudo apt upgrade -y
```

#### 2. Instalar Docker
```bash
sudo apt install -y docker.io docker-compose

# Permissões (opcional, se não quiser usar sudo)
sudo usermod -aG docker $USER
newgrp docker
```

#### 3. Iniciar Docker Service
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

#### 4. Verificar Instalação
```bash
docker --version
docker-compose --version
docker ps  # Não deve dar erro de permissão
```

#### 5. Descarregar o Projeto
```bash
git clone https://github.com/your-org/lab-zal.git
cd lab-zal
```

#### 6. Executar Check
```bash
chmod +x check-prerequisites.sh
./check-prerequisites.sh
```

#### 7. Iniciar
```bash
docker-compose up -d
```

---

### Linux (CentOS/RHEL)

#### 1. Instalar Docker
```bash
sudo yum install -y docker docker-compose

# Ou usar Podman (alternativa)
sudo yum install -y podman podman-docker
```

#### 2. Iniciar Service
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

#### 3. Resto igual a Ubuntu/Debian
```bash
sudo usermod -aG docker $USER
newgrp docker
git clone https://github.com/your-org/lab-zal.git
cd lab-zal
./check-prerequisites.sh
docker-compose up -d
```

---

### Windows (WSL2)

#### 1. Ativar WSL2
```powershell
# Executar PowerShell como Admin
wsl --install
wsl --set-default-version 2
```

#### 2. Instalar Docker Desktop
- Descarregar: https://www.docker.com/products/docker-desktop
- Executar instalador
- Ativar WSL2 integration nas settings

#### 3. Verificar
```bash
docker --version
docker-compose --version
```

#### 4. No WSL2 Terminal
```bash
git clone https://github.com/your-org/lab-zal.git
cd lab-zal
chmod +x check-prerequisites.sh
./check-prerequisites.sh
docker-compose up -d
```

---

### Windows (Sem WSL)

#### Não Recomendado
Docker Desktop in Hyper-V mode funciona mas com limitações. **Preferir WSL2**.

Se só tem Hyper-V:
- Instalar Docker Desktop
- Ou usar máquina virtual Linux

---

## 📥 Descarregar o Projeto

### Opção 1: Git (recomendado)
```bash
git clone https://github.com/your-org/lab-zal.git
cd lab-zal
```

### Opção 2: ZIP
```bash
# Descarregar: https://github.com/your-org/lab-zal/archive/refs/heads/main.zip
unzip lab-zal-main.zip
cd lab-zal-main
```

### Opção 3: Clonar com SSH (se tiver chave SSH)
```bash
git clone git@github.com:your-org/lab-zal.git
cd lab-zal
```

---

## ✅ Verificar Instalação

```bash
# Executar pre-flight check
./check-prerequisites.sh

# Esperado:
# ✅ Docker found
# ✅ Docker Compose found
# ✅ Docker daemon is running
# ✅ docker-compose.yml found
# ✅ All required ports available
# ✅ All checks passed!
```

---

## 🚀 Iniciar

```bash
# Iniciar todos os serviços
docker-compose up -d

# Verificar status
docker-compose ps

# Ver logs
docker-compose logs -f
```

---

## 🔍 Verificar Conectividade

### Teste 1: Zabbix Web UI
```bash
curl -s http://localhost:8080/index.php | head -20
```

### Teste 2: Prometheus
```bash
curl -s http://localhost:9090/api/v1/targets | jq .
```

### Teste 3: Alert Manager
```bash
curl -s http://localhost:9093/api/v2/status | jq .
```

### Teste 4: Webhook
```bash
curl -s http://localhost:5001/health
# Esperado: OK
```

---

## 🔧 Troubleshooting Instalação

### "Docker command not found"
```bash
# macOS
brew install docker docker-compose

# Linux
sudo apt install docker.io docker-compose

# Windows
Descarregar Docker Desktop
```

### "Permission denied"
```bash
# Linux
sudo usermod -aG docker $USER
newgrp docker
```

### "Cannot connect to Docker daemon"
```bash
# macOS
open /Applications/Docker.app

# Linux
sudo systemctl start docker

# Windows
Iniciar Docker Desktop
```

### "Port 8080 already in use"
Editar `docker-compose.yml`:
```yaml
zabbix-web:
  ports:
    - "8081:8080"  # Usar 8081 em vez de 8080
```

---

## 📊 Versões Testadas

| Component | Versão | Status |
|-----------|--------|--------|
| Docker | 20.10.21 | ✅ |
| Docker Compose | 1.29.2 | ✅ |
| Docker Compose | 2.x | ✅ |
| Ubuntu | 20.04, 22.04 | ✅ |
| macOS | 10.15, 11, 12, 13 | ✅ |
| CentOS | 7, 8 | ✅ |

---

## 🎯 Próximos Passos

1. **Ler QUICKSTART.md**
   ```bash
   cat QUICKSTART.md
   ```

2. **Ler README.md**
   ```bash
   cat README.md
   ```

3. **Executar setup (first time)**
   ```bash
   cd scripts
   python3 setup_hosts.py
   ```

---

## 📞 Suporte

- Verificar logs: `docker-compose logs <service>`
- Executar check: `./check-prerequisites.sh`
- Ver documentação: `README.md`
