import httpx
import json
import re
import logging
from typing import Dict, Any, List, Optional

from .zabbix_manager import ZabbixManager
from .grafana_client import GrafanaClient

logger = logging.getLogger(__name__)

# Problem → remediation strategy mapping
_REMEDIATION_RULES = [
    # (keywords_in_problem_name, strategy, reason)
    (["agent", "not available", "unreachable", "unavailable", "ping"],
     "fix_agent",
     "Agent não disponível — ativando monitorização interna e verificando configuração"),
    (["no data", "nodata", "sem dados"],
     "fix_agent",
     "Sem dados — ativando monitorização interna"),
    (["not running", "process", "service", "daemon"],
     "maintenance",
     "Serviço não disponível — host em manutenção por 4h"),
    (["disk", "filesystem", "space", "storage", "espaço", "disco"],
     "acknowledge",
     "Problema de disco — reconhecido para análise manual"),
    (["cpu", "memory", "ram", "load", "carga"],
     "acknowledge",
     "Problema de performance — reconhecido para análise manual"),
]

def _pick_remediation(problem_name: str) -> tuple:
    """Return (strategy, reason) for a given problem name."""
    pn = problem_name.lower()
    for keywords, strategy, reason in _REMEDIATION_RULES:
        if any(kw in pn for kw in keywords):
            return strategy, reason
    return "acknowledge", "Problema reconhecido pelo assistente de IA"


PROMPT_TEMPLATE = """You are an automation and diagnostics assistant for Zabbix and Grafana.
Analyze the user request and respond ONLY with valid JSON.

Available Zabbix hosts:
{hosts}

Available Zabbix templates:
{templates}

AVAILABLE ACTIONS:

=== DIAGNOSTICS ===
get_active_problems
  params: {{"host_name": "optional"}}
  Use for: "problemas", "a quanto tempo", "o que está a falhar", "está com problemas", "alertas ativos", "erros", "avisos", "fora", "indisponivel", "não responde", "estado"

get_host_status
  params: {{"host_name": "required"}}
  Use for: "estado de X", "health de X", "como está X", "verificar host X", "disponibilidade"

acknowledge_problem
  params: {{"host_name": "required", "problem_name": "partial description", "message": "reason"}}
  Use for: "aceitar problema", "acknowledge", "reconhecer alerta"

fix_problem
  params: {{"host_name": "optional"}}
  Use for: "arranja", "corrige", "resolve", "fix", "repara", "trata o problema", "soluciona", "remedeia"
  Analyzes active problems and applies the best automated remediation for each one.

get_zabbix_items
  params: {{"host_name": "required"}}

get_zabbix_triggers
  params: {{"host_name": "required"}}

=== LISTS ===
list_zabbix_hosts
  params: {{}}

list_zabbix_templates
  params: {{}}

list_grafana_dashboards
  params: {{}}

=== CREATE ZABBIX ===
create_zabbix_item
  params: {{"host_name": "X", "name": "X", "key_": "X", "value_type": "float/uint/string/text", "delay": "60s", "units": "%"}}

create_zabbix_trigger
  params: {{"host_name": "X", "description": "X", "expression": "X", "priority": "info/warning/average/high/disaster"}}
  Expression syntax (Zabbix 5.x): {{{{HOST:KEY.last()}}}} > VALUE
  Examples: {{{{web01:system.cpu.util[,user].last()}}}}>90  |  {{{{web01:vfs.fs.size[/,pfree].last()}}}}<10

create_zabbix_template
  params: {{"name": "X", "description": "optional"}}

create_zabbix_host
  params: {{"hostname": "X", "ip": "127.0.0.1", "port": 10050, "group_name": "Linux servers"}}

=== CREATE GRAFANA ===
create_grafana_dashboard
  params: {{"title": "X", "dashboard_type": "overview/cpu/memory/disk/network/custom", "instance_filter": "optional"}}

create_grafana_folder
  params: {{"name": "X"}}

=== DELETE ===
delete_grafana_dashboard
  params: {{"title": "optional — omit to delete ALL"}}
  Use for: "excluir dashboard", "apagar dashboard", "deletar dashboard", "remover dashboard"

delete_zabbix_host
  params: {{"host_name": "required"}}
  Use for: "excluir host", "apagar host", "remover host"

delete_zabbix_item
  params: {{"host_name": "required", "item_name": "partial match"}}

disable_zabbix_trigger
  params: {{"host_name": "required", "trigger_name": "partial match"}}

enable_zabbix_trigger
  params: {{"host_name": "required", "trigger_name": "partial match"}}

=== FALLBACK ===
unknown — use ONLY when truly cannot understand

User request: {user_message}

JSON response:
{{"action": "ACTION_NAME", "params": {{...}}, "explanation": "O que vou fazer (em português)"}}"""


SEVERITY_LABELS = {0: "Not classified", 1: "Info", 2: "Warning", 3: "Average", 4: "High", 5: "Disaster"}
SEVERITY_EMOJI  = {0: "⚪", 1: "🔵", 2: "🟡", 3: "🟠", 4: "🔴", 5: "💀"}
AVAIL_LABELS    = {"0": "Unknown", "1": "Available", "2": "Unavailable"}


def _extract_json(text: str) -> Optional[Dict]:
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return None


def _fast_classify(message: str) -> Optional[Dict]:
    """Instant classification using object+intent detection — handles broad Portuguese variation."""
    ml = message.lower()

    # ── Detect objects ────────────────────────────────────────────────────────
    has_dashboard = bool(re.search(r'dashboard|dash\b', ml))
    has_host      = bool(re.search(r'\bhost[s]?\b|\bservidor[es]?\b|\bmáquina[s]?\b|\bserver[s]?\b', ml))
    has_template  = bool(re.search(r'\btemplate[s]?\b|\bmodelo[s]?\b', ml))
    has_trigger   = bool(re.search(r'\btrigger[s]?\b|\bgatilho[s]?\b', ml))
    has_item      = bool(re.search(r'\bitem[s]?\b|\bmétrica[s]?\b|\bmetric[s]?\b', ml))
    has_problem   = bool(re.search(r'\bproblem|\balerta[s]?\b|\bfalhando|\bfora\b|\bindispon|\berro[s]?\b|\baviso[s]?\b|\bativo[s]?\b', ml))

    # ── Detect intent ─────────────────────────────────────────────────────────
    is_fix    = bool(re.search(r'arran[jg]|corrig|resolv|repara|soluciona|remedeia|conserta|fix\b', ml))
    is_delete = bool(re.search(r'\bexclu|\bdelet|\bremov|\bapag', ml))
    is_create = bool(re.search(r'\bcriar?\b|\bcria\b|\bnov[oa]\b|\badiciona|\bgera[r]?\b|\bmonta[r]?\b|\bprecis|\bquero\b|\bfaz[e]?\b', ml))
    is_list   = bool(re.search(r'\bver\b|\bveja\b|\bmostra[r]?\b|\blist[a]?[r]?\b|\btem\b|\bexist|\bhá\b|\bquai[s]?\b|\bverific|\bcheck\b|\bsão\b|\bquant[o]?', ml))
    is_diag   = bool(re.search(r'\bquanto tempo|\bfalhar|\bfora\b|\bindispon|\bquant[o]?[s]? problem', ml))
    is_enable  = bool(re.search(r'\bativa[r]?\b|\benable\b|\bliga[r]?\b|\bligar\b', ml))
    is_disable = bool(re.search(r'\bdesativ|\bdisable\b|\bdesliga[r]?\b', ml))
    is_status  = bool(re.search(r'\bestado\b|\bhealth\b|\bstatus\b|\bdisponib|\bcomo est[aá]\b|\bverific', ml))

    # ── Fix / remediation ─────────────────────────────────────────────────────
    if is_fix and (has_problem or has_host):
        host = _extract_hostname(ml)
        return {"action": "fix_problem",
                "params": {"host_name": host} if host else {},
                "explanation": f"Analisando e corrigindo problemas{' no host ' + host if host else ''}"}

    # ── Active problems ───────────────────────────────────────────────────────
    if has_problem or is_diag:
        host = _extract_hostname(ml)
        if is_status and host:
            return {"action": "get_host_status", "params": {"host_name": host},
                    "explanation": f"Verificando estado do host {host}"}
        return {"action": "get_active_problems",
                "params": {"host_name": host} if host else {},
                "explanation": f"Verificando problemas ativos{' no host ' + host if host else ''}"}

    # ── Host status ───────────────────────────────────────────────────────────
    if is_status and has_host:
        host = _extract_hostname(ml)
        if host:
            return {"action": "get_host_status", "params": {"host_name": host},
                    "explanation": f"Verificando estado do host {host}"}

    # ── Delete ────────────────────────────────────────────────────────────────
    if is_delete:
        if has_dashboard:
            title_m = re.search(r'(?:dashboard|dash)\s+["\']?([^"\']+?)["\']?\s*(?:do grafana|$)', ml)
            title   = title_m.group(1).strip() if title_m else ""
            quoted  = f'"{title}"' if title else "(todos)"
            return {"action": "delete_grafana_dashboard",
                    "params": {"title": title} if title else {},
                    "explanation": f"Excluindo dashboard {quoted}"}
        if has_host:
            host = _extract_hostname(ml)
            return {"action": "delete_zabbix_host",
                    "params": {"host_name": host or ""},
                    "explanation": f"Excluindo host {host or ''}"}

    # ── Enable / disable trigger ──────────────────────────────────────────────
    if has_trigger and is_enable:
        host = _extract_hostname(ml)
        return {"action": "enable_zabbix_trigger",
                "params": {"host_name": host or ""}, "explanation": "Ativando trigger"}
    if has_trigger and is_disable:
        host = _extract_hostname(ml)
        return {"action": "disable_zabbix_trigger",
                "params": {"host_name": host or ""}, "explanation": "Desativando trigger"}

    # ── Create dashboard (before list, so "cria dashboard" beats "lista") ─────
    if has_dashboard and is_create:
        dtype, title = "overview", "Infrastructure Overview"
        if re.search(r'gerenci|executiv|gestion|resumo geral', ml):
            dtype, title = "management", "Management Overview"
        elif re.search(r'\bcpu\b', ml):     dtype, title = "cpu",      "CPU Monitoring"
        elif re.search(r'memor|ram\b', ml): dtype, title = "memory",   "Memory Monitoring"
        elif re.search(r'rede|network', ml):dtype, title = "network",  "Network Monitoring"
        elif re.search(r'disco|disk', ml):  dtype, title = "disk",     "Disk Monitoring"
        title_m = re.search(r'(?:título|titulo|title|chamado|nome)[:\s]+["\']?([^"\'\n]{3,40})', ml)
        if title_m:
            title = title_m.group(1).strip()
        return {"action": "create_grafana_dashboard",
                "params": {"title": title, "dashboard_type": dtype},
                "explanation": f"Criando dashboard '{title}'"}

    # ── Lists — most specific first ───────────────────────────────────────────
    if has_trigger and is_list:
        host = _extract_hostname(ml)
        if host:
            return {"action": "get_zabbix_triggers", "params": {"host_name": host},
                    "explanation": f"Listando triggers do host {host}"}
    if has_item and is_list:
        host = _extract_hostname(ml)
        if host:
            return {"action": "get_zabbix_items", "params": {"host_name": host},
                    "explanation": f"Listando items do host {host}"}
    if has_template and is_list:
        return {"action": "list_zabbix_templates", "params": {}, "explanation": "Listando templates"}
    if has_dashboard and is_list:
        return {"action": "list_grafana_dashboards", "params": {}, "explanation": "Listando dashboards"}
    if has_host and is_list and not is_create and not is_delete:
        return {"action": "list_zabbix_hosts", "params": {}, "explanation": "Listando hosts"}

    return None  # Let LLM handle it


_PT_STOPWORDS = {
    "problemas", "ativos", "ativas", "erros", "avisos", "alertas", "todos", "todas",
    "tenho", "hosts", "host", "o", "a", "os", "as", "que", "no", "na", "do", "da",
    "para", "com", "sem", "mais", "menos", "status", "estado", "health",
    "ativo", "ativa", "problema", "alerta", "erro", "aviso",
}


def _extract_hostname(text: str) -> Optional[str]:
    """Try to extract a host name (possibly multi-word) from the message.

    Matches explicit host indicators only to avoid false positives with
    Portuguese prepositions like 'de'.
    """
    # Multi-word: "do host Zabbix server", "no host web-01 prod"
    match = re.search(
        r'\b(?:no host|do host|para o host|para host|host)\s+([a-zA-Z0-9._-]+(?:\s+[a-zA-Z0-9._-]+)?)',
        text, re.I
    )
    if match:
        candidate = match.group(1).strip()
        if candidate.lower() not in _PT_STOPWORDS:
            return candidate
    return None


def _fallback_intent(message: str) -> Dict:
    """Keyword-based fallback when LLM is unavailable."""
    ml = message.lower()
    is_create = any(w in ml for w in ["cria", "criar", "add", "novo", "nova", "adiciona", "create"])
    is_list   = any(w in ml for w in ["lista", "listar", "mostrar", "show", "ver", "list"])
    is_diag   = any(w in ml for w in ["problema", "erro", "fora", "falhar", "alerta", "quanto tempo",
                                        "estado", "health", "disponib", "indispon", "status"])

    if is_diag:
        return {"action": "get_active_problems", "params": {}, "explanation": "Verificando problemas ativos no Zabbix"}
    if is_list:
        if "host" in ml:
            return {"action": "list_zabbix_hosts", "params": {}, "explanation": "Listando hosts do Zabbix"}
        if "template" in ml:
            return {"action": "list_zabbix_templates", "params": {}, "explanation": "Listando templates do Zabbix"}
        if "dashboard" in ml:
            return {"action": "list_grafana_dashboards", "params": {}, "explanation": "Listando dashboards do Grafana"}
    if is_create:
        hints = {
            "trigger":   "Para criar um trigger preciso: host, condição (ex: CPU > 90%), severidade.",
            "dashboard": "Para criar um dashboard preciso: título e tipo (overview, cpu, memory, disk, network).",
            "item":      "Para criar um item preciso: host, nome e chave do item.",
            "host":      "Para criar um host preciso: nome e IP.",
            "template":  "Para criar um template preciso: nome.",
        }
        for key, hint in hints.items():
            if key in ml:
                return {"action": "unknown", "params": {}, "explanation": hint}
    return {
        "action": "unknown",
        "params": {},
        "explanation": (
            "Não consegui entender o pedido.\n"
            "Exemplos:\n"
            "• 'Quais os problemas ativos?'\n"
            "• 'Estado do host Zabbix server'\n"
            "• 'Cria um trigger de CPU > 90% no host web01'\n"
            "• 'Cria um dashboard de overview'\n"
            "• 'Lista os hosts'"
        ),
    }


class AssistantEngine:
    def __init__(self, zabbix: ZabbixManager, grafana: GrafanaClient,
                 ollama_url: str, model: str, grafana_external_url: str):
        self.zabbix = zabbix
        self.grafana = grafana
        self.ollama_url = ollama_url
        self.model = model
        self.grafana_ext = grafana_external_url.rstrip("/")

    async def process(self, message: str) -> Dict:
        context = await self._get_context()
        intent  = await self._classify(message, context)
        return await self._execute(intent, context)

    async def _get_context(self) -> Dict:
        try:
            ok = await self.zabbix.authenticate()
            if ok:
                hosts     = await self.zabbix.get_hosts()
                templates = await self.zabbix.get_templates()
                return {"hosts": hosts, "templates": templates, "zabbix_ok": True}
        except Exception as e:
            logger.warning(f"Context fetch failed: {e}")
        return {"hosts": [], "templates": [], "zabbix_ok": False}

    async def _classify(self, message: str, context: Dict) -> Dict:
        # Fast path: skip LLM for unambiguous queries
        fast = _fast_classify(message)
        if fast:
            logger.info(f"Fast-path: {fast['action']} (no LLM needed)")
            return fast

        # Slow path: call LLM for complex/ambiguous queries
        hosts_short     = [{"id": h["hostid"], "name": h["host"]} for h in context["hosts"][:25]]
        templates_short = [{"id": t["templateid"], "name": t["host"]} for t in context["templates"][:15]]
        prompt = PROMPT_TEMPLATE.format(
            hosts=json.dumps(hosts_short, ensure_ascii=False),
            templates=json.dumps(templates_short, ensure_ascii=False),
            user_message=message,
        )
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                        "options": {"temperature": 0.1, "num_predict": 600},
                    },
                    timeout=15,
                )
                r.raise_for_status()
                raw    = r.json().get("response", "")
                logger.debug(f"LLM raw: {raw[:300]}")
                parsed = _extract_json(raw)
                if parsed and "action" in parsed:
                    return parsed
        except Exception as e:
            logger.warning(f"LLM unavailable ({type(e).__name__}) — using fallback")
        return _fallback_intent(message)

    async def _execute(self, intent: Dict, context: Dict) -> Dict:
        action      = intent.get("action", "unknown")
        params      = intent.get("params", {}) or {}
        explanation = intent.get("explanation", "")
        try:
            dispatch = {
                "create_zabbix_item":      self._do_create_item,
                "create_zabbix_trigger":   self._do_create_trigger,
                "create_zabbix_template":  self._do_create_template,
                "create_zabbix_host":      self._do_create_host,
                "create_grafana_dashboard":self._do_create_dashboard,
                "create_grafana_folder":   self._do_create_folder,
                "list_zabbix_hosts":       self._do_list_hosts,
                "list_zabbix_templates":   self._do_list_templates,
                "list_grafana_dashboards": self._do_list_dashboards,
                "get_zabbix_items":        self._do_get_items,
                "get_zabbix_triggers":     self._do_get_triggers,
                "get_active_problems":     self._do_get_active_problems,
                "get_host_status":         self._do_get_host_status,
                "acknowledge_problem":     self._do_acknowledge_problem,
                "fix_problem":             self._do_fix_problem,
                "delete_grafana_dashboard":self._do_delete_dashboard,
                "delete_zabbix_host":      self._do_delete_host,
                "delete_zabbix_item":      self._do_delete_item,
                "disable_zabbix_trigger":  self._do_toggle_trigger,
                "enable_zabbix_trigger":   self._do_toggle_trigger,
            }
            if action in dispatch:
                fn = dispatch[action]
                if action in ("list_zabbix_hosts", "list_zabbix_templates",
                              "get_active_problems", "fix_problem",
                              "delete_zabbix_host", "delete_zabbix_item",
                              "disable_zabbix_trigger", "enable_zabbix_trigger"):
                    return await fn(params, context)
                elif action in ("list_grafana_dashboards", "create_grafana_dashboard",
                                "create_grafana_folder", "delete_grafana_dashboard"):
                    return await fn(params)
                else:
                    return await fn(params, context)
            return {
                "success": True,
                "action":  "info",
                "message": explanation or "Pode reformular o pedido com mais detalhes?",
                "data":    None,
                "links":   None,
            }
        except Exception as e:
            logger.error(f"Action {action} failed: {e}")
            return {
                "success": False,
                "action":  action,
                "message": f"Erro: {str(e)}",
                "data":    None,
                "links":   None,
            }

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def _resolve_host(self, host_name: str, context: Dict) -> Dict:
        if not host_name:
            raise ValueError("Nome do host não especificado.")
        host = self.zabbix.find_host(host_name, context["hosts"])
        if not host:
            raise ValueError(
                f"Host '{host_name}' não encontrado. "
                f"Hosts disponíveis: {', '.join(h['host'] for h in context['hosts'][:10])}"
            )
        return host

    # ── Diagnostic actions ────────────────────────────────────────────────────

    async def _do_get_active_problems(self, params: Dict, context: Dict) -> Dict:
        host_name = params.get("host_name", "")
        hostid    = None
        host_label = "todos os hosts"

        if host_name:
            host       = await self._resolve_host(host_name, context)
            hostid     = host["hostid"]
            host_label = host["host"]

        problems = await self.zabbix.get_active_problems(hostid)

        if not problems:
            return {
                "success": True,
                "action":  "get_active_problems",
                "message": f"Nenhum problema ativo em **{host_label}**. Tudo operacional!",
                "data":    {"problems": [], "count": 0, "host": host_label},
                "links":   {"zabbix": f"{self.zabbix.url}/zabbix.php?action=problem.view"},
            }

        items = []
        for p in problems:
            sev  = int(p.get("severity", 0))
            host = p.get("hosts", [{}])[0].get("host", "?")
            items.append({
                "eventid":     p.get("eventid"),
                "name":        p.get("name", "?"),
                "severity":    SEVERITY_LABELS.get(sev, "?"),
                "severity_num":sev,
                "emoji":       SEVERITY_EMOJI.get(sev, "⚪"),
                "duration":    p.get("duration", "?"),
                "host":        host,
                "acknowledged":p.get("acknowledged", False),
            })

        worst_sev = max(i["severity_num"] for i in items)
        return {
            "success": True,
            "action":  "get_active_problems",
            "message": f"**{len(items)}** problema(s) ativo(s) em **{host_label}**.",
            "data": {
                "problems": items,
                "count":    len(items),
                "host":     host_label,
                "worst_severity": SEVERITY_LABELS.get(worst_sev, "?"),
            },
            "links": {"zabbix": f"{self.zabbix.url}/zabbix.php?action=problem.view"},
        }

    async def _do_get_host_status(self, params: Dict, context: Dict) -> Dict:
        host      = await self._resolve_host(params.get("host_name", ""), context)
        problems  = await self.zabbix.get_active_problems(host["hostid"])
        avail_info = await self.zabbix.get_host_availability(host["hostid"])

        avail_code  = avail_info.get("available", "0")
        avail_label = AVAIL_LABELS.get(str(avail_code), "Unknown")
        avail_ok    = str(avail_code) == "1"

        prob_items = []
        for p in problems:
            sev = int(p.get("severity", 0))
            prob_items.append({
                "name":     p.get("name", "?"),
                "severity": SEVERITY_LABELS.get(sev, "?"),
                "emoji":    SEVERITY_EMOJI.get(sev, "⚪"),
                "duration": p.get("duration", "?"),
            })

        status_emoji = "✅" if (avail_ok and not problems) else ("⚠️" if problems else "❌")
        return {
            "success": True,
            "action":  "get_host_status",
            "message": f"{status_emoji} Host **{host['host']}**: {avail_label} — {len(problems)} problema(s) ativo(s).",
            "data": {
                "host":        host["host"],
                "availability":avail_label,
                "available":   avail_ok,
                "problems":    prob_items,
                "problem_count":len(problems),
                "agent_error": avail_info.get("error", ""),
            },
            "links": {
                "zabbix": f"{self.zabbix.url}/zabbix.php?action=problem.view&hostids%5B%5D={host['hostid']}",
            },
        }

    async def _do_acknowledge_problem(self, params: Dict, context: Dict) -> Dict:
        host = await self._resolve_host(params.get("host_name", ""), context)
        problems = await self.zabbix.get_active_problems(host["hostid"])

        search = params.get("problem_name", "").lower()
        target = None
        for p in problems:
            if not search or search in p.get("name", "").lower():
                target = p
                break

        if not target:
            return {
                "success": False,
                "action":  "acknowledge_problem",
                "message": f"Nenhum problema encontrado para '{search}' no host **{host['host']}**.",
                "data":    None,
                "links":   None,
            }

        message = params.get("message", "Acknowledged by AI Assistant")
        await self.zabbix.acknowledge_problem(target["eventid"], message)
        return {
            "success": True,
            "action":  "acknowledge_problem",
            "message": f"Problema **{target['name']}** reconhecido no host **{host['host']}**.",
            "data": {"eventid": target["eventid"], "problem": target["name"], "message": message},
            "links": {"zabbix": f"{self.zabbix.url}/zabbix.php?action=problem.view"},
        }

    # ── Zabbix create/read actions ────────────────────────────────────────────

    async def _do_create_item(self, params: Dict, context: Dict) -> Dict:
        host    = await self._resolve_host(params.get("host_name", ""), context)
        result  = await self.zabbix.create_item(
            hostid=host["hostid"],
            name=params.get("name", "New Item"),
            key_=params.get("key_", "custom.item"),
            value_type=params.get("value_type", "float"),
            delay=params.get("delay", "60s"),
            units=params.get("units", ""),
        )
        item_id = result.get("itemids", ["?"])[0]
        return {
            "success": True,
            "action":  "create_zabbix_item",
            "message": f"Item **{params.get('name')}** criado no host **{host['host']}**.",
            "data": {
                "itemid": item_id, "name": params.get("name"),
                "key_": params.get("key_"), "host": host["host"],
                "value_type": params.get("value_type"), "delay": params.get("delay", "60s"),
            },
            "links": {"zabbix": f"{self.zabbix.url}/items.php?filter_set=1&filter_hostids%5B%5D={host['hostid']}"},
        }

    async def _do_create_trigger(self, params: Dict, context: Dict) -> Dict:
        host_name = params.get("host_name", "")
        if host_name:
            await self._resolve_host(host_name, context)
        description = params.get("description", "New Trigger")
        expression  = params.get("expression", "")
        priority    = params.get("priority", "average")
        result      = await self.zabbix.create_trigger(description=description, expression=expression, priority=priority)
        trigger_id  = result.get("triggerids", ["?"])[0]
        prio_num    = {"info": 1, "warning": 2, "average": 3, "high": 4, "disaster": 5}.get(
            str(priority).lower(), priority if isinstance(priority, int) else 3)
        return {
            "success": True,
            "action":  "create_zabbix_trigger",
            "message": f"Trigger **{description}** criado com sucesso.",
            "data": {
                "triggerid": trigger_id, "description": description,
                "expression": expression,
                "priority": SEVERITY_LABELS.get(prio_num, str(priority)),
                "host": host_name,
            },
            "links": {"zabbix": f"{self.zabbix.url}/triggers.php"},
        }

    async def _do_create_template(self, params: Dict, context: Dict) -> Dict:
        result  = await self.zabbix.create_template(name=params.get("name", "New Template"), description=params.get("description", ""))
        tmpl_id = result.get("templateids", ["?"])[0]
        return {
            "success": True,
            "action":  "create_zabbix_template",
            "message": f"Template **{params.get('name')}** criado.",
            "data":    {"templateid": tmpl_id, "name": params.get("name")},
            "links":   {"zabbix": f"{self.zabbix.url}/templates.php"},
        }

    async def _do_create_host(self, params: Dict, context: Dict) -> Dict:
        group_name = params.get("group_name", "Linux servers")
        groups     = await self.zabbix.get_hostgroups()
        group      = self.zabbix.find_hostgroup(group_name, groups)
        group_id   = group["groupid"] if group else (await self.zabbix.create_hostgroup(group_name)).get("groupids", ["1"])[0]
        hostname   = params.get("hostname", "new-host")
        result     = await self.zabbix.create_host(hostname=hostname, group_ids=[group_id], ip=params.get("ip", "127.0.0.1"), port=int(params.get("port", 10050)))
        host_id    = result.get("hostids", ["?"])[0]
        return {
            "success": True,
            "action":  "create_zabbix_host",
            "message": f"Host **{hostname}** criado no grupo **{group_name}**.",
            "data":    {"hostid": host_id, "hostname": hostname, "ip": params.get("ip", "127.0.0.1"), "group": group_name},
            "links":   {"zabbix": f"{self.zabbix.url}/hosts.php"},
        }

    async def _do_list_hosts(self, params: Dict, context: Dict) -> Dict:
        hosts = context.get("hosts") or await self.zabbix.get_hosts()
        items = [{"id": h["hostid"], "name": h["host"], "display_name": h.get("name", h["host"])} for h in hosts]
        return {
            "success": True,
            "action":  "list_zabbix_hosts",
            "message": f"Encontrados **{len(items)}** hosts no Zabbix.",
            "data":    {"hosts": items, "count": len(items)},
            "links":   {"zabbix": f"{self.zabbix.url}/hosts.php"},
        }

    async def _do_list_templates(self, params: Dict, context: Dict) -> Dict:
        templates = context.get("templates") or await self.zabbix.get_templates()
        items = [{"id": t["templateid"], "name": t["host"]} for t in templates]
        return {
            "success": True,
            "action":  "list_zabbix_templates",
            "message": f"Encontrados **{len(items)}** templates.",
            "data":    {"templates": items, "count": len(items)},
            "links":   {"zabbix": f"{self.zabbix.url}/templates.php"},
        }

    async def _do_get_items(self, params: Dict, context: Dict) -> Dict:
        host  = await self._resolve_host(params.get("host_name", ""), context)
        items = await self.zabbix.get_items(host["hostid"])
        simplified = [{"id": i["itemid"], "name": i["name"], "key": i["key_"]} for i in items]
        return {
            "success": True,
            "action":  "get_zabbix_items",
            "message": f"Host **{host['host']}** tem **{len(simplified)}** items.",
            "data":    {"host": host["host"], "items": simplified, "count": len(simplified)},
            "links":   {"zabbix": f"{self.zabbix.url}/items.php?filter_set=1&filter_hostids%5B%5D={host['hostid']}"},
        }

    async def _do_get_triggers(self, params: Dict, context: Dict) -> Dict:
        host     = await self._resolve_host(params.get("host_name", ""), context)
        triggers = await self.zabbix.get_triggers(host["hostid"])
        simplified = [{
            "id": t["triggerid"], "description": t["description"],
            "expression": t["expression"],
            "priority": SEVERITY_LABELS.get(int(t.get("priority", 0)), "?"),
            "status": "Enabled" if t.get("status") == "0" else "Disabled",
        } for t in triggers]
        return {
            "success": True,
            "action":  "get_zabbix_triggers",
            "message": f"Host **{host['host']}** tem **{len(simplified)}** triggers.",
            "data":    {"host": host["host"], "triggers": simplified, "count": len(simplified)},
            "links":   {"zabbix": f"{self.zabbix.url}/triggers.php?filter_set=1&filter_hostids%5B%5D={host['hostid']}"},
        }

    # ── Smart remediation ─────────────────────────────────────────────────────

    async def _do_fix_problem(self, params: Dict, context: Dict) -> Dict:
        host_name  = params.get("host_name", "")
        hostid     = None
        host_label = "todos os hosts"

        if host_name:
            host       = await self._resolve_host(host_name, context)
            hostid     = host["hostid"]
            host_label = host["host"]

        problems = await self.zabbix.get_active_problems(hostid)
        if not problems:
            return {
                "success": True,
                "action":  "fix_problem",
                "message": f"Nenhum problema ativo em **{host_label}**. Ambiente operacional!",
                "data":    {"fixes": [], "host": host_label},
                "links":   None,
            }

        # Pre-load all hosts so we can resolve hostids from problem host names
        all_hosts = context.get("hosts") or []

        fixes = []
        for p in problems:
            pname    = p.get("name", "")
            eventid  = p.get("eventid")
            p_hosts  = p.get("hosts") or []
            p_hostid = p_hosts[0].get("hostid") if p_hosts else hostid
            p_host   = p_hosts[0].get("host", host_label) if p_hosts else host_label

            # If Zabbix didn't populate selectHosts, try to find host from all_hosts
            if not p_hostid and all_hosts:
                found = self.zabbix.find_host(p_host, all_hosts) if p_host != host_label else None
                if not found and hostid:
                    p_hostid = hostid
                elif found:
                    p_hostid = found["hostid"]
                    p_host   = found["host"]
                else:
                    # last resort: use first host
                    p_hostid = all_hosts[0]["hostid"] if all_hosts else None
                    p_host   = all_hosts[0]["host"] if all_hosts else host_label

            sev      = int(p.get("severity", 0))

            strategy, reason = _pick_remediation(pname)
            fix_result = {"problem": pname, "host": p_host, "strategy": strategy, "reason": reason, "done": False}

            try:
                if strategy == "fix_agent" and p_hostid:
                    # Re-enable the agent trigger if it was previously disabled by us
                    trigger = await self.zabbix.find_trigger_by_problem(p_hostid, pname)
                    if trigger and trigger.get("status") == "1":
                        await self.zabbix.enable_trigger(trigger["triggerid"])
                        fix_result["trigger_reenabled"] = trigger["description"]

                    # Add Zabbix internal monitoring items (no agent needed)
                    created = await self.zabbix.setup_internal_monitoring(p_hostid)

                    # Acknowledge the problem with a clear explanation
                    note = (
                        "[AI] Agent não instalado/inacessível. "
                        f"Monitorização interna ativada ({len(created)} items). "
                        "Para métricas completas (CPU/RAM/disco), instale o Zabbix Agent no host."
                    )
                    await self.zabbix.acknowledge_problem(eventid, note)

                    detail_parts = []
                    if trigger and trigger.get("status") == "1":
                        detail_parts.append("Trigger reativado")
                    if created:
                        detail_parts.append(f"{len(created)} items internos adicionados: " + ", ".join(created[:3]) + ("…" if len(created) > 3 else ""))
                    else:
                        detail_parts.append("Items internos já existiam ou foram adicionados")
                    detail_parts.append("Para CPU/RAM/disco: instale o Zabbix Agent no host")

                    fix_result["detail"] = " | ".join(detail_parts)
                    fix_result["internal_items"] = created
                    fix_result["done"] = True

                elif strategy == "maintenance" and p_hostid:
                    maint_name = f"AI Auto-Maintenance — {p_host}"
                    await self.zabbix.create_maintenance(maint_name, [p_hostid], duration_hours=4)
                    await self.zabbix.close_problem(eventid, f"[AI] Host em manutenção por 4h — {reason}")
                    fix_result["detail"] = "Host em manutenção por 4h e problema fechado"
                    fix_result["done"] = True

                else:  # acknowledge
                    await self.zabbix.close_problem(eventid, f"[AI Assistant] {reason}")
                    fix_result["detail"] = "Problema reconhecido e fechado pelo assistente"
                    fix_result["done"] = True

            except Exception as e:
                fix_result["error"] = str(e)

            fixes.append(fix_result)

        done_count  = sum(1 for f in fixes if f["done"])
        fail_count  = len(fixes) - done_count
        summary_parts = []
        if done_count:
            summary_parts.append(f"**{done_count}** problema(s) tratado(s)")
        if fail_count:
            summary_parts.append(f"**{fail_count}** com erro")

        return {
            "success": done_count > 0,
            "action":  "fix_problem",
            "message": f"{', '.join(summary_parts)} em **{host_label}**.",
            "data":    {"fixes": fixes, "host": host_label, "total": len(fixes), "done": done_count},
            "links":   {"zabbix": f"{self.zabbix.url}/zabbix.php?action=problem.view"},
        }

    # ── Delete / toggle actions ───────────────────────────────────────────────

    async def _do_delete_host(self, params: Dict, context: Dict) -> Dict:
        host = await self._resolve_host(params.get("host_name", ""), context)
        await self.zabbix._call("host.delete", [host["hostid"]])
        return {
            "success": True, "action": "delete_zabbix_host",
            "message": f"Host **{host['host']}** eliminado do Zabbix.",
            "data": {"host": host["host"], "hostid": host["hostid"]},
            "links": {"zabbix": f"{self.zabbix.url}/hosts.php"},
        }

    async def _do_delete_item(self, params: Dict, context: Dict) -> Dict:
        host  = await self._resolve_host(params.get("host_name", ""), context)
        items = await self.zabbix.get_items(host["hostid"])
        search = params.get("item_name", "").lower()
        targets = [i for i in items if not search or search in i["name"].lower()]
        if not targets:
            return {"success": False, "action": "delete_zabbix_item",
                    "message": f"Nenhum item encontrado com '{search}' no host **{host['host']}**.",
                    "data": None, "links": None}
        ids = [i["itemid"] for i in targets[:20]]
        await self.zabbix._call("item.delete", ids)
        return {
            "success": True, "action": "delete_zabbix_item",
            "message": f"**{len(ids)}** item(s) eliminado(s) no host **{host['host']}**.",
            "data": {"deleted": [i["name"] for i in targets[:20]], "count": len(ids)},
            "links": {"zabbix": f"{self.zabbix.url}/items.php?filter_set=1&filter_hostids%5B%5D={host['hostid']}"},
        }

    async def _do_toggle_trigger(self, params: Dict, context: Dict) -> Dict:
        action  = params.get("_action", "disable_zabbix_trigger")
        enable  = "enable" in action
        host    = await self._resolve_host(params.get("host_name", ""), context)
        search  = params.get("trigger_name", "").lower()
        triggers = await self.zabbix.get_triggers(host["hostid"])
        targets  = [t for t in triggers if not search or search in t["description"].lower()]
        if not targets:
            return {"success": False, "action": action,
                    "message": f"Nenhum trigger encontrado com '{search}' no host **{host['host']}**.",
                    "data": None, "links": None}
        for t in targets:
            if enable:
                await self.zabbix.enable_trigger(t["triggerid"])
            else:
                await self.zabbix.disable_trigger(t["triggerid"])
        verb = "ativado" if enable else "desativado"
        return {
            "success": True, "action": action,
            "message": f"**{len(targets)}** trigger(s) {verb}(s) no host **{host['host']}**.",
            "data": {"triggers": [t["description"] for t in targets[:10]], "count": len(targets)},
            "links": {"zabbix": f"{self.zabbix.url}/triggers.php?filter_set=1&filter_hostids%5B%5D={host['hostid']}"},
        }

    # ── Grafana actions ───────────────────────────────────────────────────────

    async def _do_create_dashboard(self, params: Dict) -> Dict:
        title   = params.get("title", "New Dashboard")
        dtype   = params.get("dashboard_type", "overview").lower()
        ifilter = params.get("instance_filter", "")
        if dtype == "management":
            dash = self.grafana.build_management_dashboard(title)
        elif dtype == "overview":
            dash = self.grafana.build_overview_dashboard(title, ifilter)
        elif dtype in ("cpu", "memory", "disk", "network"):
            dash = self.grafana.build_category_dashboard(title, dtype, ifilter)
        elif dtype == "custom" and params.get("panels"):
            dash = self.grafana.build_custom_dashboard(title, params["panels"])
        else:
            dash = self.grafana.build_overview_dashboard(title, ifilter)
        result   = await self.grafana.create_dashboard(dash)
        uid      = result.get("uid", "")
        url_path = result.get("url", f"/d/{uid}/")
        full_url = f"{self.grafana_ext}{url_path}"
        return {
            "success": True,
            "action":  "create_grafana_dashboard",
            "message": f"Dashboard **{title}** criado no Grafana.",
            "data":    {"uid": uid, "title": title, "type": dtype, "instance_filter": ifilter, "url": full_url},
            "links":   {"grafana": full_url},
        }

    async def _do_delete_dashboard(self, params: Dict) -> Dict:
        title   = params.get("title", "").lower().strip()
        all_dash = await self.grafana.list_dashboards()
        if title:
            targets = [d for d in all_dash if title in d.get("title", "").lower()]
        else:
            targets = all_dash
        if not targets:
            suffix = f' com "{title}"' if title else ""
            return {"success": False, "action": "delete_grafana_dashboard",
                    "message": f"Nenhum dashboard encontrado{suffix}.",
                    "data": None, "links": None}
        deleted = []
        for d in targets:
            try:
                await self.grafana.delete_dashboard(d["uid"])
                deleted.append(d["title"])
            except Exception as e:
                logger.warning(f"Could not delete dashboard {d['uid']}: {e}")
        return {
            "success": True, "action": "delete_grafana_dashboard",
            "message": f"**{len(deleted)}** dashboard(s) eliminado(s) no Grafana.",
            "data": {"deleted": deleted, "count": len(deleted)},
            "links": {"grafana": f"{self.grafana_ext}/dashboards"},
        }

    async def _do_create_folder(self, params: Dict) -> Dict:
        result = await self.grafana.create_folder(params.get("name", "New Folder"))
        return {
            "success": True,
            "action":  "create_grafana_folder",
            "message": f"Pasta **{result.get('title')}** criada no Grafana.",
            "data":    {"uid": result.get("uid"), "title": result.get("title")},
            "links":   {"grafana": f"{self.grafana_ext}/dashboards/f/{result.get('uid')}/"},
        }

    async def _do_list_dashboards(self, params: Dict = None) -> Dict:
        dashboards = await self.grafana.list_dashboards()
        items = [{"uid": d.get("uid"), "title": d.get("title"), "url": f"{self.grafana_ext}{d.get('url', '')}"} for d in dashboards]
        return {
            "success": True,
            "action":  "list_grafana_dashboards",
            "message": f"Encontrados **{len(items)}** dashboards no Grafana.",
            "data":    {"dashboards": items, "count": len(items)},
            "links":   {"grafana": f"{self.grafana_ext}/dashboards"},
        }
