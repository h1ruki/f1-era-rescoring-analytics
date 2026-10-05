"""Connection boundary for an immutable, standalone F1DB source file."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
import sqlite3


class SourceDatabaseError(RuntimeError):
    """The supplied file cannot be used as the expected source snapshot."""


class SourceSnapshotChanged(SourceDatabaseError):
    """The source changed while capturing an assessment image."""


@contextmanager
def open_read_only(db_path: str | Path) -> Iterator[sqlite3.Connection]:
    """Open an existing file without creating it; always close the connection.

    immutable=1 is appropriate because this boundary accepts standalone source
    snapshots, never a live database. Active journal/WAL sidecars are rejected
    rather than silently omitted from the snapshot's content identity.
    """
    path = Path(db_path).resolve(strict=True)
    if not path.is_file():
        raise SourceDatabaseError(f"Source database is not a file: {path}")
    for suffix in ("-wal", "-journal"):
        sidecar = Path(str(path) + suffix)
        if sidecar.exists() and sidecar.stat().st_size:
            raise SourceDatabaseError(
                f"Source must be a standalone immutable snapshot; found {sidecar.name}"
            )
    connection = sqlite3.connect(
        path.as_uri() + "?mode=ro&immutable=1", uri=True
    )
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        yield connection
    finally:
        connection.close()
