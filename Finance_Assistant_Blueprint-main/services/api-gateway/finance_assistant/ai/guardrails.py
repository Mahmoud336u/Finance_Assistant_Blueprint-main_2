"""Meridian AI — Prompt Injection Guardrails.

Implements multi-layer defense against prompt injection attacks:
1. Pattern-based blocking (known attack patterns)
2. Structural analysis (detects role hijacking attempts)
3. Financial guardrails (prevents dangerous financial actions)

Per the blueprint's Section 9.3 — AI Security Controls.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from ..logging import get_logger

logger = get_logger(__name__)


class ThreatLevel(str, Enum):
    """Severity of a detected threat."""

    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class GuardrailResult:
    """Result of a guardrail check."""

    is_safe: bool
    threat_level: ThreatLevel
    blocked_reason: str | None = None
    matched_pattern: str | None = None


# ============================================================
# Pattern-Based Detection (Layer 1)
# ============================================================

# Known prompt injection patterns — curated from OWASP LLM Top 10
# and real-world attack corpuses.
INJECTION_PATTERNS: list[tuple[str, str, ThreatLevel]] = [
    # --- Role hijacking ---
    (r"(?i)ignore\s+(all\s+)?previous\s+(instructions|prompts?|rules?)", "role_hijack", ThreatLevel.CRITICAL),
    (r"(?i)disregard\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts?)", "role_hijack", ThreatLevel.CRITICAL),
    (r"(?i)forget\s+(everything|all)\s+(you|that)\s+(were|was)\s+told", "role_hijack", ThreatLevel.CRITICAL),
    (r"(?i)you\s+are\s+now\s+(a|an|my)\s+", "role_hijack", ThreatLevel.HIGH),
    (r"(?i)act\s+as\s+(if\s+you\s+are|a|an)\s+", "role_hijack", ThreatLevel.HIGH),
    (r"(?i)pretend\s+(to\s+be|you\s+are)\s+", "role_hijack", ThreatLevel.HIGH),
    (r"(?i)new\s+instruction[s]?\s*:", "role_hijack", ThreatLevel.HIGH),
    (r"(?i)system\s*prompt\s*:", "role_hijack", ThreatLevel.CRITICAL),
    (r"(?i)\[system\]", "role_hijack", ThreatLevel.CRITICAL),
    (r"(?i)<<\s*sys\s*>>", "role_hijack", ThreatLevel.CRITICAL),

    # --- Prompt leaking ---
    (r"(?i)show\s+me\s+(your|the)\s+(system|original)\s+(prompt|instructions)", "prompt_leak", ThreatLevel.HIGH),
    (r"(?i)what\s+(are|were)\s+(your|the)\s+(original|system)\s+(instructions|prompt)", "prompt_leak", ThreatLevel.HIGH),
    (r"(?i)reveal\s+(your|the)\s+(system|hidden)\s+(prompt|instructions)", "prompt_leak", ThreatLevel.HIGH),
    (r"(?i)repeat\s+(the|your)\s+instructions\s+(back|verbatim)", "prompt_leak", ThreatLevel.HIGH),
    (r"(?i)print\s+(your|the)\s+system\s+(prompt|message)", "prompt_leak", ThreatLevel.HIGH),

    # --- Code execution attempts ---
    (r"(?i)execute\s+(this|the\s+following)\s+(code|command|script)", "code_exec", ThreatLevel.CRITICAL),
    (r"(?i)run\s+(this|the\s+following)\s+(python|bash|shell|sql)", "code_exec", ThreatLevel.CRITICAL),
    (r"(?i)(import|eval|exec|os\.system|subprocess)\s*\(", "code_exec", ThreatLevel.CRITICAL),
    (r"(?i)```(python|bash|sql|javascript)\s*\n.*?(os\.|exec|eval|import)", "code_exec", ThreatLevel.CRITICAL),

    # --- Jailbreak patterns ---
    (r"(?i)DAN\s*(mode|prompt|jailbreak)", "jailbreak", ThreatLevel.CRITICAL),
    (r"(?i)developer\s+mode\s+(enabled|on|activated)", "jailbreak", ThreatLevel.CRITICAL),
    (r"(?i)do\s+anything\s+now", "jailbreak", ThreatLevel.CRITICAL),
    (r"(?i)in\s+this\s+hypothetical\s+scenario", "jailbreak", ThreatLevel.MEDIUM),
    (r"(?i)for\s+(educational|research|academic)\s+purposes\s+only", "jailbreak", ThreatLevel.LOW),

    # --- Data exfiltration ---
    (r"(?i)list\s+all\s+(users?|accounts?|passwords?|emails?)", "data_exfil", ThreatLevel.HIGH),
    (r"(?i)show\s+me\s+(all|every)\s+(user|account|record)", "data_exfil", ThreatLevel.HIGH),
    (r"(?i)dump\s+(the\s+)?(database|table|schema)", "data_exfil", ThreatLevel.CRITICAL),
    (r"(?i)(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\s+", "sql_injection", ThreatLevel.HIGH),
]

# Financial-specific guardrails
FINANCIAL_GUARDRAILS: list[tuple[str, str, ThreatLevel]] = [
    (r"(?i)transfer\s+\$?\d+.*to\s+(account|wallet|address)", "financial_action", ThreatLevel.CRITICAL),
    (r"(?i)authorize\s+(a\s+)?(payment|transfer|withdrawal)", "financial_action", ThreatLevel.CRITICAL),
    (r"(?i)approve\s+(this\s+)?(transaction|transfer|payment)", "financial_action", ThreatLevel.CRITICAL),
    (r"(?i)(buy|sell|trade)\s+\d+\s+(shares?|stocks?|bitcoin|crypto)", "investment_advice", ThreatLevel.HIGH),
    (r"(?i)invest\s+(all|my|this)\s+(money|savings|funds)\s+in", "investment_advice", ThreatLevel.HIGH),
]


def check_prompt_injection(text: str) -> GuardrailResult:
    """Check a user input for prompt injection attempts (Layer 1).

    Uses pattern-based detection against known attack vectors.

    Args:
        text: The raw user input to check.

    Returns:
        GuardrailResult indicating whether the input is safe.
    """
    # Check prompt injection patterns
    for pattern, attack_type, threat_level in INJECTION_PATTERNS:
        if re.search(pattern, text):
            return GuardrailResult(
                is_safe=False,
                threat_level=threat_level,
                blocked_reason=f"Prompt injection detected: {attack_type}",
                matched_pattern=pattern,
            )

    # Check financial guardrails
    for pattern, guard_type, threat_level in FINANCIAL_GUARDRAILS:
        if re.search(pattern, text):
            return GuardrailResult(
                is_safe=False,
                threat_level=threat_level,
                blocked_reason=f"Financial guardrail triggered: {guard_type}",
                matched_pattern=pattern,
            )

    return GuardrailResult(is_safe=True, threat_level=ThreatLevel.SAFE)


# ============================================================
# Structural Analysis (Layer 2)
# ============================================================

# Heuristic scores for suspicious structural patterns
STRUCTURAL_THRESHOLDS = {
    "delimiter_density": 0.05,      # > 5% of chars are delimiters → suspicious
    "instruction_keywords": 3,       # > 3 instruction keywords → suspicious
    "role_markers": 1,               # Any role markers → suspicious
}

INSTRUCTION_KEYWORDS = {
    "instruction", "instructions", "respond", "reply", "output",
    "generate", "create", "format", "always", "never", "must",
    "override", "bypass", "constraint", "restriction",
}

ROLE_MARKERS = {"[SYSTEM]", "[USER]", "[ASSISTANT]", "<<SYS>>", "<|system|>", "<|user|>"}


def check_structural_anomaly(text: str) -> GuardrailResult:
    """Check for structural anomalies that indicate prompt injection (Layer 2).

    Analyzes the text structure for unusual patterns that don't match
    typical financial questions.

    Args:
        text: The raw user input.

    Returns:
        GuardrailResult.
    """
    text_lower = text.lower()
    words = text_lower.split()

    # Check for role markers
    for marker in ROLE_MARKERS:
        if marker.lower() in text_lower:
            return GuardrailResult(
                is_safe=False,
                threat_level=ThreatLevel.HIGH,
                blocked_reason="Structural anomaly: role marker detected",
                matched_pattern=marker,
            )

    # Check delimiter density
    delimiters = sum(1 for c in text if c in "{}[]<>|`~^")
    if len(text) > 0 and delimiters / len(text) > STRUCTURAL_THRESHOLDS["delimiter_density"]:
        return GuardrailResult(
            is_safe=False,
            threat_level=ThreatLevel.MEDIUM,
            blocked_reason="Structural anomaly: high delimiter density",
        )

    # Check instruction keyword density
    keyword_count = sum(1 for w in words if w in INSTRUCTION_KEYWORDS)
    if keyword_count > STRUCTURAL_THRESHOLDS["instruction_keywords"]:
        return GuardrailResult(
            is_safe=False,
            threat_level=ThreatLevel.MEDIUM,
            blocked_reason="Structural anomaly: excessive instruction keywords",
        )

    return GuardrailResult(is_safe=True, threat_level=ThreatLevel.SAFE)


# ============================================================
# Combined Guardrail Pipeline
# ============================================================


async def validate_user_input(text: str) -> GuardrailResult:
    """Run the full guardrail pipeline on user input.

    Runs all layers sequentially, returning the first failure.
    If all layers pass, the input is considered safe.

    Args:
        text: The raw user input.

    Returns:
        GuardrailResult from the first failing check, or SAFE.
    """
    # Layer 1: Pattern-based blocking
    result = check_prompt_injection(text)
    if not result.is_safe:
        await logger.awarning(
            "Guardrail blocked input",
            layer="pattern",
            threat_level=result.threat_level,
            reason=result.blocked_reason,
        )
        return result

    # Layer 2: Structural analysis
    result = check_structural_anomaly(text)
    if not result.is_safe:
        await logger.awarning(
            "Guardrail blocked input",
            layer="structural",
            threat_level=result.threat_level,
            reason=result.blocked_reason,
        )
        return result

    return GuardrailResult(is_safe=True, threat_level=ThreatLevel.SAFE)
