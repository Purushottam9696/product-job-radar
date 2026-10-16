# ProductPulse — 100% Free Automated Product Company Job Radar

An open-source, zero-cost job tracker that monitors real-time engineering openings across 120 top product companies in India and globally.

## How It Works (100% Free Tier Architecture)
1. **GitHub Actions (`.github/workflows/sync_jobs.yml`)** runs on a scheduled cron every 6 hours.
2. **`fetch_jobs.py`** queries open public ATS endpoints (Greenhouse, Lever, etc.) keylessly.
3. The script commits the refreshed `jobs.json` back to your repo.
4. **GitHub Pages** serves `index.html` and `jobs.json` globally with zero hosting fees.
