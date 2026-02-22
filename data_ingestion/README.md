# Neon Data Loader

This folder contains a single-run loader that creates tables, truncates previous loaded data, and reloads all datasets into Neon PostgreSQL.

## Files
- `load_all_to_neon.py` — all-in-one schema + load script
- `download.csv` — purchase-side bond data
- `redemption.csv` — redemption-side bond data

## What the loader does
1. Creates required tables (if not already present)
2. Creates indexes (if not already present)
3. Truncates previously loaded model tables (`RESTART IDENTITY CASCADE`)
4. Loads raw CSV data into `download_bonds` and `redemption_bonds`
5. Populates derived tables:
   - `bond_master`
   - `bond_purchase_event`
   - `bond_redemption_event`
   - `entity`
   - `entity_alias`
   - `relationship_edge`

## Run
Use your Neon connection string as an environment variable:

```bash
NEON_DATABASE_URL='your_neon_url' .venv/bin/python load_all_to_neon.py
```

## Output
The script prints row counts for all model tables after load completion.

## Note
`risk_alert` and `risk_explanation` are created but intentionally left empty by this loader (for downstream scoring/inference jobs).
