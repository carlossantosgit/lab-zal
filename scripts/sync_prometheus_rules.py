#!/usr/bin/env python3
"""
Script para sincronizar regras Prometheus com Zabbix
Pode ser executado manualmente para sincronizar hosts
"""

import requests
import argparse
import sys
import os

# Adicionar webhook ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'webhook'))

from prometheus_sync import sync_prometheus_rules_for_host

ZABBIX_API_URL = "http://localhost:8080/api_jsonrpc.php"
ZABBIX_USER = "Admin"
ZABBIX_PASSWORD = "zabbix"

def zabbix_login():
    """Login no Zabbix e retornar token"""
    payload = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "user": ZABBIX_USER,
            "password": ZABBIX_PASSWORD
        },
        "id": 1
    }

    try:
        resp = requests.post(ZABBIX_API_URL, json=payload, timeout=5)
        result = resp.json()

        if "result" in result:
            return result["result"]
        else:
            print(f"❌ Login failed: {result.get('error')}")
            return None
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return None

def get_all_hosts(auth_token):
    """Obter todos os hosts do Zabbix"""
    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["hostid", "host", "name"],
            "limit": 1000
        },
        "auth": auth_token,
        "id": 1
    }

    try:
        resp = requests.post(ZABBIX_API_URL, json=payload, timeout=5)
        result = resp.json()

        if "result" in result:
            return result["result"]
        else:
            print(f"❌ Error: {result.get('error')}")
            return []
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return []

def main():
    parser = argparse.ArgumentParser(
        description="Sincroniza regras Prometheus com Zabbix"
    )
    parser.add_argument(
        "--host",
        help="Host específico para sincronizar (ex: prod-db-01)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Sincronizar todos os hosts"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Usar arquivo fake de rules (para demonstração)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Listar todos os hosts disponíveis"
    )

    args = parser.parse_args()

    print("\n" + "="*60)
    print("🔄 SINCRONIZADOR DE REGRAS PROMETHEUS → ZABBIX")
    print("="*60 + "\n")

    # Login Zabbix
    print("🔐 Conectando ao Zabbix...")
    auth_token = zabbix_login()
    if not auth_token:
        print("❌ Não conseguiu conectar ao Zabbix")
        sys.exit(1)
    print("✅ Conectado ao Zabbix\n")

    # Listar hosts
    if args.list:
        print("📋 HOSTS DISPONÍVEIS EM ZABBIX:\n")
        hosts = get_all_hosts(auth_token)

        if not hosts:
            print("   Nenhum host encontrado")
        else:
            for host in hosts:
                print(f"   • {host['host']:30} | {host['name']:40} (ID: {host['hostid']})")
        print()
        return

    # Sincronizar host específico
    if args.host:
        print(f"🔄 Sincronizando host: {args.host}\n")

        hosts = get_all_hosts(auth_token)
        host_data = None

        for h in hosts:
            if h['host'] == args.host:
                host_data = h
                break

        if not host_data:
            print(f"❌ Host '{args.host}' não encontrado em Zabbix")
            sys.exit(1)

        result = sync_prometheus_rules_for_host(
            hostname=args.host,
            hostid=host_data['hostid'],
            auth_token=auth_token,
            use_fake=args.demo
        )

        print("\n" + "="*60)
        print("📊 RESULTADO DA SINCRONIZAÇÃO:")
        print("="*60)
        print(f"Host:              {result['hostname']}")
        print(f"Rules totais:      {result['rules_total']}")
        print(f"Items criados:     {result['items_created']}")
        print(f"Triggers criadas:  {result['triggers_created']}")

        if result.get('errors'):
            print(f"\n⚠️  Erros encontrados:")
            for error in result['errors']:
                print(f"   • {error}")

        print()
        return

    # Sincronizar todos os hosts
    if args.all:
        print("🔄 Sincronizando TODOS os hosts...\n")

        hosts = get_all_hosts(auth_token)
        if not hosts:
            print("❌ Nenhum host encontrado")
            sys.exit(1)

        total_items = 0
        total_triggers = 0

        for host in hosts:
            print(f"Processando: {host['host']:30}", end=" ")

            result = sync_prometheus_rules_for_host(
                hostname=host['host'],
                hostid=host['hostid'],
                auth_token=auth_token,
                use_fake=args.demo
            )

            if result.get('success'):
                print(f"✅ ({result['items_created']} items, {result['triggers_created']} triggers)")
                total_items += result['items_created']
                total_triggers += result['triggers_created']
            else:
                print(f"❌ {result.get('message')}")

        print("\n" + "="*60)
        print("📊 RESULTADO TOTAL:")
        print("="*60)
        print(f"Hosts processados: {len(hosts)}")
        print(f"Items totais:      {total_items}")
        print(f"Triggers totais:   {total_triggers}")
        print()
        return

    # Se nenhuma opção, mostrar ajuda
    parser.print_help()

if __name__ == "__main__":
    main()
