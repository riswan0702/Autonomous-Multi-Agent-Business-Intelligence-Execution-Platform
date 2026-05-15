"""Planner Agent — converts strategy into execution tasks."""
from typing import Dict, Any
from agents.base import BaseAgent
from core.llm_router import TaskType


class PlannerAgent(BaseAgent):
    name = "Planner Agent"
    task_type = TaskType.PLANNING

    def get_system_prompt(self) -> str:
        return """You are a Head of Operations who converts strategic vision into 
precise execution plans. You think in terms of sprints, owners, dependencies, 
and measurable outcomes. Your plans are realistic given the constraints provided.

You output structured, week-by-week execution plans with clear ownership, 
success metrics, and priority scores."""

    def build_prompt(self, context: Dict[str, Any]) -> str:
        bi = context["business_input"]
        strategy = context.get("strategy_report", "")[:1200]
        critique = context.get("critique_report", "")[:400]

        return f"""Convert the following strategy into a detailed execution plan:

**Business Context:**
- Company: {bi['company']}
- Goals: {bi['goals']}
- Constraints: {bi.get('constraints', 'None')}

**Strategy Summary:**
{strategy}

**Key Critique to Address:**
{critique[:300]}

Create a comprehensive execution plan:

1. **90-Day Execution Roadmap**
   
   **Month 1 — Foundation (Weeks 1-4)**
   For each week: List 3-5 specific tasks with:
   - Task name
   - Owner (role, not person)
   - Effort (hours)
   - Priority: P1/P2/P3
   - Success metric
   
   **Month 2 — Launch (Weeks 5-8)**
   [Same format]
   
   **Month 3 — Scale (Weeks 9-12)**
   [Same format]

2. **Growth Experiments** (prioritized backlog)
   List 8-10 experiments, each with:
   - Hypothesis
   - Channel/tactic
   - Effort: Low/Medium/High
   - Expected impact: Low/Medium/High
   - How to measure success
   - Timeline

3. **Key Milestones & KPIs**
   - Week 4 milestone
   - Month 2 milestone  
   - Month 3 milestone
   - Monthly KPIs to track (5 metrics)

4. **Resource Requirements**
   - Team roles needed
   - Tool/tech stack (with free tier options)
   - Budget breakdown (in INR)

5. **Risk Mitigation Plan**
   - Top 3 risks + mitigation actions

Make this actionable for a small team. Be specific about tasks."""

    def parse_output(self, raw: str) -> Dict[str, Any]:
        return {
            "execution_plan": raw,
            "agent": self.name,
            "status": "completed",
        }
