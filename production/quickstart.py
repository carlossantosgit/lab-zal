#!/usr/bin/env python3
"""
Quick Start - Produção
Inicia tudo com poucos comandos
"""

import os
import sys
import subprocess

def run_command(cmd, description):
    """Executa comando e mostra resultado"""
    print(f"\n{'='*60}")
    print(f"▶️  {description}")
    print(f"{'='*60}\n")

    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"\n❌ Erro ao executar: {description}")
        return False

    return True

def main():
    print("\n" + "="*60)
    print("🚀 QUICK START - PRODUÇÃO")
    print("="*60)

    # 1. Verificar Python
    if not run_command("python3 --version", "1️⃣  Verificando Python"):
        return 1

    # 2. Instalar dependências
    if not run_command("pip install -r requirements.txt", "2️⃣  Instalando dependências"):
        return 1

    # 3. Validar configuração
    if not run_command("python3 validate.py", "3️⃣  Validando configuração"):
        return 1

    # 4. Listar hosts
    if not run_command("python3 sync_prometheus.py --list", "4️⃣  Listando hosts Zabbix"):
        return 1

    # 5. Propor sincronização
    print("\n" + "="*60)
    print("5️⃣  Sincronizar?")
    print("="*60)
    print("\nOpções:")
    print("  1. Sincronizar TODOS os hosts: python3 sync_prometheus.py --all")
    print("  2. Sincronizar host específico: python3 sync_prometheus.py --host <name>")
    print("  3. Ver mais opções: python3 sync_prometheus.py --help")
    print("\n✅ Setup concluído! Pronto para sincronizar.\n")

    return 0

if __name__ == "__main__":
    sys.exit(main())
