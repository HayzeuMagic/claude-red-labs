# Architecture & Rationale

## 1. What Claude-Red actually is, and what transfers to Ollama

[Claude-Red](https://github.com/SnailSploit/claude-red) (`SnailSploit/claude-red`, also
mirrored at `SnailSploit/Claude-Red`) is a library of 78 **`SKILL.md` files**, organized as:

```
Skills/<category>/<skill-name>/SKILL.md
```

e.g. `Skills/web/offensive-idor/SKILL.md`, `Skills/web/offensive-sqli/SKILL.md`,
`Skills/utility/offensive-reporting/SKILL.md`.

Each `SKILL.md` is **plain Markdown with a metadata block** — in the current repo, two
metadata styles both appear:

- A YAML frontmatter form documented in `CONTRIBUTING.md`:
  ```yaml
  ---
  name: offensive-<bug-class-or-domain>
  description: "One paragraph... Claude uses this for trigger matching..."
  ---
  ```
- An older Markdown-header form used by some existing skills (e.g.
  `offensive-fast-checking`), with a `## Metadata` section (`Skill Name`, `Folder`,
  `Source`), a `## Description`, a `## Trigger Phrases` list, and an
  `## Instructions for Claude` section, followed by the actual methodology body.

**What is Claude-specific:** the *auto-loading* mechanism — Claude's product (claude.ai
Projects, the Claude Skills system, Claude Code) watches the conversation for the
`description:` / `Trigger Phrases` text and injects the matching `SKILL.md` body into context
automatically, without you pasting it in. The repo's own README install instructions
(`git clone ... ~/.claude/skills/claude-red`, `./install.sh`) only set up *that* auto-loading —
they assume a Claude client is reading `~/.claude/skills/`. **None of that exists in Ollama.**
Ollama has no concept of a skill, a trigger phrase, or a skills directory; it only ever sees
whatever text you put in the `system` field of a chat request.

**What is not Claude-specific — and is exactly what we reuse:** the `SKILL.md` body itself.
It's just domain-expert text: a numbered workflow, concrete commands, a defender's-view
section, a reporting cheat-sheet. Any instruction-following chat model can read that same text
as a system prompt and use it to shape its answers. The skill file is reusable; the
auto-loading harness around it is not.

### Three different things, and which one this kit does

| Approach | What it means | Needed here? |
|---|---|---|
| **Load skill instructions into a prompt** | Paste/inject the `SKILL.md` body as the model's system message for that conversation. No code changes to the model. | **Yes — this is the whole mechanism.** |
| **Build a skill-aware agent** | Write code that (a) watches the conversation, (b) picks the right skill(s) automatically based on keywords, (c) optionally lets the model call real tools (a scanner, a shell) via function-calling. | **Partially, and explicitly scoped down** — `tools/skill_loader.py` does simple keyword→skill selection *ahead of time* (the instructor/student picks the skill file, the script just avoids hand-copying). It does **not** wire the model up to call tools automatically; see §4. |
| **Fine-tune model weights** | Train/adjust the model's weights on skill content so the behavior is baked in permanently. | **No.** Unnecessary, slow, needs a GPU/dataset most student laptops don't have, and loses the ability to swap skills per-lab. Prompting a 7B instruct model with a well-written SKILL.md is a close enough substitute for this kit's purposes. |

## 2. Recommended architecture

```
 ┌─────────────────────────────┐        ┌──────────────────────────────┐
 │ Claude-Red repo (local copy)│        │ OWASP Juice Shop (Docker, Lab1)│
 │ Skills/<cat>/<skill>/SKILL.md│        │ or vuln_app Flask app (Lab 2)  │
 └──────────────┬───────────────┘        └───────────────┬────────────────┘
                │ read by                                  │ student probes with
                ▼                                           ▼ curl / browser / ZAP
      tools/skill_loader.py  ──creates──►  Ollama custom model
      (strips Claude-only metadata,          (`ollama create redlab-idor -f Modelfile`)
       writes a Modelfile)                          │
                                                       ▼
                                          `ollama run redlab-idor`  (local chat, CLI or REST)
                                                       │
                                          student reads AI suggestions,
                                          decides what to try, runs it themselves
```

- **Runtime:** [Ollama](https://ollama.com) — free, runs entirely on the student's machine,
  no account needed for local models (accounts/`:cloud` tags are for Ollama's *cloud* models,
  which we do not use).
- **Model:** an instruct/coder model pulled once with `ollama pull`, then cached under
  Ollama's local model storage and usable with zero network access afterward. See hardware
  tiers below.
- **Skill delivery:** `tools/skill_loader.py` (included in this repo) reads a `SKILL.md` file,
  strips the Claude-product-specific framing (the "Trigger Phrases" list, "auto-loads",
  references to `~/.claude/skills`), and writes the remaining methodology text into an Ollama
  `Modelfile`'s `SYSTEM` block. It then shells out to `ollama create`. This is ~120 lines of
  plain Python, no framework.
- **Interface:** `ollama run <model>` (terminal chat) is sufficient for both labs and needs
  nothing beyond Ollama itself. An optional free local web UI
  ([Open WebUI](https://github.com/open-webui/open-webui)) is mentioned as an enhancement in
  the installation guide for instructors who want a nicer in-browser chat, but it is **not**
  required and adds a second thing to install offline, so the labs as written use the CLI.
- **Target applications:** OWASP Juice Shop (Docker image `bkimminich/juice-shop`, MIT-licensed,
  intentionally vulnerable, designed for exactly this kind of training) for Lab 1; a small
  original Flask app (`lab2/vuln_app/app.py`, included in this repo) for Lab 2.
- **Supporting tools:** curl (ships with Windows/macOS/Linux), a browser's dev tools, and
  OWASP ZAP (free, open source) for anyone who wants a proxy/scanner beyond manual requests.
  Burp Suite Community Edition is an equally valid free substitute for ZAP; pick one per lab
  room to keep install instructions uniform.

### Why this is the simplest reliable option

- No GPU required (every tier below runs CPU-only; a GPU just makes it faster).
- No account, license, or payment anywhere in the stack.
- No fine-tuning pipeline, no dataset curation, no training hardware.
- Swapping skills is a re-run of one script, not a retrain.
- The security boundary is simple to reason about and to teach: **the model never touches the
  target application directly.** It only ever talks to the student, in text, in a terminal.

## 3. Hardware tiers (rule-of-thumb, not a vendor guarantee)

Ollama's own listed download sizes (verified against `ollama.com/library`) scale roughly with
RAM needed to run a model comfortably on CPU (model size + a few GB of headroom for context
and the OS). Pick the smallest tier that fits comfortably in each lab machine's RAM:

| Student RAM | Model | Ollama tag | Download size |
|---|---|---|---|
| 8 GB (minimum, CPU-only, will be slow) | Qwen2.5-Coder 1.5B | `qwen2.5-coder:1.5b` | ~1.0 GB |
| 16 GB (recommended default) | Qwen2.5-Coder 7B | `qwen2.5-coder:7b` | ~4.7 GB |
| 16 GB, general-purpose alternative | Llama 3.1 8B | `llama3.1:8b` | ~4.9 GB |
| 32 GB+, or a GPU with ≥10 GB VRAM | Qwen2.5-Coder 14B | `qwen2.5-coder:14b` | ~9.0 GB |

Qwen2.5-Coder is recommended as the default because both labs involve reading/writing code
(Lab 2 especially) as well as web-request reasoning (Lab 1), and it's one of the strongest
openly-downloadable code-capable models in the size range most student laptops can run.
Llama 3.1 8B is a fine drop-in alternative if Qwen is unavailable on a given mirror.

**Assumption, labeled as such:** exact tokens/sec on any given student laptop cannot be
predicted here — it depends on CPU, RAM speed, and whether a GPU is used. Budget at least one
extra class session (or a take-home pull step, see installation guide) for the model download,
and expect the 7B tier to answer in a few seconds to ~1 minute per response on a typical
2020s laptop CPU.

## 4. What works out of the box vs. what needs integration

| Capability | Status |
|---|---|
| Local chat with a skill's methodology as system prompt | **Works out of the box** once Ollama + model + `skill_loader.py` are set up. This is the entire mechanism both labs rely on. |
| Switching between skills (e.g. IDOR vs. SQLi) | **Works out of the box** — re-run `skill_loader.py` with a different `SKILL.md`, or keep several named models side by side (`redlab-idor`, `redlab-sqli`, ...). |
| Automatic skill selection by conversational trigger (what Claude's product does) | **Not implemented** in this kit. Students/instructors choose the skill file explicitly. Building real trigger-matching would mean writing a keyword classifier or a second small routing model — out of scope here, and not needed for a taught lab where the instructor already knows which skill applies. |
| The model directly running tools (scanners, curl, a shell) against the target | **Not implemented, and not claimed.** Nothing in this kit gives the model execution access to the target or the student's shell. Everything the model "recommends," a human runs. If an instructor later wants real tool-calling, Ollama supports function-calling-style tool definitions for compatible models via the `/api/chat` `tools` field, and a harness (e.g. a short Python loop) would need to be written and *tested end-to-end* before any claim of autonomous execution — that is future work, not part of this kit. |
| Offline operation after setup | **Works out of the box.** Ollama serves models from local disk; Docker serves Juice Shop from a locally cached image; the Flask app in Lab 2 has no external dependencies at runtime. Verify with `docs/06-offline-readiness-checklist.md`. |
