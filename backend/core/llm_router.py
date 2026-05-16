"""
LLM Router — intelligently selects Groq model based on task type.
Uses Groq's OpenAI-compatible API (completely free tier).

Model routing strategy:
  - Heavy reasoning (research, strategy) → llama-3.3-70b-versatile
  - Fast/cheap tasks (critic, planner, QA, summary) → llama-3.1-8b-instant

Observability:
  - Every prompt and response is logged (prompt logging requirement)
  - Token tracking per call
  - Latency per call
  - Retry attempts logged
"""
import os
import time
import asyncio
import logging
from enum import Enum
from openai import OpenAI

logger = logging.getLogger("bi-platform.llm")


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
    TaskType.CHEAP_SUMMARY:         "llama-3.1-8b-instant",
    TaskType.STRATEGIC_REASONING:   "llama-3.3-70b-versatile",
    TaskType.STRUCTURED_EXTRACTION: "llama-3.1-8b-instant",
    TaskType.CRITIQUE:              "llama-3.1-8b-instant",
    TaskType.PLANNING:              "llama-3.1-8b-instant",
    TaskType.RESEARCH:              "llama-3.3-70b-versatile",
    TaskType.QA:                    "llama-3.1-8b-instant",
}

FALLBACK_CHAIN = {
    "llama-3.3-70b-versatile": "llama-3.1-8b-instant",
    "llama-3.1-8b-instant":    "llama-3.1-8b-instant",
}

MAX_TOKENS_MAP = {
    TaskType.CHEAP_SUMMARY:         800,
    TaskType.STRATEGIC_REASONING:   2000,
    TaskType.STRUCTURED_EXTRACTION: 1200,
    TaskType.CRITIQUE:              1000,
    TaskType.PLANNING:              1500,
    TaskType.RESEARCH:              2000,
    TaskType.QA:                    800,
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
        # Prompt log for observability — every LLM call recorded here
        self.prompt_log: list[dict] = []

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
        Logs every prompt + response for observability (prompt logging requirement).
        """
        self.check_budget()

        model_name = self.get_model(task_type)
        max_tokens = MAX_TOKENS_MAP.get(task_type, 1000)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ]

        # ── PROMPT LOGGING (Observability requirement) ──────────────────
        prompt_entry = {
            "task_type": task_type,
            "model": model_name,
            "system_prompt_preview": system_prompt[:200],
            "user_prompt_preview": user_prompt[:300],
        }
        logger.info(
            f"[LLM] task={task_type} model={model_name} "
            f"system_len={len(system_prompt)} user_len={len(user_prompt)}"
        )
        # ────────────────────────────────────────────────────────────────

        # Try primary model, then fallback
        for attempt_model in [model_name, FALLBACK_CHAIN.get(model_name, model_name)]:
            for attempt in range(3):
                t0 = time.time()
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
                    latency_ms = round((time.time() - t0) * 1000, 1)
                    self.total_tokens_used += tok_in + tok_out

                    # ── LOG RESPONSE ─────────────────────────────────────
                    prompt_entry.update({
                        "model_used": attempt_model,
                        "tokens_in": tok_in,
                        "tokens_out": tok_out,
                        "latency_ms": latency_ms,
                        "response_preview": text[:200],
                        "success": True,
                    })
                    self.prompt_log.append(prompt_entry)
                    logger.info(
                        f"[LLM] ✅ {attempt_model} | {tok_in}+{tok_out} tokens "
                        f"| {latency_ms}ms | attempt={attempt+1}"
                    )
                    # ─────────────────────────────────────────────────────

                    return text, attempt_model, tok_in, tok_out

                except Exception as e:
                    latency_ms = round((time.time() - t0) * 1000, 1)
                    logger.warning(
                        f"[LLM] ❌ {attempt_model} attempt {attempt+1} failed "
                        f"({latency_ms}ms): {str(e)[:120]}"
                    )
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        break

        prompt_entry["success"] = False
        self.prompt_log.append(prompt_entry)
        raise RuntimeError(f"All retry attempts failed for task_type={task_type}")

    def get_usage_summary(self) -> dict:
        return {
            "total_tokens_used": self.total_tokens_used,
            "budget": self.max_tokens_budget,
            "budget_remaining": self.max_tokens_budget - self.total_tokens_used,
            "budget_used_pct": round(
                self.total_tokens_used / self.max_tokens_budget * 100, 1
            ),
            "total_llm_calls": len(self.prompt_log),
        }

    def get_prompt_log(self) -> list[dict]:
        """Return full prompt log for observability endpoint."""
        return self.prompt_log
