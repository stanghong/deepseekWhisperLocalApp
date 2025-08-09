from __future__ import annotations

import uuid
from typing import Dict, List, Tuple, Optional


Message = Tuple[str, str]  # (role, content) where role in {"user", "assistant"}


class ConversationStore:
    """In-memory conversation storage with a per-conversation cap.

    Not for production persistence; suitable for single-process local usage.
    """

    def __init__(self, max_turns: int = 20) -> None:
        self._conversations: Dict[str, List[Message]] = {}
        self._max_turns = max_turns

    def ensure_conversation_id(self, conversation_id: Optional[str]) -> str:
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        self._conversations.setdefault(conversation_id, [])
        return conversation_id

    def append_turn(self, conversation_id: str, user_text: str, assistant_text: str) -> None:
        history = self._conversations.setdefault(conversation_id, [])
        history.append(("user", user_text))
        history.append(("assistant", assistant_text))
        # Cap to last N messages
        if len(history) > self._max_turns * 2:
            self._conversations[conversation_id] = history[-self._max_turns * 2 :]

    def get_history(self, conversation_id: str) -> List[Message]:
        return list(self._conversations.get(conversation_id, []))

    def reset(self, conversation_id: str) -> None:
        self._conversations.pop(conversation_id, None)


