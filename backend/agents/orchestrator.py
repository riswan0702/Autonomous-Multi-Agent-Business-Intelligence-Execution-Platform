"""
Orchestrator Agent — controls the full multi-agent workflow.
Pipeline: Research → Strategy → Critic → Planner → QA
Handles: memory retrieval, loop detection, failure recovery, event streaming.
"""
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from agents.research import ResearchAgent
from agents.strategy import StrategyAgent
from agents.critic import CriticAgent
from agents.planner import PlannerAgent
from agents.qa import QAAgent
from core.llm_router import LLMRouter
from core.security import loop_detector, SecurityError
from memory.vector_store import get_memory_store
from observability.tracer import RunTracer, AgentStatus


class OrchestratorAgent:
    """
    Runs agents sequentially, passing context between them.
    Research and Strategy are critical (failure aborts the run).
    Critic, Planner, QA are non-critical (failure is logged but run continues).
    """

    PIPELINE = [
        ("research", ResearchAgent, "Researching market and competitors..."),
        ("strategy", StrategyAgent, "Developing strategic recommendations..."),
        ("critic",   CriticAgent,   "Critically reviewing outputs..."),
        ("planner",  PlannerAgent,  "Building execution plan..."),
        ("qa",       QAAgent,       "Running quality assurance..."),
    ]

    CRITICAL_STEPS = {"research", "strategy"}

    def __init__(self):
        self.router = LLMRouter()
        self.memory = get_memory_store()

    async def run(
        self,
        run_id: str,
        business_input: Dict[str, Any],
        run_tracer: RunTracer,
        event_callback=None,
    ) -> Dict[str, Any]:
        run_tracer.status = AgentStatus.RUNNING
        context = {"business_input": business_input}

        # Pull relevant memories from past runs
        memory_context = self.memory.get_context_for_run(business_input)
        if memory_context:
            context["memory_context"] = memory_context

        results = {}

        for step_key, AgentClass, description in self.PIPELINE:
            agent = AgentClass(self.router)

            # FIX: check THEN increment (correct order prevents off-by-one)
            try:
                loop_detector.check(run_id, agent.name)
            except SecurityError as e:
                if event_callback:
                    await event_callback("agent_error", {"agent": agent.name, "error": str(e)})
                if step_key in self.CRITICAL_STEPS:
                    run_tracer.status = AgentStatus.FAILED
                    raise
                continue
            loop_detector.increment(run_id, agent.name)

            tracer = run_tracer.start_agent(agent.name)

            if event_callback:
                await event_callback("agent_start", {
                    "agent": agent.name,
                    "step": step_key,
                    "description": description,
                })

            try:
                output = await self._run_with_retry(agent, context, tracer)
                results[step_key] = output

                # Feed outputs into context for downstream agents
                context_map = {
                    "research": "research_report",
                    "strategy": "strategy_report",
                    "critic":   "critique_report",
                    "planner":  "execution_plan",
                }
                if step_key in context_map:
                    key = context_map[step_key]
                    context[key] = output.get(key, "")

                # Persist to memory
                content_key = next(iter(output), step_key)
                content = str(output.get(content_key, ""))
                self.memory.store(
                    run_id=run_id,
                    agent_name=agent.name,
                    content=content,
                    metadata={"company": business_input.get("company", "")},
                )

                if event_callback:
                    await event_callback("agent_complete", {
                        "agent": agent.name,
                        "step": step_key,
                        "tokens_used": tracer.tokens_input + tracer.tokens_output,
                        "latency_ms": tracer.latency_ms,
                        "model": tracer.model,
                        "preview": content[:200],
                    })

            except Exception as e:
                tracer.fail(str(e))
                results[step_key] = {"error": str(e), "status": "failed"}

                if event_callback:
                    await event_callback("agent_error", {
                        "agent": agent.name,
                        "step": step_key,
                        "error": str(e),
                    })

                if step_key in self.CRITICAL_STEPS:
                    run_tracer.status = AgentStatus.FAILED
                    raise

            # Small courtesy delay between agents
            await asyncio.sleep(0.3)

        final_report = self._build_final_report(business_input, results, run_id)
        run_tracer.status = AgentStatus.COMPLETED

        if event_callback:
            await event_callback("workflow_complete", {
                "run_id": run_id,
                "qa_score": results.get("qa", {}).get("qa_score", 0),
                "verdict": results.get("qa", {}).get("verdict", "COMPLETED"),
                "total_tokens": run_tracer.get_total_tokens(),
                "summary": run_tracer.get_summary(),
            })

        return final_report

    async def _run_with_retry(self, agent, context, tracer, max_retries: int = 2):
        """Run an agent with exponential backoff retry."""
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                return await agent.run(context, tracer)
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)
                    tracer.iteration += 1
        raise last_error

    def _build_final_report(self, business_input: Dict, results: Dict, run_id: str) -> Dict[str, Any]:
        return {
            "run_id": run_id,
            "generated_at": datetime.utcnow().isoformat(),
            "company": business_input.get("company", ""),
            "product": business_input.get("product", ""),
            "market_research":  results.get("research", {}).get("research_report", ""),
            "strategy":         results.get("strategy", {}).get("strategy_report", ""),
            "critique":         results.get("critic",   {}).get("critique_report", ""),
            "execution_plan":   results.get("planner",  {}).get("execution_plan", ""),
            "qa_report":        results.get("qa",       {}).get("qa_report", ""),
            "qa_score":         results.get("qa", {}).get("qa_score", 0),
            "confidence_score": results.get("critic", {}).get("confidence_score", 0),
            "verdict":          results.get("qa", {}).get("verdict", "COMPLETED"),
            "token_usage":      self.router.get_usage_summary(),
            "sections_completed": [
                k for k, v in results.items()
                if isinstance(v, dict) and v.get("status") == "completed"
            ],
        }
