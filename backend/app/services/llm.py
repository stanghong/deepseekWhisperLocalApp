from __future__ import annotations

from typing import Optional, List, Dict
import json
import re

import httpx


class LLMService:
    """Client for a local Ollama server for text generation."""

    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self._base_url, timeout=None)
        return self._client

    async def generate_reply(self, prompt: str, timeout_seconds: int) -> str:
        client = await self._get_client()
        instruction = (
            "Respond ONLY as a compact JSON object with a single key 'final', e.g. {\"final\":\"...\"}. "
            "Do not include any other text or keys."
        )
        payload = {
            "model": self._model,
            "prompt": f"{instruction}\n\n{prompt}",
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.3,
                "num_predict": 384,
            },
        }
        resp = await client.post("/api/generate", json=payload, timeout=timeout_seconds)
        resp.raise_for_status()
        data = resp.json()
        # Ollama returns { response: str, ... }
        text = (data.get("response") or "").strip()
        parsed = self._parse_json_candidate(text)
        if parsed:
            return parsed
        cleaned = self._strip_think_text(text)
        final = self._extract_final(cleaned)
        return final or cleaned or text

    async def generate_chat(
        self,
        system_prompt: Optional[str],
        history: List[Dict[str, str]],
        user_message: str,
        timeout_seconds: int,
    ) -> str:
        """Generate a reply given chat history and optional system prompt.

        Uses the Ollama chat endpoint for better behavior with roles.
        """
        client = await self._get_client()
        messages: list[dict[str, str]] = []
        builtin_guard = (
            "You are a concise assistant. Provide only the final answer. "
            "Do not include chain-of-thought or analysis. "
            "Respond ONLY as a compact JSON object with a single key 'final', e.g. {\"final\":\"...\"}. "
            "Return JSON only."
        )
        merged_system = f"{builtin_guard} " + (system_prompt or "")
        messages.append({"role": "system", "content": merged_system.strip()})
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        payload = {
            "model": self._model,
            "stream": False,
            "messages": messages,
            "format": "json",
            "options": {
                "temperature": 0.25,
                "num_predict": 384,
                "stop": ["</think>"]
            },
        }
        # Prefer to allow the model to complete after </think>; do not stop at <think>
        resp = await client.post("/api/chat", json=payload, timeout=timeout_seconds)
        resp.raise_for_status()
        data = resp.json()
        # Ollama chat returns { message: {role, content}, ... }
        message = (data.get("message") or {})
        raw_text = (message.get("content") or "").strip()
        parsed = self._parse_json_candidate(raw_text)
        if parsed:
            return parsed
        cleaned = self._strip_think_text(raw_text)
        final = self._extract_final(cleaned)
        return final or cleaned or raw_text

    @staticmethod
    def _parse_json_candidate(text: str) -> Optional[str]:
        try:
            obj = json.loads(text)
        except Exception:
            return None
        if isinstance(obj, dict):
            # Prefer common answer keys
            for key in ("final", "answer", "output", "response", "result"):
                val = obj.get(key)
                if isinstance(val, str) and val.strip():
                    return val.strip()
            # Else, join first non-empty string value
            for val in obj.values():
                if isinstance(val, str) and val.strip():
                    return val.strip()
        if isinstance(obj, list):
            for item in obj:
                if isinstance(item, str) and item.strip():
                    return item.strip()
                if isinstance(item, dict):
                    for key in ("final", "answer", "output", "response", "result"):
                        v = item.get(key) if isinstance(item, dict) else None
                        if isinstance(v, str) and v.strip():
                            return v.strip()
        return None

    @staticmethod
    def _strip_think_text(text: str) -> str:
        """Remove any <think>...</think> sections and similar traces.

        This avoids exposing chain-of-thought and returns only the final answer.
        """
        # Remove any <think>...</think> blocks (non-greedy, case-insensitive)
        cleaned = re.sub(r"(?is)<think>.*?</think>", "", text)
        # Also remove residual tags like <think> without closing, and stray XML tags if any
        cleaned = re.sub(r"(?is)</?think>", "", cleaned)
        # Trim whitespace
        return cleaned.strip()

    @staticmethod
    def _extract_final(text: str) -> str:
        """Heuristically select the final answer without chain-of-thought.

        Strategy:
        1) If a line starts with 'FINAL:' return text after it.
        2) Else, if multiple paragraphs exist, return the last non-empty paragraph.
        3) Else, return the text as-is.
        """
        if not text:
            return ""
        m = re.search(r"(?im)^\s*FINAL\s*:\s*(.*)$", text)
        if m:
            return m.group(1).strip()
        parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        if len(parts) >= 2:
            # choose last paragraph that doesn't look like meta/planning
            for para in reversed(parts):
                if not LLMService._looks_meta(para):
                    return para.strip()
            return parts[-1].strip()
        # Fallback: remove meta-like lines
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        non_meta = [ln for ln in lines if not LLMService._looks_meta(ln)]
        if non_meta:
            return non_meta[-1]
        return text.strip()

    @staticmethod
    def _looks_meta(s: str) -> bool:
        return bool(re.search(r"(?i)\b(structure|explain|mention|avoid|guideline|steps|plan|let's|we should|potential gaps|as per instructions|analysis|think)\b", s))

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


