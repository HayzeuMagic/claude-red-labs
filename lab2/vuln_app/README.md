# Lab 2 target app

Two Flask apps, same schema and data, for a before/after comparison:

- `app.py` — **vulnerable** (SQL injection via string-built query). Runs on port 5000.
- `app_fixed.py` — **fixed** (parameterized query). Runs on port 5001.

## Run

```bash
cd lab2/vuln_app
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
python app.py          # in one terminal
python app_fixed.py    # in another terminal, optional, for side-by-side comparison
```

Both bind to `127.0.0.1` only. Stop with Ctrl+C.

## Manual smoke test

```bash
curl "http://127.0.0.1:5000/user?username=alice"
curl "http://127.0.0.1:5000/user?username=' OR '1'='1"
```

The second request returns every user (including `admin`) from the vulnerable app, and an
empty list from the fixed app on port 5001.
