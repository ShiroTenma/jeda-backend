# JEDA Backend

FastAPI backend untuk prototype JEDA (Digital Wellness & Behavioral Interception System).

## Requirements

- Python 3.11+
- uv (package manager)
- Tailscale (untuk koneksi Android-laptop)

## Setup

1. Clone repository
2. Copy environment template:
   ```bash
   cp .env.example .env
   ```
3. Generate secure backend token:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   Paste hasil ke `.env` di `BACKEND_TOKEN`

## Development

Install dependencies dan run tests:

```bash
uv run pytest
```

Run development server:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Server akan berjalan di `http://0.0.0.0:8000`

## Tailscale Setup

1. Install Tailscale di laptop dan HP
2. Login dengan akun yang sama di kedua device
3. Dapatkan Tailscale IP laptop:
   ```bash
   # Windows PowerShell
   tailscale ip -4
   ```
4. Dari HP, akses: `http://<tailscale-ip>:8000/health`

Expected response:
```json
{
  "status": "ok",
  "service": "jeda-backend",
  "version": "0.1.0"
}
```

Panduan lengkap: `../JEDA-app/docs/SETUP_TAILSCALE.md`

## API Endpoints

### Public

- `GET /health` - Service health check

### Protected (require `X-Backend-Token` header)

- `POST /api/analyze-frame` - Visual frame analysis (M5+)
- `POST /api/calculate-fds` - FDS calculation (M2+)
- `POST /api/intervention` - AI intervention message (M7+)

## Project Structure

```
jeda-backend/
├── app/
│   ├── main.py           # FastAPI app dan routes
│   ├── core/
│   │   ├── config.py     # Centralized settings
│   │   └── security.py   # Token authentication
│   ├── services/
│   │   ├── fds.py        # FDS calculation
│   │   ├── rrs.py        # RRS calculation
│   │   └── inference.py  # ONNX inference
│   └── schemas/          # Pydantic models
├── tests/                # Pytest tests
├── .env                  # Local config (gitignored)
└── pyproject.toml        # Dependencies
```

## Testing

Run all tests:
```bash
uv run pytest -v
```

Run specific test:
```bash
uv run pytest tests/test_health.py -v
```

## Milestones

- **M0** (current): Health endpoint + Tailscale connectivity ✓
- **M1**: Android monitoring foundation
- **M2**: FDS behavioral sensing
- **M5**: Visual ONNX inference
- **M6**: RRS risk aggregation
- **M7**: OpenRouter AI intervention
- **M8**: Integration testing

## Notes

- Backend hanya untuk prototype akademik, bukan production-ready
- Bind ke `0.0.0.0` agar accessible via Tailscale
- Token auth sederhana; cukup untuk prototype local
- Frame tidak disimpan permanen (privacy constraint)
