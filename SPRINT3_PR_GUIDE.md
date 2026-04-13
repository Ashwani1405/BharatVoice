# Sprint 3 — Pull Request Guide

## Merge Order
1. **PR-7 (`feat/sprint3-aadhaar-api`)** — Can operate independently.
2. **PR-8 (`feat/sprint3-ocr-engine`)** — Can operate independently.
3. **PR-9 (`feat/sprint3-face-match`)** — Can operate independently.
4. **PR-10 (`feat/sprint3-celery-tasks`)** — Must be merged LAST, as it wraps the services from PRs 7-9 into a unified background pipeline.

## PR Summary Table

| PR | Branch | Owner | Files Changed | Status |
|----|--------|-------|---------------|--------|
| **PR-7** | `feat/sprint3-aadhaar-api` | **TBD** | `app/services/kyc/aadhaar.py` | [ ] |
| **PR-8** | `feat/sprint3-ocr-engine` | **TBD** | `app/services/kyc/ocr.py`, `requirements.txt` | [ ] |
| **PR-9** | `feat/sprint3-face-match` | **TBD** | `app/services/kyc/kyc_match.py`, `requirements.txt` | [ ] |
| **PR-10** | `feat/sprint3-celery-tasks` | **TBD** | `celery_app.py`, `kyc_tasks.py`, `webhook_handler.py` | [ ] |

## Review Checklist (Applies to ALL PRs)
Before adding the "LGTM" stamp, ensure:
- [ ] No `npm` or `yarn` commands used anywhere (strictly `pnpm`).
- [ ] Absolutely no hardcoded API keys or plaintext secrets committed into tree.
- [ ] All Python functions have 100% rigorous type hints.
- [ ] All async functions gracefully `await`.
- [ ] `docker compose up --build` still safely boots after this PR.
