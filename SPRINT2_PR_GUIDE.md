# Sprint 2 — Pull Request Guide

## Merge Order
1. **PR-1 (`feat/sprint2-foundation`)** — Merge FIRST. This blocks all other PRs as it sets up configuration dependencies and global routing logic.
2. **PR-2 through PR-6** — Once PR-1 is firmly mounted on `main`, PRs 2-6 can be worked on concurrently and merged in any absolute order.

## PR Summary Table

| PR | Branch | Owner | Files Changed | Status |
|----|--------|-------|---------------|--------|
| **PR-1** | `feat/sprint2-foundation` | **Ashwani** | `session_manager.py`, `language_router.py`, `prompts/__init__.py`, `config.py`, `.env.example`, `Makefile` | [ ] |
| **PR-2** | `feat/sprint2-vapi-agent` | **Vikram Aditya Verma** | `vapi_client.py`, `agent_config.py`, `requirements.txt` | [ ] |
| **PR-3** | `feat/sprint2-stt-tts` | **Parth Garg** | `stt.py`, `tts.py`, `requirements.txt` | [ ] |
| **PR-4** | `feat/sprint2-webhook-routes` | **Yash Bahugunga** | `webhook_handler.py`, `routes.py` | [ ] |
| **PR-5** | `feat/sprint2-prompts` | **Ashwani** | `kyc_hindi.txt`, `kyc_english.txt` | [ ] |
| **PR-6** | `feat/sprint2-frontend-voice` | **Vikram Aditya Verma** | `Onboard.jsx`, `VoiceWaveform.jsx`, `TranscriptPanel.jsx`, `useVoice.js`, `package.json`, `constants.js` | [ ] |

## How Each Dev Sets Up Their Branch
Run these locally to carve out your slice of the pie:
```bash
git checkout main
git pull origin main
git checkout -b <branch-name>

# ... Make your code changes ...

git add .
git commit -m "feat(sprint2): <description>"
git push origin <branch-name>
# Open a PR on GitHub targeting the 'main' branch
```

## Environment Setup (Do this before starting any PR)
Before booting, please authenticate all your downstream vendors.
1. `cp .env.example .env`
2. Fill in: `GROQ_API_KEY`, `DEEPGRAM_API_KEY`, `ELEVENLABS_API_KEY`
3. Fill in: `VAPI_API_KEY`, `VAPI_WEB_TOKEN`, `VAPI_WEBHOOK_SECRET`
4. Fill in: `ELEVENLABS_VOICE_ID_HINDI`, `ELEVENLABS_VOICE_ID_ENGLISH`
5. `make up`
6. Verify your setup:
```bash
curl localhost:8000/api/health
# Should return -> {"database":"connected","redis":"connected"}
```

## PR-6 Local Dev Without Backend (Vikram's Warning Track)
Vikram can actively develop the frontend without waiting for PRs 2-4 to merge across the wire:
1. In `useVoice.js`: There is a mock hook `useMockVoice()` built specifically spanning `MOCK_SESSION_DATA`.
2. In `Onboard.jsx`: Just import `useMockVoice` instead of `useVoice` temporarily while scaffolding.
3. This allows seamless rendering of the whole UI, tailwind keyframes, and transcript panels with fake socket injections. 
4. Just remember to switch it back over to `useVoice` tightly nested before issuing your PR.

## Review Checklist (Applies to ALL PRs)
Before adding the "LGTM" stamp, ensure:
- [ ] No `npm` or `yarn` commands used anywhere (strictly `pnpm`).
- [ ] Absolutely no hardcoded API keys or plaintext secrets committed into tree.
- [ ] All Python functions have 100% rigorous type hints.
- [ ] All async functions gracefully `await` (No synchronously blocking I/O calls to the thread pool).
- [ ] Error states handled cleanly — no unhandled promise rejections on the web layer.
- [ ] Python imports strictly use absolute origin paths (`app.*`), nothing relative.
- [ ] `docker compose up --build` still safely boots after this PR.
