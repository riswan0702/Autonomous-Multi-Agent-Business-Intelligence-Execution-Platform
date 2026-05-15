"""
Security module:
- Prompt injection detection
- Input sanitization
- Rate limiting (per IP)
- Agent loop detection
- Sensitive data redaction in logs
"""
import re
import os
from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict


# Known prompt injection patterns
INJECTION_PATTERNS = [
    r"ignore (all |previous |above )?instructions",
    r"disregard (your |all |previous )?instructions",
    r"you are now",
    r"act as (an? )?(unrestricted|jailbroken|different|evil|malicious)",
    r"forget (everything|all|your|previous)",
    r"new (system )?prompt",
    r"override (your |all )?safety",
    r"bypass (all |your )?filter",
    r"do anything now",
    r"dan mode",
]
COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

# Sensitive data to redact from logs
SENSITIVE_PATTERNS = [
    (re.compile(r'gsk_[A-Za-z0-9]{40,}'), "[REDACTED_GROQ_KEY]"),
    (re.compile(r'AIzaSy[A-Za-z0-9_-]{30,}'), "[REDACTED_GOOGLE_KEY]"),
    (re.compile(r'sk-[A-Za-z0-9]{40,}'), "[REDACTED_API_KEY]"),
]

# In-memory rate limit store: IP → list of request timestamps
_rate_limit_store: dict = defaultdict(list)
RATE_LIMIT_MAX = 20        # max requests
RATE_LIMIT_WINDOW = 3600   # per hour (seconds)


class SecurityError(Exception):
    pass


def sanitize_input(text: str) -> str:
    """Remove control characters and excessive whitespace."""
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    text = re.sub(r' {10,}', '   ', text)
    return text.strip()


def detect_prompt_injection(text: str) -> tuple[bool, Optional[str]]:
    for pattern in COMPILED_PATTERNS:
        match = pattern.search(text)
        if match:
            return True, pattern.pattern
    return False, None


def validate_business_input(data: dict) -> dict:
    """Sanitize and injection-check all string fields."""
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            clean = sanitize_input(value)
            is_injection, pattern = detect_prompt_injection(clean)
            if is_injection:
                raise SecurityError(
                    f"Potential prompt injection detected in field '{key}'."
                )
            sanitized[key] = clean
        else:
            sanitized[key] = value
    return sanitized


def redact_sensitive(text: str) -> str:
    """Redact API keys from log output."""
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def check_rate_limit(client_ip: str) -> bool:
    """Return False if IP has exceeded rate limit."""
    now = datetime.utcnow()
    window_start = now - timedelta(seconds=RATE_LIMIT_WINDOW)
    _rate_limit_store[client_ip] = [
        ts for ts in _rate_limit_store[client_ip] if ts > window_start
    ]
    if len(_rate_limit_store[client_ip]) >= RATE_LIMIT_MAX:
        return False
    _rate_limit_store[client_ip].append(now)
    return True


class LoopDetector:
    """Tracks how many times each agent runs per workflow run."""

    def __init__(self, max_iterations: int = 10):
        self.max_iterations = max_iterations
        self.counters: dict = defaultdict(int)

    def increment(self, run_id: str, agent_name: str) -> int:
        key = f"{run_id}:{agent_name}"
        self.counters[key] += 1
        return self.counters[key]

    def check(self, run_id: str, agent_name: str):
        key = f"{run_id}:{agent_name}"
        count = self.counters.get(key, 0)
        if count >= self.max_iterations:
            raise SecurityError(
                f"Infinite loop: agent '{agent_name}' has run {count} times. Aborting."
            )

    def reset(self, run_id: str):
        keys = [k for k in self.counters if k.startswith(f"{run_id}:")]
        for k in keys:
            del self.counters[k]


loop_detector = LoopDetector(
    max_iterations=int(os.getenv("MAX_AGENT_LOOPS", "10"))
)
