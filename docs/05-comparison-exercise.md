# Comparison Exercise: With vs. Without the Claude-Red Skill

**Goal:** make the effect of the skill prompt visible and concrete, so students don't treat
"the AI said so" as inherently authoritative — the skill changes *how structured and
checkable* the answer is, not whether the model is infallible.

## Setup

You already built `redlab-baseline` in the installation guide (same base model, only the
generic safety banner, no skill content). If not, **RUN IN:** Windows PowerShell — Normal
User, from the `claude-red-labs` root:
```powershell
python tools\skill_loader.py --baseline --name redlab-baseline --base qwen2.5-coder:7b
```

## Procedure

Pick one scenario from Lab 1 or Lab 2 (e.g. "is `/rest/basket/<id>` vulnerable to IDOR?" or
"is this Flask route SQL-injectable?"). Ask **the same question, worded identically**, to:

1. `ollama run redlab-baseline` — no skill loaded.
2. `ollama run redlab-idor` (or `redlab-sqli`) — skill loaded.

## What to record

| | Baseline | With skill |
|---|---|---|
| Does it name a concrete test to run (not just "test for injection")? | | |
| Does it state what a positive vs. negative result looks like? | | |
| Does it mention false-positive traps (e.g. "this could be a legitimately shared resource")? | | |
| Does it reference anything specific to the actual framework/app, or stay generic? | | |
| Overall, how much editing would a report based on this answer need? | | |

## Discussion questions (for the reflection/worksheet)

1. Was the skill-loaded answer *more correct*, or just *more structured and specific*? Are
   those the same thing?
2. Did either model say anything confidently that turned out to be wrong once you verified
   it? What does that imply about trusting either answer without verification?
3. The skill content is public, MIT-licensed Markdown — nothing about it is secret model
   behavior. Given that, what's actually different between "with skill" and "without skill"
   here? (Expected answer: the system prompt adds domain-specific structure and checklists;
   it doesn't add facts the base model couldn't in principle produce, but it reliably makes
   the model *produce* that structure instead of a generic answer.)
