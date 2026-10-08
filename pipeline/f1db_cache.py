"""Local cache of F1DB SQLite snapshots, one directory per release version.

    <cache_root>/
      state.json        {"current": <version>, "previous": <version> or null}
      <version>/
        metadata.json   the release spec plus databaseSha256
        f1db.db

ensure() returns the database of the release it is asked for and nothing else: it never picks
a version itself and never falls back to another snapshot. A promoted snapshot is never
modified. At most two survive a successful ensure: the requested release, and the release that
was current before it, kept for reference only.

state.json is disposable bookkeeping for that one relationship. When it is missing or
malformed the cache forgets the earlier snapshot rather than guess at it.
"""

import contextlib
import hashlib
import io
import json
import os
import shutil
import sqlite3
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

BASE_URL = "https://github.com/f1db/f1db/releases/download"
DB_NAME = "f1db.db"
METADATA_NAME = "metadata.json"
STATE_NAME = "state.json"
CHUNK = 1 << 20


def read_json_object(path: Path) -> dict | None:
    """The JSON object stored at path, or None if it is missing, unreadable or not an object."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def download(url: str, sha256: str) -> bytearray:
    """Read url into memory, raising ValueError unless its SHA-256 is the expected one."""
    digest, data = hashlib.sha256(), bytearray()
    with urllib.request.urlopen(url) as response:
        while chunk := response.read(CHUNK):
            digest.update(chunk)
            data += chunk
    if digest.hexdigest() != sha256:
        raise ValueError(f"SHA-256 mismatch for {url}: expected {sha256}, got {digest.hexdigest()}")
    return data


def install(spec: dict[str, str], cache_root: Path, base_url: str) -> None:
    """Download, verify and promote the snapshot for spec to cache_root/<version>."""
    segments = (urllib.parse.quote(spec[key], safe="") for key in ("version", "asset"))
    url = "/".join([base_url.rstrip("/"), *segments])
    # Nothing touches the cache until the archive is downloaded, verified and known to hold
    # the database, so those failures leave the cache exactly as it was.
    data = download(url, spec["sha256"])
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        archive.getinfo(DB_NAME)
        incoming = Path(tempfile.mkdtemp(dir=cache_root, prefix=".incoming-"))
        try:
            database, digest = incoming / DB_NAME, hashlib.sha256()
            with archive.open(DB_NAME) as src, database.open("wb") as dst:
                while chunk := src.read(CHUNK):
                    digest.update(chunk)
                    dst.write(chunk)
            # closing(): a connection used as a context manager stays open, and on Windows an
            # open handle would block the rename below.
            read_only = f"{database.as_uri()}?mode=ro"
            with contextlib.closing(sqlite3.connect(read_only, uri=True)) as conn:
                check = conn.execute("PRAGMA quick_check").fetchall()
            if check != [("ok",)]:
                raise ValueError(f"{DB_NAME} from {url} failed PRAGMA quick_check: {check}")
            metadata = {**spec, "databaseSha256": digest.hexdigest()}
            (incoming / METADATA_NAME).write_text(
                json.dumps(metadata, indent=2) + "\n", encoding="utf-8", newline="\n"
            )
            os.rename(incoming, cache_root / spec["version"])
        finally:
            if incoming.exists():
                shutil.rmtree(incoming, ignore_errors=True)


def check_requested(target: Path, spec: dict[str, str]) -> None:
    """Raise ValueError unless the existing target is a snapshot of exactly spec."""
    metadata = read_json_object(target / METADATA_NAME)
    if (
        not target.is_dir()
        or not (target / DB_NAME).is_file()
        or metadata is None
        or any(key not in metadata or metadata[key] != value for key, value in spec.items())
    ):
        raise ValueError(
            f"cached snapshot {target} is malformed or does not match release {spec['version']}; "
            "delete that directory manually and run again"
        )


def is_retained_snapshot(directory: Path) -> bool:
    """Structural check only: the files exist and the metadata names this directory."""
    metadata = read_json_object(directory / METADATA_NAME)
    return (
        directory.is_dir()
        and (directory / DB_NAME).is_file()
        and metadata is not None
        and metadata.get("version") == directory.name
    )


def read_state(cache_root: Path) -> dict | None:
    """The recorded state, or None unless state.json holds current and previous as str or null."""
    state = read_json_object(cache_root / STATE_NAME)
    if state is None:
        return None
    for key in ("current", "previous"):
        if key not in state or not (state[key] is None or isinstance(state[key], str)):
            return None
    return state


def write_state(cache_root: Path, state: dict[str, str | None]) -> None:
    fd, tmp = tempfile.mkstemp(dir=cache_root, prefix=".state-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(state, indent=2) + "\n")
        os.replace(tmp, cache_root / STATE_NAME)
    finally:
        with contextlib.suppress(OSError):
            os.unlink(tmp)


def ensure(spec: dict[str, str], cache_root: Path, base_url: str = BASE_URL) -> Path:
    """Path of the cached database for spec, installing that release if it is not cached."""
    cache_root.mkdir(parents=True, exist_ok=True)
    current = spec["version"]
    target = cache_root / current
    if target.exists():
        check_requested(target, spec)
    else:
        install(spec, cache_root, base_url)

    entries = set(os.listdir(cache_root))
    recorded = read_state(cache_root)
    old = recorded or {"current": None, "previous": None}
    # The snapshot being replaced becomes previous; on a repeat run the recorded previous stays.
    candidate = old["previous"] if old["current"] == current else old["current"]
    kept = candidate != current and candidate in entries and is_retained_snapshot(cache_root / candidate)
    state = {"current": current, "previous": candidate if kept else None}
    if state != recorded:
        write_state(cache_root, state)

    # Prune last and loudly: a path that cannot be removed fails this run, and the next one
    # finishes the job from the state already written.
    for name in sorted(entries - {STATE_NAME, current, state["previous"]}):
        stale = cache_root / name
        if stale.is_dir():
            shutil.rmtree(stale)
        else:
            stale.unlink()
    return target / DB_NAME
