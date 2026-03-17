#!/bin/bash
#
# Deploy Script - Deploy para QUA/Produção
# Use este script para fazer deploy completo
#

set -e

DEPLOY_PATH="${1:-.}"
SERVER="${2:-qua-server}"

echo "==========================================="
echo "📦 Deploy para Produção"
echo "==========================================="
echo ""
echo "Destino: $SERVER:$DEPLOY_PATH"
echo ""

# Validar arquivos
echo "1️⃣  Validando arquivos..."
required_files=(
    "sync_prometheus.py"
    "validate.py"
    "config.py"
    "requirements.txt"
    "README.md"
    "install.sh"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Arquivo não encontrado: $file"
        exit 1
    fi
done
echo "✅ Todos os arquivos presentes"

# Testar sintaxe Python
echo ""
echo "2️⃣  Testando sintaxe Python..."
python3 -m py_compile sync_prometheus.py
python3 -m py_compile validate.py
python3 -m py_compile config.py
echo "✅ Sintaxe OK"

# Copiar para servidor
echo ""
echo "3️⃣  Copiando arquivos para $SERVER..."
scp -r ./* $SERVER:$DEPLOY_PATH/
echo "✅ Arquivos copiados"

# Executar install no servidor remoto
echo ""
echo "4️⃣  Instalando no servidor remoto..."
ssh $SERVER "cd $DEPLOY_PATH && bash install.sh"

echo ""
echo "==========================================="
echo "✅ DEPLOY CONCLUÍDO!"
echo "==========================================="
echo ""
echo "🔗 Conectar ao servidor:"
echo "   ssh $SERVER"
echo "   cd $DEPLOY_PATH"
echo ""
echo "▶️  Sincronizar:"
echo "   python3 sync_prometheus.py --all"
echo ""
