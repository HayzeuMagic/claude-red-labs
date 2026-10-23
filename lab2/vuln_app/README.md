# Lab 2 target app

Two Flask apps, same schema and data, for a before/after comparison:

- `app.py` — **vulnerable** (SQL injection via string-built query). Runs on port 5000.
- `app_fixed.py` — **fixed** (parameterized query). Runs on port 5001.

## Run

**RUN IN:** Windows PowerShell — Normal User
**Directory:** `lab2\vuln_app`

```powershell
cd lab2\vuln_app
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```
Open a second PowerShell terminal, activate the same venv the same way, and optionally run
`python app_fixed.py` there for a side-by-side comparison.

**Activation differs by shell — not interchangeable:**
- PowerShell: `.venv\Scripts\Activate.ps1`
- Command Prompt (CMD): `.venv\Scripts\activate.bat`
- macOS/Linux: `source .venv/bin/activate`

Both apps bind to `127.0.0.1` only. Stop with `Ctrl+C`.

## Manual smoke test

**RUN IN:** Windows PowerShell — Normal User, in a separate terminal from the running app(s)

```powershell
curl.exe "http://127.0.0.1:5000/user?username=alice"
curl.exe "http://127.0.0.1:5000/user?username=' OR '1'='1"
```
Use `curl.exe` explicitly, not bare `curl` — in PowerShell, plain `curl` is an alias for
`Invoke-WebRequest`, which behaves differently from real curl. In Command Prompt, plain
`curl` is already the real binary.

The second request returns every user (including `admin`) from the vulnerable app, and an
empty list from the fixed app on port 5001.
