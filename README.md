# DataCheck

A researcher uploads a measurement file, a quality check runs, and the report comes back, behind a login.
This is the demo backend for the Day 2 training ("from git clone to a running backend"): small enough to read
in one sitting, complete enough to run in a container.

## Run it

```
uv sync                                    # install exactly what uv.lock says
cp .env.example .env                       # local settings (AUTH_MODE=off: everyone is a researcher)
uv run alembic upgrade head                # create the tables
uv run uvicorn app.main:create_app --factory --reload     # the API, then open http://localhost:8000/docs
uv run python -m app.worker                # the worker, in a SECOND terminal

uv run pytest                              # the safety net
uv run ruff check . ; uv run ty check      # lint and types
```

Or the whole stack (Postgres, API with migrations, two workers) in containers:

```
docker compose up --build -d --scale worker=2      # API_PORT=8010 if port 8000 is taken
docker compose down -v                             # stop and wipe the database
```

Try it with the files in `samples/`: `bench-run.csv` (clean), `bench-run-gaps.csv` (missing values and gaps),
`bench-run-no-time.csv` (refused with a 400).

## The map

| Where | What it holds | Part of the day |
|---|---|---|
| `pyproject.toml`, `uv.lock`, `.python-version` | what we ask for, what we got, which Python | 1 uv |
| `src/app/core/` | settings (fail fast), auth, feature flags | 1 and 7 |
| `src/app/routers/` | HTTP only, plus `deps.py` with the provider functions | 3 and 4 |
| `src/app/schemas/` | the data in and out (the contract) | 3 |
| `src/app/services/` | business rules, no HTTP and no SQL | 2 and 4 |
| `src/app/repositories/` | all queries, and the storage interface | 5 |
| `src/app/db/` | tables and sessions | 5 |
| `src/app/main.py` | `create_app`, the composition root | 4 |
| `src/quality/` | the algorithm, no web code, importable from a notebook | 2 |
| `migrations/` | Alembic: the schema as versioned code | 5 |
| `tests/` | fast tests with fakes, no running server | 4 |
| `Dockerfile`, `compose.yaml` | the image and the dev stack | 6 |
| `demo/` | scripts for the demos | 5 |

`DEMO.md` has the step-by-step runbook for the demos.

## Layer rules

A request goes router, service, repository. Each layer only talks to the one below it.

- **Routers** translate HTTP: parse the request, call one service method, turn the result or the domain error
  into a response. No business rules, no queries.
- **Services** hold the rules (does the dataset exist, is the report ready, may this user touch it). They raise domain errors from
  `services/errors.py` (and `InvalidUpload` / `TooLarge` for uploads), never `HTTPException`, and they never
  import FastAPI. The worker uses the same `JobService` as the API.
- **Repositories** hold all queries and own the commit. Services never touch the session directly.
- **Providers** in `routers/deps.py` are the only place that builds a service from its parts, so a test can
  swap one provider (`dependency_overrides`) or test a service on its own with mocked repositories.
- Job statuses are the `JobStatus` enum, never bare strings.

Ownership: a dataset or job belongs to the user who created it. Owners and Admins may touch it; the rule lives in
`services/access.py`. Deleting someone else's dataset is a 403 (`NotAllowed`). Reading someone else's job or
report is a 404 (`JobNotFound`), the same answer as a missing id, so the API does not leak which ids exist.
The worker runs jobs without a user (`run_next` takes none). Jobs created before the `owner_oid` migration
were given the owner of their dataset.

To add an endpoint: add the rule to a service method, raise a domain error for each failure, map each error to
a status code in the router, and test the rule in `tests/test_*_service.py` before the HTTP test.

## Settings

Everything comes from environment variables or `.env` (see `.env.example`). A wrong value stops the app at
startup: `MAX_UPLOAD_MB=ten` is an error, and `AUTH_MODE=entra` without `TENANT_ID` and `API_CLIENT_ID` is too.
The feature flag `FEATURE_CSV_EXPORT` switches on `GET /api/v1/datasets/export.csv`.

## Deliberately simplified

- Files are stored on local disk behind a `Storage` interface. In Azure that becomes Blob Storage (one new class).
- The worker polls the `jobs` table. That is enough here, a queue is a later step.
- No CORS, no structured logging, no Key Vault.

## Follow-ups before production

Known gaps, in rough order of importance:

- `GET /datasets/export.csv` builds its CSV by hand in the router and does not quote names with commas.
  Move it into the service and use the `csv` module.
- Every repository method commits on its own, so a service call that writes twice is not atomic. Move the
  commit to the service or to the request boundary when that matters.
- `InvalidUpload` and `TooLarge` still live in `services/datasets.py`; move them to `services/errors.py`.
- The upload size limit is checked in the router (how much to read) and again in `DatasetService`.
- CORS, structured logging, secrets in Key Vault, and a queue instead of polling (see above).
