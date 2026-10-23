# Offline Installation Guide

This is the detailed version of the README's Steps 1–9, with the exact command, the exact
expected output, and troubleshooting after each one. Follow it top to bottom, once per lab
machine, with internet access. Do this before lab day, not during it.

> **Note:** nothing in this guide requires a Claude account, an Ollama account, or any paid
> service. The only things you need online access for are listed in each step below; every
> one of them is a one-time download.

---

# Step 1: Confirm Prerequisites Are Installed

### 1.1 Git

```bash
git --version
```
Expected output: `git version 2.x.x` (any recent version works). If this fails, install from
https://git-scm.com/downloads.

### 1.2 Python 3.9+

```bash
python --version
```
Expected output: `Python 3.9.x` or newer. If this fails, install from
https://www.python.org/downloads/. On Windows, make sure "Add python.exe to PATH" is checked
during install.

### 1.3 Docker

```bash
docker --version
```
Expected output: `Docker version 2x.x.x, build xxxxxxx`. If this fails, install Docker
Desktop (Windows/macOS) or Docker Engine (Linux) from
https://www.docker.com/products/docker-desktop/, then **start Docker Desktop at least once**
before continuing — the `docker` command only works while the Docker daemon is running.

---

# Step 2: Install Ollama

### 2.1 Run the installer

**Windows (PowerShell):**
```powershell
irm https://ollama.com/install.ps1 | iex
```
**macOS / Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```
Both commands download and run Ollama's own installer. If your network blocks piping a
script directly, download `OllamaSetup.exe` manually from https://ollama.com/download and
run it instead — same result.

### 2.2 Verify the CLI installed

```bash
ollama --version
```
Expected output: `ollama version 0.x.x`.

> **Note:** Ollama does not ask you to sign in or create an account to run a local model.
> You'll only see an account prompt if you try to use one of Ollama's `:cloud` model tags —
> this kit never does that.

> **Note:** these target PCs do not have Hyper-V installed or enabled, and don't need it.
> Ollama runs as a native Windows background process, not inside a VM — nothing in this step
> or the ones that follow assumes or depends on Hyper-V. See `01-architecture.md` §3 for the
> full virtualization note.

### 2.3 Confirm the server is running

```powershell
Get-Process ollama -ErrorAction SilentlyContinue
```
Expected: a process is listed. The installer starts the Ollama background server
automatically; you normally don't need to run `ollama serve` yourself.

### 2.4 Verify the local API answers

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```
Expected: a JSON response (a `models` list — empty until Step 3 pulls one). If 2.3 or 2.4
doesn't come back clean — including the error `Error: timed out waiting for server to start`
or `listen tcp 127.0.0.1:11434: bind: An attempt was made to access a socket in a way
forbidden by its access permissions` — stop here and work through
[`07-ollama-windows-troubleshooting.md`](07-ollama-windows-troubleshooting.md) before
continuing to Step 3.

---

# Step 3: Pull a Local Model

### 3.1 Choose your tier

| Student machine RAM | Tag to pull | Approximate download |
|---|---|---|
| 8 GB (CPU-only, slower) | `qwen2.5-coder:1.5b` | ~1.0 GB |
| 16 GB (recommended default) | `qwen2.5-coder:7b` | ~4.7 GB |
| 32 GB+, or GPU with ≥10 GB VRAM | `qwen2.5-coder:14b` | ~9.0 GB |

See `docs/01-architecture.md` §3 for why this model was chosen and what the tiers trade off.

### 3.2 Pull it

```bash
ollama pull qwen2.5-coder:7b
```
Expected output ends with:
```
success
```
This is the single biggest download in the whole setup. Do it on a wired connection or good
Wi-Fi if you can — a 4.7 GB pull over a bad connection is the single most likely place for
setup day to go wrong.

### 3.3 Verify it runs

```bash
ollama run qwen2.5-coder:7b "say hi in exactly 3 words"
```
Expected: a short reply from the model, printed to your terminal. If this works, you will
never need the network for this model again.

---

# Step 4: Clone Claude-Red and This Kit

### 4.1 Clone the skill library

```bash
git clone https://github.com/SnailSploit/claude-red claude-red-skills
```
Expected output ends with `Receiving objects: 100% ...`. Confirm it worked:
```bash
ls claude-red-skills/Skills
```
You should see category folders (`web`, `auth`, `wireless`, `utility`, ...).

### 4.2 Clone (or confirm you already have) this kit

```bash
git clone https://github.com/HayzeuMagic/claude-red-labs.git
cd claude-red-labs
```

> **Important:** the commands in Step 5 assume `claude-red-skills` and `claude-red-labs`
> are **sibling folders** (same parent directory), because they use a relative path
> (`../claude-red-skills/...`). If you put them somewhere else, adjust the `--skill` paths
> accordingly.

---

# Step 5: Build the Skill-Loaded Models

### 5.1 Run `skill_loader.py` for each model you need

```bash
python tools/skill_loader.py \
  --skill ../claude-red-skills/Skills/web/offensive-idor/SKILL.md \
  --name redlab-idor --base qwen2.5-coder:7b
```
Expected output:
```
Wrote Modelfile (XXXXX bytes, base=qwen2.5-coder:7b)
Running: ollama create redlab-idor -f Modelfile
...
Done. Try it with:
    ollama run redlab-idor
```

Repeat for the rest:
```bash
python tools/skill_loader.py --skill ../claude-red-skills/Skills/web/offensive-sqli/SKILL.md --name redlab-sqli --base qwen2.5-coder:7b

python tools/skill_loader.py --skill ../claude-red-skills/Skills/utility/offensive-fast-checking/SKILL.md --skill ../claude-red-skills/Skills/utility/offensive-reporting/SKILL.md --name redlab-webtriage --base qwen2.5-coder:7b

python tools/skill_loader.py --baseline --name redlab-baseline --base qwen2.5-coder:7b
```

### 5.2 Verify all four models exist

```bash
ollama list
```
Expected to see, among others:
```
redlab-idor         ...
redlab-sqli         ...
redlab-webtriage    ...
redlab-baseline     ...
qwen2.5-coder:7b    ...
```

### 5.3 Sanity-check one of them

```bash
ollama run redlab-idor
>>> what's an IDOR in one sentence?
```
If you get a relevant, on-topic answer (not an error), the skill loaded correctly. Type
`/bye` to exit the chat.

---

# Step 6: Pull the Lab 1 Target Image

### 6.1 Pull

From the `claude-red-labs` root, where `docker-compose.yml` lives:
```bash
docker compose pull
```
Expected output ends with the image digest and `Status: Downloaded newer image`.

### 6.2 Confirm it's cached locally

```bash
docker images | grep juice-shop
```
You should see `bkimminich/juice-shop` listed with a size and an image ID. This confirms the
image is on local disk — Step 9 will prove it starts without the network.

---

# Step 7: Set Up the Lab 2 App

### 7.1 Create a virtual environment

```bash
cd lab2/vuln_app
python -m venv .venv
```

### 7.2 Activate it

- **Windows:** `.venv\Scripts\activate`
- **macOS / Linux:** `source .venv/bin/activate`

Your prompt should now be prefixed with `(.venv)`.

### 7.3 Install dependencies

```bash
pip install -r requirements.txt
pip install pytest
```

### 7.4 Confirm it runs

```bash
python app.py
```
Expected output includes:
```
 * Running on http://127.0.0.1:5000
```
Leave it running, open a second terminal, and check:
```bash
curl http://127.0.0.1:5000/
```
Expected: a short text response confirming the app is up. Stop the app with `Ctrl+C`, then:
```bash
cd ../..
```

---

# Step 8: (Optional) Install OWASP ZAP

### 8.1 Download and install

Get the installer for your OS from https://www.zaproxy.org/download/ and run it once, online.

### 8.2 Decline the update prompt

The first time ZAP opens, it may offer to check for add-on updates — decline this if you are
testing offline readiness, since the update check needs the network and nothing in either lab
requires an add-on.

> **Note:** Burp Suite Community Edition (https://portswigger.net/burp/communitydownload) is
> an equally valid free substitute for ZAP. Standardize on one per lab room so troubleshooting
> instructions stay consistent across students.

---

# Step 9: Verify Everything Works Offline

Turn off Wi-Fi (or unplug Ethernet, or use a VM with no network adapter), then run through
**every item** in [`docs/06-offline-readiness-checklist.md`](06-offline-readiness-checklist.md).

> **WARNING:** do not skip this step. A setup that "worked" only because it quietly fell back
> to the network is exactly the failure mode that ruins a lab session with the Wi-Fi off — and
> it is far easier to catch now, one machine at a time, than during class with twenty students
> stuck at once.

Once every box on that checklist is checked, re-enable the network and move on to running the
labs: [`03-lab1-web-vuln-assessment.md`](03-lab1-web-vuln-assessment.md) and
[`04-lab2-vuln-remediation.md`](04-lab2-vuln-remediation.md).
