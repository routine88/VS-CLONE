"""Custom exceptions raised by the asset importer pipeline."""

from __future__ import annotations


class ImporterError(RuntimeError):
    """Raised when an unrecoverable import failure occurs."""

