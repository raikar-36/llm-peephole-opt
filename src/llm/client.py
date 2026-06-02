#!/usr/bin/env python3
"""
LLM Client (Task 5)

Queries LLM APIs (Gemini or Groq) to suggest LLVM IR peephole optimizations.
Supports provider switching via LLM_PROVIDER environment variable.
"""

import json
import logging
import os
import re
import time
from collections import Counter, deque
from typing import List, Optional

# ── System Prompt ──────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert LLVM compiler engineer.
Analyze the given LLVM IR function and suggest a simpler, equivalent rewrite.

YOUR JOB: Find algebraic simplifications, identity eliminations, or constant
folds that make the function shorter. Be willing to suggest rewrites even if
you are not 100% certain — that is what the confidence field is for.

RULES:
- Output must have FEWER instructions than the input
- Do not change the function name or argument types
- Preserve nsw/nuw/exact flags from the original unless the operation is eliminated entirely
- SSA values must be numbered sequentially: %1, %2, %3 and so on — never skip a number
- If you truly cannot find any simplification, use NO_OPT
- IMPORTANT: If the pattern looks already minimal or fully simplified, say NO_OPT. It is better to refuse than to suggest a wrong rewrite.

OUTPUT FORMAT — respond ONLY with this JSON, no markdown, no backticks, no extra text:
{
  "optimized_ir": "<full LLVM IR function, or the string NO_OPT>",
  "reason": "<one sentence: what algebraic rule applies>",
  "precondition": "<constraints needed, or the string none>",
  "confidence": "HIGH or MEDIUM or LOW"
}"""

# ── Few-Shot Examples ──────────────────────────────────────────────────
FEW_SHOT_EXAMPLES = """
EXAMPLES — study these carefully before responding:

Input:
define i32 @f(i32 %x) {
entry:
  %1 = xor i32 %x, 0
  ret i32 %1
}
Output: {"optimized_ir": "define i32 @f(i32 %x) {\nentry:\n  ret i32 %x\n}", "reason": "x XOR 0 equals x for all x", "precondition": "none", "confidence": "HIGH"}

Input:
define i32 @f(i32 %x) {
entry:
  %1 = or i32 %x, 0
  ret i32 %1
}
Output: {"optimized_ir": "define i32 @f(i32 %x) {\nentry:\n  ret i32 %x\n}", "reason": "x OR 0 equals x for all x", "precondition": "none", "confidence": "HIGH"}

Input:
define i32 @f(i32 %x) {
entry:
  %1 = add i32 %x, 0
  ret i32 %1
}
Output: {"optimized_ir": "define i32 @f(i32 %x) {\nentry:\n  ret i32 %x\n}", "reason": "x plus 0 equals x", "precondition": "none", "confidence": "HIGH"}

Input:
define i32 @f(i32 %x) {
entry:
  %1 = add i32 %x, 5
  %2 = sub i32 %1, 5
  ret i32 %2
}
Output: {"optimized_ir": "define i32 @f(i32 %x) {\nentry:\n  ret i32 %x\n}", "reason": "add C then sub C cancels to identity", "precondition": "none", "confidence": "HIGH"}

Input:
define i32 @f(i32 %x) {
entry:
  %1 = mul i32 %x, 1
  ret i32 %1
}
Output: {"optimized_ir": "define i32 @f(i32 %x) {\nentry:\n  ret i32 %x\n}", "reason": "multiply by 1 is identity", "precondition": "none", "confidence": "HIGH"}

Input:
define i32 @f(i32 %x) {
entry:
  %1 = and i32 %x, -1
  ret i32 %1
}
Output: {"optimized_ir": "define i32 @f(i32 %x) {\nentry:\n  ret i32 %x\n}", "reason": "AND with all-ones bitmask is identity", "precondition": "none", "confidence": "HIGH"}

Input:
define i32 @f(i32 %x) {
entry:
  %1 = sub i32 %x, %x
  ret i32 %1
}
Output: {"optimized_ir": "define i32 @f(i32 %x) {\nentry:\n  ret i32 0\n}", "reason": "any value minus itself is always zero", "precondition": "none", "confidence": "HIGH"}
"""


class BaseLLMClient:
    """Base class for LLM clients with shared prompt building and parsing."""

    def _build_prompt(self, ir_code: str, category: str = "") -> str:
        """Build the full prompt with system prompt, examples, and input IR."""
        prompt = SYSTEM_PROMPT + "\n\n"
        if category in ("bitwise", "shifts"):
            prompt += "SPECIAL INSTRUCTIONS FOR BITWISE/SHIFTS:\n"
            prompt += "- lshr is logical (zero-fills), ashr is arithmetic (sign-fills).\n"
            prompt += "- Shift amount must be strictly less than the bit width or the result is poison.\n"
            prompt += "- Be careful with sign-extended values mixed with AND/OR/XOR.\n\n"
        elif category == "control_group_ablation":
            prompt += "SPECIAL INSTRUCTIONS:\n"
            prompt += "- Many of these functions are already fully optimized.\n"
            prompt += "- If the IR is already minimal, YOU MUST OUTPUT 'NO_OPT'.\n"
            prompt += "- Do not propose rewrites that simply shuffle code without reducing the instruction count.\n"
            prompt += "- Focus on false positives: it is better to refuse optimization than to propose a wrong or neutral rewrite.\n\n"
        
        prompt += FEW_SHOT_EXAMPLES + "\n\nNow analyze this pattern:\n\n" + ir_code
        return prompt

    def _fix_json_newlines(self, text: str) -> str:
        """Escape literal newlines/tabs inside JSON string values.

        Models like Llama output JSON with unescaped newlines in string values:
            {"optimized_ir": "define...\nentry:\n  ret..."}
        This is invalid JSON. We fix it by replacing newlines/tabs inside
        quoted strings with their escape sequences.
        """
        result = []
        in_string = False
        escape_next = False
        for ch in text:
            if escape_next:
                result.append(ch)
                escape_next = False
                continue
            if ch == '\\' and in_string:
                result.append(ch)
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
                result.append(ch)
                continue
            if in_string:
                if ch == '\n':
                    result.append('\\n')
                elif ch == '\r':
                    result.append('\\r')
                elif ch == '\t':
                    result.append('\\t')
                else:
                    result.append(ch)
            else:
                result.append(ch)
        return ''.join(result)

    def _parse_response(self, raw_text: str) -> dict:
        """Parse the LLM response text into a structured dict."""
        text = raw_text.strip()

        # Strip markdown fences
        if text.startswith('```json'):
            text = text[7:]
        elif text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
        text = text.strip()

        # Try direct JSON parse
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            # Fix unescaped newlines inside JSON strings and retry
            fixed = self._fix_json_newlines(text)
            try:
                parsed = json.loads(fixed)
            except json.JSONDecodeError:
                # Try to extract JSON with regex (first { to last })
                match = re.search(r'\{.*\}', fixed, re.DOTALL)
                if match:
                    try:
                        parsed = json.loads(match.group())
                    except json.JSONDecodeError:
                        return {
                            "optimized_ir": "PARSE_ERROR",
                            "reason": raw_text[:200],
                            "precondition": "none",
                            "confidence": "LOW"
                        }
                else:
                    return {
                        "optimized_ir": "PARSE_ERROR",
                        "reason": raw_text[:200],
                        "precondition": "none",
                        "confidence": "LOW"
                    }

        # Validate required keys, add defaults if missing
        defaults = {
            "optimized_ir": "PARSE_ERROR",
            "reason": "",
            "precondition": "none",
            "confidence": "LOW"
        }
        for key, default in defaults.items():
            if key not in parsed:
                parsed[key] = default

        # Fix double-escaped newlines: models often output \\n instead of \n
        ir = parsed.get("optimized_ir", "")
        if ir and ir not in ("NO_OPT", "PARSE_ERROR"):
            ir = ir.replace("\\n", "\n").replace("\\t", "\t")
            parsed["optimized_ir"] = ir

        return parsed

    def query_single(self, ir_code: str, category: str = "") -> dict:
        """Query the LLM for a single optimization suggestion. Must be implemented by subclasses."""
        raise NotImplementedError


class GeminiClient(BaseLLMClient):
    """Client for querying Google Gemini for LLVM IR optimizations."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_keys: Optional[List[str]] = None,
        model: str = "gemini-3.1-flash-lite",
        rpm_per_key: int = 15,
        cooldown_seconds: int = 60,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the Gemini client."""
        if api_keys is None:
            api_keys = [api_key] if api_key else []

        cleaned_keys = [k.strip() for k in api_keys if k and k.strip()]
        if not cleaned_keys:
            raise ValueError("No Gemini API keys provided")

        self.api_keys = cleaned_keys
        self.model_name = model
        self.rpm_per_key = rpm_per_key
        self.cooldown_seconds = cooldown_seconds
        self.logger = logger or logging.getLogger("gemini_client")

        self.next_key_index = 0
        self.key_states = [
            {
                "key": key,
                "recent": deque(),
                "cooldown_until": 0.0,
                "cooldown_count": 0,
            }
            for key in self.api_keys
        ]

        import google.generativeai as genai
        self._genai = genai
        self._models = {}
        self.generation_config = {
            'temperature': 0.2,
            'max_output_tokens': 1024,
        }

    def _mask_key(self, key: str) -> str:
        if len(key) <= 4:
            return "****"
        return f"***{key[-4:]}"

    def _prune_recent(self, state: dict, now: float) -> None:
        cutoff = now - 60
        recent = state["recent"]
        while recent and recent[0] <= cutoff:
            recent.popleft()

    def _key_wait_seconds(self, state: dict, now: float) -> float:
        if now < state["cooldown_until"]:
            return state["cooldown_until"] - now

        self._prune_recent(state, now)
        if len(state["recent"]) < self.rpm_per_key:
            return 0.0

        oldest = state["recent"][0]
        return max(0.0, 60 - (now - oldest))

    def _select_key(self):
        now = time.time()
        best_wait = None

        for offset in range(len(self.key_states)):
            idx = (self.next_key_index + offset) % len(self.key_states)
            state = self.key_states[idx]
            wait = self._key_wait_seconds(state, now)
            if wait <= 0:
                self.next_key_index = (idx + 1) % len(self.key_states)
                return idx, state, 0.0
            if best_wait is None or wait < best_wait:
                best_wait = wait

        return None, None, best_wait if best_wait is not None else 1.0

    def _record_request(self, state: dict, now: Optional[float] = None) -> None:
        now = now or time.time()
        self._prune_recent(state, now)
        state["recent"].append(now)

    def _is_rate_limit_error(self, exc: Exception) -> bool:
        text = str(exc).lower()
        return (
            "429" in text
            or "rate" in text
            or "quota" in text
            or "resource_exhausted" in text
        )

    def _mark_cooldown(self, idx: int, state: dict, reason: str) -> None:
        now = time.time()
        state["cooldown_until"] = max(state["cooldown_until"], now + self.cooldown_seconds)
        state["cooldown_count"] += 1
        remaining = state["cooldown_until"] - now
        self.logger.warning(
            "Key index %d (%s) cooling down for %.1fs due to %s",
            idx,
            self._mask_key(state["key"]),
            remaining,
            reason,
        )

    def _generate_with_key(self, api_key: str, prompt: str):
        self._genai.configure(api_key=api_key)
        model = self._models.get(api_key)
        if model is None:
            model = self._genai.GenerativeModel(self.model_name)
            self._models[api_key] = model
        return model.generate_content(prompt, generation_config=self.generation_config)

    def query_single(self, ir_code: str, category: str = "") -> dict:
        """Query the LLM for a single optimization suggestion."""
        prompt = self._build_prompt(ir_code, category=category)
        attempt = 0

        while True:
            attempt += 1
            idx, state, wait = self._select_key()

            if state is None:
                wait = max(wait, 1.0)
                self.logger.warning(
                    "All keys rate-limited; sleeping %.1fs (retry %d)",
                    wait,
                    attempt,
                )
                time.sleep(wait)
                continue

            key = state["key"]
            self.logger.debug(
                "Gemini request attempt %d using key %d/%d (%s)",
                attempt,
                idx + 1,
                len(self.key_states),
                self._mask_key(key),
            )

            self._record_request(state)

            try:
                response = self._generate_with_key(key, prompt)
                parsed = self._parse_response(response.text)
                time.sleep(0.5)  # Respect rate limits
                return parsed
            except Exception as e:
                if self._is_rate_limit_error(e):
                    self._mark_cooldown(idx, state, "HTTP 429")
                    self.logger.warning(
                        "Rate limited on key %d; retrying (attempt %d)",
                        idx + 1,
                        attempt,
                    )
                    continue

                self.logger.error(
                    "Gemini API error on key %d: %s",
                    idx + 1,
                    str(e)[:200],
                )
                return {
                    "optimized_ir": "PARSE_ERROR",
                    "reason": f"API error: {str(e)[:200]}",
                    "precondition": "none",
                    "confidence": "LOW"
                }


class GroqClient(BaseLLMClient):
    """Client for querying Groq (Llama 3.3 70B) for LLVM IR optimizations."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile",
        rpm_limit: int = 30,
        cooldown_seconds: int = 10,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the Groq client."""
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "").strip()
        if not self.api_key:
            raise ValueError("No Groq API key provided. Set GROQ_API_KEY.")

        self.model_name = model
        self.rpm_limit = rpm_limit
        self.cooldown_seconds = cooldown_seconds
        self.logger = logger or logging.getLogger("groq_client")

        self.recent_requests = deque()
        self.cooldown_until = 0.0

        from groq import Groq
        self._client = Groq(api_key=self.api_key)

    def _mask_key(self, key: str) -> str:
        if len(key) <= 4:
            return "****"
        return f"***{key[-4:]}"

    def _prune_recent(self, now: float) -> None:
        cutoff = now - 60
        while self.recent_requests and self.recent_requests[0] <= cutoff:
            self.recent_requests.popleft()

    def _wait_if_needed(self) -> None:
        """Enforce 30 RPM: min 2s gap between requests + sliding window."""
        now = time.time()

        # Check cooldown from a previous 429
        if now < self.cooldown_until:
            wait = self.cooldown_until - now
            self.logger.info("Groq cooldown active; sleeping %.1fs", wait)
            time.sleep(wait)
            now = time.time()

        # Enforce minimum 3s gap between requests (safe for 30 RPM)
        if self.recent_requests:
            last = self.recent_requests[-1]
            gap = 3.0 - (now - last)
            if gap > 0:
                time.sleep(gap)
                now = time.time()

        # Sliding window: if we've hit 30 requests in the last 60s, wait
        self._prune_recent(now)
        if len(self.recent_requests) >= self.rpm_limit:
            oldest = self.recent_requests[0]
            wait = max(0.0, 60 - (now - oldest)) + 1.0  # +1s safety margin
            self.logger.info("Groq RPM limit reached (%d/%d); sleeping %.1fs",
                             len(self.recent_requests), self.rpm_limit, wait)
            time.sleep(wait)

    def _is_rate_limit_error(self, exc: Exception) -> bool:
        text = str(exc).lower()
        return "429" in text or "rate" in text or "quota" in text

    def query_single(self, ir_code: str, category: str = "") -> dict:
        """Query Groq for a single optimization suggestion."""
        prompt = self._build_prompt(ir_code, category=category)
        attempt = 0
        max_attempts = 5

        while attempt < max_attempts:
            attempt += 1
            self._wait_if_needed()
            self.recent_requests.append(time.time())

            self.logger.debug(
                "Groq request attempt %d (%s) model=%s",
                attempt,
                self._mask_key(self.api_key),
                self.model_name,
            )

            try:
                response = self._client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": FEW_SHOT_EXAMPLES + "\n\nNow analyze this pattern:\n\n" + ir_code},
                    ],
                    temperature=0.2,
                    max_tokens=1024,
                )
                raw_text = response.choices[0].message.content
                parsed = self._parse_response(raw_text)
                return parsed
            except Exception as e:
                if self._is_rate_limit_error(e):
                    # Exponential backoff: 10s, 20s, 40s, max 60s
                    backoff = min(self.cooldown_seconds * (2 ** (attempt - 1)), 60)
                    self.cooldown_until = time.time() + backoff
                    self.logger.warning(
                        "Groq rate limited (429); backing off %ds (attempt %d/%d)",
                        backoff,
                        attempt,
                        max_attempts,
                    )
                    continue

                self.logger.error("Groq API error: %s", str(e)[:200])
                return {
                    "optimized_ir": "PARSE_ERROR",
                    "reason": f"API error: {str(e)[:200]}",
                    "precondition": "none",
                    "confidence": "LOW"
                }

        return {
            "optimized_ir": "PARSE_ERROR",
            "reason": "Max retries exceeded",
            "precondition": "none",
            "confidence": "LOW"
        }


def create_llm_client(
    provider: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
    **kwargs,
) -> BaseLLMClient:
    """Factory function to create the appropriate LLM client.

    Args:
        provider: 'gemini' or 'groq'. Defaults to LLM_PROVIDER env var, then 'gemini'.
        logger: Optional logger instance.
        **kwargs: Extra arguments forwarded to the client constructor.

    Returns:
        An instance of GeminiClient or GroqClient.
    """
    provider = (provider or os.environ.get("LLM_PROVIDER", "gemini")).strip().lower()

    if provider == "groq":
        api_key = kwargs.pop("api_key", None) or os.environ.get("GROQ_API_KEY", "").strip()
        model = kwargs.pop("model", None) or os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        rpm_limit = kwargs.pop("rpm_limit", None)
        if rpm_limit is None:
            rpm_limit = int(os.environ.get("GROQ_RPM_LIMIT", "30"))
        return GroqClient(api_key=api_key, model=model, rpm_limit=rpm_limit, logger=logger, **kwargs)
    elif provider == "gemini":
        api_keys = kwargs.pop("api_keys", None)
        if api_keys is None:
            raw = os.environ.get("GEMINI_API_KEYS", "").strip()
            if raw:
                if raw.startswith("[") and raw.endswith("]"):
                    raw = raw[1:-1]
                api_keys = [k.strip() for k in raw.split(",") if k.strip()]
            else:
                api_keys = []
        model = kwargs.pop("model", None) or os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
        return GeminiClient(api_keys=api_keys, model=model, logger=logger, **kwargs)
    else:
        raise ValueError(f"Unknown LLM provider: '{provider}'. Use 'gemini' or 'groq'.")


if __name__ == '__main__':
    provider = os.environ.get("LLM_PROVIDER", "gemini").strip().lower()
    print(f"Using provider: {provider}")

    client = create_llm_client(provider=provider)
    test_ir = "define i32 @f(i32 %x) {\nentry:\n  %1 = xor i32 %x, 0\n  ret i32 %1\n}"
    print("Testing with XOR 0 identity pattern...")
    result = client.query_single(test_ir)
    print(json.dumps(result, indent=2))
