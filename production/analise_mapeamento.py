#!/usr/bin/env python3
"""
Script de Análise de Mapeamento
Prometheus labels "app" → Zabbix Host Groups

Extrai informações de:
1. Zabbix: Host Groups existentes
2. Prometheus: Labels "app" encontrados

Gera relatório para mapeamento manual
"""

import requests
import json
import sys
from collections import defaultdict

# ============================================================================
# CONFIGURAÇÃO - EDITE AQUI
# ============================================================================

ZABBIX_API_URL = "http://seu-zabbix-qua:8080/api_jsonrpc.php"
ZABBIX_USER = "Admin"
ZABBIX_PASSWORD = "zabbix"

PROMETHEUS_API_URL = "http://seu-prometheus-prod:9090"

# ============================================================================
# FUNÇÕES
# ============================================================================

def get_zabbix_token():
    """Faz login e retorna token"""
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {"user": ZABBIX_USER, "password": ZABBIX_PASSWORD},
            "id": 1
        }
        resp = requests.post(ZABBIX_API_URL, json=payload, timeout=5)
        result = resp.json()

        if "result" in result:
            print("✅ Zabbix: Login bem-sucedido")
            return result["result"]
        else:
            print(f"❌ Zabbix: Login falhou - {result.get('error')}")
            return None
    except Exception as e:
        print(f"❌ Zabbix: Erro de conexão - {str(e)}")
        return None

def get_zabbix_hostgroups(token):
    """Retorna todos os host groups do Zabbix"""
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "hostgroup.get",
            "params": {"output": ["groupid", "name"]},
            "auth": token,
            "id": 1
        }
        resp = requests.post(ZABBIX_API_URL, json=payload, timeout=5)
        result = resp.json()

        if "result" in result:
            groups = result["result"]
            print(f"✅ Zabbix: {len(groups)} Host Groups encontrados")
            return groups
        else:
            print(f"❌ Zabbix: Erro ao listar grupos")
            return []
    except Exception as e:
        print(f"❌ Zabbix: Erro - {str(e)}")
        return []

def get_prometheus_targets():
    """Retorna todos os targets do Prometheus com labels"""
    try:
        url = f"{PROMETHEUS_API_URL}/api/v1/targets"
        resp = requests.get(url, timeout=5)
        data = resp.json()

        if data.get("status") == "success":
            targets = data.get("data", {}).get("activeTargets", [])
            print(f"✅ Prometheus: {len(targets)} targets encontrados")
            return targets
        else:
            print(f"❌ Prometheus: Erro ao listar targets")
            return []
    except Exception as e:
        print(f"❌ Prometheus: Erro de conexão - {str(e)}")
        return []

def get_prometheus_rules():
    """Retorna alerting rules do Prometheus"""
    try:
        url = f"{PROMETHEUS_API_URL}/api/v1/rules"
        resp = requests.get(url, timeout=5)
        data = resp.json()

        if data.get("status") == "success":
            groups = data.get("data", {}).get("groups", [])
            rule_count = 0
            for group in groups:
                for rule in group.get("rules", []):
                    if rule.get("type") == "alerting":
                        rule_count += 1
            print(f"✅ Prometheus: {rule_count} alerting rules encontradas")
            return groups
        else:
            print(f"❌ Prometheus: Erro ao listar rules")
            return []
    except Exception as e:
        print(f"❌ Prometheus: Erro - {str(e)}")
        return []

def analyze_prometheus_labels(targets, rules):
    """Analisa todos os labels encontrados"""
    app_labels = defaultdict(list)

    print("\n" + "="*70)
    print("📊 ANÁLISE DE LABELS DO PROMETHEUS")
    print("="*70)

    # De targets
    for target in targets:
        labels = target.get("labels", {})
        app = labels.get("app")
        if app:
            instance = labels.get("instance", "unknown")
            app_labels[app].append(instance)

    # De rules (labels)
    for group in rules:
        for rule in group.get("rules", []):
            if rule.get("type") == "alerting":
                labels = rule.get("labels", {})
                app = labels.get("app")
                if app:
                    # Já registrado, skip
                    pass

    # Imprimir consolidado
    print("\n📋 Labels 'app' encontrados em Prometheus:\n")
    for app, instances in sorted(app_labels.items()):
        print(f"\n  app='{app}'")
        print(f"    Quantidade: {len(instances)} targets")
        print(f"    Exemplos:")
        for instance in instances[:3]:
            print(f"      - {instance}")
        if len(instances) > 3:
            print(f"      ... e mais {len(instances)-3}")

    return dict(app_labels)

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "="*70)
    print("🔍 ANÁLISE DE MAPEAMENTO")
    print("Prometheus labels 'app' ↔ Zabbix Host Groups")
    print("="*70 + "\n")

    # 1. Conectar Zabbix
    print("1️⃣  Conectando ao Zabbix...")
    token = get_zabbix_token()
    if not token:
        return 1

    # 2. Listar grupos Zabbix
    print("\n2️⃣ Listando Host Groups Zabbix...")
    groups = get_zabbix_hostgroups(token)

    # 3. Conectar Prometheus
    print("\n3️⃣ Conectando ao Prometheus...")
    print(f"   URL: {PROMETHEUS_API_URL}")

    # 4. Listar targets e rules
    print("\n4️⃣ Analisando Prometheus...")
    targets = get_prometheus_targets()
    rules = get_prometheus_rules()

    # 5. Analisar labels
    app_labels = analyze_prometheus_labels(targets, rules)

    # 6. Gerar tabela de mapeamento
    print("\n" + "="*70)
    print("📊 ZABBIX HOST GROUPS")
    print("="*70 + "\n")
    print("| Group ID | Group Name | Descrição |")
    print("|----------|-----------|-----------|")
    for group in groups:
        gid = group["groupid"]
        name = group["name"]
        print(f"| {gid:<8} | {name:<27} | |")

    # 7. Tabela de mapeamento recomendado
    print("\n" + "="*70)
    print("📋 MAPEAMENTO RECOMENDADO")
    print("="*70 + "\n")
    print("| Prometheus 'app' | Zabbix Group | Group ID | Targets |")
    print("|------------------|--------------|----------|---------|")

    for app, instances in sorted(app_labels.items()):
        print(f"| {app:<16} | [DEFINIR]    | [??]     | {len(instances):>7} |")

    # 8. Gerar YAML para salvar
    print("\n" + "="*70)
    print("📝 YAML DE MAPEAMENTO (COPIE E COMPLETE)")
    print("="*70 + "\n")

    yaml_template = "mapping:\n"
    for app in sorted(app_labels.keys()):
        yaml_template += f"""  {app}:
    zabbix_group: "[DEFINIR - qual grupo?]"
    group_id: "[DEFINIR - qual ID?]"
    prometheus_app_label: "app={app}"
    hosts:
      - [liste hosts que usam app={app}]
    alerting_rules:
      - [liste rules que monitoram app={app}]

"""

    print(yaml_template)

    # 9. Salvar resultado
    output_file = "analise_mapeamento_resultado.txt"
    with open(output_file, "w") as f:
        f.write("# RESULTADO DA ANÁLISE DE MAPEAMENTO\n\n")
        f.write(f"## Zabbix Host Groups ({len(groups)})\n\n")
        for group in groups:
            f.write(f"- {group['name']} (ID: {group['groupid']})\n")

        f.write(f"\n## Prometheus App Labels ({len(app_labels)})\n\n")
        for app, instances in sorted(app_labels.items()):
            f.write(f"- app={app} ({len(instances)} targets)\n")

        f.write(f"\n## YAML Template\n\n{yaml_template}")

    print(f"\n✅ Resultado salvo em: {output_file}")

    print("\n" + "="*70)
    print("📋 PRÓXIMAS ETAPAS")
    print("="*70)
    print("""
1. Revisar a tabela acima
2. Definir para cada "app" qual Zabbix Group deve ir
3. Completar o YAML de mapeamento com:
   - zabbix_group: nome exato do grupo
   - group_id: ID do grupo
   - hosts: lista de hosts para esse app
   - alerting_rules: quais rules monitoram esse app
4. Salvar em: MAPPING_PROMETHEUS_ZABBIX.md
5. Implementar no production/sync_prometheus.py

Documentação: ANALISE_MAPEAMENTO.md
""")

    return 0

if __name__ == "__main__":
    sys.exit(main())
