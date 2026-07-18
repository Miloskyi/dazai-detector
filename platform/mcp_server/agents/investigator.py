"""Answers `alert_lookup` and `similar_cases` questions.

Both intents concern a specific alert, so one agent owns the transaction-id
regex used to detect which alert (if any) the question is about.
"""

from __future__ import annotations

import re

from mcp_server.agents.base import Agent, AgentResponse
from mcp_server.tools import alert_tools, rag_tools

_ALERT_ID_RE = re.compile(r"TXN-\d+", re.IGNORECASE)


def _extract_alert_id(question: str) -> str | None:
    match = _ALERT_ID_RE.search(question)
    return match.group(0).upper() if match else None


class InvestigatorAgent(Agent):
    name = "investigator"

    def respond(self, question: str) -> AgentResponse:
        if "similar" in question.lower() or "like this" in question.lower() or "related" in question.lower():
            return self._respond_similar(question)
        return self._respond_lookup(question)

    def _respond_lookup(self, question: str) -> AgentResponse:
        alert_id = _extract_alert_id(question)
        if not alert_id:
            return AgentResponse(
                answer=(
                    "I couldn't find a transaction ID in your question (expected a format "
                    "like TXN-000123). Please include the alert ID you want to investigate."
                ),
                sources=[],
            )

        alert = alert_tools.get_alert(alert_id)
        if not alert:
            return AgentResponse(
                answer=f"No alert with ID {alert_id} was found in the current dataset.",
                sources=["alert_tools.get_alert"],
            )

        top_features = ", ".join(f["feature"] for f in alert.get("shap_explanation", [])[:3])
        narrative = alert.get("narrative", "")
        answer = (
            f"Alert {alert_id}: ${alert['amount']:.2f}, tier {alert['risk_tier']} "
            f"(risk score {alert['risk_score']:.2f}). Top contributing features: {top_features}. "
            f"{narrative}"
        ).strip()
        return AgentResponse(answer=answer, sources=[f"alert_tools.get_alert({alert_id})"])

    def _respond_similar(self, question: str) -> AgentResponse:
        alert_id = _extract_alert_id(question)
        query = question
        if alert_id:
            alert = alert_tools.get_alert(alert_id)
            if alert:
                query = alert.get("narrative") or f"Amount ${alert['amount']} tier {alert['risk_tier']}"

        hits = rag_tools.search_similar(query, k=5)
        if not hits:
            return AgentResponse(
                answer="No similar cases were found in the alert history.",
                sources=["rag_tools.search_similar"],
            )

        summary = "; ".join(f"{h['alert_id']} ({h['metadata']['risk_tier']})" for h in hits)
        return AgentResponse(
            answer=f"Found {len(hits)} similar cases: {summary}.",
            sources=["rag_tools.search_similar"],
        )
