#!/usr/bin/env python3
"""
Add additional hosts to Zabbix for Prometheus alerts
"""
import requests
import json

ZABBIX_URL = "http://localhost:8080/api_jsonrpc.php"

def zabbix_call(method, params, auth_token=None):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    if auth_token:
        payload["auth"] = auth_token

    response = requests.post(ZABBIX_URL, json=payload)
    return response.json()

# Login
result = zabbix_call("user.login", {
    "user": "Admin",
    "password": "zabbix"
})

token = result["result"]
print(f"✅ Logged in")

# Get or create Prometheus group
groups = zabbix_call("hostgroup.get", {"filter": {"name": "Prometheus"}}, token)
groupid = groups["result"][0]["groupid"] if groups["result"] else None

print(f"Using group: {groupid}")

# Hosts to create
hosts_to_create = [
    {
        "name": "prometheus-server",
        "display_name": "Prometheus Server",
        "ip": "127.0.0.1"
    },
    {
        "name": "node-01",
        "display_name": "Node 01 (Local Node Exporter)",
        "ip": "127.0.0.1"
    }
]

for host_info in hosts_to_create:
    # Check if host already exists
    hosts = zabbix_call("host.get", {"filter": {"host": host_info["name"]}}, token)

    if hosts["result"]:
        print(f"⏭️  Host '{host_info['name']}' already exists")
        hostid = hosts["result"][0]["hostid"]
    else:
        # Create host
        result = zabbix_call("host.create", {
            "host": host_info["name"],
            "name": host_info["display_name"],
            "groups": [{"groupid": groupid}],
            "interfaces": [{
                "type": 1,
                "main": 1,
                "useip": 1,
                "ip": host_info["ip"],
                "dns": "",
                "port": "10050"
            }]
        }, token)

        if "error" in result:
            print(f"❌ Failed to create host '{host_info['name']}': {result['error']}")
            continue

        hostid = result["result"]["hostids"][0]
        print(f"✅ Created host: {host_info['name']} (ID: {hostid})")

    # Create items for this host
    alertitems = [
        {"key": "prometheus.deadmansswitch", "name": "Prometheus - Dead Man's Switch"},
        {"key": "prometheus.highcpu", "name": "Prometheus - High CPU"},
        {"key": "prometheus.lowmemory", "name": "Prometheus - Low Memory"},
    ]

    for item_info in alertitems:
        # Check if item already exists
        items = zabbix_call("item.get", {
            "filter": {"key_": item_info["key"], "hostid": hostid}
        }, token)

        if items["result"]:
            print(f"  ⏭️  Item '{item_info['key']}' already exists")
            continue

        # Create item
        result = zabbix_call("item.create", {
            "name": item_info["name"],
            "key_": item_info["key"],
            "hostid": hostid,
            "type": 2,  # Trapper
            "value_type": 3,  # Unsigned
            "history": "7d",
            "trends": "30d",
            "interfaceid": 0  # Trapper doesn't need interface
        }, token)

        if "error" in result:
            print(f"  ⚠️  Item '{item_info['key']}': {result['error']}")
        else:
            print(f"  ✅ Created item: {item_info['key']}")

print("\n✅ Setup completed!")
