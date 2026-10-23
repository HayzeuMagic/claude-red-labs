# Offline Installation Guide

Do these steps **with internet access**, once per machine, ideally before lab day.
Everything after this guide works with the network disconnected (verify with
`06-offline-readiness-checklist.md`).

## 0. Prerequisites

| Tool | Why | Check |
|---|---|---|
| Git | clone Claude-Red and this kit | `git --version` |
| Python 3.9+ | `skill_loader.py`, Lab 2 app, pytest | `python --version` |
| Docker Desktop (or Docker Engine) | run Juice Shop | `docker --version` |
| A free Ollama account is **not** required for local models — accounts are only for
  Ollama's optional `:cloud` models, which this kit never uses. | | |

## 1. Install Ollama

**Windows (PowerShell):**
```powershell
irm https://ollama.com/install.ps1 | iex
```
or download `OllamaSetup.exe` from https://ollama.com/download and run it.

**macOS / Linux:** download from https://ollama.com/download, or on Linux:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verify:
```bash
ollama --version
```

## 2. Pull a local model (do this online, once)

Pick a tier from `docs/01-architecture.md` §3. Default recommendation:
```bash
ollama pull qwen2.5-coder:7b
```
This downloads the model into Ollama's local store (~4.7 GB). After this completes,
`ollama run qwen2.5-coder:7b` works with no network connection at all — Ollama is a local
runtime; it never calls out to the internet to serve a pulled model.

If a lab machine is 8 GB RAM, pull the smaller tier instead:
```bash
ollama pull qwen2.5-coder:1.5b
```

## 3. Get Claude-Red (the skill library)

```bash
git clone https://github.com/SnailSploit/claude-red claude-red-skills
```
This is just a folder of Markdown files once cloned — no further setup, and nothing in it
calls out to Claude or any API. We reuse it as read-only reference content.

## 4. Get this lab kit

If you're reading this file, you already have it. Otherwise:
```bash
git clone <this repo's URL> claude-red-labs
cd claude-red-labs
```

## 5. Build the skill-loaded models

```bash
cd claude-red-labs
python tools/skill_loader.py \
  --skill ../claude-red-skills/Skills/web/offensive-idor/SKILL.md \
  --name redlab-idor --base qwen2.5-coder:7b

python tools/skill_loader.py \
  --skill ../claude-red-skills/Skills/utility/offensive-fast-checking/SKILL.md \
  --skill ../claude-red-skills/Skills/utility/offensive-reporting/SKILL.md \
  --name redlab-webtriage --base qwen2.5-coder:7b

python tools/skill_loader.py --baseline --name redlab-baseline --base qwen2.5-coder:7b
```
Each command prints `Wrote Modelfile ...` and then runs `ollama create`, which is local and
offline (it just repackages the already-pulled base model with a new system prompt — no
download happens here).

Verify each model exists:
```bash
ollama list
```
You should see `redlab-idor`, `redlab-webtriage`, `redlab-baseline`, and your base tag.

## 6. Pull the Lab 1 target image (online, once)

```bash
docker compose pull
```
(run from the `claude-red-labs` root, where `docker-compose.yml` lives)

## 7. Set up the Lab 2 app

```bash
cd lab2/vuln_app
python -m venv .venv
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pip install pytest
```

## 8. (Optional) OWASP ZAP

Download the installer for your OS from https://www.zaproxy.org/download/ and run it once
online. ZAP works fully offline afterward; only its optional add-on marketplace needs
internet, and the labs don't require any add-ons.

## 9. Test everything offline

See `docs/06-offline-readiness-checklist.md` — **disconnect the network and run through it**
before lab day. Don't skip this; a step that silently needed the internet is much easier to
catch now than mid-class.
