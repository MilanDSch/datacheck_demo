"""The second process: same codebase, same database, no web server.

Run with: uv run python -m app.worker
"""

import logging
import time

from .core.settings import get_settings
from .db.session import make_engine, new_session
from .repositories.datasets import DatasetRepository
from .repositories.jobs import JobRepository
from .repositories.storage import LocalStorage
from .services.jobs import JobService

log = logging.getLogger("worker")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    settings = get_settings()
    # Alembic owns the tables: the worker only uses them.
    engine = make_engine(settings.database_url)
    storage = LocalStorage(settings.upload_dir)
    log.info("worker started, waiting for jobs")
    while True:
        try:
            with new_session(engine) as session:
                service = JobService(JobRepository(session), DatasetRepository(session), storage)
                did_work = service.run_next()
        except Exception:  # a database hiccup must not kill the worker: log it and try again
            log.exception("loop failed, retrying in 5 seconds")
            time.sleep(5)
            continue
        if not did_work:
            time.sleep(2)  # polling the jobs table; simple and good enough


if __name__ == "__main__":
    main()
