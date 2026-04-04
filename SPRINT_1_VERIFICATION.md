# Sprint 1 Checkpoints Verification & Fixes

Below is the complete verification checklist for the BharatVoice KYC Platform Sprint 1 scaffolding, along with the technical fixes applied to get the local environment running smoothly on Windows.

## ✅ Verification Checklist

- [x] **`docker compose up` runs without errors**
- [x] **`GET localhost:8000/api/health` returns `{"database": "connected", "redis": "connected"}`**
- [x] **`localhost:3000` loads the Landing page**
- [x] **PostgreSQL `users` table exists** (Ran migration manually)
- [x] **All placeholder service files exist** (`apps/backend/app/services/voice/`)
- [x] **`pnpm install` completed successfully from monorepo root**
- [x] **`turbo.json` pipeline is working** (`pnpm build` runs without error)

---

## 🛠️ Issues Found & How They Were Fixed

During verification, a few configuration mismatches were identified and resolved to ensure cross-platform compatibility:

### 1. Missing Database Driver in Backend
**Issue:** The FastAPI backend failed to start because `SQLAlchemy` was attempting to execute synchronous table definitions using the `postgresql://` URI scheme but lacked the required database driver (`psycopg2`).
**Fix:** Appended `psycopg2-binary==2.9.9` to `apps/backend/requirements.txt`. This allows SQLAlchemy to successfully build the schema while `asyncpg` seamlessly handles the asynchronous app connections.

### 2. Frontend Docker Build Context Error
**Issue:** Running `docker compose up --build` crashed on the `frontend` service because the monorepo workspace `packages/` directory was not found. The Docker `context` was mistakenly set to `./apps/frontend`, making Docker blind to the root directory.
**Fix:** Updated `docker-compose.yml` and `docker-compose.prod.yml` to set the `context` to the root `.` and point explicitly to the Dockerfile via `dockerfile: ./apps/frontend/Dockerfile`.

### 3. Missing Local Environment Variables
**Issue:** `docker compose` warned about missing PostgreSQL variables (`POSTGRES_USER`, etc.).
**Fix:** Created `.env` from the `.env.example` template to properly inject the variables into the containers.

### 4. `make migrate` Failure on Windows
**Issue:** The user is on Windows PowerShell, which does not have the macOS/Linux `make` command installed natively. As a result, the `make migrate` shortcut failed.
**Fix:** Manually injected the migration blueprint directly into the PostgreSQL container using the following command to bypass `make`:
```powershell
cmd.exe /c "docker compose exec -T db psql -U postgres -d bharatvoice < apps\backend\migrations\001_initial.sql"
```

The environment is now successfully verified, stable, and running!
