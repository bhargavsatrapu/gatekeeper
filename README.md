# Smart API Test Runner (FastAPI UI)

Simple FastAPI + Jinja2 UI that calls your existing functions in `backend_interface.py`:

- `__upload_swagger_document()`
- `__generate_testcases_for_every_endpoint()`
- `__run_only_positive_flow()`
- `__execute_all_test_cases_differnt_endpoint()`

No changes to your backend logic; this UI only invokes them.

## Requirements

- Python 3.10+
- pip
- `backend_interface.py` in project root with the functions above

Create a python virtual environment:
python -m venv .venv
.venv\Scripts\Activate.ps1 (powershell) 

Install dependencies:
pip install -r requirements.txt 
 
```bash
pip install fastapi uvicorn jinja2
```

(Plus any libraries your backend functions require.)

## Structure

```
SMARTAPI_NOFRAMEWORK/
├─ backend_interface.py
├─ main.py
├─ templates/
│  ├─ base.html
│  └─ index.html
└─ static/
   ├─ styles.css
   └─ app.js
```

The uploaded Swagger JSON is saved at the project root as `swagger.json`.

## Run

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://localhost:8000`.

## UI Tabs

- Swagger Upload
  - Upload Swagger/OpenAPI JSON → saves to `swagger.json` (root)
  - Calls `__upload_swagger_document()`
- Generate Testcases
  - Calls `__generate_testcases_for_every_endpoint()`
- Positive Tests
  - Calls `__run_only_positive_flow()`
- All Tests
  - Calls `__execute_all_test_cases_differnt_endpoint()`
- Latest Messages
  - Shows success banner after actions

## Routes

- `GET /` — render UI
- `POST /upload-swagger` — save to `BASE_DIR/swagger.json`, call upload function, redirect with message
- `POST /generate-testcases` — call generator, redirect with message
- `POST /run-positive` — run positive flow, redirect with message
- `POST /run-all-tests` — run all tests, redirect with message

## Notes

- Ensure `backend_interface.py` reads `swagger.json` from the root if needed.
- If any function requires configuration or DB connectivity, keep that logic in your backend.

## Troubleshooting

- ImportError for `backend_interface`: ensure the file exists and function names match exactly.
- Permission error writing `swagger.json`: run with proper permissions or change path in `main.py`.
- Missing libs: install the packages your backend functions depend on.

## Customize

- Styles: `static/styles.css`
- Tabs/HTML: `templates/index.html` and `templates/base.html`
- Routes: `main.py`
