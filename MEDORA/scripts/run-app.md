# Run MEDORA for real-time UI testing

## 1. Backend (from repo root or MEDORA/)

```bash
cd MEDORA/backend
# If you use a venv: source .venv/bin/activate  (or source venv/bin/activate)
pip install -r requirements.txt   # once
export PYTHONPATH=.
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Or with `python -m` if `uvicorn` isn’t on PATH:

```bash
cd MEDORA/backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Leave this terminal open. You should see: `Uvicorn running on http://127.0.0.1:8000`.

## 2. Frontend

In a **second terminal**:

```bash
cd MEDORA/frontend
npm install   # once
npm run dev
```

Note the URL (e.g. `http://localhost:5173` or another port if 5173 is in use).

## 3. Test Diagnostics in the UI

1. Open the frontend URL in your browser.
2. In the sidebar, click **Diagnostics** (or go to `/diagnostic`).
3. Optional: add context in the message (e.g. “Chest X-ray, 45-year-old male, cough”).
4. **Upload a medical image** (X-ray, CT, MRI, fundus, etc.) using the attachment/upload in the chat input.
5. Send. The app will call the diagnostic agent, run ACR report generation, and show the report plus an inline PDF if available.

**Backend .env:** Ensure `MEDORA/backend/.env` has a valid `GEMINI_API_KEY` for image analysis and report generation.
