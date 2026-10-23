# Quickstart — Already Built (Start Here for Every Returning Session)

Use this doc if this machine has **already** been through
[`08-fresh-pc-setup.md`](08-fresh-pc-setup.md) / [`02-offline-installation.md`](02-offline-installation.md)
once — Git/Python/Docker/Ollama installed, the base model pulled, the custom models built, the
Juice Shop image pulled, and the Lab 2 virtual environment created. You are **not** reinstalling
anything here; you're just turning the already-built kit back on for a class session.

If any check below fails in a way its troubleshooting line doesn't resolve, that component
needs to be rebuilt — go to the matching step in `08-fresh-pc-setup.md`, not this doc.

---

## Step 1 — Confirm Ollama is reachable (every session, every terminal)

**RUN IN:** Windows PowerShell — Normal User · **Directory:** any

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```
Expected: a JSON object listing your models.

**If this fails:** some machines need a non-default port (confirmed via
[`07-ollama-windows-troubleshooting.md`](07-ollama-windows-troubleshooting.md) when this kit
was first set up on *that specific machine*). If this machine is one of those, set the same
port it was configured with before, in **this** terminal:
```powershell
$env:OLLAMA_HOST = "127.0.0.1:<the port this machine uses>"
Invoke-RestMethod http://127.0.0.1:<that port>/api/tags
```
This does not persist across terminals — set it again in every new window you open for this
kit, including the one you'll start Lab 2 from if it ever touches Ollama. If you don't
remember whether this machine needs this, or which port, re-run `07-ollama-windows-troubleshooting.md`
Steps 1–3 once to check — don't guess, and don't copy another machine's port number without
verifying it applies here too.

## Step 2 — Confirm the models are all there and actually answer

**RUN IN:** Windows PowerShell — Normal User (same terminal, same `OLLAMA_HOST` if you set one)

```powershell
ollama list
```
Expected: your base model tag (e.g. `qwen2.5-coder:7b`) plus `redlab-idor`, `redlab-webtriage`,
`redlab-baseline`, and `redlab-sqli` if it was successfully built on this machine.

Spot-check one with a real prompt (don't rely on `ollama list` alone):
```powershell
ollama run redlab-idor "what's an IDOR in one sentence?"
```
Expected: a real, on-topic reply, not an error.

**If a model you expect is missing:** rebuild just that one with its command from
`08-fresh-pc-setup.md` Step 6 / `02-offline-installation.md` Step 5 — `ollama create` with the
same `--name` overwrites cleanly, it doesn't duplicate. If it's specifically `redlab-sqli` and
it was never built on this machine because its source skill file was deleted (see
`02-offline-installation.md` Step 4.1), that's a known, separate issue — don't keep retrying
the build command expecting a different result until that's resolved.

## Step 3 — Start Lab 1 (OWASP Juice Shop)

**RUN IN:** Windows PowerShell — Normal User · **Directory:** `claude-red-labs` root

```powershell
docker compose up -d
docker compose ps
```
Expected: a row for `redlab-juiceshop`, `127.0.0.1:3000->3000/tcp`, `STATUS` starting with `Up`.
Open http://127.0.0.1:3000 in a browser to confirm.

**If `docker compose up` fails:** Docker Desktop's background service probably isn't running
yet — open "Docker Desktop" from the Start menu, wait ~30–60 seconds, and retry. No image
should need to download here; if one does, you're missing Step 7 of the fresh-PC setup on
this machine.

When the session is done:
```powershell
docker compose down
```

## Step 4 — Start Lab 2 (Flask SQL injection app)

**RUN IN:** Windows PowerShell — Normal User · **Directory:** `claude-red-labs` root

```powershell
cd lab2\vuln_app
.venv\Scripts\Activate.ps1
```
(CMD: `.venv\Scripts\activate.bat`. Your prompt should show `(.venv)` once this works.)

```powershell
python app.py
```
Expected: `* Running on http://127.0.0.1:5000`. Leave this terminal open for the whole lab
session. Open a **second** terminal for student requests (curl, browser, ZAP/Burp):
```powershell
Invoke-WebRequest http://127.0.0.1:5000/ -UseBasicParsing
```

To run the regression tests at any point (from a **third** terminal, or after stopping the
app with `Ctrl+C` in the first one):
```powershell
cd C:\Users\Administrator\claude-red-labs
pytest lab2\tests\test_security_regression.py -v
```
Expected: `5 passed` (`6 passed` once a student has added their own test, per the Lab 2
manual).

**If `ModuleNotFoundError: flask`:** the venv isn't active in that terminal — redo the
`Activate.ps1` line above in the terminal you're actually running the command from.

When the session is done, `Ctrl+C` in the terminal running `app.py`.

## Step 5 — End-of-session cleanup

**RUN IN:** Windows PowerShell — Normal User · **Directory:** `claude-red-labs` root

```powershell
docker compose down
```
(stops and removes the Juice Shop container; the image itself stays cached for next time — no
re-download needed). Stop `app.py` with `Ctrl+C` in its terminal if it's still running. Nothing
else needs to be torn down — the Ollama models and server stay as they are between sessions.

---

## If something that used to work has stopped working

| Symptom | Likely cause | Fix |
|---|---|---|
| Ollama API unreachable on the port that used to work | Server process wasn't running (e.g. after a reboot) | Redo Step 1; if this machine needs a non-default `OLLAMA_HOST`, remember to set it again |
| A model is missing from `ollama list` | It was removed (`ollama rm`), or never finished building | Rebuild it with its Step 6 command from `08-fresh-pc-setup.md` |
| `docker compose up -d` can't reach the image | Docker Desktop's backend isn't started yet | Open Docker Desktop from the Start menu, wait, retry — this should never need the network again once the image was pulled once |
| Lab 2 venv errors on import | The `.venv` folder was deleted or moved | Recreate it: `08-fresh-pc-setup.md` Step 8, from `python -m venv .venv` onward |
| `redlab-sqli` was never built on this machine | Its source `SKILL.md` was deleted (commonly by antivirus flagging example payload content) | See `02-offline-installation.md` Step 4.1 — this needs a deliberate decision by whoever manages security policy on this machine, not a routine retry |

Full reinstall procedure, if several of the above are true at once or this is actually a
different machine than the one that was set up before: [`08-fresh-pc-setup.md`](08-fresh-pc-setup.md).
