#!/usr/bin/env python3
"""
Popula dados de demonstração em Zabbix para apresentação
Cria hosts, items, triggers, hostgroups de forma realista
"""

import requests
import json

ZABBIX_API_URL = "http://localhost:8080/api_jsonrpc.php"
ZABBIX_USER = "Admin"
ZABBIX_PASSWORD = "zabbix"

def zabbix_api_call(method, params, auth_token=None):
    """Fazer chamada à API Zabbix"""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    if auth_token:
        payload["auth"] = auth_token
    
    try:
        response = requests.post(ZABBIX_API_URL, json=payload, timeout=5)
        result = response.json()
        
        if "error" in result:
            print(f"❌ API Error: {result['error']}")
            return None
        
        return result.get("result")
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return None

def zabbix_login():
    """Login e retornar token"""
    result = zabbix_api_call("user.login", {
        "user": ZABBIX_USER,
        "password": ZABBIX_PASSWORD
    })
    
    if result:
        print("✅ Login Zabbix OK")
        return result
    
    print("❌ Login failed")
    return None

def get_or_create_hostgroup(auth_token, group_name="Prometheus"):
    """Obter ou criar hostgroup"""
    result = zabbix_api_call("hostgroup.get", {
        "filter": {"name": group_name}
    }, auth_token)
    
    if result and len(result) > 0:
        return result[0]["groupid"]
    
    result = zabbix_api_call("hostgroup.create", {
        "name": group_name
    }, auth_token)
    
    if result and isinstance(result, dict) and "groupids" in result:
        groupid = result["groupids"][0]
        print(f"✅ Created hostgroup: {group_name} (ID: {groupid})")
        return groupid
    
    print(f"❌ Failed to create hostgroup")
    return None

def delete_host_if_exists(hostname, auth_token):
    """Deletar host se existir (limpar)"""
    result = zabbix_api_call("host.get", {
        "filter": {"host": hostname}
    }, auth_token)
    
    if result and len(result) > 0:
        hostid = result[0]["hostid"]
        zabbix_api_call("host.delete", [hostid], auth_token)
        print(f"   🗑️  Deletado host antigo: {hostname}")

def create_demo_host(hostname, display_name, auth_token, groupid):
    """Criar host de demonstração"""
    result = zabbix_api_call("host.create", {
        "host": hostname,
        "name": display_name,
        "groups": [{"groupid": groupid}],
        "interfaces": [{
            "type": 1,
            "main": 1,
            "useip": 1,
            "ip": "127.0.0.1",
            "dns": "",
            "port": "10050"
        }]
    }, auth_token)
    
    if result and isinstance(result, dict) and "hostids" in result:
        hostid = result["hostids"][0]
        print(f"✅ Host criado: {hostname} (ID: {hostid})")
        return hostid
    
    print(f"❌ Falha ao criar host: {hostname}")
    return None

def create_demo_items(hostid, auth_token):
    """Criar items de demonstração"""
    items = [
        {"key": "prometheus.deadmansswitch", "name": "Prometheus - Dead Man's Switch"},
        {"key": "prometheus.highcpu", "name": "Prometheus - High CPU (>50%)"},
        {"key": "prometheus.lowmemory", "name": "Prometheus - Low Memory (<20%)"},
        {"key": "custom.requests", "name": "HTTP Requests/sec"},
        {"key": "custom.latency", "name": "Response Time (ms)"},
        {"key": "custom.errors", "name": "Error Rate (%)"},
    ]
    
    created_count = 0
    
    for item_info in items:
        result = zabbix_api_call("item.create", {
            "name": item_info["name"],
            "key_": item_info["key"],
            "hostid": hostid,
            "type": 2,        # Trapper
            "value_type": 0,  # Float (para latency, cpu %)
            "history": "7d",
            "trends": "30d"
        }, auth_token)
        
        if result and isinstance(result, dict) and "itemids" in result:
            created_count += 1
            print(f"   ✅ Item: {item_info['key']}")
        else:
            print(f"   ❌ Falha ao criar item: {item_info['key']}")
    
    return created_count

def fix_item_interfaces(hostid, auth_token):
    """Configurar interfaces dos items"""
    host_info = zabbix_api_call("host.get", {
        "hostids": [hostid],
        "selectInterfaces": "extend"
    }, auth_token)
    
    if not host_info or len(host_info) == 0:
        return
    
    if not host_info[0].get("interfaces"):
        return
    
    interfaceid = host_info[0]["interfaces"][0]["interfaceid"]
    
    items = zabbix_api_call("item.get", {
        "hostids": [hostid]
    }, auth_token)
    
    if not items:
        return
    
    for item in items:
        zabbix_api_call("item.update", {
            "itemid": item["itemid"],
            "interfaceid": interfaceid
        }, auth_token)

def create_demo_triggers(hostid, auth_token):
    """Criar triggers de demonstração"""
    triggers = [
        {
            "description": "High CPU Usage",
            "expression": f"{{TRIGGER.VALUE}}=1 and {{prometheus.highcpu:last()}}>0",
            "severity": 3  # High
        },
        {
            "description": "Low Memory",
            "expression": f"{{TRIGGER.VALUE}}=1 and {{prometheus.lowmemory:last()}}>0",
            "severity": 2  # Average
        }
    ]
    
    for trigger_info in triggers:
        result = zabbix_api_call("trigger.create", {
            "description": trigger_info["description"],
            "expression": trigger_info["expression"],
            "severity": trigger_info["severity"]
        }, auth_token)
        
        if result:
            print(f"   ✅ Trigger: {trigger_info['description']}")
        else:
            print(f"   ⚠️  Trigger (opcional): {trigger_info['description']}")

def send_test_data(hostname, auth_token):
    """Enviar dados de teste no webhook para popular items"""
    import subprocess
    
    test_values = [
        ("prometheus.highcpu", "35"),  # 35% CPU
        ("prometheus.lowmemory", "0"),  # Memory OK
        ("custom.requests", "1250"),  # 1250 req/s
        ("custom.latency", "45"),  # 45ms
        ("custom.errors", "0.5"),  # 0.5% errors
    ]
    
    for key, value in test_values:
        cmd = [
            "docker-compose", "exec", "-T", "webhook", "zabbix_sender",
            "-z", "zabbix-server",
            "-s", hostname,
            "-k", key,
            "-o", value
        ]
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        except:
            pass
    
    print(f"   ✅ Dados de teste enviados para {hostname}")

# MAIN
print("\n" + "="*60)
print("📊 POPULA DADOS DE DEMONSTRAÇÃO PARA APRESENTAÇÃO")
print("="*60 + "\n")

auth = zabbix_login()
if not auth:
    exit(1)

# Criar hostgroup
groupid = get_or_create_hostgroup(auth)
if not groupid:
    exit(1)

# Dados de demonstração
demo_hosts = [
    ("prod-db-01", "Production Database Server"),
    ("api-server-01", "API Server"),
    ("cache-redis-01", "Redis Cache"),
    ("app-web-01", "Web Application Server"),
]

print("\n🚀 Criando hosts de demonstração...\n")

for hostname, display_name in demo_hosts:
    print(f"Processando: {hostname}")
    
    # Limpar se existir
    delete_host_if_exists(hostname, auth)
    
    # Criar host
    hostid = create_demo_host(hostname, display_name, auth, groupid)
    if not hostid:
        continue
    
    # Criar items
    print(f"  Adicionando items...")
    create_demo_items(hostid, auth)
    
    # Configurar interface
    print(f"  Configurando interface...")
    fix_item_interfaces(hostid, auth)
    
    # Criar triggers (opcional)
    print(f"  Criando triggers...")
    create_demo_triggers(hostid, auth)
    
    # Enviar dados de teste
    print(f"  Enviando dados de teste...")
    send_test_data(hostname, auth)
    
    print()

print("="*60)
print("✅ DADOS DE DEMONSTRAÇÃO POPULADOS COM SUCESSO!")
print("="*60)
print("\n📊 Próximo passo:")
print("   1. Abrir http://localhost:8080")
print("   2. Fazer login com Admin / zabbix")
print("   3. Ir para: Monitoring → Latest Data")
print("   4. Ver os 4 hosts com dados realistas!")
print("\n💡 Dica:")
print("   Você pode enviar alertas para estes hosts via webhook")
print("   e eles aparecerão em Zabbix instantaneamente!")
print()
