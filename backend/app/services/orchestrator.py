from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .asr import ASRService
from .llm import LLMService
from .tts import TTSService
from .memory import ConversationStore
from typing import Optional


@dataclass
class TalkResult:
    transcript: str
    reply_text: str
    audio_wav_bytes: bytes
    conversation_id: str


class Orchestrator:
    """Coordinates ASR -> LLM -> TTS."""

    def __init__(
        self,
        asr: ASRService,
        llm: LLMService,
        tts: TTSService,
        per_step_timeout_seconds: int,
        memory: Optional[ConversationStore] = None,
    ) -> None:
        self._asr = asr
        self._llm = llm
        self._tts = tts
        self._timeout = per_step_timeout_seconds
        self._memory = memory or ConversationStore(max_turns=20)

    async def talk(
        self,
        audio_path: Path,
        conversation_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> TalkResult:
        from app.core.config import settings
        transcript = await self._asr.transcribe_audio_file(
            audio_path,
            timeout_seconds=self._timeout,
            language=getattr(settings, "asr_language", None),
        )

        # Build chat history
        conv_id = self._memory.ensure_conversation_id(conversation_id)
        history_pairs = self._memory.get_history(conv_id)
        history_msgs = [{"role": role, "content": content} for role, content in history_pairs]

        reply_text = await self._llm.generate_chat(
            system_prompt=system_prompt,
            history=history_msgs,
            user_message=transcript,
            timeout_seconds=self._timeout,
        )

        # Store turn always so history persists until explicit reset
        self._memory.append_turn(conv_id, transcript, reply_text)

        audio_wav = await self._tts.synthesize_text(reply_text, timeout_seconds=self._timeout)
        return TalkResult(
            transcript=transcript,
            reply_text=reply_text,
            audio_wav_bytes=audio_wav,
            conversation_id=conv_id,
        )

    def reset_conversation(self, conversation_id: str) -> None:
        """Clear stored history for a conversation id."""
        self._memory.reset(conversation_id)


