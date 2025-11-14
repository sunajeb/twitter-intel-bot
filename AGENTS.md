# Repository Guidelines

## Project Structure & Module Organization
- Root Python modules: `twitter_monitor.py`, `daily_complete_scan.py`, `daily_summary.py`, `linkedin_monitor.py`, `twitter_api_io_client.py`.
- CI workflows: `.github/workflows/*` (daily + test trackers).
- Config and data: `config.json` (local only), `accounts*.txt`, `daily_intelligence.json`, `rotation_state.json`, `user_id_cache.json`.
- Tests and utilities: `test_*.py` scripts for targeted checks.

## Build, Test, and Development Commands
```bash
pip install -r requirements.txt               # Install deps
python twitter_monitor.py                      # Run daily analysis locally
python daily_complete_scan.py                  # One-pass scan (Slack summary)
python linkedin_monitor.py                     # LinkedIn daily analysis
python test_twitterapi_io.py                   # Verify TwitterAPI.io client
```
GitHub Actions: see `.github/workflows/daily-monitor.yml` (scheduled) and `test-twitter-tracker.yml` (manual test).

## Coding Style & Naming Conventions
- Python 3.9+, PEP 8, 4‑space indentation, UTF‑8.
- Functions/variables: `snake_case`. Modules: short, descriptive (e.g., `twitter_api_io_client.py`).
- Keep implementations minimal; prefer small, composable functions.
- Log errors clearly; do not swallow exceptions silently.

## Testing Guidelines
- Ad‑hoc test scripts live as `test_*.py`. Run directly with `python <file>`.
- Prefer deterministic tests that avoid external calls; if needed, mock HTTP.
- When adding tests, mirror existing naming and place in repo root or alongside modules.

## Commit & Pull Request Guidelines
- Commit messages: imperative, concise, scoped (e.g., "Add TwitterAPI.io client error handling").
- Use `[skip ci]` for state-only updates (e.g., `daily_intelligence.json`).
- PRs should include: purpose, summary of changes, verification steps (logs or Slack screenshot), and any config/secrets required.

## Security & Configuration Tips
- Never commit secrets. Local config via `config.json`; CI via repository secrets: `TWITTERAPI_IO_KEY`, `GEMINI_API_KEY`, `SLACK_WEBHOOK_URL` (and `SCRAPIN_API` for LinkedIn).
- Validate environment presence before network calls; fail fast with actionable messages.

## Architecture Overview
- Data sources: Twitter via TwitterAPI.io, LinkedIn via ScrapIn.
- Analysis: Google Gemini (2.x Flash).
- Output: Slack webhook with categorized, linked headlines.
- Tracked accounts configured in `twitter_accounts.txt` (`username:Company`).
