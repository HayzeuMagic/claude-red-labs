# Offline AI Cybersecurity Labs — Claude-Red + Ollama

A ready-to-run instructor's kit for two hands-on, fully offline, AI-assisted security labs,
built for undergraduate cybersecurity / intro-pentesting students who do not have a paid
Claude account. The AI model runs locally through [Ollama](https://ollama.com), primed with
real [Claude-Red](https://github.com/SnailSploit/claude-red) skill files as plain prompt
content — no subscription, no API key, no cloud inference anywhere in the stack.

This README is a condensed, Windows-first walkthrough. Every step number here matches the
same step number in [`docs/02-offline-installation.md`](docs/02-offline-installation.md),
which has the full detail (exact terminal, exact directory, expected output,
troubleshooting) — follow this README for the overview, that doc when you need the detail.

## Lab Resources

| Resource | What it's for | Where |
|---|---|---|
| This repository | Lab manuals, worksheets, rubrics, scripts, and the Lab 2 target app | you're in it |
| Claude-Red | The skill library (`SKILL.md` methodology files) that becomes the AI's system prompt | https://github.com/SnailSploit/claude-red |
| Ollama | The local model runtime | https://ollama.com |
| OWASP Juice Shop | The Lab 1 target application (Docker image) | `bkimminich/juice-shop` on Docker Hub |
| OWASP ZAP (optional) | Free proxy/scanner for sending and inspecting requests | https://www.zaproxy.org/download/ |

## What's Inside This Repo

```
docs/01-architecture.md                 why this design, hardware/system requirements
docs/02-offline-installation.md         Step 1-10: full detail for one-time setup
docs/03-lab1-web-vuln-assessment.md     Lab 1 manual: Juice Shop + IDOR
docs/04-lab2-vuln-remediation.md        Lab 2 manual: SQL injection + fix + regression test
docs/05-comparison-exercise.md          optional: AI with skill vs. without skill
docs/06-offline-readiness-checklist.md  run this with the network OFF before lab day
docs/07-ollama-windows-troubleshooting.md  Ollama won't start / port 11434 issues on Windows
docs/worksheets/                        student fill-in sheets for both labs
docs/rubrics/                           pointer to the grading tables (inline in each manual)
tools/skill_loader.py                   turns a Claude-Red SKILL.md into a local Ollama model
tools/Modelfile.template                reference Modelfile, shown for transparency
docker-compose.yml                       launches OWASP Juice Shop for Lab 1
lab2/vuln_app/app.py                    intentionally vulnerable Flask app (SQLi) for Lab 2
lab2/vuln_app/app_fixed.py              the fixed version, for comparison
lab2/tests/test_security_regression.py pytest proof that the fix closes the bug
```

## Before You Start

> **Note:** Steps 1–7 below need internet access once, to download software and models.
> Everything after Step 7 is designed to run with the network **disconnected** — Step 10
> and `docs/06-offline-readiness-checklist.md` exist specifically to prove that.

> **Important:** every target in these labs is a disposable, local-only application
> (`127.0.0.1`). Nothing here is to be pointed at a system you do not own or have not been
> explicitly authorized to test. See **Scope and Safety** at the bottom of this file.

Minimum hardware: 8 GB RAM (CPU-only, slower, uses a smaller model tier). Recommended: 16 GB
RAM. Full tier breakdown, plus CPU/storage/virtualization notes, is in
`docs/01-architecture.md` §3.

> **Note — two different environments:** the target deployment PCs this kit is written for
> do not have Hyper-V installed or enabled, and Ollama runs directly on Windows without it —
> nothing here needs Hyper-V. A separate development PC used to build/test this kit does have
> Hyper-V, and hit a real, documented port-conflict issue there (see
> [`docs/07-ollama-windows-troubleshooting.md`](docs/07-ollama-windows-troubleshooting.md)).
> That doc explains how to diagnose the same symptoms on *either* kind of PC without assuming
> Hyper-V is the cause — it usually isn't, on a PC that doesn't have it.

---

# Step 1: Confirm Prerequisites Are Installed

**RUN IN:** Windows PowerShell — Normal User

- **Git** — https://git-scm.com/downloads. Verify:
  ```powershell
  git --version
  ```
- **Python 3.9+** — https://www.python.org/downloads/ (check "Add python.exe to PATH" during
  install). Verify:
  ```powershell
  python --version
  ```
- **Docker Desktop** (needed for Lab 1 only) — https://www.docker.com/products/docker-desktop/.
  Its installer needs an elevated prompt (Windows will ask automatically); the `docker`
  command itself afterward does not. Verify:
  ```powershell
  docker --version
  ```

Full detail: [`docs/02-offline-installation.md`](docs/02-offline-installation.md) Step 1.

---

# Step 2: Install Ollama

**RUN IN:** Windows PowerShell — Normal User (this installs per-user; no Administrator
rights needed)

```powershell
irm https://ollama.com/install.ps1 | iex
```
or download `OllamaSetup.exe` from https://ollama.com/download and run it.

**macOS / Linux** (not this kit's target deployment, kept here for anyone running the labs
cross-platform):
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verify the CLI, then verify the server is actually answering — these are two different
checks:
```powershell
ollama --version
Get-Process | Where-Object { $_.Name -like "*ollama*" }
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

> **Note:** no Ollama account is needed for anything in this kit. Accounts only matter for
> Ollama's optional `:cloud` models, which these labs never use.

> **Note:** if any command above fails — including `Error: timed out waiting for server to
> start`, `Warning: could not connect to a running Ollama instance`, or a `bind: An attempt
> was made to access a socket in a way forbidden by its access permissions` error — go to
> [`docs/07-ollama-windows-troubleshooting.md`](docs/07-ollama-windows-troubleshooting.md).
> Short version: check for an already-running Ollama process, check if port 11434 is already
> in use or excluded by Windows, and only fall back to a different port (via `OLLAMA_HOST`,
> set identically on both the server and every client terminal) once you've confirmed the
> default one is genuinely unavailable — don't make a non-default port the default for every
> PC.

Full detail: [`docs/02-offline-installation.md`](docs/02-offline-installation.md) Step 2.

---

# Step 3: Pull the Base Model

**RUN IN:** Windows PowerShell — Normal User

Check what you already have before pulling anything:
```powershell
ollama list
```
Pick the tier that matches your RAM (full table in `docs/01-architecture.md` §3) and pull it:

| RAM | Command |
|---|---|
| 8 GB | `ollama pull qwen2.5-coder:1.5b` |
| 16 GB (recommended) | `ollama pull qwen2.5-coder:7b` |
| 32 GB+ / GPU ≥10 GB VRAM | `ollama pull qwen2.5-coder:14b` |

This is the only large download in the whole setup (~4.7 GB for the 7B tier) and needs the
server from Step 2 reachable first. Once it finishes, the model lives on local disk —
`ollama run qwen2.5-coder:7b` works with the network off.

Full detail: [`docs/02-offline-installation.md`](docs/02-offline-installation.md) Step 3.

---

# Step 4: Clone Claude-Red and This Kit

**RUN IN:** Windows PowerShell — Normal User

```powershell
git clone https://github.com/SnailSploit/claude-red claude-red-skills
```

This is a folder of Markdown `SKILL.md` files once cloned — nothing in it executes, and
nothing in it calls any API. We read it as plain text.

If you're not already inside this kit's repository:
```powershell
git clone https://github.com/HayzeuMagic/claude-red-labs.git
cd claude-red-labs
```

Your two clones must sit next to each other (Step 5 uses a relative path that depends on it):
```
C:\Users\<you>\claude-red-skills\     <- Step 4's first clone
C:\Users\<you>\claude-red-labs\       <- this kit (you are here)
```

Full detail: [`docs/02-offline-installation.md`](docs/02-offline-installation.md) Step 4.

---

# Step 5: Build the Skill-Loaded Models

**RUN IN:** Windows PowerShell — Normal User
**Directory:** inside `claude-red-labs`

```powershell
python tools\skill_loader.py --skill ..\claude-red-skills\Skills\web\offensive-idor\SKILL.md --name redlab-idor --base qwen2.5-coder:7b
```
```powershell
python tools\skill_loader.py --skill ..\claude-red-skills\Skills\web\offensive-sqli\SKILL.md --name redlab-sqli --base qwen2.5-coder:7b
```
```powershell
python tools\skill_loader.py --skill ..\claude-red-skills\Skills\utility\offensive-fast-checking\SKILL.md --skill ..\claude-red-skills\Skills\utility\offensive-reporting\SKILL.md --name redlab-webtriage --base qwen2.5-coder:7b
```
```powershell
python tools\skill_loader.py --baseline --name redlab-baseline --base qwen2.5-coder:7b
```

Each command prints `Wrote Modelfile ...` and then runs `ollama create`, which is local and
offline — it repackages the already-pulled base model with a new system prompt (plain
prompting, not fine-tuning or retraining). No new download happens.

**Check:**
```powershell
ollama list
```
You should see `redlab-idor`, `redlab-sqli`, `redlab-webtriage`, `redlab-baseline`, and your
base model tag.

> **Note:** `--base` must match whatever tag you pulled in Step 3. If you pulled the 1.5B
> tier, pass `--base qwen2.5-coder:1.5b` on every line above instead.

> **If `ollama create` fails with `Error: timed out waiting for server to start`:** the
> Modelfile was still written correctly — the failure is purely the server-connectivity
> problem from Step 2. See
> [`docs/07-ollama-windows-troubleshooting.md`](docs/07-ollama-windows-troubleshooting.md)
> Step 9 to fix it and rerun just the `ollama create` line without rerunning the whole script.

Full detail: [`docs/02-offline-installation.md`](docs/02-offline-installation.md) Step 5.

---

# Step 6: Maintaining and Removing Custom Models

**RUN IN:** Windows PowerShell — Normal User

```powershell
ollama show redlab-idor --modelfile   # inspect what a model was actually built from
ollama rm redlab-baseline              # remove a model you no longer need
```
To update a model after a skill file changes, just rerun its `skill_loader.py` command from
Step 5 with the same `--name` — that overwrites it in place.

Full detail: [`docs/02-offline-installation.md`](docs/02-offline-installation.md) Step 6.

---

# Step 7: Pull the Lab 1 Target Image

**RUN IN:** Windows PowerShell — Normal User
**Directory:** the `claude-red-labs` root (where `docker-compose.yml` lives)

```powershell
docker compose pull
```

This is the last step that needs the internet. Everything from here on works offline.

Full detail: [`docs/02-offline-installation.md`](docs/02-offline-installation.md) Step 7.

---

# Step 8: Set Up the Lab 2 App

**RUN IN:** Windows PowerShell — Normal User

```powershell
cd lab2\vuln_app
python -m venv .venv
```
Activate it — **this command differs by shell, these are not interchangeable:**
- **PowerShell:** `.venv\Scripts\Activate.ps1` (the bare `.venv\Scripts\activate`, with no
  extension, silently does nothing in PowerShell — confirmed while writing this guide)
- **Command Prompt (CMD):** `.venv\Scripts\activate.bat`
- **macOS/Linux:** `source .venv/bin/activate`

```powershell
pip install -r requirements.txt
pip install pytest
cd ..\..
```

Full detail: [`docs/02-offline-installation.md`](docs/02-offline-installation.md) Step 8.

---

# Step 9: (Optional) Install OWASP ZAP

Download the installer for your OS from https://www.zaproxy.org/download/ and run it once,
online. ZAP works fully offline afterward — only its add-on marketplace needs internet, and
neither lab requires an add-on. Burp Suite Community Edition is an equally valid free
substitute if your lab room already standardizes on it.

Full detail: [`docs/02-offline-installation.md`](docs/02-offline-installation.md) Step 9.

---

# Step 10: Verify Everything Works Offline

**Disconnect the network** and run through `docs/06-offline-readiness-checklist.md` in full.
This is not optional for a lab you intend to run without internet in the room — catch a step
that silently needed the network now, not mid-class.

---

# Running the Labs

| Lab | Manual | Target |
|---|---|---|
| Lab 1 — Web vulnerability assessment | [`docs/03-lab1-web-vuln-assessment.md`](docs/03-lab1-web-vuln-assessment.md) | OWASP Juice Shop (`127.0.0.1:3000`) |
| Lab 2 — Vulnerability analysis & remediation | [`docs/04-lab2-vuln-remediation.md`](docs/04-lab2-vuln-remediation.md) | `lab2/vuln_app/app.py` (`127.0.0.1:5000`) |

Each manual is self-contained: learning objectives, prerequisites, the exact Claude-Red
skill used, copy-paste student prompts, a step-by-step procedure, troubleshooting, student
deliverables, and a grading rubric.

Optional, run after either lab: [`docs/05-comparison-exercise.md`](docs/05-comparison-exercise.md)
— the same question asked of the skill-loaded model vs. a bare baseline model, so students
see concretely what the skill content changes.

For the reasoning behind this design (why prompt-loading and not fine-tuning, what would be
needed for the AI to run tools itself, hardware tiers) see
[`docs/01-architecture.md`](docs/01-architecture.md).

---

## Scope and Safety

- Every target in these labs is deployed **by the instructor, inside the lab environment**
  (a local Juice Shop container, a local Flask app). Students must not point any tool,
  payload, or AI-suggested technique at a system they do not own or have not been explicitly
  authorized to test.
- The local model is an **advisor, not an operator**. Nothing in this kit lets the model
  execute a command, send a request, or touch the target on its own — it only ever talks to
  the student, in text. The student decides what to run, and runs it themselves.
- This kit reuses the public [Claude-Red](https://github.com/SnailSploit/claude-red) skill
  library (MIT-licensed `SKILL.md` files) purely as **prompt text**. No Claude-Red code
  executes, and no part of this kit uses a Claude subscription or API.
