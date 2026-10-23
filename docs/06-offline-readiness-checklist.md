# Offline-Readiness Checklist

Run this **after** completing `02-offline-installation.md`, with the network disconnected
(turn off Wi-Fi / unplug Ethernet, or use a VM with no network adapter), on every lab machine
before class.

- [ ] `ollama --version` runs (Ollama itself doesn't need network to start).
- [ ] `ollama list` shows your base model tag plus `redlab-idor`, `redlab-sqli`,
      `redlab-webtriage`, `redlab-baseline`.
- [ ] `ollama run redlab-idor` starts a chat and responds to a test question
      (e.g. "what's an IDOR?") with no error.
- [ ] `docker compose up -d` (from the repo root) brings up Juice Shop using the
      **already-pulled** image — `docker compose ps` shows it running, and
      `http://127.0.0.1:3000` loads in a browser.
- [ ] `cd lab2/vuln_app && python app.py` starts without error (venv already created and
      dependencies already installed from the online step).
- [ ] `pytest lab2/tests/test_security_regression.py -v` passes 5/5, offline.
- [ ] (If using ZAP) ZAP launches and can proxy a request to `127.0.0.1:3000` without trying
      to reach its update server (decline any update prompt).
- [ ] Re-enable the network and confirm nothing silently failed/retried in the background
      (check `docker compose logs`, Ollama's logs) — a step that "worked" by silently
      retrying over a flaky connection is not actually offline-ready.

If any box fails: re-run the matching step in `02-offline-installation.md` while online, then
re-test this checklist offline again. Don't assume a step is fine because it worked once
while connected — pulls, image fetches, and package installs are exactly the failure mode
this checklist exists to catch.
