# Lab 2: AI-Assisted Vulnerability Analysis and Remediation

**Target:** `lab2/vuln_app/app.py` — a small, original, intentionally vulnerable local Flask
app included in this kit (SQL injection, CWE-89).
**AI model:** `redlab-sqli` (built below, using Claude-Red's `offensive-sqli` skill)
**Duration:** ~2 hours

## Learning objectives

By the end of this lab, students will be able to:
1. Read application source code and identify a SQL injection vulnerability and explain its
   root cause (untrusted input reaching a query as code, not data).
2. Use a local AI model, primed with a structured skill methodology, to help explain the
   vulnerability and propose a fix.
3. Safely and non-destructively demonstrate the issue against a local-only instance.
4. Implement a code fix and a regression test that proves the fix holds.
5. Verify the fix does not break legitimate functionality.

## Prerequisites

- Completed `docs/02-offline-installation.md`, including the Lab 2 virtualenv
  (`lab2/vuln_app/.venv`) with `flask` and `pytest` installed.
- Build the skill model (if not already done in installation):
  ```bash
  python tools/skill_loader.py \
    --skill ../claude-red-skills/Skills/web/offensive-sqli/SKILL.md \
    --name redlab-sqli --base qwen2.5-coder:7b
  ```

## The relevant Claude-Red skill

`Skills/web/offensive-sqli/SKILL.md` — SQL injection methodology (identifying injectable
parameters, error-based vs. blind indicators, why parameterization closes the class of bug).
This is the primary skill for this lab.

## Step-by-step procedure

### Phase 1 — Read and hypothesize (20 min)

1. Open `lab2/vuln_app/app.py` and read the `/user` route **without** running it yet.
2. Start the model:
   ```bash
   ollama run redlab-sqli
   ```
3. Paste the route's code (just that function) and ask:
   ```
   Here is a Flask route from a local training app I'm authorized to test.
   [paste the get_user() function from app.py]
   Is there a SQL injection vulnerability here? Explain exactly why, what input would
   demonstrate it, and what the fix should be. This is for a lab exercise — I will verify
   everything myself before treating it as confirmed.
   ```
4. Record the model's explanation and its proposed payload as a **hypothesis** — you haven't
   run anything yet.

### Phase 2 — Controlled demonstration (20–30 min)

```bash
cd lab2/vuln_app
.venv\Scripts\activate       # or: source .venv/bin/activate
python app.py                 # binds to 127.0.0.1:5000 ONLY
```
In a second terminal:
```bash
curl "http://127.0.0.1:5000/user?username=alice"
curl "http://127.0.0.1:5000/user?username=' OR '1'='1"
```
- The first call should return only Alice.
- The second call, if the model's hypothesis is correct, returns **every** user, including
  `admin` — more data than a lookup for one named user should ever return. This is your
  controlled, local, non-destructive demonstration: no data is modified or deleted, only a
  `SELECT` boundary is bypassed.

Capture both request/response pairs as evidence (copy/paste or screenshot).

### Phase 3 — Propose and apply a fix (30 min)

1. Ask the model:
   ```
   I confirmed the injection: [paste your curl evidence]. Show me a parameterized-query
   fix for this exact route, and explain why it closes this specific injection.
   ```
2. Compare the model's suggested fix with `lab2/vuln_app/app_fixed.py` (already included in
   this kit as a reference — don't look at it until after you've written your own, then
   compare). The core idea in both should be: bind `username` as a parameter
   (`execute(query, (username,))`), never format it into the SQL string.
3. Edit your own copy of `app.py` (or work directly against `app_fixed.py`) to apply the fix
   if you haven't already matched it.

### Phase 4 — Regression test and verification (30 min)

1. Run the included regression test suite:
   ```bash
   cd ../..        # repo root
   pytest lab2/tests/test_security_regression.py -v
   ```
   Read `lab2/tests/test_security_regression.py`. Note what each test proves:
   - `test_vulnerable_app_leaks_all_users_via_injection` — documents the bug against `app.py`.
   - `test_fixed_app_blocks_the_same_injection` — the actual regression test: the same
     payload must return zero rows against `app_fixed.py`.
   - `test_fixed_app_normal_lookup_still_works` — the fix must not break legitimate use.
2. **Write one additional test of your own** targeting a variant payload (e.g.
   `"bob' --"` or a UNION-based attempt) and confirm it also fails against `app.py` and is
   blocked by `app_fixed.py`. This is the deliverable that proves you understand the fix,
   not just that you can run an existing test file.
3. Re-run `pytest` and confirm everything passes, including your new test.

## Expected results

- `app.py` with payload `' OR '1'='1`: returns 3 users (alice, bob, admin) for a request that
  named only one username.
- `app_fixed.py` with the same payload: returns `[]` (no user literally named
  `' OR '1'='1`).
- `pytest lab2/tests/test_security_regression.py -v`: 5/5 passing against the apps as shipped
  in this kit (verified while building this guide); 6/6 once you've added your own test.

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `ModuleNotFoundError: flask` | Activate the venv (`.venv\Scripts\activate`) before running `python app.py` or `pytest`. |
| Port 5000 already in use | Something else is bound to it (common on macOS with AirPlay Receiver) — either stop that service or change the port argument in `app.run(...)`. |
| `pytest` can't find the test file | Run it from the repo root, with the path exactly as shown (`lab2/tests/test_security_regression.py`). |
| Your added test passes against `app.py` too (i.e. doesn't demonstrate the bug) | Your payload probably isn't actually changing the query logic — check that it includes an unterminated quote plus a tautology (`' OR '1'='1`) or a comment terminator (`' --`), not just a weird-looking string. |

## Student deliverables

1. Your Phase 1 hypothesis notes (model's explanation + proposed payload, before you ran
   anything).
2. Evidence from Phase 2 (both curl calls, request + response).
3. Your fixed `app.py` (or confirmation you're using `app_fixed.py`) plus a short explanation,
   in your own words, of why the fix works.
4. Your added regression test (diff or new test function) and a `pytest` run showing it pass.
5. A one-paragraph reflection comparing the model's proposed fix to the reference fix: did
   they match? If not, was the model's version still correct?

## Grading rubric (100 pts)

| Criterion | Points |
|---|---|
| Correctly identifies the vulnerability and root cause, in their own words, before/independent of just quoting the model | 20 |
| Controlled demonstration includes real request/response evidence, non-destructive | 20 |
| Applied fix uses parameterized queries correctly (not string-escaping or blocklist patching) | 20 |
| Added regression test correctly fails against the vulnerable app and passes against the fixed app | 25 |
| Reflection shows understanding of why the fix works, not just that tests pass | 15 |
