# Ollama Startup & Port Troubleshooting (Windows)

This doc covers Ollama failing to start or failing to answer on its local API on a Windows
PC. It applies to the deployment environment used for this kit: **Windows, Ollama running
natively, no Hyper-V installed or enabled, no VM involved.**

> **Important:** because these PCs do not have Hyper-V, do not diagnose a port conflict as
> "a Hyper-V virtual switch took the port" — that explanation requires Hyper-V to be present,
> and it isn't. If port 11434 is unavailable, the cause is something else on the machine:
> another process, a security product, or a Windows-level port reservation unrelated to
> Hyper-V. The checks below find the real cause instead of guessing.

## The two errors this doc addresses

1. ```
   Error: timed out waiting for server to start
   ```
   The `ollama` CLI started the background server process and gave up waiting for it to
   report ready. This is almost always a **symptom** of the server failing to bind its port —
   work through the checks below rather than retrying the same command repeatedly.

2. ```
   listen tcp 127.0.0.1:11434: bind: An attempt was made to access a socket in a way
   forbidden by its access permissions.
   ```
   This is Windows socket error WSAEACCES (10013): the process was denied permission to bind
   that address/port. On Windows this typically means one of:
   - the port falls inside a Windows **excluded port range** (Step 3 below), or
   - another process already holds the port exclusively, or
   - a firewall policy or endpoint-security agent is blocking the bind, or
   - (rare) an actual permissions/policy restriction on binding local ports.

   It does **not**, by itself, tell you which of these it is — that's what Steps 1–4 are for.

---

# Step 1: Check Whether Ollama Is Already Running

```powershell
Get-Process ollama -ErrorAction SilentlyContinue
```

If this returns a process, Ollama's server is already running — a second `ollama serve` or a
second launch of the app will conflict with it on the same port. Stop here and just use the
existing instance (skip to Step 6 to verify it answers), or stop it first if you need a clean
restart:
```powershell
Stop-Process -Name ollama -Force
```
Only force-stop it if you intend to restart it — don't do this as a routine "fix" without a
reason.

---

# Step 2: Check Whether Port 11434 Is Already Listening

```powershell
Get-NetTCPConnection -LocalPort 11434 -State Listen -ErrorAction SilentlyContinue
```

If this returns a result, note the owning process ID (`OwningProcess`) and cross-reference it
with `Get-Process -Id <pid>` to see what already holds the port.

> **This check alone does not prove the port is available if it comes back empty.** Windows
> can reserve or exclude a port range from ever being bound by *any* process, even with
> nothing currently listening on it. An empty result here only rules out "something is
> actively listening right now" — it does not rule out "Windows won't let anything bind this
> port." Step 3 checks that separately.

---

# Step 3: Check Windows Excluded Port Ranges

```powershell
netsh interface ipv4 show excludedportrange protocol=tcp
```

Look for 11434 falling inside any listed range. Windows creates these exclusions for its own
dynamic port management and when certain services/features reserve ranges on startup — this
can happen independent of Hyper-V. **Since Hyper-V is not installed on these PCs, do not
assume a Hyper-V virtual switch caused an exclusion you see here** — if 11434 is excluded,
treat it as a Windows-level reservation to investigate (what changed recently: a VPN client,
a container runtime, a network driver update, etc.), not as confirmed evidence of any
specific cause unless you find it.

---

# Step 4: Check Services, Firewall, and Endpoint Security

If Steps 1–3 don't explain the failure:

- **Services:** `Get-Service | Where-Object {$_.Status -eq 'Running'}` — look for anything
  unexpected bound to local networking that started around the same time as the failure.
- **Windows Defender Firewall:** check for an inbound or outbound rule specifically blocking
  port 11434 or the `ollama.exe` process (Windows Security → Firewall & network protection →
  Advanced settings).
- **Endpoint security / antivirus:** some EDR or AV products intercept local socket binds.
  Check its logs for a blocked-connection or blocked-bind event around the failure time.

Report findings to IT if a managed security policy is the actual blocker — **do not disable
Windows Defender Firewall, endpoint security, or any Windows networking service as a routine
fix.** That is a security-policy decision for whoever manages these PCs, not something to
work around unilaterally.

---

# Step 5: Confirm With a Direct Connection Test

```powershell
Test-NetConnection 127.0.0.1 -Port 11434
```
`TcpTestSucceeded : True` means something is listening and reachable on that port right now.
`False` means either nothing is listening, or something is actively refusing the connection —
combine with Steps 1–3 to tell which.

---

# Step 6: Verify the API Once Ollama Is Running

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```
Expected: a JSON object listing your locally pulled models (`qwen2.5-coder:7b`,
`redlab-idor`, etc.) under a `models` key. If this returns data, Ollama's server and API are
both working — the setup is fine on this PC.

If this fails with a connection error, Ollama's server isn't listening on 11434 yet — go back
to Step 1.

---

# Step 7: Only If 11434 Is Genuinely Unavailable — Use an Alternate Port

Do this **only after Steps 1–4 showed the default port is actually blocked**, not as a
default setting applied to every PC. Most machines should keep the default port.

### 7.1 Confirm the alternate port is itself free and not excluded

```powershell
Get-NetTCPConnection -LocalPort 20000 -State Listen -ErrorAction SilentlyContinue
netsh interface ipv4 show excludedportrange protocol=tcp
```
Pick a port that appears in neither check. (20000 is used here as an example, not a mandated
value — any genuinely free, non-excluded port works.)

### 7.2 Set `OLLAMA_HOST` for the current session

The syntax differs between shells — set it in whichever shell you'll launch Ollama from:

**PowerShell:**
```powershell
$env:OLLAMA_HOST = "127.0.0.1:20000"
```

**Command Prompt:**
```cmd
set OLLAMA_HOST=127.0.0.1:20000
```

Both forms are **session-scoped** — they only apply to commands run in that same terminal
window, and are forgotten once it closes. To make the setting persist across reboots/new
terminals, set it as a permanent Windows environment variable instead (System Properties →
Environment Variables → New, under either the user or system section) rather than relying on
students/staff to re-type it every session.

### 7.3 Start Ollama and re-verify

```powershell
ollama serve
```
In a second terminal (with the same `OLLAMA_HOST` set, since the API now listens on the new
port):
```powershell
Invoke-RestMethod http://127.0.0.1:20000/api/tags
ollama pull qwen2.5-coder:7b
ollama run qwen2.5-coder:7b "say hi in exactly 3 words"
```

> **Note:** if a client/script (including this kit's `tools/skill_loader.py`, which shells
> out to `ollama create`) doesn't see `OLLAMA_HOST` set in its environment, it will still try
> the default port. Make sure `OLLAMA_HOST` is set in **every terminal** you use for this kit,
> not just the one that ran `ollama serve`.

---

# Step 8: Re-verify After Any Fix

Whichever of the above resolved it, confirm the full chain works before considering the PC
ready:
```powershell
ollama --version
Get-Process ollama -ErrorAction SilentlyContinue
Invoke-RestMethod http://127.0.0.1:11434/api/tags      # or your alternate port
ollama list
ollama run qwen2.5-coder:7b "say hi in exactly 3 words"
```
If all five succeed, continue with `docs/02-offline-installation.md` from wherever you left
off.

---

## What this doc does not claim

- It does not claim any specific fix above has been tested on your exact PC model — these are
  the standard, documented Windows/Ollama diagnostic steps, applied in the order that finds
  the real cause fastest. Record what Steps 1–4 actually find on a given PC, since that's the
  real diagnosis, not a guess made in advance.
- It does not recommend disabling Windows Defender Firewall, endpoint security, or any
  virtualization-related Windows service as a routine fix, and it does not ask you to remove
  a Windows port exclusion — those are decisions for whoever manages security policy on these
  machines.
- It does not attribute a port conflict to Hyper-V. These PCs don't have it installed, so it
  cannot be the cause — if you find Hyper-V-related evidence anyway (for example, because a
  different team later enables it), that's new information that would need separate
  investigation, not covered by this doc as written.
