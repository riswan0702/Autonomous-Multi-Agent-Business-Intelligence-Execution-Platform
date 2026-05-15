"""Base agent — all agents inherit from this."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from core.llm_router import LLMRouter, TaskType
from observability.tracer import AgentTracer


class BaseAgent(ABC):
    name: str = "base"
    task_type: TaskType = TaskType.CHEAP_SUMMARY

    def __init__(self, router: LLMRouter):
        self.router = router

    @abstractmethod
    def get_system_prompt(self) -> str:
        pass

    @abstractmethod
    def build_prompt(self, context: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    def parse_output(self, raw: str) -> Dict[str, Any]:
        pass

    async def run(
        self,
        context: Dict[str, Any],
        tracer: Optional[AgentTracer] = None,
    ) -> Dict[str, Any]:
        prompt = self.build_prompt(context)
        system = self.get_system_prompt()

        text, model, tok_in, tok_out = await self.router.call(
            task_type=self.task_type,
            system_prompt=system,
            user_prompt=prompt,
        )

        if tracer:
            tracer.complete(text, tok_in, tok_out, model)

        return self.parse_output(text)
