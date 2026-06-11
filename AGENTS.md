ma# AGENTS.md — MF Analytics Capstone

## Pipeline execution order (required)
1. `python scripts/data_cleaning.py` — reads `data/raw/*.csv`, writes cleaned CSVs to `data/processed/`
2. `python scripts/load_database.py` — reads `data/processed/*.csv`, writes SQLite DB to `data/db/bluestock_mf.db`

## Scripts status
- `data_cleaning.py` / `load_database.py` — actively used, working
- `etl_pipeline.py` — **PostgreSQL variant** (hardcoded local pgAdmin creds); not the main path
- `compute_metrics.py`, `recommender.py` — empty stubs (not yet implemented)
- `live_nav_fetch.py` — contains only a stale git message, not real code

## Database
- **SQLite** via `sqlalchemy` is the primary store (`data/db/bluestock_mf.db`)
- Schema is defined **inline** in `load_database.py` (DDL); `sql/schema.sql` and `sql/queries.sql` are empty
- Star schema: `dim_date`, `dim_fund` + `fact_nav`, `fact_transactions`, `fact_performance`, `fact_aum`
- SQLite `.gitignore`d under `data/`

## Dependencies
- `pandas`, `numpy`, `sqlalchemy`, `psycopg2-binary` (venv-installed; `requirements.txt` is empty)
- `plotly`, `jupyter` available for notebooks

## Project structure
| Path | Purpose |
|---|---|
| `scripts/` | Pipeline Python scripts |
| `notebooks/` | EDA + performance analytics (`.ipynb`) |
| `dashboard/` | Power BI report (`bluestock_mf.pbix`) |
| `reports/` | Final report PDF + presentation |
| `data/raw/` | Source CSVs (currently empty — populate before running) |
| `data/processed/` | Cleaned CSVs (pipeline output) |
| `data/db/` | SQLite database (pipeline output) |

## Conventions
- No tests, no linting/formatting config, no CI — raw scripts only
- Only `main` branch in use
- `.gitignore` excludes `data/`, `.venv/`, `__pycache__/`, `.ipynb_checkpoints/`
- `data_dictionary.md` and `requirements.txt` are empty placeholders
