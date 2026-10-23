# Lab 1: AI-Assisted Web Vulnerability Assessment

**Target:** OWASP Juice Shop (local Docker container, `127.0.0.1:3000`)
**AI model:** `redlab-idor` (Qwen2.5-Coder 7B + Claude-Red's `offensive-idor` skill) and
`redlab-webtriage` (+ `offensive-fast-checking` / `offensive-reporting`)
**Duration:** ~2–3 hours (one lab session, or two shorter sessions)

## Learning objectives

By the end of this lab, students will be able to:
1. Explain what an Insecure Direct Object Reference (IDOR) / broken access control flaw is
   and why it occurs.
2. Use a locally-run LLM, primed with a structured skill methodology, to generate testable
   hypotheses about where such a flaw might exist in a target application.
3. Distinguish an AI-generated hypothesis from a verified finding, and verify a hypothesis by
   reproducing it with an actual HTTP request.
4. Write a professional, evidence-backed finding report.
5. Operate entirely inside an authorized, isolated lab environment, and articulate why that
   boundary matters.

## Prerequisites

- Completed `docs/02-offline-installation.md`.
- `ollama list` shows `redlab-idor` and `redlab-webtriage`.
- `docker compose up -d` run from the repo root; `http://127.0.0.1:3000` loads in a browser.
- A way to send raw HTTP requests: `curl`, the browser's Network tab / dev tools, and/or
  OWASP ZAP as a proxy. No prior Juice Shop experience assumed.

## The relevant Claude-Red skill(s)

- `Skills/web/offensive-idor/SKILL.md` — IDOR / broken access control methodology
  (enumeration patterns, authorization-boundary testing, how to tell a true positive from a
  coincidence). This is the primary skill for this lab.
- `Skills/utility/offensive-fast-checking/SKILL.md` and
  `Skills/utility/offensive-reporting/SKILL.md` — a rapid-triage checklist and a reporting
  structure, loaded together into `redlab-webtriage` for the recon and write-up phases.

## Environment setup (isolated, reproducible)

```bash
docker compose up -d
docker compose logs -f juice-shop   # wait for "server listening on port 3000"
```
Open `http://127.0.0.1:3000`. Create a throwaway account from the Juice Shop UI (any
fictitious email/password — this is a local, disposable instance; do not reuse real
credentials). This is the **only** target for this lab. Nothing else is in scope.

Reset between attempts if needed: `docker compose down && docker compose up -d` (data does
not persist across a `down`, giving every student/group a clean instance).

## Step-by-step procedure

### Phase 1 — Baseline recon (15–20 min)

1. Browse the app as a normal user: register, log in, view "your" basket, orders, and
   profile/account pages. Note every URL that includes an ID, a username, or an order number
   (e.g. `/rest/basket/<id>`, `/rest/user/whoami`, `/profile`).
2. Open a terminal with `redlab-webtriage`:
   ```bash
   ollama run redlab-webtriage
   ```
3. Prompt:
   ```
   I'm doing an authorized assessment of a local OWASP Juice Shop instance
   (http://127.0.0.1:3000) for a university lab. I've logged in as a normal user and
   found these endpoints that reference an ID: [paste your list]. Using a fast-checking
   methodology, what should I check first, and why?
   ```
4. Record the model's suggested priority order in your lab notebook (not yet verified —
   these are hypotheses).

### Phase 2 — AI-assisted hypothesis generation (30–40 min)

1. Switch to the IDOR-focused model:
   ```bash
   ollama run redlab-idor
   ```
2. For each candidate endpoint from Phase 1, ask something like:
   ```
   Endpoint: GET /rest/basket/6 (my basket ID, as a logged-in user, is 6).
   What's the IDOR hypothesis here, what would I change to test it, and what response
   would confirm vs. rule it out?
   ```
3. The model should give you: (a) what to change in the request, (b) what a *positive*
   result looks like, (c) what a *negative* result looks like, (d) what else could explain a
   positive-looking result that isn't actually the flaw (e.g. a shared/public resource by
   design). Write all four down per endpoint — this is the "hypothesis," not a finding yet.

### Phase 3 — Verification (40–60 min)

For every hypothesis from Phase 2, **reproduce it yourself** with a tool you control:

```bash
# Example shape only — use the ID values your own session actually has.
curl -s http://127.0.0.1:3000/rest/basket/5 -H "Authorization: Bearer <your token>"
```
or drive the same request through the browser's Network tab / replay it in OWASP ZAP.

- A hypothesis is **verified** only when you have the actual request and response in front
  of you, and the response demonstrates access to data/functionality that should not be
  reachable from your account.
- A hypothesis is **refuted** when the server correctly denies it (403/404, or the resource
  is legitimately public). Record refutations too — they show your process, not just your
  hits.
- If the model's suggested exact parameter name or path is wrong but the *idea* was sound
  (e.g. "the basket ID is probably sequential and guessable" turned out right even though
  the first ID it guessed wasn't yours), note that explicitly in your report. This is exactly
  the hypothesis-vs-verified-finding distinction the rubric grades on.

### Phase 4 — Evidence collection and reporting (30 min)

For each verified finding, capture:
- The exact request (method, URL, headers, body) and response (status, body, relevant
  headers) — screenshot or copy/paste text, not a description.
- Which account/session made the request vs. whose data was exposed.
- Steps to reproduce from a clean Juice Shop instance.

Then prompt `redlab-webtriage`:
```
Using a standard reporting structure, help me turn this verified finding into a
professional report section: [paste your evidence]. Keep it accurate to what I actually
observed — don't add severity claims I haven't justified.
```
Edit the model's draft — fix anything it overstates or gets wrong. You are the author; the
model is a drafting aid.

## Expected results

A default Juice Shop instance contains multiple broken-access-control / IDOR-style
challenges (e.g. around baskets, feedback, and user data). Exact behavior can vary by Juice
Shop version — if a specific endpoint doesn't behave as expected, that's a legitimate lab
outcome to report as a refuted hypothesis, not a failure of the exercise.

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `http://127.0.0.1:3000` doesn't load | `docker compose ps` — is the container running? Check `docker compose logs juice-shop` for startup errors. |
| `ollama run redlab-idor` says model not found | Re-run the `skill_loader.py` command from the installation guide; confirm with `ollama list`. |
| Model responses are very slow | Expected on CPU-only 8–16 GB machines with the 7B+ tier; switch to the 1.5b/3b tier, or be patient — see hardware tiers in `01-architecture.md`. |
| curl requests all return 401 | You need the session token/cookie from your logged-in browser session — copy it from dev tools (Application/Storage tab, or the `Authorization` header on an authenticated request in the Network tab). |

## Student deliverables

1. Lab notebook (or `docs/worksheets/lab1-worksheet.md`, filled in) with: endpoints examined,
   AI hypotheses, verification method and result for each.
2. A short written finding report (one verified finding minimum) with evidence attached.
3. A one-paragraph reflection: where did the AI's hypothesis help, where was it wrong or
   generic, and how did you tell the difference between a hypothesis and a verified finding?

## Grading rubric (100 pts)

| Criterion | Points |
|---|---|
| Baseline recon documented (endpoints, normal behavior) | 10 |
| At least 3 AI-generated hypotheses recorded with the model's stated confirm/deny criteria | 20 |
| Each hypothesis has an explicit verification attempt (curl/ZAP/browser), not just "I asked the AI again" | 25 |
| At least one finding is genuinely verified with raw request/response evidence | 20 |
| Report is accurate — no unverified claims stated as fact, severity is justified | 15 |
| Reflection clearly distinguishes AI hypothesis from verified finding and gives a concrete example of each | 10 |
