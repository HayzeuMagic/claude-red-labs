# Fresh PC Setup (Windows) — Start Here if Nothing Is Installed Yet

Use this doc if you're setting this kit up on a Windows machine that has **none** of the
required software yet — no Git, no Python, no Docker Desktop, no Ollama, neither repository
cloned. If this machine already has everything built (models created, image pulled, Lab 2
venv installed) and you just want to run a lab session, stop here and go to
[`09-quickstart-already-built.md`](09-quickstart-already-built.md) instead — redoing this
whole doc on a machine that's already set up wastes a lot of time and bandwidth for nothing.

This is the condensed, in-order checklist. Each step points to the matching step in
[`02-offline-installation.md`](02-offline-installation.md) for the full explanation,
troubleshooting, and "what verified output actually looks like" detail — read this doc to
know *what* to run, that one when something doesn't behave as expected.

> **Needs internet access throughout.** Nothing here needs Administrator rights except
> Docker Desktop's own installer (Windows prompts for that automatically). Budget 30–60
> minutes, most of it waiting on the base-model download (~4.7 GB for the recommended tier).

---

## Step 1 — Check what's already there

**RUN IN:** Windows PowerShell — Normal User · **Directory:** any

```powershell
git --version
python --version
docker --version
ollama --version
```
Anything that errors with "is not recognized" is missing — install it (next four steps cover
each). Anything that prints a version is already there; skip its install step.

Full detail: `02-offline-installation.md` Step 1.

## Step 2 — Install what's missing

- **Git** (if missing): https://git-scm.com/downloads — accept defaults.
- **Python 3.9+** (if missing, or `python --version` shows < 3.9): https://www.python.org/downloads/
  — check **"Add python.exe to PATH"** during install. (Python 3.14 is confirmed to work with
  this kit's dependencies; you don't need an older release.)
- **Docker Desktop** (if missing — needed for Lab 1 only): https://www.docker.com/products/docker-desktop/
  — its installer needs Administrator (Windows prompts automatically); open it once from the
  Start menu afterward and leave it running.
- **Ollama** (if missing):
  ```powershell
  irm https://ollama.com/install.ps1 | iex
  ```
  (per-user install, no Administrator needed)

**Close and reopen your terminal after any install** — PATH changes only apply to new
terminal windows.

Full detail: `02-offline-installation.md` Step 1 (Docker/Python caveats) and Step 2.1–2.2.

## Step 3 — Confirm Ollama's server actually answers

**RUN IN:** Windows PowerShell — Normal User

```powershell
Get-Process | Where-Object { $_.Name -like "*ollama*" }
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```
Expected: a process is listed, and the second command returns JSON with a `models` key
(empty list is fine the first time).

**If either fails** — including `Error: timed out waiting for server to start`,
`Warning: could not connect to a running Ollama instance`, or a `bind: ... forbidden by its
access permissions` error — stop and work through
[`07-ollama-windows-troubleshooting.md`](07-ollama-windows-troubleshooting.md) before
continuing. Only fall back to a non-default port if that doc's checks actually prove 11434 is
blocked on *this* machine — don't assume it is just because another machine needed that.

Full detail: `02-offline-installation.md` Step 2.3–2.4.

## Step 4 — Pull the base model

**RUN IN:** Windows PowerShell — Normal User

Pick the tier for this machine's RAM (check with
`Get-CimInstance Win32_OperatingSystem | Select-Object @{n='GB';e={[math]::Round($_.TotalVisibleMemorySize/1MB,1)}}`):

| RAM | Command |
|---|---|
| 8 GB | `ollama pull qwen2.5-coder:1.5b` |
| 16 GB (recommended) | `ollama pull qwen2.5-coder:7b` |
| 32 GB+ / GPU ≥10 GB VRAM | `ollama pull qwen2.5-coder:14b` |

Then verify it actually works, not just that it downloaded:
```powershell
ollama run qwen2.5-coder:7b "say hi in exactly 3 words"
```
A real reply means this step is genuinely done — the model is now on local disk for good.

Full detail: `02-offline-installation.md` Step 3.

## Step 5 — Clone both repositories as sibling folders

**RUN IN:** Windows PowerShell — Normal User · **Directory:** wherever both clones should
live, e.g. `C:\Users\<you>\`

```powershell
git clone https://github.com/SnailSploit/claude-red claude-red-skills
git clone https://github.com/HayzeuMagic/claude-red-labs.git
cd claude-red-labs
```

Verify all four skill files this kit needs are actually present:
```powershell
Test-Path ..\claude-red-skills\Skills\web\offensive-idor\SKILL.md
Test-Path ..\claude-red-skills\Skills\web\offensive-sqli\SKILL.md
Test-Path ..\claude-red-skills\Skills\utility\offensive-fast-checking\SKILL.md
Test-Path ..\claude-red-skills\Skills\utility\offensive-reporting\SKILL.md
```
All four should print `True`. **If one prints `False` right after a successful clone**, don't
assume the clone failed — on at least one machine, Windows Defender quarantined and deleted
`offensive-sqli\SKILL.md` minutes later as a heuristic match on an example payload in the
text. Check for that specifically before re-cloning — see `02-offline-installation.md`
Step 4.1 for the exact commands and why this doc does not restore a quarantined file for you
automatically (it's a security-policy decision for whoever owns that machine, not a routine
step). If it stays missing, treat `redlab-sqli` (and Lab 2's AI-assisted step) as blocked and
continue — nothing else here depends on that one file.

Full detail: `02-offline-installation.md` Step 4.

## Step 6 — Build the four custom models

**RUN IN:** Windows PowerShell — Normal User · **Directory:** `claude-red-labs` root

Run each line separately, one at a time (replace `qwen2.5-coder:7b` everywhere if you picked
a different tier in Step 4):

```powershell
python tools\skill_loader.py --skill ..\claude-red-skills\Skills\web\offensive-idor\SKILL.md --name redlab-idor --base qwen2.5-coder:7b
```
```powershell
python tools\skill_loader.py --skill ..\claude-red-skills\Skills\web\offensive-sqli\SKILL.md --name redlab-sqli --base qwen2.5-coder:7b
```
(skip this one if Step 5's troubleshooting applies and the file is still missing)
```powershell
python tools\skill_loader.py --skill ..\claude-red-skills\Skills\utility\offensive-fast-checking\SKILL.md --skill ..\claude-red-skills\Skills\utility\offensive-reporting\SKILL.md --name redlab-webtriage --base qwen2.5-coder:7b
```
```powershell
python tools\skill_loader.py --baseline --name redlab-baseline --base qwen2.5-coder:7b
```

Verify — do both, not just the first:
```powershell
ollama list
ollama run redlab-idor "what's an IDOR in one sentence?"
```
A model only showing up in `ollama list` is not proof it works; the second command getting a
real, on-topic answer is.

Full detail: `02-offline-installation.md` Step 5.

## Step 7 — Pull the Lab 1 target image

**RUN IN:** Windows PowerShell — Normal User · **Directory:** `claude-red-labs` root

```powershell
docker compose pull
docker compose up -d
docker compose ps
```
Expected: a row for `redlab-juiceshop` showing `127.0.0.1:3000->3000/tcp` (not `0.0.0.0`) and
`STATUS` starting with `Up`. Confirm it actually answers:
```powershell
Invoke-WebRequest http://127.0.0.1:3000 -UseBasicParsing
```
Expected: `StatusCode 200`. You can leave it running or stop it with `docker compose down`.

Full detail: `02-offline-installation.md` Step 7.

## Step 8 — Set up the Lab 2 app

**RUN IN:** Windows PowerShell — Normal User · **Directory:** `claude-red-labs` root

```powershell
cd lab2\vuln_app
python -m venv .venv
.venv\Scripts\Activate.ps1
```
(CMD users: `.venv\Scripts\activate.bat` instead — the two are not interchangeable, and the
extension-less `.venv\Scripts\activate` silently does nothing in PowerShell.) If PowerShell
blocks activation with an execution-policy error, run
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` once for the current window
(not system-wide) and retry.

```powershell
pip install -r requirements.txt
pip install pytest
```

Verify:
```powershell
python app.py
```
Expected: `* Running on http://127.0.0.1:5000`. In a second terminal:
`Invoke-WebRequest http://127.0.0.1:5000/ -UseBasicParsing` should return `200`. Stop with
`Ctrl+C`, then:
```powershell
cd ..\..
pytest lab2\tests\test_security_regression.py -v
```
Expected: `5 passed`.

Full detail: `02-offline-installation.md` Step 8.

## Step 9 — (Optional) Install OWASP ZAP

Only if your lab plans to use a proxy. https://www.zaproxy.org/download/, run once online,
decline the add-on update check if testing offline readiness. Burp Suite Community Edition is
an equally valid substitute. Neither lab strictly requires it.

Full detail: `02-offline-installation.md` Step 9.

## Step 10 — Verify everything works with the network off

Disconnect the network, then run every item in
[`06-offline-readiness-checklist.md`](06-offline-readiness-checklist.md). Don't skip this
before a real class session — it's far easier to catch a step that quietly needed the
network now than mid-class with twenty students stuck at once.

Full detail: `02-offline-installation.md` Step 10.

---

**Once every step above is done:** switch to
[`09-quickstart-already-built.md`](09-quickstart-already-built.md) for every future session on
this machine — you never need to redo Steps 1–9 again unless something is removed or a
skill file changes.
