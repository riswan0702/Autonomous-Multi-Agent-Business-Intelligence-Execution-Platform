"""Critic Agent — reviews for hallucinations, logic gaps, weak reasoning."""
from typing import Dict, Any
from agents.base import BaseAgent
from core.llm_router import TaskType


class CriticAgent(BaseAgent):
    name = "Critic Agent"
    task_type = TaskType.CRITIQUE

    def get_system_prompt(self) -> str:
        return 

    def build_prompt(self, context: Dict[str, Any]) -> str:
        research = context.get("research_report", "")[:800]
        strategy = context.get("strategy_report", "")[:800]
        bi = context["business_input"]

        return f"""Critically review the following research and strategy outputs for:
{bi['company']} — {bi['product']}

**Research Output (excerpt):**
{research}

**Strategy Output (excerpt):**
{strategy}


    def parse_output(self, raw: str) -> Dict[str, Any]:
        # Try to extract confidence score
        import re
        overall_match = re.search(r'overall reliability[:\s]+(\d+)/100', raw, re.IGNORECASE)
        confidence = int(overall_match.group(1)) if overall_match else 65

        return {
            "critique_report": raw,
            "confidence_score": confidence,
            "agent": self.name,
            "status": "completed",
        }
