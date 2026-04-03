# HackBLR — BharatVoice KYC Platform

![HackBLR 2026](https://img.shields.io/badge/HackBLR-2026-blue)
![Status](https://img.shields.io/badge/Status-Sprint_1_Complete-brightgreen)

BharatVoice is a voice-first financial inclusion platform for rural Indian users, enabling quick, seamless onboarding and transactions by Voice.

## Architecture

```
           [ User via Call ]
                  |
             (VAPI Phone)
                  |
         [ FastAPI Backend ] <---> [ Redis (Celery + Cache) ]
         /        |        \                                
[ Postgres ] [ Qdrant ] [ Worker Nodes ] -> (External APIs: Razorpay, Aadhaar)
```

## Prerequisites
- Docker + Docker Compose
- Node.js 18+
- pnpm 9+ (`corepack enable && corepack prepare pnpm@9.0.0 --activate`)
- Python 3.11+ (local development only, not required if using Docker exclusively)

> **NOTE:** Do NOT use `npm` or `yarn`. This monorepo strictly uses `pnpm`.

## Quick Start
1. `git clone <repo_url>`
2. `corepack enable`
3. `pnpm install`
4. `cp .env.example .env` (fill in your API keys)
5. `make up`
6. Open http://localhost:3000 to see the frontend
7. API Swagger docs at http://localhost:8000/docs
8. To run migrations: `make migrate`

## Turborepo Workflow
- `pnpm dev`: Runs `turbo run dev` to start all apps in development mode.
- `pnpm build`: Efficiently builds the packages with caching via Turborepo.
- `pnpm lint`: Runs `eslint` and other linters in the frontend/backend.
- `pnpm clean`: Wipes all `node_modules` and build directories.

## Project Sprints

| Sprint | Description | Status |
|---|---|---|
| Sprint 1 | Core Architecture & Scaffold | ✅ |
| Sprint 2 | Voice Infrastructure Setup | 🔄 |
| Sprint 3 | AI-driven KYC & OCR | 🔄 |
| Sprint 4 | Fraud Detection & Vectors | 🔄 |
| Sprint 5 | Payments & Ledgers | 🔄 |
| Sprint 6 | Auditing & Compliance | 🔄 |
| Sprint 7 | Final Polish & Handoff | 🔄 |

## Team
**Team Coral Reef**  
*MAIT Delhi*
