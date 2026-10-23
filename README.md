# Offline AI Cybersecurity Labs — Claude-Red + Ollama

A ready-to-run instructor's kit for two hands-on, fully offline, AI-assisted security labs,
built for undergraduate cybersecurity / intro-pentesting students who do not have a paid
Claude account. The AI model runs locally through [Ollama](https://ollama.com), primed with
real [Claude-Red](https://github.com/SnailSploit/claude-red) skill files as plain prompt
content — no subscription, no API key, no cloud inference anywhere in the stack.

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
docs/01-architecture.md                 why this design, hardware tiers, what's in/out of scope
docs/02-offline-installation.md         Step 1-9: one-time setup, done once per machine
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

> **Note:** Steps 1–6 below need internet access once, to download software and models.
> Everything after Step 6 is designed to run with the network **disconnected** — Step 9
> and `docs/06-offline-readiness-checklist.md` exist specifically to prove that.

> **Important:** every target in these labs is a disposable, local-only application
> (`127.0.0.1`). Nothing here is to be pointed at a system you do not own or have not been
> explicitly authorized to test. See **Scope and Safety** at the bottom of this file.

Minimum hardware: 8 GB RAM (CPU-only, slower, uses a smaller model tier). Recommended: 16 GB
RAM. Full tier breakdown, plus CPU/storage/virtualization notes, is in `docs/01-architecture.md` §3.

> **Note:** these PCs do not have Hyper-V installed or enabled. Ollama runs directly on
> Windows, not inside a VM, and nothing in this setup needs Hyper-V. If Ollama fails to start
> on port 11434, see [`docs/07-ollama-windows-troubleshooting.md`](docs/07-ollama-windows-troubleshooting.md)
> — the cause is never Hyper-V on these machines, since it isn't installed.

---

# Step 1: Install Git, Python, and Docker

- **Git** — https://git-scm.com/downloads. Verify with:
  ```bash
  git --version
  ```
- **Python 3.9+** — https://www.python.org/downloads/. Verify with:
  ```bash
  python --version
  ```
- **Docker Desktop** (Windows/macOS) or Docker Engine (Linux) — https://www.docker.com/products/docker-desktop/.
  Verify with:
  ```bash
  docker --version
  ```

---

# Step 2: Install Ollama

**Windows**, in PowerShell:
```powershell
irm https://ollama.com/install.ps1 | iex
```
or download `OllamaSetup.exe` from https://ollama.com/download and run it.

**macOS / Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verify:
```bash
ollama --version
```

Then confirm the server itself is up and answering, not just that the CLI installed:
```powershell
Get-Process ollama -ErrorAction SilentlyContinue
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

> **Note:** no Ollama account is needed for anything in this kit. Accounts only matter for
> Ollama's optional `:cloud` models, which these labs never use.

> **Note:** if either command above fails — including the errors `timed out waiting for
> server to start` or a `bind: An attempt was made to access a socket in a way forbidden by
> its access permissions` — go to
> [`docs/07-ollama-windows-troubleshooting.md`](docs/07-ollama-windows-troubleshooting.md).
> Full step-by-step diagnosis is there; the short version is: check for an already-running
> Ollama process, check if port 11434 is already in use or excluded by Windows, and only fall
> back to a different port (via `OLLAMA_HOST`) once you've confirmed the default one is
> genuinely unavailable — don't make a non-default port the default for every PC.

---

# Step 3: Pull a Local Model

Pick the tier that matches your RAM (full table in `docs/01-architecture.md`):

| RAM | Command |
|---|---|
| 8 GB | `ollama pull qwen2.5-coder:1.5b` |
| 16 GB (recommended) | `ollama pull qwen2.5-coder:7b` |
| 32 GB+ / GPU ≥10 GB VRAM | `ollama pull qwen2.5-coder:14b` |

This is the only large download in the whole setup (~4.7 GB for the 7B tier). Once it
finishes, the model lives on local disk — `ollama run qwen2.5-coder:7b` works with the
network off.

---

# Step 4: Clone Claude-Red and This Kit

```bash
git clone https://github.com/SnailSploit/claude-red claude-red-skills
```

This is a folder of Markdown `SKILL.md` files once cloned — nothing in it executes, and
nothing in it calls any API. We read it as plain text.

If you're not already inside this kit's repository:
```bash
git clone https://github.com/HayzeuMagic/claude-red-labs.git
cd claude-red-labs
```

Your two clones should sit next to each other, e.g.:
```
C:\labs\claude-red-skills\     <- Step 4's first clone
C:\labs\claude-red-labs\       <- this kit (you are here)
```

---

# Step 5: Build the Skill-Loaded Models

From inside `claude-red-labs`:

```bash
python tools/skill_loader.py --skill ../claude-red-skills/Skills/web/offensive-idor/SKILL.md --name redlab-idor --base qwen2.5-coder:7b

python tools/skill_loader.py --skill ../claude-red-skills/Skills/web/offensive-sqli/SKILL.md --name redlab-sqli --base qwen2.5-coder:7b

python tools/skill_loader.py --skill ../claude-red-skills/Skills/utility/offensive-fast-checking/SKILL.md --skill ../claude-red-skills/Skills/utility/offensive-reporting/SKILL.md --name redlab-webtriage --base qwen2.5-coder:7b

python tools/skill_loader.py --baseline --name redlab-baseline --base qwen2.5-coder:7b
```

Each line prints `Wrote Modelfile ...` and then runs `ollama create`, which is local and
offline — it repackages the already-pulled base model with a new system prompt, no new
download happens.

**Check:**
```bash
ollama list
```
You should see `redlab-idor`, `redlab-sqli`, `redlab-webtriage`, `redlab-baseline`, and your
base model tag.

> **Note:** `--base` must match whatever tag you pulled in Step 3. If you pulled the 1.5B
> tier, pass `--base qwen2.5-coder:1.5b` on every line above instead.

---

# Step 6: Pull the Lab 1 Target Image

From the `claude-red-labs` root (where `docker-compose.yml` lives):
```bash
docker compose pull
```

This is the last step that needs the internet. Everything from here on works offline.

---

# Step 7: Set Up the Lab 2 App

```bash
cd lab2/vuln_app
python -m venv .venv
```
Activate it:
- **Windows:** `.venv\Scripts\activate`
- **macOS/Linux:** `source .venv/bin/activate`

```bash
pip install -r requirements.txt
pip install pytest
cd ../..
```

---

# Step 8: (Optional) Install OWASP ZAP

Download the installer for your OS from https://www.zaproxy.org/download/ and run it once,
online. ZAP works fully offline afterward — only its add-on marketplace needs internet, and
neither lab requires an add-on. Burp Suite Community Edition is an equally valid free
substitute if your lab room already standardizes on it.

---

# Step 9: Verify Everything Works Offline

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
