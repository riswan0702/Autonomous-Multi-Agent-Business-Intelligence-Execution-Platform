"""Research Agent — competitor analysis, market sizing, trends."""
from typing import Dict, Any
from agents.base import BaseAgent
from core.llm_router import TaskType


class ResearchAgent(BaseAgent):
    name = "Research Agent"
    task_type = TaskType.RESEARCH

    def get_system_prompt(self) -> str:
        return """You are a Senior Market Research Analyst with expertise in startup ecosystems, 
competitive intelligence, and market sizing. You produce structured, data-rich analysis 
with specific numbers, company names, and actionable insights.

Always structure your output with clear sections. Be specific — name real competitors, 
cite realistic market sizes, and identify concrete pain points. For Indian market context, 
use INR figures and India-specific market dynamics."""

    def build_prompt(self, context: Dict[str, Any]) -> str:
        bi = context["business_input"]
        memory_context = context.get("memory_context", "")

        return f"""Conduct comprehensive market research for the following business:

**Company:** {bi['company']}
**Product:** {bi['product']}
**Target Audience:** {bi['target_audience']}
**Goals:** {bi['goals']}
**Constraints:** {bi.get('constraints', 'None specified')}

{memory_context}

Provide a detailed research report covering:

1. **Market Overview**
   - TAM (Total Addressable Market) with specific numbers
   - SAM (Serviceable Addressable Market)
   - SOM (Serviceable Obtainable Market) — realistic 12-month target
   - Key market trends (3-5 trends)

2. **Competitor Analysis** (identify 4-6 real competitors)
   For each competitor: Name, Pricing, Key Features, Weaknesses, Market Position

3. **Target Audience Deep Dive**
   - Psychographic profile
   - Key pain points (5 specific ones)
   - Buying triggers and barriers
   - Where they spend time online

4. **Market Gaps & Opportunities**
   - 3 clear gaps in the current market
   - Whitespace opportunities

5. **Key Risks**
   - 3 market/competitive risks to watch

Be specific, use real data where possible, and focus on actionable intelligence."""

    def parse_output(self, raw: str) -> Dict[str, Any]:
        return {
            "research_report": raw,
            "agent": self.name,
            "status": "completed",
        }
