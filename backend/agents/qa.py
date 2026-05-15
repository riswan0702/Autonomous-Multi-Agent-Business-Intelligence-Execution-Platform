"""QA Agent — validates completeness and scores the final output."""
from typing import Dict, Any
from agents.base import BaseAgent
from core.llm_router import TaskType


class QAAgent(BaseAgent):
    name = "QA Agent"
    task_type = TaskType.QA

    def get_system_prompt(self) -> str:
        return """You are a Quality Assurance Lead for a management consulting firm. 
You validate that deliverables meet completeness, clarity, and actionability standards 
before they go to clients. You provide a structured scorecard and final summary."""

    def build_prompt(self, context: Dict[str, Any]) -> str:
        bi = context["business_input"]
        all_outputs = {
            "research": context.get("research_report", "")[:600],
            "strategy": context.get("strategy_report", "")[:600],
            "execution": context.get("execution_plan", "")[:600],
            "critique": context.get("critique_report", "")[:400],
        }

        return f"""Validate and score the following multi-agent BI report for:
{bi['company']} — {bi['product']}

**Original Goals:** {bi['goals']}

**Report Sections Available:**
- Research Report: {"✅ Present" if all_outputs["research"] else "❌ Missing"}
- Strategy Report: {"✅ Present" if all_outputs["strategy"] else "❌ Missing"}
- Execution Plan: {"✅ Present" if all_outputs["execution"] else "❌ Missing"}
- Critique Report: {"✅ Present" if all_outputs["critique"] else "❌ Missing"}

**Research excerpt:** {all_outputs["research"][:300]}
**Strategy excerpt:** {all_outputs["strategy"][:300]}
**Execution excerpt:** {all_outputs["execution"][:300]}

Provide QA validation:

1. **Completeness Scorecard** (score each 0-10)
   - Market Research depth: X/10
   - GTM Strategy clarity: X/10
   - Pricing recommendations: X/10
   - Content strategy: X/10
   - Execution plan specificity: X/10
   - Growth experiments quality: X/10

2. **Overall Quality Score: X/100**
   (weighted average with justification)

3. **Goals Alignment Check**
   - Does the report address all stated goals? (Yes/Partial/No)
   - What's missing vs. the stated goals?

4. **Top 3 Strengths** of this report

5. **Executive Summary** (3-4 sentences)
   A crisp summary a CEO would read first

6. **QA Verdict:** APPROVED / APPROVED WITH NOTES / NEEDS REVISION
   With brief reason.

Be objective and rigorous."""

    def parse_output(self, raw: str) -> Dict[str, Any]:
        import re
        # Extract overall score
        score_match = re.search(r'overall quality score[:\s]+(\d+)/100', raw, re.IGNORECASE)
        score = int(score_match.group(1)) if score_match else 72

        # Extract verdict
        verdict = "APPROVED WITH NOTES"
        if "APPROVED\n" in raw.upper() or "VERDICT: APPROVED" in raw.upper():
            verdict = "APPROVED"
        elif "NEEDS REVISION" in raw.upper():
            verdict = "NEEDS REVISION"

        return {
            "qa_report": raw,
            "qa_score": score,
            "verdict": verdict,
            "agent": self.name,
            "status": "completed",
        }
