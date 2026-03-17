#!/bin/bash
#
# Install Script - Prometheus → Zabbix Sync
# Instalação rápida no servidor QUA/Prod
#

set -e

echo "==========================================="
echo "🚀 Instalando Sincronização Prod"
echo "==========================================="

# Verificar Python
echo ""
echo "1️⃣  Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "✅ $PYTHON_VERSION"

# Criar ambiente virtual
echo ""
echo "2️⃣  Criando ambiente virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Ambiente virtual criado"
else
    echo "✅ Ambiente virtual já existe"
fi

# Ativar ambiente
source venv/bin/activate
echo "✅ Ambiente ativado"

# Instalar dependências
echo ""
echo "3️⃣  Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependências instaladas"

# Verificar instalação
echo ""
echo "4️⃣  Verificando instalação..."
python3 -c "import requests; print('✅ requests OK')"

# Criar logs directory
echo ""
echo "5️⃣  Configurando logs..."
LOGS_DIR="/var/log/prometheus-sync"
if [ ! -d "$LOGS_DIR" ]; then
    sudo mkdir -p "$LOGS_DIR"
    sudo chown $(whoami) "$LOGS_DIR"
    echo "✅ Diretório de logs criado: $LOGS_DIR"
else
    echo "✅ Diretório de logs já existe"
fi

# Testar
echo ""
echo "6️⃣  Testando instalação..."
echo "Executando: python3 validate.py"
python3 validate.py

echo ""
echo "==========================================="
echo "✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO!"
echo "==========================================="
echo ""
echo "📝 Próximos passos:"
echo ""
echo "1. Configurar variáveis de ambiente:"
echo "   export ZABBIX_API_URL='http://seu-zabbix:8080/api_jsonrpc.php'"
echo "   export ZABBIX_USER='Admin'"
echo "   export ZABBIX_PASSWORD='sua-senha'"
echo "   export PROMETHEUS_API_URL='http://seu-prometheus:9090'"
echo ""
echo "2. Testar sincronização:"
echo "   python3 sync_prometheus.py --list"
echo "   python3 sync_prometheus.py --all"
echo ""
echo "3. Configurar automação (cron/systemd)"
echo ""
echo "✅ Pronto para uso!"
