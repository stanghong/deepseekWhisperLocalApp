# Write a Markdown scaffold without any code, commands, or snippets
from pathlib import Path

content = """# Local Voice Assistant (100% Local) — Architecture & Build Guide

This document is a **Cursor-ready scaffold** describing how to build a fully local, voice-enabled assistant using the following components, without including any code. It is structured so you can paste sections as prompts into Cursor and let it generate files for you.

---

## 1) Goal

Enable a private, offline voice chat system that:
- Listens to the user via a browser microphone.
- Transcribes speech locally using Whisper Tiny (via an on-device ASR library).
- Generates an answer locally using a reasoning LLM (DeepSeek R1 via Ollama).
- Converts the answer to speech locally using an offline TTS engine (Piper).
- Serves a single-page UI and one or more API endpoints via a lightweight web framework.
- Runs entirely on a single machine with no internet dependency after installation.

---

## 2) High-Level Architecture

**Data Flow**  
1. User speaks into the browser microphone.  
2. Browser captures audio and sends it to the backend over a single POST endpoint.  
3. Backend transcribes audio into text using a local ASR model (Whisper Tiny).  
4. Backend sends the transcribed text to the local LLM endpoint (DeepSeek R1 via a local model server).  
5. Backend receives the textual reply from the LLM.  
6. Backend synthesizes a spoken version with a local TTS engine (Piper).  
7. Backend returns an audio stream back to the browser along with the user transcript and assistant reply for display.  
8. Browser plays the audio reply and shows the texts.

**ASCII Diagram**  
[Mic] → Browser UI → Backend (/talk) → ASR → LLM → TTS → Backend → Browser (audio + text)

- **Browser UI**: single HTML page handles recording, submit, and playback.  
- **Backend**: simple web framework with one health check endpoint and one talk endpoint.  
- **ASR**: small-footprint, on-device model (Whisper Tiny) for speed.  
- **LLM**: DeepSeek R1 running under a local model runtime.  
- **TTS**: local offline TTS (Piper) with a chosen voice model.  

---

## 3) Components & Responsibilities

- **Frontend (Browser UI)**
  - Record audio using native media APIs.
  - POST the audio to a single endpoint.
  - Display the returned user transcript and model reply text.
  - Auto-play the returned audio reply.
  - Graceful states: recording, sending, playing, idle, error.

- **Backend (Web Framework)**
  - Serve static assets (the UI) and expose a health endpoint.
  - Accept audio uploads on a single endpoint.
  - Manage temporary files safely and clean them up.
  - Orchestrate ASR, LLM, and TTS modules sequentially.
  - Return audio bytes and useful headers for the UI.
  - Provide clear error messages and status codes.

- **ASR (Whisper Tiny)**
  - Load once at startup.
  - Transcribe short utterances quickly with reasonable accuracy.
  - Support voice activity detection and language auto-detection where possible.

- **LLM (DeepSeek R1 via local runtime)**
  - Accept plain text prompts and return plain text completions.
  - Optional controls: temperature, max tokens, context window.
  - Handle brief system or instruction prompts to keep style concise.

- **TTS (Piper)**
  - Load voice model and synthesize to an audio format playable by browsers.
  - Provide consistent sampling rate and channel format.
  - Keep latency low; consider pre-warming on startup.

---

## 4) Minimal File Structure (No Code)

- Project root directory: a short, hyphenated name.
- Backend file for the web server and endpoints.
- Requirements file for Python dependencies (or equivalent environment manifest).
- Optional environment file for local configuration overrides.
- Web folder with a single-page HTML UI and minimal CSS/JS assets.
- README file referencing this build guide.

**Example layout (names only):**
- Root folder  
  - Backend file (single module)  
  - Requirements manifest  
  - Environment configuration (optional)  
  - Web folder  
    - HTML file (root page)  
    - Optional icons or small assets  

---

## 5) Implementation Checklist (Cursor Prompts)

Use these task-oriented prompts in Cursor. Each item should produce or refine a specific file. Do not paste code into the prompts; describe behavior and interfaces precisely.

### A. Create README
- Describe the purpose, the all-local design, and the major components.
- Include the system requirements and any installation prerequisites in human language.
- Clarify that no internet is required after local models are installed.

### B. Create Backend Module
- Define a health endpoint that returns a simple JSON confirmation.
- Define one “talk” endpoint that accepts a short audio file upload from the browser.
- The endpoint should:
  - Save the incoming audio to a temporary file and close the file safely.
  - Transcribe speech to text using the locally loaded ASR model.
  - Send the transcription to the local LLM endpoint and receive a text reply.
  - Synthesize the reply with the local TTS engine to a browser-playable format.
  - Return audio bytes in the response body, and include the user transcript and assistant reply in response headers.
- Ensure robust error handling, timeouts, and cleanup of temporary resources.
- Load ASR models once on startup to reduce per-request latency.
- Mount and serve the static web UI from the same server process.

### C. Create Frontend Page
- A single page with:
  - A start button to begin recording.
  - A stop button to finish recording and trigger upload.
  - A visible area to display the “You said” transcript and the “Assistant reply” text.
  - An audio player element that auto-plays the returned audio.
  - Clear recording/idle states and simple styles.
- Use the browser’s media capture and ensure microphone permission prompts are handled gracefully.
- Handle errors by showing a short message and returning to idle state.

### D. Configuration Strategy
- Define environment variables for:
  - Local LLM server URL and model identifier.
  - ASR model size and compute mode.
  - TTS engine path and voice model path.
- Document reasonable defaults and when to adjust them.
- Decide on logging verbosity for dev vs. quiet production.

### E. Testing Plan
- Local manual testing sequence:
  - Confirm health endpoint responds.
  - Load the UI and allow microphone permission.
  - Speak a short sentence and verify the returned transcript and audio.
  - Validate that response headers contain the expected fields.
  - Test error cases: no audio, very short audio, very long audio, missing local model server.
- Optional CLI-based sanity checks with a short test clip.

### F. Performance & Quality Tuning
- ASR:
  - Choose the smallest model that meets accuracy needs.
  - Consider voice activity detection and short segments to reduce latency.
- LLM:
  - Prefer a reasoning-capable model tuned for concise answers.
  - Tune generation parameters to avoid overly long outputs.
- TTS:
  - Choose a voice size that balances quality and speed.
  - Consider synthesizing at a consistent sample rate compatible with browsers.
- Backend:
  - Preload models at startup.
  - Avoid disk I/O bottlenecks by minimizing conversions and copies.

### G. Resilience & UX
- Timeouts for ASR, LLM, and TTS steps with actionable error messages.
- Graceful degradation if any component is unavailable.
- Visual feedback on the frontend: recording, uploading, generating, and playing states.
- Clear failure messages with guidance for next steps.

---

## 6) Security, Privacy, and Offline Guarantees

- All data stays on the device; no network calls after models are installed.
- Do not log raw audio or transcripts unless explicitly enabled for debugging.
- Clean up temporary files immediately after use.
- Use restrictive CORS or same-origin hosting for the UI and API.
- Make the offline requirement explicit in the README to avoid confusion.

---

## 7) Local Runbook (Conceptual, No Commands)

- Ensure the local LLM runtime is installed and the target model is present.
- Ensure the TTS engine is installed and a voice model file exists.
- Ensure an ASR runtime is available and configured for a small model.
- Start the backend server.
- Open the local web page served by the backend.
- Grant microphone access and perform a test round-trip.
- Validate the health endpoint and logs if anything fails.

---

## 8) Troubleshooting Guide (Conceptual, No Commands)

- If the UI cannot record:
  - Check browser permissions for the microphone.
  - Ensure HTTPS is not required for local mic capture in the chosen browser context.
- If transcription is empty:
  - Speak closer to the mic; check input device settings.
  - Verify that the ASR model is properly loaded at startup.
- If LLM replies fail:
  - Verify the local LLM runtime is running and the model identifier is correct.
  - Reduce prompt length to rule out context window issues.
- If TTS audio is not returned or cannot play:
  - Verify the TTS voice model path.
  - Confirm the generated audio format is playable by the browser.
- If latency is high:
  - Use smaller ASR and TTS models.
  - Trim long silences in recorded audio.
  - Preload or warm up subsystems on startup.

---

## 9) Extension Ideas

- Streaming partial transcripts and partial TTS for lower perceived latency.
- Adding a system-instruction switch (concise vs. friendly vs. technical).
- Keeping a short local conversation memory with explicit reset.
- Hotkey-based push-to-talk in the browser.
- Multiple voices or language support.
- Optional on-device noise suppression or AGC.

---

## 10) Deliverables Checklist

- A single repository with:
  - The backend module (one file is fine).
  - A minimal web UI folder.
  - A requirements manifest or environment spec.
  - A README that echoes this architecture and explains the setup in words.
- One health endpoint and one talk endpoint.
- Clear logs and error messages suitable for debugging.
- A short demo recording workflow documented in the README (in words only).

---

## 11) Cursor Handoff Notes

When prompting Cursor, keep prompts **outcome-focused** and **code-agnostic**, for example:
- “Create a FastAPI backend with one health endpoint and a ‘talk’ endpoint as described in the Architecture section.”
- “Create a single HTML file that records audio, sends it to the backend, and plays the returned audio, with simple UI states.”
- “Add environment-based configuration to the backend for model locations and endpoints, following the Configuration Strategy section.”
- “Implement error handling and logging aligned with the Troubleshooting Guide and Resilience & UX sections.”

Attach this document to Cursor so it can reference each section while generating the code for you.

---

**End of scaffold.**"""

out_path = Path("/mnt/data/local_voice_assistant_scaffold.md")
out_path.write_text(content, encoding="utf-8")
str(out_path)
