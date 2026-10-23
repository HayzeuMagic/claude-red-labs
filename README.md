# Offline AI Cybersecurity Labs — Claude-Red + Ollama

An instructor's kit for running two hands-on, offline AI-assisted security labs with
undergraduate cybersecurity / intro-pentesting students, using a **free, locally
running LLM** instead of a paid Claude subscription or any cloud API.

- **Lab 1** — AI-assisted web vulnerability assessment against OWASP Juice Shop.
- **Lab 2** — AI-assisted vulnerability analysis and remediation of a small, intentionally
  vulnerable Python/Flask application, with a regression test.

Everything here — model, interface, lab targets, skill content — runs on the student's
machine with no internet connection required once setup is complete.

## Start here

1. Read [`docs/01-architecture.md`](docs/01-architecture.md) — what we're building and why.
2. Follow [`docs/02-offline-installation.md`](docs/02-offline-installation.md) — one-time setup
   (do this step with internet access; everything after is offline).
3. Run [`docs/03-lab1-web-vuln-assessment.md`](docs/03-lab1-web-vuln-assessment.md).
4. Run [`docs/04-lab2-vuln-remediation.md`](docs/04-lab2-vuln-remediation.md).
5. Optional comparison exercise: [`docs/05-comparison-exercise.md`](docs/05-comparison-exercise.md).
6. Before class, run through [`docs/06-offline-readiness-checklist.md`](docs/06-offline-readiness-checklist.md).

## What's in this repo

```
docs/                          instructor guide, lab manuals, worksheets, rubrics
tools/skill_loader.py           turns a Claude-Red SKILL.md into a local Ollama model
tools/Modelfile.template        template used by skill_loader.py
docker-compose.yml               OWASP Juice Shop target for Lab 1
lab2/vuln_app/                  intentionally vulnerable Flask app for Lab 2 (SQLi)
lab2/tests/                      pytest regression test for the Lab 2 fix
```

## Scope and safety

- All testing in these labs is confined to applications the instructor deploys **inside the
  lab environment** (a local Juice Shop container, a local Flask app). Students must not point
  any tool, payload, or AI-suggested technique at a system they do not own or have not been
  explicitly authorized to test.
- The local model is an **advisor**, not an autonomous operator. No agent in this kit executes
  attacks on its own; students read the model's suggestions, understand them, and run the actual
  commands themselves through tools they control (curl, a browser, OWASP ZAP). See
  `docs/01-architecture.md` for why, and what *would* be required to change that.
- This kit reuses the public [Claude-Red](https://github.com/SnailSploit/claude-red) skill
  library (MIT-licensed `SKILL.md` methodology files) purely as **prompt content** — no
  Claude-Red code runs, no Claude subscription or API is used anywhere in this kit.
