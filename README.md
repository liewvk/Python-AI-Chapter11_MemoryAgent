# Chapter 11 – Python AI Agent with Memory

Standalone companion source code for *Python AI Agents Made Easy*.

## Requirements

- Visual Studio 2026 with Python development tools
- Python 3.12 and a project `.venv`
- Ollama running locally at `http://localhost:11434`
- Local model `qwen3.5:9b` (or modify `settings.py` to use `qwen3.5:4b`)

## Setup (PowerShell in project folder)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
ollama pull qwen3.5:9b
.\.venv\Scripts\python.exe main.py
```

If Ollama is not already running, launch its Windows app or run `ollama serve` in another terminal.

## Commands

- `/remember project | I am building a school management system in Python.`
- `/remember preference | I prefer short Python examples.`
- `/memories` – list saved information and IDs
- `/recall python` – find related memory records
- `/update ID | corrected text`
- `/forget ID` – delete a saved memory
- `/history` – view this session's recent messages
- `/clear` – clear recent chat without deleting long-term memory
- `/status`, `/help`, `/exit`

The assistant saves only information explicitly confirmed with `/remember`. Long-term memories are plain-text JSON in the user's local application data directory. They are *not encrypted*; do not save passwords, credentials, sensitive personal information, or confidential business data. Recent conversation history is **not** saved and is cleared when the program exits. Retrieval uses simple keyword matching and may miss paraphrased questions.

No paid cloud API is required. The code does not send email or schedule reminders.
