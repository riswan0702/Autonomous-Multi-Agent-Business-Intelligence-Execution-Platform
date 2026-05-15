"""Strategy Agent — GTM, pricing, positioning."""
from typing import Dict, Any
from agents.base import BaseAgent
from core.llm_router import TaskType


class StrategyAgent(BaseAgent):
    name = "Strategy Agent"
    task_type = TaskType.STRATEGIC_REASONING

    def get_system_prompt(self) -> str:
        return """You are a Chief Strategy Officer at a top-tier management consulting firm 
(McKinsey/BCG caliber). You specialize in go-to-market strategy, growth frameworks, 
and pricing for digital products in emerging markets, especially India.

Your recommendations are bold, specific, and grounded in proven frameworks (Jobs-to-be-Done, 
Blue Ocean, Growth Loops). You always back recommendations with reasoning and expected outcomes."""

    def build_prompt(self, context: Dict[str, Any]) -> str:
        bi = context["business_input"]
        research = context.get("research_report", "No research available")

        return f"""Based on the following business context and market research, develop a comprehensive strategy:

**Business:**
- Company: {bi['company']}
- Product: {bi['product']}
- Audience: {bi['target_audience']}
- Goals: {bi['goals']}
- Constraints: {bi.get('constraints', 'None')}

**Market Research Summary:**
{research[:1500]}

Develop a complete strategy covering:

1. **Go-To-Market Strategy**
   - Positioning statement (specific, differentiated)
   - Launch sequence (Phase 1: Month 1-2, Phase 2: Month 3-4, Phase 3: Month 5-6)
   - Primary and secondary channels with rationale
   - Key partnerships to pursue

2. **Pricing Strategy**
   - Recommended pricing model (freemium/subscription/one-time)
   - Specific tier breakdown with prices in INR
   - Justification vs. competitors
   - Revenue projections (Month 1, Month 6, Month 12)

3. **Positioning & Messaging**
   - Core value proposition (1 sentence)
   - Key differentiators (3)
   - Messaging for each audience segment
   - Brand personality

4. **Growth Strategy**
   - Primary growth loop (acquisition → activation → retention → referral)
   - Top 3 acquisition channels with CAC estimates
   - Retention mechanics
   - Viral/referral mechanism

5. **Content Strategy**
   - Content pillars (3)
   - 30-day content calendar outline
   - Distribution strategy
   - Key content formats

Be bold. Make specific recommendations, not generic advice."""

    def parse_output(self, raw: str) -> Dict[str, Any]:
        return {
            "strategy_report": raw,
            "agent": self.name,
            "status": "completed",
        }
