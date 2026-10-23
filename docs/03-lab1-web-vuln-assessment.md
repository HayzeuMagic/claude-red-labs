# Lab 1: AI-Assisted Web Vulnerability Assessment

**Target:** OWASP Juice Shop (local Docker container, `127.0.0.1:3000`)
**AI model:** `redlab-idor` (Qwen2.5-Coder 7B + Claude-Red's `offensive-idor` skill) and
`redlab-webtriage` (+ `offensive-fast-checking` / `offensive-reporting`)
**Duration:** ~2–3 hours (one lab session, or two shorter sessions)

## Learning Objectives

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
- A way to send raw HTTP requests: `curl`, the browser's Network tab / dev tools, and/or
  OWASP ZAP as a proxy. No prior Juice Shop experience assumed.

## The Relevant Claude-Red Skill(s)

- `Skills/web/offensive-idor/SKILL.md` — IDOR / broken access control methodology
  (enumeration patterns, authorization-boundary testing, how to tell a true positive from a
  coincidence). This is the primary skill for this lab.
- `Skills/utility/offensive-fast-checking/SKILL.md` and
  `Skills/utility/offensive-reporting/SKILL.md` — a rapid-triage checklist and a reporting
  structure, loaded together into `redlab-webtriage` for the recon and write-up phases.

> **Important:** this lab is confined to the Juice Shop container you start below. Do not
> run any command, payload, or AI suggestion from this lab against any other host.

---

# Step 1: Start the Lab Environment

### 1.1 Bring the target up

```bash
docker compose up -d
docker compose logs -f juice-shop
```
Wait for the log line:
```
info: Server listening on port 3000
```
Then `Ctrl+C` to stop following logs (the container keeps running).

### 1.2 Open it

Go to `http://127.0.0.1:3000` in a browser. You should see the Juice Shop storefront.

### 1.3 Create a throwaway account

Use the **Account** menu → **Login** → **Not yet a customer?** and register with any
fictitious email/password. This is a disposable local instance — never reuse a real password
here.

> **Note:** to reset to a clean instance for a new attempt or a new group, run:
> ```bash
> docker compose down && docker compose up -d
> ```
> Juice Shop does not persist data across a `down`, so this always gives a fresh target.

---

# Step 2: Baseline Recon (15–20 min)

### 2.1 Browse as a normal user

Visit your basket, your orders, and your profile/account pages. Note every URL that includes
an ID, a username, or an order number (e.g. `/rest/basket/<id>`, `/rest/user/whoami`,
`/profile`). Write these down — you'll need them in Step 3.

### 2.2 Ask the triage model to prioritize them

```bash
ollama run redlab-webtriage
```
**Prompt:**
```
I'm doing an authorized assessment of a local OWASP Juice Shop instance
(http://127.0.0.1:3000) for a university lab. I've logged in as a normal user and
found these endpoints that reference an ID: [paste your list]. Using a fast-checking
methodology, what should I check first, and why?
```

### 2.3 Record the result

Write the model's suggested priority order into your lab notebook (or
`docs/worksheets/lab1-worksheet.md`). **This is a hypothesis, not a finding** — nothing has
been verified yet.

---

# Step 3: AI-Assisted Hypothesis Generation (30–40 min)

### 3.1 Switch to the IDOR-focused model

```bash
ollama run redlab-idor
```

### 3.2 Ask about each candidate endpoint

**Prompt (repeat per endpoint):**
```
Endpoint: GET /rest/basket/6 (my basket ID, as a logged-in user, is 6).
What's the IDOR hypothesis here, what would I change to test it, and what response
would confirm vs. rule it out?
```

### 3.3 Record four things per endpoint

1. What to change in the request.
2. What a **positive** result looks like.
3. What a **negative** result looks like.
4. What else could explain a positive-looking result that isn't actually the flaw (e.g. a
   resource that's legitimately public by design).

---

# Step 4: Verification (40–60 min)

> **Important:** every hypothesis from Step 3 must be reproduced by **you**, with a tool you
> control, before it counts as anything more than a guess.

### 4.1 Reproduce each hypothesis

```bash
curl -s http://127.0.0.1:3000/rest/basket/5 -H "Authorization: Bearer <your token>"
```
or drive the same request through the browser's Network tab, or replay it in OWASP ZAP.

### 4.2 Classify the result

- **Verified** — you have the actual request and response in front of you, and the response
  demonstrates access to data/functionality that should not be reachable from your account.
- **Refuted** — the server correctly denied it (403/404), or the resource turned out to be
  legitimately public. Record these too; they show your process, not just your hits.

> **Note:** if the model's exact parameter name or path was wrong but the underlying idea was
> sound (e.g. "the basket ID is probably sequential and guessable" turned out right even
> though the first guessed ID wasn't yours), say so explicitly in your report. This is exactly
> the hypothesis-vs-verified-finding distinction the rubric grades on.

---

# Step 5: Evidence Collection and Reporting (30 min)

### 5.1 Capture evidence for each verified finding

- The exact request (method, URL, headers, body) and response (status, body, relevant
  headers) — a screenshot or a copy/paste, not a description.
- Which account/session made the request vs. whose data was exposed.
- Steps to reproduce from a clean Juice Shop instance.

### 5.2 Draft the report with the triage model

```bash
ollama run redlab-webtriage
```
**Prompt:**
```
Using a standard reporting structure, help me turn this verified finding into a
professional report section: [paste your evidence]. Keep it accurate to what I actually
observed — don't add severity claims I haven't justified.
```

### 5.3 Edit it

You are the author; the model is a drafting aid. Fix anything it overstates, generalizes, or
gets wrong before you submit it.

---

## Expected Results

A default Juice Shop instance contains multiple broken-access-control / IDOR-style
challenges (e.g. around baskets, feedback, and user data). Exact behavior can vary by Juice
Shop version — if a specific endpoint doesn't behave as expected, that's a legitimate lab
outcome to report as a refuted hypothesis, not a failure of the exercise.

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `http://127.0.0.1:3000` doesn't load | `docker compose ps` — is the container running? Check `docker compose logs juice-shop` for startup errors. |
| `ollama run redlab-idor` says model not found | Re-run the matching `skill_loader.py` command from Step 5 of the installation guide; confirm with `ollama list`. |
| Model responses are very slow | Expected on CPU-only 8–16 GB machines with the 7B+ tier; switch to the 1.5b/3b tier, or be patient — see hardware tiers in `01-architecture.md`. |
| curl requests all return 401 | You need the session token/cookie from your logged-in browser session — copy it from dev tools (Application/Storage tab, or the `Authorization` header on an authenticated request in the Network tab). |

## Student Deliverables

1. Lab notebook (or `docs/worksheets/lab1-worksheet.md`, filled in) with: endpoints examined,
   AI hypotheses, verification method and result for each.
2. A short written finding report (one verified finding minimum) with evidence attached.
3. A one-paragraph reflection: where did the AI's hypothesis help, where was it wrong or
   generic, and how did you tell the difference between a hypothesis and a verified finding?

## Grading Rubric (100 pts)

| Criterion | Points |
|---|---|
| Baseline recon documented (endpoints, normal behavior) | 10 |
| At least 3 AI-generated hypotheses recorded with the model's stated confirm/deny criteria | 20 |
| Each hypothesis has an explicit verification attempt (curl/ZAP/browser), not just "I asked the AI again" | 25 |
| At least one finding is genuinely verified with raw request/response evidence | 20 |
| Report is accurate — no unverified claims stated as fact, severity is justified | 15 |
| Reflection clearly distinguishes AI hypothesis from verified finding and gives a concrete example of each | 10 |
