"""Domain errors raised by the services. The routers turn them into HTTP responses."""


class DatasetNotFound(Exception):
    """No dataset with that id."""


class NotAllowed(Exception):
    """The caller is known but may not do this to someone else's resource."""


class JobNotFound(Exception):
    """No job with that id."""


class ReportNotReady(Exception):
    """The job exists but has no report yet (still queued or running, or it failed)."""

    def __init__(self, status: str) -> None:
        super().__init__(status)
        self.status = status
