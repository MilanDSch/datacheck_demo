"""The algorithm library: no web code, no database, no storage. A notebook can import it on its own."""

from .checks import Report, check_quality

__all__ = ["Report", "check_quality"]
