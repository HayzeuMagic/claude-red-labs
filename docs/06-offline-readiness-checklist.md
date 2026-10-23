# Offline-Readiness Checklist (Windows)

Run this **after** completing `02-offline-installation.md`, with the network disconnected
(turn off Wi-Fi / unplug Ethernet), on every lab machine before class. Every command below:
**RUN IN:** Windows PowerShell — Normal User, from the `claude-red-labs` root unless noted.

> **Note:** this checklist doesn't use `&&` to chain commands. Windows PowerShell 5.1 (the
> default on most Windows installs) does not support `&&`/`||` as pipeline chain operators —
> it's a parser error there, even though it works in PowerShell 7+ and in Bash. Each line
> below is one standalone command for that reason.

- [ ] `ollama --version` runs (Ollama itself doesn't need network to start).
- [ ] `Invoke-RestMethod http://127.0.0.1:11434/api/tags` returns a JSON model list (confirms
      the server is actually listening, not just that the CLI is installed — and not the
      same thing as being offline-ready; if this fails, see
      `07-ollama-windows-troubleshooting.md`, since it can fail with or without a network).
- [ ] `ollama list` shows your base model tag plus `redlab-idor`, `redlab-sqli`,
      `redlab-webtriage`, `redlab-baseline`. If `redlab-sqli` is missing because
      `claude-red-skills\Skills\web\offensive-sqli\SKILL.md` keeps disappearing, check for a
      Windows Defender quarantine of that specific file before re-cloning again — see
      `02-offline-installation.md` Step 4.1. Treat Lab 2's AI step as **blocked**, not failed,
      until that's resolved; Lab 1 does not depend on it.
- [ ] `ollama run redlab-idor "what's an IDOR in one sentence?"` responds with no error.
- [ ] `docker compose up -d` (from the `claude-red-labs` root) brings up Juice Shop using the
      **already-pulled** image — `docker compose ps` shows it running, and
      `http://127.0.0.1:3000` loads in a browser.
- [ ] From `lab2\vuln_app`, with the venv activated (`.venv\Scripts\Activate.ps1`):
      `python app.py` starts without error (venv already created and dependencies already
      installed from the online step).
- [ ] From the repo root: `pytest lab2\tests\test_security_regression.py -v` passes 5/5,
      offline.
- [ ] (If using ZAP) ZAP launches and can proxy a request to `127.0.0.1:3000` without trying
      to reach its update server (decline any update prompt).
- [ ] Re-enable the network and confirm nothing silently failed/retried in the background
      (check `docker compose logs`, Ollama's logs) — a step that "worked" by silently
      retrying over a flaky connection is not actually offline-ready.

If any box fails: re-run the matching step in `02-offline-installation.md` while online, then
re-test this checklist offline again. Don't assume a step is fine because it worked once
while connected — pulls, image fetches, and package installs are exactly the failure mode
this checklist exists to catch.
