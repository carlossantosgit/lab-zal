#!/usr/bin/env python3
"""Fix Zabbix items interface"""
import requests
import json
import time

ZABBIX_URL = "http://localhost:8080/api_jsonrpc.php"

def zabbix_call(method, params, auth_token):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "auth": auth_token,
        "id": 1
    }
    response = requests.post(ZABBIX_URL, json=payload)
    return response.json()

# Login
result = zabbix_call("user.login", {
    "user": "Admin",
    "password": "zabbix"
}, None)

token = result["result"]
print(f"✅ Logged in")

# Get all prometheus items
items = zabbix_call("item.get", {
    "filter": {"key_": ["prometheus.deadmansswitch", "prometheus.highcpu", "prometheus.lowmemory"]}
}, token)

print(f"Found {len(items['result'])} items")

# Update each item with interface
for item in items["result"]:
    result = zabbix_call("item.update", {
        "itemid": item["itemid"],
        "interfaceid": "2"  # The interface we found
    }, token)

    if "error" in result:
        print(f"❌ Failed to update {item['key_']}: {result['error']}")
    else:
        print(f"✅ Updated {item['key_']}")

print("\n✅ All items updated!")
