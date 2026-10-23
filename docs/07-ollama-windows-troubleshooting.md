# Ollama Startup & Port Troubleshooting (Windows)

This doc covers Ollama failing to start, or failing to answer on its local API, on a Windows
PC. It applies to **two different environments**, and this doc is explicit about which is
which everywhere it matters:

| | Current development PC | Target deployment PCs |
|---|---|---|
| Hyper-V | **Installed and in use** (`vmms`/`hns` services running, hypervisor active — confirmed below) | **Not installed, not enabled** |
| Ollama runs | Natively on Windows | Natively on Windows |
| Purpose | Building/testing this kit | Running the labs with students |

> **Important:** do not import the dev-PC findings below onto a target PC as if they were a
> guaranteed diagnosis. A target PC without Hyper-V can still hit the same two errors — the
> checks in Steps 1–5 apply to **both** environments and find the real cause either way,
> without assuming Hyper-V is involved.

## The two errors this doc addresses

1. ```
   Error: timed out waiting for server to start
   ```
   The `ollama` CLI started (or tried to start) the background server process and gave up
   waiting for it to report ready. This is almost always a **symptom**, not the root cause —
   work through Steps 1–5 rather than retrying the same command repeatedly.

2. ```
   listen tcp 127.0.0.1:11434: bind: An attempt was made to access a socket in a way
   forbidden by its access permissions.
   ```
   This is Windows socket error WSAEACCES (10013): the process was denied permission to bind
   that address/port. On Windows this typically means one of:
   - the port falls inside a Windows **excluded port range** (Step 3), or
   - another process already holds the port exclusively (Step 2), or
   - a firewall policy or endpoint-security agent is blocking the bind (Step 4), or
   - (rare) an actual permissions/policy restriction on binding local ports.

   It does **not**, by itself, tell you which of these it is — that's what Steps 1–4 are for.

Related, often seen alongside the above:
```
Warning: could not connect to a running Ollama instance
```
This means the `ollama` CLI reached out to the API and got nothing back — either no server
process exists yet, or one exists but isn't listening (exactly the state found on the dev PC
below). Treat it as a prompt to run Steps 1–2, not as a separate problem.

---

# Step 1: Check Whether Ollama Is Already Running

**RUN IN:** Windows PowerShell — Normal User
**Directory:** any

```powershell
Get-Process ollama -ErrorAction SilentlyContinue
```

> **Caution, verified on the dev PC:** this exact command can come back **empty even while
> Ollama is running**, because the background app's process is named `ollama app`, not
> `ollama` (the plain CLI binary is named `ollama`, but the tray/background application is a
> separate process with a space in its name). Run the broader check too:

```powershell
Get-Process | Where-Object { $_.Name -like "*ollama*" }
```

If this returns a process (e.g. `ollama app`), Ollama's background app is already running —
a second launch, or `ollama serve` run manually, will conflict with it. Skip to Step 6 to
check whether it's actually answering before deciding anything is broken.

If you need to restart it cleanly:
```powershell
Get-Process | Where-Object { $_.Name -like "*ollama*" } | Stop-Process -Force
```
Only do this if you intend to restart it right after — don't run it as a routine "fix" with
no follow-up. Stopping your own user's process this way does not require an elevated
terminal.

---

# Step 2: Check Whether Port 11434 Is Already Listening

**RUN IN:** Windows PowerShell — Normal User
**Directory:** any

```powershell
Get-NetTCPConnection -LocalPort 11434 -ErrorAction SilentlyContinue
```

If this returns a result, note the `OwningProcess` ID and cross-reference it:
```powershell
Get-Process -Id <paste the OwningProcess number here>
```

> **This check alone does not prove the port is available if it comes back empty.** On the
> dev PC, this returned nothing — no one was listening — and yet the server still could not
> bind the port (confirmed in Step 3). Windows can reserve or exclude a port range from ever
> being bound by *any* process, even with nothing currently listening on it. An empty result
> here only rules out "something is actively listening right now." Step 3 checks the other
> possibility.

---

# Step 3: Check Windows Excluded Port Ranges

**RUN IN:** Windows PowerShell — Normal User (does not require elevation; `netsh ... show ...`
is a read-only query)
**Directory:** any

```powershell
netsh interface ipv4 show excludedportrange protocol=tcp
```

Look for 11434 (and, per the dev-PC history, 11500) falling inside any listed range.

> **Dev-PC evidence, captured directly from this command on 2026-10-23:**
> ```
> Start Port    End Port
> ----------    --------
>       5985        5985
>      10378       10477
>      10478       10577
>      10578       10677
>      10678       10777
>      10778       10877
>      10878       10977
>      10978       11077
>      11078       11177
>      11178       11277
>      11278       11377
>      11378       11477      <-- covers 11434
>      11478       11577      <-- covers 11500
>      11578       11677
>      11678       11777
>      47001       47001
> ```
> **11434 and 11500 are both inside an excluded range on this PC, right now.** This is real,
> observed evidence — not a guess — and it directly explains the WSAEACCES bind error: Windows
> refuses to let *any* process bind a port inside an excluded range, which matches "nothing is
> listening" (Step 2) plus "bind is forbidden" (the error text) occurring together.

**What this does and doesn't prove, on this specific PC:**
- It proves 11434/11500 cannot be bound right now, by anything, regardless of Ollama.
- It does **not**, by itself, prove *why* these ranges are excluded. This PC has Hyper-V
  installed and in use (its `vmms` and `hns` services are confirmed `Running` — see the box
  below), and large, evenly-spaced port-exclusion blocks like this are a pattern commonly
  associated with Hyper-V's / Windows container networking's dynamic port reservations.
  **That correlation was observed, not proven causal** — disabling Hyper-V and re-running this
  command to see whether the ranges disappear would be the actual test, and that test was
  **not performed** (it's disruptive and out of scope for writing documentation). Treat
  Hyper-V as a plausible contributing factor on this PC, not a confirmed cause.

> **Supporting evidence gathered (RUN IN: Windows PowerShell — Administrator, for reference):**
> ```powershell
> Get-Service -Name hns, vmms
> bcdedit /enum
> ```
> On this dev PC: both services returned `Running`, and `bcdedit /enum` showed
> `hypervisorlaunchtype    Auto`, confirming Hyper-V's hypervisor is active here. **This does
> not apply to target deployment PCs**, which don't have Hyper-V installed — on those
> machines, if 11434/11500 ever show up excluded, look for a different cause (see the callout
> at the end of this step), since Hyper-V cannot be it.

**On a target PC without Hyper-V:** if you run this same command and find 11434 excluded,
**do not attribute it to Hyper-V** — it isn't installed there. Likely alternative causes to
check instead: Docker Desktop's WSL2 backend (if installed for Lab 1), a VPN client, or
another container/virtualization-adjacent tool that reserves dynamic port ranges. Identify
what's actually installed on that PC before guessing.

---

# Step 4: Check Services, Firewall, and Endpoint Security

**RUN IN:** Windows PowerShell — Normal User (listing services/rules doesn't need elevation;
*changing* any of them would, and this doc doesn't ask you to)
**Directory:** any

If Steps 1–3 don't explain the failure:

```powershell
Get-Service | Where-Object { $_.Status -eq 'Running' }
```
Look for anything unexpected bound to local networking that started around the same time as
the failure.

- **Windows Defender Firewall:** check for an inbound or outbound rule specifically blocking
  port 11434 or the `ollama.exe` / `ollama app.exe` process (Windows Security → Firewall &
  network protection → Advanced settings).
- **Endpoint security / antivirus:** some EDR or AV products intercept local socket binds.
  Check its logs for a blocked-connection or blocked-bind event around the failure time.

Report findings to IT if a managed security policy is the actual blocker. **Do not disable
Windows Defender Firewall, endpoint security, or any Windows networking service as a routine
fix** — that is a security-policy decision for whoever manages these PCs, not something this
doc tells you to work around unilaterally.

---

# Step 5: Confirm With a Direct Connection Test

**RUN IN:** Windows PowerShell — Normal User
**Directory:** any

```powershell
Test-NetConnection 127.0.0.1 -Port 11434
```
`TcpTestSucceeded : True` means something is listening and reachable on that port right now.
`False` means either nothing is listening, or something is actively refusing the connection —
combine with Steps 1–3 to tell which. (On the dev PC, this returned `False`, consistent with
the port being excluded and nothing able to bind it.)

---

# Step 6: Verify the API Once Ollama Is Running

**RUN IN:** Windows PowerShell — Normal User
**Directory:** any

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```
Expected: a JSON object listing your locally pulled models (`qwen2.5-coder:7b`,
`redlab-idor`, etc.) under a `models` key. If this returns data, Ollama's server and API are
both working — the setup is fine on this PC.

If this fails with a connection error, Ollama's server isn't listening on 11434 yet — go back
to Step 1.

> **Note on `curl` instead of `Invoke-RestMethod`:** in PowerShell, typing `curl` runs an
> **alias for `Invoke-WebRequest`**, not the real curl.exe — flags like `-s` or `-H` will
> fail or silently mean something different (confirmed: `curl -s URL -H "X: 1"` in PowerShell
> throws `Cannot bind parameter 'Headers'...`, not a working header). If you specifically want
> real curl syntax in PowerShell, call `curl.exe` explicitly (the real binary, by default at
> `C:\Windows\System32\curl.exe`). In Command Prompt, plain `curl` is already the real
> curl.exe — no alias to worry about there.

---

# Step 7: Only If 11434 Is Genuinely Unavailable — Use an Alternate Port

Do this **only after Steps 1–4 showed the default port is actually blocked**, not as a
default setting applied to every PC. Most machines should keep the default port.

### 7.1 Confirm the alternate port is itself free and not excluded

**RUN IN:** Windows PowerShell — Normal User

```powershell
Get-NetTCPConnection -LocalPort 20000 -ErrorAction SilentlyContinue
netsh interface ipv4 show excludedportrange protocol=tcp
```
Pick a port that appears in neither check's results. 20000 is used in this doc because it was
confirmed free and non-excluded on the dev PC at the time of writing — it is an example, not
a mandated value. Check it fresh on whichever PC you're working on.

### 7.2 Set `OLLAMA_HOST` for the current session

The syntax differs between shells. **Both forms below only set the variable for the current
process and whatever child processes it launches afterward** — they do not configure every
terminal, and they do not change any permanent Windows setting. Closing the terminal forgets
the value.

**RUN IN:** Windows PowerShell — Normal User
```powershell
$env:OLLAMA_HOST = "127.0.0.1:20000"
```

**RUN IN:** Command Prompt (CMD) — Normal User
```cmd
set OLLAMA_HOST=127.0.0.1:20000
```

These two are **not interchangeable syntax for the same shell** — `set VAR=value` is CMD-only
and does nothing useful if typed in PowerShell (PowerShell will try to run `set` as an alias
for `Set-Variable` with different argument rules); `$env:VAR = "value"` is PowerShell-only and
is a syntax error in CMD. Use the one that matches the terminal you actually opened.

To make the setting persist across reboots and new terminals instead of retyping it every
session, set it as a permanent Windows environment variable:

**RUN IN:** Windows PowerShell — Normal User (no elevation needed for a per-user variable)
```powershell
[System.Environment]::SetEnvironmentVariable("OLLAMA_HOST", "127.0.0.1:20000", "User")
```
This takes effect in **new** terminals opened after running it — it does not affect terminals
already open, and does not need Administrator rights since it's a per-user, not a
system-wide, setting.

### 7.3 Start the server and verify — client and server must agree on the port

**The Ollama client and server must use matching host/port settings, or the client will try
to talk to the wrong place and fail even though the server is running fine.** Set
`OLLAMA_HOST` in every terminal you use for this kit, including the one that will run
`skill_loader.py` or `ollama create` — not just the one running the server.

**RUN IN:** Windows PowerShell — Normal User, Terminal 1
```powershell
$env:OLLAMA_HOST = "127.0.0.1:20000"
ollama serve
```
Leave this running. Expected: no immediate error, and the window stays open (it's the
foreground server process now).

**RUN IN:** Windows PowerShell — Normal User, Terminal 2 (separate window — the variable from
Terminal 1 does not carry over automatically)
```powershell
$env:OLLAMA_HOST = "127.0.0.1:20000"
Invoke-RestMethod http://127.0.0.1:20000/api/tags
ollama list
```
Expected: both commands return without a connection error.

**Verified on the dev PC:** after applying exactly this sequence (stop the stuck
`ollama app` process from Step 1, set `OLLAMA_HOST` to `127.0.0.1:20000` in the same session,
start `ollama serve`), `Get-NetTCPConnection -LocalPort 20000` showed a real listener, and
`Invoke-RestMethod http://127.0.0.1:20000/api/tags` returned the expected model list. This is
a **verified resolution for this specific PC at this specific time** — stated as such, not as
a universal guarantee for every machine or every future reboot.

---

# Step 8: Re-verify the Full Chain

**RUN IN:** Windows PowerShell — Normal User (same terminal, `OLLAMA_HOST` still set if you're
on an alternate port)

```powershell
ollama --version
Get-Process | Where-Object { $_.Name -like "*ollama*" }
Invoke-RestMethod http://127.0.0.1:11434/api/tags      # or your alternate port
ollama list
ollama run qwen2.5-coder:7b "say hi in exactly 3 words"
```
If all five succeed, continue with `docs/02-offline-installation.md` from wherever you left
off, or with building a skill-loaded model (`tools/skill_loader.py`).

**Verified on the dev PC, using port 20000:** `ollama create redlab-idor -f Modelfile`
completed with `success`, `ollama list` showed both `qwen2.5-coder:7b` and
`redlab-idor:latest`, and `ollama run redlab-idor "In exactly one sentence, what is an IDOR
vulnerability?"` returned a correct, on-topic answer. The full chain — skill loader → custom
model → running model — works once the port conflict is worked around. This confirms
`tools/skill_loader.py` itself was never broken; the earlier failure was entirely the
server-startup problem documented in Steps 1–3, not the Python script (see Step 9 below for
the specific error that was observed from the script).

---

# Step 9: If Model Creation Specifically Fails (Case H)

If `ollama pull` or `ollama create` (including when run via `tools/skill_loader.py`) fails
while the server itself won't start, you'll see the same `Error: timed out waiting for server
to start` from Step 1's error list, surfaced through the Python script's `subprocess.run(...,
check=True)` call. This is expected — the script shells out to the real `ollama create`
command and surfaces whatever that command prints.

**Observed on the dev PC, exact sequence:** `python tools/skill_loader.py --skill
../claude-red-skills/Skills/web/offensive-idor/SKILL.md --name redlab-idor --base
qwen2.5-coder:7b` **did** write a complete, correctly-formed `Modelfile` (confirmed by
reading it afterward — it starts with `FROM qwen2.5-coder:7b` and a `SYSTEM """..."""` block
containing the skill content). The subsequent `ollama create` step then failed with the
server-timeout error. **This does not mean the Python script is broken** — it had already
done its job by the time the failure happened. Fix the server issue (Steps 1–7), then rerun
just the `ollama create` step without rerunning the script, by pointing directly at the
already-written file:

**RUN IN:** Windows PowerShell — Normal User
**Directory:** wherever the `Modelfile` was written (the repo root, by default)
```powershell
Get-Content .\Modelfile -TotalCount 5    # sanity-check it looks right first
ollama create redlab-idor -f .\Modelfile
```

---

## What This Doc Does Not Claim

- It does not claim any fix above has been tested on every PC — Steps 1–8 were verified,
  with real command output, on the specific dev PC described at the top of this doc, on
  2026-10-23. Treat that as one confirmed data point, not a guarantee for a different machine.
- It does not claim Hyper-V caused the dev PC's port exclusions. The evidence (Hyper-V
  services running, a port-exclusion pattern commonly associated with that kind of
  networking) is **correlational**, stated as such throughout Step 3, not **causal**. No test
  that would prove causation (disabling Hyper-V and re-checking) was performed.
- It does not recommend disabling Windows Defender Firewall, endpoint security, or any
  virtualization-related Windows service as a routine fix, and it does not instruct removing
  a Windows port exclusion — those are decisions for whoever manages security policy on these
  machines, not something to self-serve from a lab guide.
- It does not assume target deployment PCs share the dev PC's exact exclusion ranges,
  hardware, or Python version. Run Steps 1–6 fresh on a target PC rather than assuming its
  port 11434 is also excluded — it may not be, since it doesn't have Hyper-V.
