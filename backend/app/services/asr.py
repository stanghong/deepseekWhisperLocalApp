from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from faster_whisper import WhisperModel


class ASRService:
    """ASR service backed by faster-whisper.

    Loads the model once and provides an async method to transcribe audio files.
    """

    def __init__(
        self,
        model_size: str,
        compute_type: str = "int8",
        device: str = "auto",
        cpu_threads: int = 4,
    ) -> None:
        self._model_size = model_size
        self._compute_type = compute_type
        self._device = device
        self._cpu_threads = cpu_threads
        self._model: Optional[WhisperModel] = None

    def load(self) -> None:
        if self._model is None:
            self._model = WhisperModel(
                self._model_size,
                compute_type=self._compute_type,
                device=self._device,
                cpu_threads=self._cpu_threads,
            )

    async def transcribe_audio_file(self, audio_path: Path, timeout_seconds: int, language: Optional[str] = None) -> str:
        """Transcribe an audio file to text.

        Args:
            audio_path: Path to an audio file readable by ffmpeg.
            timeout_seconds: Max seconds to allow for transcription.

        Returns:
            Transcribed text.
        """
        if self._model is None:
            # Load lazily if not preloaded
            self.load()

        assert self._model is not None

        def _do_transcribe() -> str:
            segments, _ = self._model.transcribe(
                str(audio_path), language=language, vad_filter=True, beam_size=1, best_of=1
            )
            return " ".join(seg.text.strip() for seg in segments).strip()

        return await asyncio.wait_for(asyncio.to_thread(_do_transcribe), timeout=timeout_seconds)


