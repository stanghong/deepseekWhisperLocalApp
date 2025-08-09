from __future__ import annotations

import asyncio
import shutil
import tempfile
from pathlib import Path

import subprocess


class TTSService:
    """TTS service with Piper as primary and macOS 'say' as fallback.

    If `voice_model_path` is not provided, we fall back to using the macOS `say`
    command to generate an AIFF file, and then convert it to WAV using `afconvert`.
    """

    def __init__(self, piper_path: str, voice_model_path: str) -> None:
        self._piper_path = piper_path
        self._voice_model_path = voice_model_path

    def validate(self) -> None:
        # Piper is optional if we have macOS 'say' fallback
        if self._voice_model_path:
            if not self._piper_path:
                raise ValueError("Piper executable path must be set when using Piper")
            if not Path(self._voice_model_path).exists():
                raise ValueError(f"Piper voice model not found: {self._voice_model_path}")

    async def synthesize_text(self, text: str, timeout_seconds: int) -> bytes:
        """Synthesize text to WAV bytes.

        Uses Piper if a voice model path is configured; otherwise uses macOS `say`
        as a fallback so local testing works without Piper.
        """

        if self._voice_model_path:
            return await self._synthesize_with_piper(text, timeout_seconds)
        return await self._synthesize_with_macos_say(text, timeout_seconds)

    async def _synthesize_with_piper(self, text: str, timeout_seconds: int) -> bytes:
        def _run() -> bytes:
            with tempfile.TemporaryDirectory() as td:
                out_path = Path(td) / "out.wav"
                cmd = [
                    self._piper_path,
                    "-m",
                    self._voice_model_path,
                    "-f",
                    str(out_path),
                    "-q",
                ]
                proc = subprocess.run(
                    cmd,
                    input=text.encode("utf-8"),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                    timeout=timeout_seconds,
                )
                if proc.returncode != 0 or not out_path.exists():
                    raise RuntimeError(
                        f"Piper failed (code={proc.returncode}): {proc.stderr.decode(errors='ignore')}"
                    )
                return out_path.read_bytes()

        return await asyncio.to_thread(_run)

    async def _synthesize_with_macos_say(self, text: str, timeout_seconds: int) -> bytes:
        def _run() -> bytes:
            if shutil.which("say") is None:
                raise RuntimeError(
                    "No TTS configured: set PIPER_VOICE_PATH or install macOS 'say' command"
                )
            with tempfile.TemporaryDirectory() as td:
                aiff_path = Path(td) / "out.aiff"
                wav_path = Path(td) / "out.wav"
                # Generate AIFF via macOS 'say'
                proc1 = subprocess.run(
                    ["say", "-o", str(aiff_path), text],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                    timeout=timeout_seconds,
                )
                if proc1.returncode != 0 or not aiff_path.exists():
                    raise RuntimeError(
                        f"macOS say failed (code={proc1.returncode}): {proc1.stderr.decode(errors='ignore')}"
                    )
                # Convert to WAV using afconvert (macOS)
                if shutil.which("afconvert") is None:
                    raise RuntimeError("afconvert not found; cannot convert AIFF to WAV")
                proc2 = subprocess.run(
                    [
                        "afconvert",
                        str(aiff_path),
                        str(wav_path),
                        "-f",
                        "WAVE",
                        "-d",
                        "LEI16",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                    timeout=timeout_seconds,
                )
                if proc2.returncode != 0 or not wav_path.exists():
                    raise RuntimeError(
                        f"afconvert failed (code={proc2.returncode}): {proc2.stderr.decode(errors='ignore')}"
                    )
                return wav_path.read_bytes()

        return await asyncio.to_thread(_run)


