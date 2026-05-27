import httpx
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class OllamaAnalyzer:
    def __init__(self, ollama_url: str, model: str = "mistral"):
        self.ollama_url = ollama_url
        self.model = model

    async def ensure_model_loaded(self) -> bool:
        """Ensure the model is available"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.ollama_url}/api/tags",
                    timeout=5,
                )
                response.raise_for_status()
                data = response.json()

                models = [m["name"] for m in data.get("models", [])]
                if f"{self.model}:latest" in models:
                    logger.info(f"✅ Model {self.model} is available")
                    return True
                else:
                    logger.warning(f"⚠️ Model {self.model} not found. Pulling...")
                    return await self._pull_model()
        except Exception as e:
            logger.error(f"❌ Error checking model: {e}")
            return False

    async def _pull_model(self) -> bool:
        """Pull model from Ollama"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_url}/api/pull",
                    json={"name": self.model},
                    timeout=300,
                )
                response.raise_for_status()
                logger.info(f"✅ Model {self.model} pulled successfully")
                return True
        except Exception as e:
            logger.error(f"❌ Error pulling model: {e}")
            return False

    async def analyze_alerts(
        self, alerts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze alerts using LLM"""
        if not alerts:
            return {
                "summary": "No alerts to analyze.",
                "recommendations": [],
                "patterns": [],
            }

        try:
            # Prepare alert summary
            alert_text = self._format_alerts(alerts)

            # Call Ollama with short timeout — fallback to local analysis if slow
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": self._create_analysis_prompt(alert_text),
                        "stream": False,
                    },
                    timeout=8,
                )
                response.raise_for_status()
                data = response.json()

                analysis_text = data.get("response", "")
                logger.info(f"✅ LLM analysis completed for {len(alerts)} alerts")

                return self._parse_analysis(analysis_text)
        except Exception as e:
            logger.warning(f"⚠️ LLM unavailable or slow ({e}) — using local analysis")
            return self._local_analysis(alerts)

    def _format_alerts(self, alerts: List[Dict[str, Any]]) -> str:
        """Format alerts for LLM analysis (supports both Zabbix and direct formats)"""
        formatted = []
        for alert in alerts:
            severity = alert.get("severity", "unknown")
            # Support both direct "host" and Zabbix "hosts" list
            host = alert.get("host") or (
                alert.get("hosts", [{}])[0].get("host", "unknown")
                if alert.get("hosts") else "unknown"
            )
            # Support both "message" and Zabbix "name"
            message = alert.get("message") or alert.get("name", "No message")
            timestamp = alert.get("timestamp") or alert.get("clock", "unknown")

            formatted.append(
                f"- [{severity}] Host: {host} | Message: {message} | Time: {timestamp}"
            )

        return "\n".join(formatted)

    def _create_analysis_prompt(self, alert_text: str) -> str:
        """Create analysis prompt for LLM"""
        # Send only first 10 alerts to keep prompt short and fast
        lines = alert_text.split("\n")[:10]
        short_text = "\n".join(lines)
        return f"""Infrastructure alerts summary:
{short_text}

Reply in 3 short sections:
1. Summary (1 sentence)
2. Patterns (2 bullet points starting with -)
3. Recommendations (2 bullet points starting with -)"""

    def _parse_analysis(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response into structured data"""
        # Simple parsing - in production you'd use more sophisticated parsing
        sections = response_text.split("\n\n")

        result = {
            "summary": sections[0] if len(sections) > 0 else "",
            "patterns": [],
            "recommendations": [],
            "risk_level": "Medium",
        }

        # Extract recommendations (usually after "recommendation" keyword)
        for section in sections:
            if "recommend" in section.lower():
                lines = [
                    line.strip()
                    for line in section.split("\n")
                    if line.strip() and line.startswith("-")
                ]
                result["recommendations"] = lines[:3]

            if "pattern" in section.lower():
                lines = [
                    line.strip()
                    for line in section.split("\n")
                    if line.strip() and line.startswith("-")
                ]
                result["patterns"] = lines[:3]

            if "risk" in section.lower():
                if "critical" in section.lower():
                    result["risk_level"] = "Critical"
                elif "high" in section.lower():
                    result["risk_level"] = "High"
                elif "low" in section.lower():
                    result["risk_level"] = "Low"

        return result

    def _local_analysis(self, alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Rule-based analysis when LLM is unavailable or too slow"""
        from collections import Counter

        severity_counts: Counter = Counter()
        hosts: Counter = Counter()
        messages = []

        for a in alerts:
            sev = str(a.get("severity", "low"))
            # Normalize Zabbix numeric severity
            sev_map = {"4": "critical", "5": "critical", "3": "high", "2": "medium", "1": "low", "0": "low"}
            sev = sev_map.get(sev, sev)
            severity_counts[sev] += 1

            host = a.get("host") or (a.get("hosts", [{}])[0].get("host", "unknown") if a.get("hosts") else "unknown")
            hosts[host] += 1
            messages.append(a.get("message") or a.get("name", ""))

        total = len(alerts)
        top_host = hosts.most_common(1)[0][0] if hosts else "unknown"
        risk = "Critical" if severity_counts["critical"] > 0 else ("High" if severity_counts["high"] > 0 else "Medium")

        # Detect common patterns
        patterns = []
        msg_text = " ".join(messages).lower()
        if "cpu" in msg_text or "memory" in msg_text:
            patterns.append("- Resource exhaustion detected: CPU/Memory pressure on multiple hosts")
        if "disk" in msg_text or "storage" in msg_text:
            patterns.append("- Storage capacity issues identified")
        if "database" in msg_text or "db" in msg_text or "sql" in msg_text:
            patterns.append("- Database layer showing stress indicators")
        if "network" in msg_text or "packet" in msg_text:
            patterns.append("- Network instability detected")
        if not patterns:
            patterns.append(f"- {severity_counts['critical']} critical and {severity_counts['high']} high severity alerts require immediate attention")

        return {
            "summary": (
                f"Analysis of {total} alerts reveals {severity_counts['critical']} critical, "
                f"{severity_counts['high']} high, {severity_counts['medium']} medium and "
                f"{severity_counts['low']} low severity issues. "
                f"Host '{top_host}' is the most affected. "
                f"Overall risk level: {risk}."
            ),
            "patterns": patterns[:3],
            "recommendations": [
                f"- Immediately investigate {severity_counts['critical']} critical alert(s) on high-priority hosts",
                "- Review resource utilization trends and set up capacity planning alerts",
                "- Ensure backup and failover systems are operational for affected services",
            ],
            "risk_level": risk,
        }
