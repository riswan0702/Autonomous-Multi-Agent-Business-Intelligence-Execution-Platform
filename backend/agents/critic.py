"""Critic Agent — reviews for hallucinations, logic gaps, weak reasoning."""
from typing import Dict, Any
from agents.base import BaseAgent
from core.llm_router import TaskType


class CriticAgent(BaseAgent):
    name = "Critic Agent"
    task_type = TaskType.CRITIQUE

    def get_system_prompt(self) -> str:
        return """You are a ruthless but constructive Devil's Advocate and fact-checker. 
Your job is to identify:
- Logical inconsistencies and contradictions
- Unsupported claims and hallucinations
- Weak reasoning and hand-wavy statements
- Missing critical considerations
- Overly optimistic assumptions

You are NOT negative for the sake of it — you provide specific, actionable critique 
that makes the final output stronger. Rate each section and provide a confidence score."""

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

Provide a structured critique:

1. **Hallucination Check**
   - List any specific claims that appear fabricated or unverifiable
   - Flag any statistics that seem unrealistic
   - Note any competitor details that seem incorrect

2. **Logic Gap Analysis**
   - Identify 3-5 logical inconsistencies or contradictions
   - Point out missing causal links
   - Flag circular reasoning

3. **Assumption Audit**
   - List the top 5 assumptions being made
   - Rate each: LOW / MEDIUM / HIGH risk if assumption is wrong
   - Suggest how to validate each assumption

4. **Missing Elements**
   - What critical topics were not addressed?
   - What questions remain unanswered?

5. **Confidence Scores** (0-100)
   - Research quality: X/100 — [reason]
   - Strategy quality: X/100 — [reason]
   - Overall reliability: X/100 — [reason]

6. **Top 3 Recommended Improvements**
   - Specific, actionable improvements to make the output stronger

Be specific. Reference exact claims from the reports."""

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
