# Generations Covered – Backend API

REST API that powers the **Generations Covered** financial-assistance application.

- Pure Python (standard library only – no external dependencies)
- CORS enabled for any website frontend
- Ready to deploy on **Render**, Railway, Fly.io, etc.

---

## Quick Start (Local)

```bash
# From the project root
python -m api.server
```

Server starts on `http://0.0.0.0:8000`

---

## Deploy on Render (Recommended)

### Option A – One-click with Blueprint

1. Push this repository to GitHub
2. Go to [https://render.com](https://render.com) → **New** → **Blueprint**
3. Connect the repo
4. Render will read `render.yaml` and create the service automatically

### Option B – Manual Web Service

1. Push this repo to GitHub
2. Render → **New** → **Web Service**
3. Connect the repository
4. Settings:

   | Setting          | Value                          |
   |------------------|--------------------------------|
   | Runtime          | Python 3                       |
   | Build Command    | `pip install -r requirements.txt` |
   | Start Command    | `python -m api.server`         |
   | Instance Type    | Free                           |

5. Click **Create Web Service**

Your public URL will look like:
```
https://generations-covered-api.onrender.com
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/health` | Health check |
| `GET`  | `/api/v1/fpl` | 2026 Federal Poverty Level table |
| `GET`  | `/api/v1/hospitals` | List hospitals |
| `GET`  | `/api/v1/hospitals/{id}` | Full hospital policy |
| `GET`  | `/api/v1/hospitals/{id}/documents` | Required documents checklist |
| `GET`  | `/api/v1/hospitals/{id}/form-mapping` | PDF form field mapping |
| `POST` | `/api/v1/eligibility` | **Main eligibility calculator** |
| `GET`  | `/api/v1/personas` | Demo personas |
| `GET`  | `/api/v1/personas/{id}` | Single persona |

### Example – Check Eligibility

```bash
curl -X POST https://YOUR-URL.onrender.com/api/v1/eligibility \
  -H "Content-Type: application/json" \
  -d '{
    "hospital_id": "piedmont",
    "household_size": 3,
    "annual_income": 28400,
    "uninsured": true,
    "georgia_resident": true,
    "bill_amount": 8750
  }'
```

### Frontend JavaScript Example

```javascript
const res = await fetch("https://YOUR-URL.onrender.com/api/v1/eligibility", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    hospital_id: "piedmont",
    household_size: 3,
    annual_income: 28400,
    uninsured: true,
    georgia_resident: true,
    bill_amount: 8750
  })
});
const data = await res.json();
console.log(data);
```

---

## Project Structure

```
generations-covered-api/
├── api/
│   ├── __init__.py
│   ├── hospital_service.py   # Eligibility engine + data loading
│   ├── server.py             # HTTP server (stdlib)
│   └── test_eligibility.py
├── hospital_data.json
├── required_documents.json
├── form_field_mapping.json
├── personas.json
├── policy_date_verification_log.json
├── requirements.txt
├── render.yaml
└── README.md
```

---

## Design Rules (from the proposal)

1. Eligibility is computed **only** from `hospital_data.json`.
2. Every number traces back to a hospital’s published policy PDF.
3. Adding a new hospital = adding one entry to the data file.
