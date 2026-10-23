# Offline Installation Guide (Windows)

This is the detailed version of the README's setup steps, written for a Windows user who
has never run any of this before. Every command below states exactly which terminal to open,
whether it needs Administrator rights, the exact directory to run it in, the exact command,
and what success looks like. Follow it top to bottom, once per lab machine, **with internet
access**. Do this before lab day, not during it.

> **Note:** nothing in this guide requires a Claude account, an Ollama account, or any paid
> service. The only things that need internet access are listed in each step below — every
> one is a one-time download.

> **Note — two different environments:** this guide applies to any Windows PC. One specific
> development PC used while building this kit has Hyper-V installed and in use; the target
> deployment PCs this kit is meant for do **not** have Hyper-V, and nothing in this guide
> needs it. Where a step's behavior was actually observed to differ because of that, it's
> called out explicitly. See `docs/01-architecture.md` §3 for the full explanation, and
> `docs/07-ollama-windows-troubleshooting.md` if Ollama won't start.

---

# Step 1: Confirm Prerequisites Are Installed

### 1.1 Git

**RUN IN:** Windows PowerShell — Normal User
**Directory:** any

```powershell
git --version
```
Expected output: `git version 2.x.x` (any recent version works). If this fails (`git` is not
recognized), install from https://git-scm.com/downloads, then open a **new** terminal window
and try again — the installer updates PATH, but only for terminals opened afterward.

### 1.2 Python 3.9+

**RUN IN:** Windows PowerShell — Normal User

```powershell
python --version
```
Expected output: `Python 3.9.x` or newer. If this fails, or prints something unexpected (some
Windows installs alias a bare `python` to the Microsoft Store listing instead of a real
interpreter), check which `python.exe` actually runs:
```powershell
Get-Command python
```
If more than one Python install is present on the PC, confirm which one is first on PATH —
that's the one every `python` command in this guide will use.

Install from https://www.python.org/downloads/ if needed. On Windows, make sure **"Add
python.exe to PATH"** is checked during install, then open a new terminal.

### 1.3 Docker (needed for Lab 1 only — Lab 2 and the model/skill workflow don't use it)

**RUN IN:** Windows PowerShell — Normal User

```powershell
docker --version
```
Expected output: `Docker version 2x.x.x, build xxxxxxx`. If this fails, install Docker
Desktop from https://www.docker.com/products/docker-desktop/ (the installer itself needs an
elevated/Administrator prompt, which Windows will ask for automatically), then **start
Docker Desktop at least once** before continuing — `docker` commands only work while the
Docker Desktop background service is running.

> **Note:** Docker Desktop needs its own backend (WSL2 or Hyper-V, chosen in Docker Desktop's
> own settings) — this is separate from whether Ollama needs Hyper-V (it doesn't). If Docker
> Desktop's installer asks to enable WSL2 or a virtualization feature, that's Docker's
> requirement, not something this kit's use of Ollama needs. See `01-architecture.md` §3.

---

# Step 2: Install Ollama

### 2.1 Run the installer

**RUN IN:** Windows PowerShell — Normal User (this is a per-user install; it does not need
Administrator rights — confirmed by its install location landing under the current user's
own `AppData`, not a system-wide `Program Files` path)
**Directory:** any

```powershell
irm https://ollama.com/install.ps1 | iex
```
If your network blocks piping a script directly, download `OllamaSetup.exe` manually from
https://ollama.com/download and run it instead — same result.

### 2.2 Verify the CLI installed

**RUN IN:** Windows PowerShell — Normal User

```powershell
ollama --version
```
Expected output: `ollama version 0.x.x` (this guide was validated against `0.40.9`).

> **Note:** Ollama does not ask you to sign in or create an account to run a local model.
> You'll only see an account prompt if you try to use one of Ollama's `:cloud` model tags —
> this kit never does that.

> **Note:** target deployment PCs do not have Hyper-V installed or enabled, and don't need
> it. Ollama runs as a native Windows background process, not inside a VM — nothing in this
> step or the ones that follow assumes or depends on Hyper-V. See `01-architecture.md` §3 for
> the full virtualization note, including what *was* observed on a PC that does have Hyper-V.

### 2.3 Confirm the server is actually running

**RUN IN:** Windows PowerShell — Normal User

```powershell
Get-Process | Where-Object { $_.Name -like "*ollama*" }
```
Expected: at least one process listed (the installer starts Ollama's background app
automatically; you normally don't need to run `ollama serve` yourself). **Do not check with
just `Get-Process ollama` (no wildcard)** — on at least one Windows install, the running
process is literally named `ollama app` (with a space), which that exact match misses even
while it's running.

### 2.4 Verify the local API answers

**RUN IN:** Windows PowerShell — Normal User

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```
Expected: a JSON response with a `models` key (an empty list is fine — you haven't pulled one
yet). If 2.3 or 2.4 doesn't come back clean — including the errors `Error: timed out waiting
for server to start`, `Warning: could not connect to a running Ollama instance`, or `listen
tcp 127.0.0.1:11434: bind: An attempt was made to access a socket in a way forbidden by its
access permissions` — **stop here** and work through
[`07-ollama-windows-troubleshooting.md`](07-ollama-windows-troubleshooting.md) before
continuing to Step 3. That doc also covers the case where a custom port ends up configured
for one side (client or server) but not the other.

---

# Step 3: Pull the Base Model

### 3.1 Choose your tier

| Student machine RAM | Tag to pull | Approximate download |
|---|---|---|
| 8 GB (CPU-only, slower) | `qwen2.5-coder:1.5b` | ~1.0 GB |
| 16 GB (recommended default) | `qwen2.5-coder:7b` | ~4.7 GB |
| 32 GB+, or GPU with ≥10 GB VRAM | `qwen2.5-coder:14b` | ~9.0 GB |

See `docs/01-architecture.md` §3 for why this model was chosen and what the tiers trade off.
The rest of this guide uses `qwen2.5-coder:7b` — substitute your chosen tag everywhere if you
picked a different tier.

### 3.2 Check whether it's already pulled

**RUN IN:** Windows PowerShell — Normal User

```powershell
ollama list
```
Look for `qwen2.5-coder:7b` in the output. If it's already there, skip to 3.3 — there's no
need to re-pull a model you already have; `ollama pull` on a model you already have just
re-checks the manifest and exits quickly, but there's no reason to wait on that if `ollama
list` already answered the question.

### 3.3 Pull it

**RUN IN:** Windows PowerShell — Normal User

```powershell
ollama pull qwen2.5-coder:7b
```
Requires the server from Step 2 to be reachable — if this hangs or errors immediately, go
back to Step 2.4. Expected output ends with:
```
success
```
This is the single biggest download in the whole setup. Do it on a wired connection or good
Wi-Fi if you can — a 4.7 GB pull over a bad connection is the single most likely place for
setup day to go wrong.

### 3.4 Verify it runs

**RUN IN:** Windows PowerShell — Normal User

```powershell
ollama run qwen2.5-coder:7b "say hi in exactly 3 words"
```
Expected: a short reply from the model, printed to your terminal. If this works, you will
never need the network for this model again.

---

# Step 4: Clone Claude-Red and This Kit

### 4.1 Clone the skill library

**RUN IN:** Windows PowerShell — Normal User
**Directory:** wherever you want both clones to live, e.g. `C:\Users\<you>\`

```powershell
git clone https://github.com/SnailSploit/claude-red claude-red-skills
```
Expected output ends with `Receiving objects: 100% ...`. Confirm it worked:
```powershell
Get-ChildItem claude-red-skills\Skills
```
You should see category folders (`web`, `auth`, `wireless`, `utility`, ...).

> **Note — antivirus can delete a skill file after the clone succeeds:** confirmed on the dev
> PC on 2026-10-23, Windows Defender quarantined and deleted
> `Skills\web\offensive-sqli\SKILL.md` **after** the clone finished successfully — Defender's
> real-time scanner flagged it as `Backdoor:PHP/Perhetshell.A!dha` (a heuristic match, almost
> certainly triggered by an example payload snippet inside that methodology document, not an
> actual backdoor) the next time something read the file. `git clone` reporting success and
> `Get-ChildItem` immediately afterward showing the file do **not** guarantee the file is still
> there a few minutes later. If a `SKILL.md` your lab needs goes missing after a clean clone,
> check for exactly this before assuming the clone itself failed:
> ```powershell
> git -C claude-red-skills status --short
> Get-MpThreatDetection | Select-Object ThreatID, Resources, InitialDetectionTime
> ```
> A local-only deletion (`git status` shows ` D <path>` against a clean upstream clone) plus a
> matching entry in `Get-MpThreatDetection` confirms Defender, not a bad clone. **This is a
> security-policy decision, not a bug to route around automatically** — restoring the file from
> quarantine (`MpCmdRun.exe -Restore`) or adding a Defender exclusion for the repo both override
> an antivirus threat verdict and need a deliberate, informed choice (and Administrator rights)
> by whoever owns that decision for the machine; this guide does not do either for you. If the
> file stays deleted, treat the model(s) that depend on it as **blocked** and continue with the
> rest of the kit — `redlab-sqli` (Lab 2) is the only model this currently affects; `offensive-idor`,
> `offensive-fast-checking`, and `offensive-reporting` were not flagged.

### 4.2 Clone (or confirm you already have) this kit

**RUN IN:** Windows PowerShell — Normal User
**Directory:** the same parent folder as 4.1

```powershell
git clone https://github.com/HayzeuMagic/claude-red-labs.git
cd claude-red-labs
```

> **Important:** the commands in Step 5 use a relative path
> (`..\claude-red-skills\...`) and assume `claude-red-skills` and `claude-red-labs` are
> **sibling folders** (same parent directory). Confirmed working layout:
> ```
> C:\Users\<you>\claude-red-skills\     <- Step 4.1's clone
> C:\Users\<you>\claude-red-labs\       <- this kit (you'll be inside it from here on)
> ```
> If you put them somewhere else, adjust the `--skill` paths in Step 5 to match. **Do not
> assume `..\claude-red-skills` exists relative to every possible working directory** — it
> only resolves correctly from directly inside `claude-red-labs`.

---

# Step 5: Build the Skill-Loaded Models

**Directory for every command in this step:** the `claude-red-labs` root (where you ended up
after Step 4.2's `cd`).

### 5.1 What you're about to run, and why

`tools\skill_loader.py` reads one or more Claude-Red `SKILL.md` files, strips the parts that
only make sense inside Claude's own product, and writes an Ollama **Modelfile** — a plain
text file with a `FROM <base model>` line and a `SYSTEM "..."` block containing the skill
text. It then runs `ollama create <name> -f Modelfile` for you. Its arguments:

| Flag | Meaning |
|---|---|
| `--skill <path>` | Path to one `SKILL.md` file. Repeatable — pass it more than once to combine skills into one model. |
| `--name <name>` | What to call the resulting Ollama model, e.g. `redlab-idor`. Required. |
| `--base <tag>` | Which already-pulled Ollama model to build on. Defaults to `qwen2.5-coder:7b`. |
| `--baseline` | Build a model with no skill content at all (used for the comparison exercise in `05-comparison-exercise.md`). |
| `--out <path>` | Where to write the generated Modelfile. Defaults to `.\Modelfile` in the current directory. |
| `--no-create` | Write the Modelfile but skip calling `ollama create` (useful for inspecting it first). |

This does not fine-tune or retrain anything — the base model's weights are untouched. It's
plain prompt engineering: the skill text becomes the model's system prompt. See
`01-architecture.md` §1 for the longer explanation of why that's the right layer here.

### 5.2 Confirm the skill file actually exists before running anything

**RUN IN:** Windows PowerShell — Normal User
**Directory:** `claude-red-labs` root

```powershell
Test-Path ..\claude-red-skills\Skills\web\offensive-idor\SKILL.md
```
Expected: `True`. If this prints `False`, fix the path before continuing — Step 5.3 will
simply report `error: skill file not found: <path>` and exit without creating anything if
the path is wrong, so check this first rather than guessing from that message alone.

### 5.3 Build a model from one skill

**RUN IN:** Windows PowerShell — Normal User
**Directory:** `claude-red-labs` root

```powershell
python tools\skill_loader.py --skill ..\claude-red-skills\Skills\web\offensive-idor\SKILL.md --name redlab-idor --base qwen2.5-coder:7b
```
(One line — PowerShell does not use the `\` line-continuation character the way a Bash
example might; if you need to split a long PowerShell command across lines, use a trailing
backtick `` ` `` at the end of each line instead, or just keep it on one line as shown here.)

Expected output:
```
Wrote Modelfile (XXXXX bytes, base=qwen2.5-coder:7b)
Running: ollama create redlab-idor -f Modelfile
...
success
Done. Try it with:
    ollama run redlab-idor
```

**If this instead ends with `Error: timed out waiting for server to start`:** the Modelfile
was still written correctly (check with `Get-Content .\Modelfile -TotalCount 5` — it should
start with `FROM qwen2.5-coder:7b`); the failure is purely at the `ollama create` step
because the server isn't reachable. This does **not** mean the script is broken. Go to
[`07-ollama-windows-troubleshooting.md`](07-ollama-windows-troubleshooting.md) Step 9, fix
the server, then rerun just the `ollama create` line shown there instead of the whole script.

### 5.4 Build the rest

**RUN IN:** Windows PowerShell — Normal User
**Directory:** `claude-red-labs` root

```powershell
python tools\skill_loader.py --skill ..\claude-red-skills\Skills\web\offensive-sqli\SKILL.md --name redlab-sqli --base qwen2.5-coder:7b
```
```powershell
python tools\skill_loader.py --skill ..\claude-red-skills\Skills\utility\offensive-fast-checking\SKILL.md --skill ..\claude-red-skills\Skills\utility\offensive-reporting\SKILL.md --name redlab-webtriage --base qwen2.5-coder:7b
```
```powershell
python tools\skill_loader.py --baseline --name redlab-baseline --base qwen2.5-coder:7b
```

> **Note:** each of these is a separate custom model, not one model loaded with every skill
> at once. This kit does not combine all skills into a single model — each lab names exactly
> which model(s) it uses, and `redlab-webtriage` combining two *utility* skills (triage +
> reporting) is the one deliberate exception, not the general pattern.

> **Note:** `--base` must match whatever tag you pulled in Step 3. If you pulled the 1.5B
> tier, pass `--base qwen2.5-coder:1.5b` on every line above instead.

### 5.5 Verify all four models exist

**RUN IN:** Windows PowerShell — Normal User

```powershell
ollama list
```
Expected to see, among others:
```
NAME                  ID              SIZE      MODIFIED
redlab-idor:latest    ...             4.7 GB    ...
redlab-sqli:latest    ...             4.7 GB    ...
redlab-webtriage:latest ...           4.7 GB    ...
redlab-baseline:latest ...            4.7 GB    ...
qwen2.5-coder:7b      ...             4.7 GB    ...
```
(Sizes match the base model, since a skill-loaded model only adds a small text layer, not new
weights — this was confirmed while writing this guide.)

### 5.6 Sanity-check one of them

**RUN IN:** Windows PowerShell — Normal User

```powershell
ollama run redlab-idor "what's an IDOR in one sentence?"
```
Expected: a relevant, on-topic answer about Insecure Direct Object References (verified while
writing this guide — the response correctly described IDOR as an authorization failure
where an app doesn't check that a requested resource belongs to the requesting user).

> **Authorized-use reminder:** `redlab-idor` and `redlab-sqli` discuss web-application attack
> techniques. Use them only against the lab targets this kit deploys for you (`03-lab1-...md`,
> `04-lab2-...md`) or other systems you have explicit written authorization to test — never
> against a third party.

---

# Step 6: Maintaining and Removing Custom Models

You'll come back to this step whenever a skill file changes, or you need to free up disk
space.

### 6.1 Inspect a model's effective system prompt

**RUN IN:** Windows PowerShell — Normal User

```powershell
ollama show redlab-idor --modelfile
```
Prints the full Modelfile Ollama actually built the model from, including the skill text.
Useful for confirming a model was built from the skill you think it was.

### 6.2 Rebuild a model after the skill file or base model changes

Just rerun the same `skill_loader.py` command from Step 5 with the same `--name` — `ollama
create` with an existing name overwrites that model with the new content; it does not leave
a stale duplicate behind.

### 6.3 Remove a model you no longer need

**RUN IN:** Windows PowerShell — Normal User

```powershell
ollama rm redlab-baseline
```
Frees the disk space used by that model's unique layers (shared layers, like the base model
weights other custom models still reference, are kept). Confirm it's gone:
```powershell
ollama list
```

---

# Step 7: Pull the Lab 1 Target Image

### 7.1 Pull

**RUN IN:** Windows PowerShell — Normal User
**Directory:** `claude-red-labs` root, where `docker-compose.yml` lives

```powershell
docker compose pull
```
Expected output ends with the image digest and `Status: Downloaded newer image`.

### 7.2 Confirm it's cached locally

**RUN IN:** Windows PowerShell — Normal User

```powershell
docker images | Select-String "juice-shop"
```
You should see `bkimminich/juice-shop` listed with a size and an image ID. This confirms the
image is on local disk — Step 10 will prove it starts without the network.

---

# Step 8: Set Up the Lab 2 App

### 8.1 Create a virtual environment

**RUN IN:** Windows PowerShell — Normal User
**Directory:** `claude-red-labs` root

```powershell
cd lab2\vuln_app
python -m venv .venv
```

### 8.2 Activate it

**The activation command is different per shell — these are not interchangeable:**

**RUN IN:** Windows PowerShell — Normal User
```powershell
.venv\Scripts\Activate.ps1
```
If this fails with a message about execution policies (it did not on the PC this guide was
written on, where the default policy is `RemoteSigned`, which already permits local scripts
like this one), run this once per terminal session and try again:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
This only loosens the policy for the current PowerShell process, not system-wide.

**RUN IN:** Command Prompt (CMD) — Normal User
```cmd
.venv\Scripts\activate.bat
```

> **Confirmed on this PC:** typing `.venv\Scripts\activate` (no extension) in PowerShell
> silently does nothing and does **not** activate the environment — PowerShell needs the
> explicit `.ps1` file. That bare form only works as written in Command Prompt, where it
> resolves to `activate.bat` automatically.

Either way, your prompt should now be prefixed with `(.venv)`.

### 8.3 Install dependencies

**RUN IN:** the same terminal as 8.2, with `(.venv)` showing in the prompt
**Directory:** `lab2\vuln_app`

```powershell
pip install -r requirements.txt
pip install pytest
```

### 8.4 Confirm it runs

**RUN IN:** same terminal, same directory

```powershell
python app.py
```
Expected output includes:
```
 * Running on http://127.0.0.1:5000
```
Leave it running, open a **second** terminal, and check:

**RUN IN:** Windows PowerShell — Normal User (second terminal)
```powershell
Invoke-RestMethod http://127.0.0.1:5000/
```
or, if you specifically want real curl syntax rather than PowerShell's `Invoke-WebRequest`
alias:
```powershell
curl.exe http://127.0.0.1:5000/
```
Expected: a short text response confirming the app is up. Stop the app in the first terminal
with `Ctrl+C`, then:
```powershell
cd ..\..
```

---

# Step 9: (Optional) Install OWASP ZAP

### 9.1 Download and install

Get the installer for your OS from https://www.zaproxy.org/download/ and run it once, online.
(The installer itself may prompt for Administrator rights; the labs don't require that for
running ZAP afterward.)

### 9.2 Decline the update prompt

The first time ZAP opens, it may offer to check for add-on updates — decline this if you are
testing offline readiness, since the update check needs the network and nothing in either lab
requires an add-on.

> **Note:** Burp Suite Community Edition (https://portswigger.net/burp/communitydownload) is
> an equally valid free substitute for ZAP. Standardize on one per lab room so troubleshooting
> instructions stay consistent across students.

---

# Step 10: Verify Everything Works Offline

Turn off Wi-Fi (or unplug Ethernet), then run through **every item** in
[`docs/06-offline-readiness-checklist.md`](06-offline-readiness-checklist.md).

> **WARNING:** do not skip this step. A setup that "worked" only because it quietly fell back
> to the network is exactly the failure mode that ruins a lab session with the Wi-Fi off — and
> it is far easier to catch now, one machine at a time, than during class with twenty students
> stuck at once.

Once every box on that checklist is checked, re-enable the network and move on to running the
labs: [`03-lab1-web-vuln-assessment.md`](03-lab1-web-vuln-assessment.md) and
[`04-lab2-vuln-remediation.md`](04-lab2-vuln-remediation.md).
