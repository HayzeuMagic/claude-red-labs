#!/usr/bin/env python3
"""
skill_loader.py — turn a Claude-Red SKILL.md into a local Ollama model.

This is intentionally small: it does ONE thing — "load skill instructions into a
prompt" (see docs/01-architecture.md for why this is the right layer, and what it
deliberately does NOT do: no trigger-based auto-selection, no tool-calling, no
fine-tuning).

What it does:
  1. Reads one or more Claude-Red SKILL.md files.
  2. Strips the parts that only make sense inside Claude's own product
     (the "Trigger Phrases" line, "Instructions for Claude" boilerplate,
     references to ~/.claude/skills or auto-loading). Everything else — the
     actual methodology — is kept verbatim.
  3. Prepends a short, non-negotiable safety banner (lab-only / authorized-only /
     advisory-only) that applies regardless of which skill is loaded.
  4. Writes an Ollama Modelfile and runs `ollama create <name> -f <Modelfile>`.

Usage:
    python tools/skill_loader.py --skill "<path to SKILL.md>" --name redlab-idor
    python tools/skill_loader.py --skill a.md --skill b.md --name redlab-web --base qwen2.5-coder:7b
    python tools/skill_loader.py --baseline --name redlab-baseline --base qwen2.5-coder:7b

Requires: Python 3.8+, and the `ollama` CLI already installed and on PATH.
No network access is used by this script itself — it only reads local files and
shells out to the already-installed, already-offline `ollama` binary.
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

SAFETY_BANNER = """\
You are a defensive-education assistant used in an authorized, instructor-controlled
university lab. You ONLY discuss the specific target application the student names in
this conversation, which is always a deliberately vulnerable training application running
on localhost inside the lab (e.g. OWASP Juice Shop, or the lab2 sample Flask app). You:
- Never assume or suggest a real-world, third-party, or production target.
- Always frame answers as hypotheses for the student to verify themselves, not confirmed
  facts — remind them to confirm with evidence (an actual request/response, a test run)
  before treating a suggestion as a finding.
- Explain WHY a technique works and what a defender would see, not just a raw payload.
- Do not claim to execute anything yourself. You give guidance in text; the student runs
  commands themselves in their own terminal/proxy/browser.
"""

# Lines/sections that are meaningless or misleading outside Claude's own product.
STRIP_LINE_PATTERNS = [
    r"^Trigger Phrases.*$",
    r"^Use this skill when.*conversation involves.*$",
    r".*auto-loads? based on conversational triggers.*",
    r".*~/\.claude/skills.*",
    r".*Claude Skills system.*",
]
STRIP_SECTION_HEADERS = [
    "trigger phrases",
    "instructions for claude",
]
# The comma-separated phrase list that follows a "Trigger Phrases" line. Only
# stripped directly after that line: elsewhere, an inline-code line with commas
# is usually real methodology (e.g. `id, user_id, account_id`).
TRIGGER_LIST_PATTERN = r"^\s*`[^`]*,.*,.*`\s*$"


def strip_claude_specific(body: str) -> str:
    lines = body.splitlines()
    out = []
    skip_level = 0  # header level of the section being stripped; 0 = not skipping
    in_fence = False
    after_trigger_line = False
    for line in lines:
        if re.match(r"^\s*(```|~~~)", line):
            in_fence = not in_fence
            if not skip_level:
                out.append(line)
            continue
        if in_fence:
            # Code samples are kept verbatim: a `# comment` in a shell snippet is
            # not a Markdown heading, and strip patterns must not touch payloads.
            if not skip_level:
                out.append(line)
            continue
        header_match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
        if header_match:
            level = len(header_match.group(1))
            if skip_level and level > skip_level:
                # A sub-heading inside a stripped section is stripped with it.
                continue
            # Normalise "**Trigger Phrases:**", "Instructions for Claude #" etc.
            title = re.sub(r"[^a-z0-9 ]+", " ", header_match.group(2).lower())
            title = " ".join(title.split())
            skip_level = level if title in STRIP_SECTION_HEADERS else 0
            if skip_level:
                continue
        if skip_level:
            # Only a header of the same or higher level ends the skip; handled above.
            continue
        if after_trigger_line:
            if not line.strip():
                continue  # blank line between "Trigger Phrases" and its list
            after_trigger_line = False
            if re.match(TRIGGER_LIST_PATTERN, line.strip()):
                continue
        if re.match(r"^Trigger Phrases", line.strip(), re.IGNORECASE):
            after_trigger_line = True
        if any(re.match(p, line.strip(), re.IGNORECASE) for p in STRIP_LINE_PATTERNS):
            continue
        out.append(line)
    return "\n".join(out).strip()


def load_skill_body(path: Path) -> str:
    # utf-8-sig drops a BOM (common for files saved by Windows editors), which
    # would otherwise hide the frontmatter's opening '---'.
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    # Drop YAML frontmatter if present: '---' on its own first line, up to the
    # next line that is exactly '---'. Splitting on every '---' substring broke
    # on values like "description: A --- B" and cut the body short.
    m = re.match(r"\A---[ \t]*\r?\n.*?^---[ \t]*(?:\r?\n|\Z)", text, re.DOTALL | re.MULTILINE)
    if m:
        text = text[m.end():]
    return strip_claude_specific(text)


def build_modelfile(base_model: str, system_text: str) -> str:
    # Triple-quoted SYSTEM block per Ollama Modelfile syntax.
    # Ollama's parser does no backslash-escape processing: a block simply ends at
    # the first `"""`, and `\"` stays a literal backslash + quote in the prompt.
    # So the only safe option is to make sure no `"""` run survives in the body.
    escaped = system_text
    while '"""' in escaped:
        escaped = escaped.replace('"""', "'''")
    return f'FROM {base_model}\nSYSTEM """\n{escaped}\n"""\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skill", action="append", default=[], help="Path to a SKILL.md file. Repeatable.")
    ap.add_argument("--name", required=True, help="Name for the resulting Ollama model, e.g. redlab-idor")
    ap.add_argument("--base", default="qwen2.5-coder:7b", help="Base Ollama model tag (default: qwen2.5-coder:7b)")
    ap.add_argument("--baseline", action="store_true",
                     help="Build a model with ONLY the safety banner, no skill content (for the comparison exercise).")
    ap.add_argument("--out", default="Modelfile", help="Where to write the generated Modelfile.")
    ap.add_argument("--no-create", action="store_true", help="Write the Modelfile but skip calling `ollama create`.")
    args = ap.parse_args()

    if not args.baseline and not args.skill:
        ap.error("pass at least one --skill <path>, or use --baseline")
    if args.baseline and args.skill:
        # A "baseline" with skill content silently invalidates the comparison exercise.
        ap.error("--baseline builds a model with NO skill content; don't combine it with --skill")

    chunks = [SAFETY_BANNER]
    for s in args.skill:
        p = Path(s)
        if not p.is_file():
            print(f"error: skill file not found: {p}", file=sys.stderr)
            sys.exit(1)
        chunks.append(f"## Skill: {p.parent.name}\n\n{load_skill_body(p)}")

    system_text = "\n\n---\n\n".join(chunks)
    modelfile_text = build_modelfile(args.base, system_text)

    out_path = Path(args.out)
    out_path.write_text(modelfile_text, encoding="utf-8")
    print(f"Wrote {out_path} ({len(modelfile_text)} bytes, base={args.base})")

    if args.no_create:
        return

    if shutil.which("ollama") is None:
        print("error: `ollama` not found on PATH. Install Ollama first (see docs/02-offline-installation.md).",
              file=sys.stderr)
        sys.exit(1)

    cmd = ["ollama", "create", args.name, "-f", str(out_path)]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"\nDone. Try it with:\n    ollama run {args.name}")


if __name__ == "__main__":
    main()
