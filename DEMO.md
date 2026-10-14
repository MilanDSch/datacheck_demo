# Demo runbook

Every demo starts from a clean `git status`. Reset after a demo with `git restore . ; git clean -fd` (careful:
this removes your uncommitted work). Font size 18 or more. Never debug live for more than 30 seconds: use the
fallback recording.

## Demo A: from clone to running (part 1)

This one is done in a fresh folder, not in this repo.

1. Old way: `python -m venv .venv`, activate it, `pip install fastapi pydantic-settings`, `pip freeze`.
2. uv: `uv init --package demo-api`, `uv add fastapi pydantic-settings`, `uv add --dev pytest`.
   Open `pyproject.toml` and `uv.lock`.
3. Delete `.venv`, run `uv sync`: it comes back in seconds.
4. In this repo: `git clone`, `uv sync`, `cp .env.example .env`, `uv run pytest`.
5. Fail fast: `MAX_UPLOAD_MB=ten uv run python -c "from app.core.settings import Settings; Settings()"` and
   `AUTH_MODE=entra uv run python -c "from app.core.settings import Settings; Settings()"`. Both stop with a clear error.

## Demo B: walk the tree (part 2)

Open the project in the editor. Top to bottom, one sentence per folder, open one file in each:
`src/app/routers/datasets.py`, `schemas/datasets.py`, `services/datasets.py`, `repositories/datasets.py`,
`db/models.py`, `core/settings.py`, `main.py`, then `src/quality/checks.py`.
Ask the change-test questions from the slide before opening the answer.

## Demo C: write an endpoint, break the contract (part 3)

1. `uv run alembic upgrade head`, then `uv run uvicorn app.main:create_app --factory --reload`. Open `/docs`.
2. Call `POST /api/v1/jobs` with `{"dataset_id": "abc"}`: a 422 you did not write. Open `/openapi.json` in a second tab.
3. In `src/app/schemas/jobs.py` rename `quality_score` to `score` in `ReportOut` (also change `routers/jobs.py`).
   Refresh `/openapi.json`: the field changed.
4. `uv run pytest`: `test_job_flow_202_then_409_then_200` fails. That test is the contract check.
5. Reset: `git restore .`

## Demo D: follow one request, then fake it (part 4)

1. Put breakpoints in `routers/datasets.py` (`list_datasets`), `routers/deps.py` (`get_dataset_service`,
   `get_dataset_repo`, `get_session`), `services/datasets.py` (`list_all`) and `repositories/datasets.py` (`list_all`).
2. Start the API in the debugger, call `GET /api/v1/datasets` from `/docs`, and step through. Note the order
   FastAPI builds the chain in, and that the session closes at the end.
3. Open `tests/test_wiring.py` and run it with the database container stopped: it passes, because nothing asks for a database.

## Demo E: count the queries, add a column (part 5)

1. `uv run python demo/n_plus_one.py`: 4 queries lazy, 2 queries with `selectinload`.
2. In `src/app/db/models.py`, add to `Dataset`:
   `comment: Mapped[str | None] = mapped_column(String(500), default=None)`
3. `uv run alembic revision --autogenerate -m "add comment"`. Open the generated file, point at `upgrade` and `downgrade`.
4. `uv run alembic upgrade head`, then look at the table. `uv run alembic downgrade -1`: it is gone again.
5. `uv run pytest tests/test_migrations.py`: the test that fails if a model changes without a migration.
6. Reset: `git restore . ; git clean -fd migrations src` and delete `datacheck.db`.

## Demo F: the whole stack on a laptop (part 6)

1. Fresh clone, `cp .env.example .env`, `docker compose up --build -d --scale worker=2`
   (`API_PORT=8010` if port 8000 is taken). Show the log: Postgres healthy, `alembic upgrade`, uvicorn, workers.
2. Open `/docs`. Upload `samples/bench-run-gaps.csv`, start a job, ask for the report at once (409), again a few seconds later (200).
3. Edit the `title` in `src/app/main.py` and show `/openapi.json` change.
4. `docker compose down -v`, then `up` again: the data is gone and the migration rebuilds the schema.
5. Prepare the images beforehand: a cold build takes minutes.

## Demo G: flip the switch (part 7)

1. `GET /api/v1/datasets/export.csv`: 404.
2. `FEATURE_CSV_EXPORT=true docker compose up -d --scale worker=2` (or set it in `.env`): the call now returns the CSV.
3. The two tests: `uv run pytest tests/test_orm_and_flags.py -k feature`.
