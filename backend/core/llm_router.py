"""
LLM Router — intelligently selects Groq model based on task type.
Uses Groq's OpenAI-compatible API (completely free tier).

Model routing strategy:
  - Heavy reasoning (research, strategy) → llama-3.3-70b-versatile
  - Fast/cheap tasks (critic, planner, QA, summary) → llama-3.1-8b-instant
"""
import os
import asyncio
from enum import Enum
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential


class TaskType(str, Enum):
    CHEAP_SUMMARY = "cheap_summary"
    STRATEGIC_REASONING = "strategic_reasoning"
    STRUCTURED_EXTRACTION = "structured_extraction"
    CRITIQUE = "critique"
    PLANNING = "planning"
    RESEARCH = "research"
    QA = "qa"


# Model routing: 70b for heavy reasoning, 8b for fast tasks
MODEL_ROUTING = {
    TaskType.CHEAP_SUMMARY:        "llama-3.1-8b-instant",
    TaskType.STRATEGIC_REASONING:  "llama-3.3-70b-versatile",
    TaskType.STRUCTURED_EXTRACTION:"llama-3.1-8b-instant",
    TaskType.CRITIQUE:             "llama-3.1-8b-instant",
    TaskType.PLANNING:             "llama-3.1-8b-instant",
    TaskType.RESEARCH:             "llama-3.3-70b-versatile",
    TaskType.QA:                   "llama-3.1-8b-instant",
}

# Fallback if primary model fails
FALLBACK_CHAIN = {
    "llama-3.3-70b-versatile": "llama-3.1-8b-instant",
    "llama-3.1-8b-instant":    "llama-3.1-8b-instant",
}

MAX_TOKENS_MAP = {
    TaskType.CHEAP_SUMMARY:        800,
    TaskType.STRATEGIC_REASONING:  2000,
    TaskType.STRUCTURED_EXTRACTION:1200,
    TaskType.CRITIQUE:             1000,
    TaskType.PLANNING:             1500,
    TaskType.RESEARCH:             2000,
    TaskType.QA:                   800,
}


class LLMRouter:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY not set. Get a free key at console.groq.com "
                "and add it to backend/.env"
            )
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        self.total_tokens_used = 0
        self.max_tokens_budget = int(os.getenv("MAX_TOKENS_PER_RUN", "80000"))

    def get_model(self, task_type: TaskType) -> str:
        return MODEL_ROUTING.get(task_type, "llama-3.1-8b-instant")

    def check_budget(self):
        if self.total_tokens_used >= self.max_tokens_budget:
            raise RuntimeError(
                f"Token budget exceeded: {self.total_tokens_used}/{self.max_tokens_budget}. "
                "Cost runaway protection triggered."
            )

    async def call(
        self,
        task_type: TaskType,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
    ) -> tuple[str, str, int, int]:
        """
        Call Groq API. Returns: (response_text, model_used, input_tokens, output_tokens)
        Has automatic retry with exponential backoff and model fallback.
        """
        self.check_budget()

        model_name = self.get_model(task_type)
        max_tokens = MAX_TOKENS_MAP.get(task_type, 1000)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ]

        # Try primary model, then fallback
        for attempt_model in [model_name, FALLBACK_CHAIN.get(model_name, model_name)]:
            for attempt in range(3):
                try:
                    response = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda m=attempt_model: self.client.chat.completions.create(
                            model=m,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                        ),
                    )
                    text = response.choices[0].message.content or ""
                    tok_in = response.usage.prompt_tokens
                    tok_out = response.usage.completion_tokens
                    self.total_tokens_used += tok_in + tok_out
                    return text, attempt_model, tok_in, tok_out

                except Exception as e:
                    err_str = str(e)
                    print(f"[LLMRouter] {attempt_model} attempt {attempt+1} failed: {err_str[:120]}")
                    if attempt < 2:
                        # Exponential backoff: 2s, 4s
                        await asyncio.sleep(2 ** attempt)
                    else:
                        # Move to fallback model
                        break

        raise RuntimeError(f"All retry attempts failed for task_type={task_type}")

    def get_usage_summary(self) -> dict:
        return {
            "total_tokens_used": self.total_tokens_used,
            "budget": self.max_tokens_budget,
            "budget_remaining": self.max_tokens_budget - self.total_tokens_used,
            "budget_used_pct": round(
                self.total_tokens_used / self.max_tokens_budget * 100, 1
            ),
        }
