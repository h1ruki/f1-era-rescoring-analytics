import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import sqlite3
import sys
import urllib.error
import zipfile
from collections.abc import Callable
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import f1db_cache
from f1db_cache import ensure

Spec = dict[str, str]
Fetch = Callable[[Spec], Path]

ASSET = "f1db-sqlite.zip"
OLD = 10**18  # a fixed modification time, in nanoseconds, in September 2001


@pytest.fixture
def cache(tmp_path: Path) -> Path:
    """A cache root that does not exist yet, and neither does its parent, as on a fresh clone."""
    return tmp_path / ".cache" / "f1db"


@pytest.fixture
def source(tmp_path: Path) -> Path:
    """The directory served as the download base: <source>/<version>/f1db-sqlite.zip."""
    path = tmp_path / "source"
    path.mkdir()
    return path


@pytest.fixture
def fetch(cache: Path, source: Path) -> Fetch:
    """ensure() against this test's cache, downloading over file:// from its source."""
    return lambda spec: ensure(spec, cache, source.as_uri())


@pytest.fixture
def rotated(fetch: Fetch, source: Path) -> tuple[Spec, Spec]:
    """The specs of vA and vB, in a cache where vB is current and vA is previous."""
    a, b = release(source, "vA"), release(source, "vB")
    fetch(a)
    fetch(b)
    return a, b


def sqlite_bytes(directory: Path, *statements: str) -> bytes:
    """The bytes of a real SQLite database built by running statements."""
    path = directory / "fixture.db"
    with contextlib.closing(sqlite3.connect(path)) as conn:
        for statement in statements:
            conn.execute(statement)
        conn.commit()
    data = path.read_bytes()
    path.unlink()
    return data


def corrupt_sqlite_bytes(directory: Path) -> bytes:
    """A real SQLite database that fails quick_check: a NULL stored under a NOT NULL schema."""
    path = directory / "corrupt.db"
    with contextlib.closing(sqlite3.connect(path)) as conn:
        conn.execute("CREATE TABLE t(a)")
        conn.execute("INSERT INTO t VALUES (NULL)")
        conn.commit()
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute("UPDATE sqlite_master SET sql = 'CREATE TABLE t(a NOT NULL)' WHERE name = 't'")
        conn.commit()
    with contextlib.closing(sqlite3.connect(path)) as conn:
        assert conn.execute("PRAGMA quick_check").fetchall() == [("NULL value in t.a",)]
    data = path.read_bytes()
    path.unlink()
    return data


def zipped(members: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    return buffer.getvalue()


def publish(source: Path, version: str, archive: bytes) -> Spec:
    """Serve archive as the release asset of version and return the release spec that pins it."""
    path = source / version / ASSET
    path.parent.mkdir()
    path.write_bytes(archive)
    return {"version": version, "asset": ASSET, "sha256": hashlib.sha256(archive).hexdigest()}


def release(source: Path, version: str) -> Spec:
    """Publish a valid release whose database records its own version."""
    database = sqlite_bytes(source, "CREATE TABLE release(version)", f"INSERT INTO release VALUES ('{version}')")
    return publish(source, version, zipped({"f1db.db": database}))


def state(cache: Path) -> dict:
    return json.loads((cache / "state.json").read_text(encoding="utf-8"))


def write_state(cache: Path, text: str) -> None:
    (cache / "state.json").write_text(text, encoding="utf-8")


def names(cache: Path) -> set[str]:
    return set(os.listdir(cache))


def snapshot(root: Path) -> dict[str, bytes | None]:
    """Every path under root mapped to its bytes, or to None for a directory."""
    return {p.relative_to(root).as_posix(): None if p.is_dir() else p.read_bytes() for p in root.rglob("*")}


def assert_refused(fetch: Fetch, cache: Path, spec: Spec, error: type[Exception], match: str | None = None) -> None:
    """Fetching spec raises error and leaves every path and byte of the cache as it was."""
    before = snapshot(cache)
    with pytest.raises(error, match=match):
        fetch(spec)
    assert snapshot(cache) == before


def test_empty_cache_installs_the_requested_release(fetch: Fetch, cache: Path, source: Path) -> None:
    a = release(source, "vA")
    database = fetch(a)
    assert database == cache / "vA" / "f1db.db"
    assert state(cache) == {"current": "vA", "previous": None}
    with contextlib.closing(sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)) as conn:
        assert conn.execute("SELECT version FROM release").fetchall() == [("vA",)]
    metadata = json.loads((cache / "vA" / "metadata.json").read_text(encoding="utf-8"))
    assert metadata == {**a, "databaseSha256": hashlib.sha256(database.read_bytes()).hexdigest()}


def test_base_url_may_end_with_a_slash(cache: Path, source: Path) -> None:
    assert ensure(release(source, "vA"), cache, source.as_uri() + "/") == cache / "vA" / "f1db.db"


def test_clean_hit_touches_nothing_and_does_not_read_the_database(fetch: Fetch, cache: Path, source: Path) -> None:
    a = release(source, "vA")
    database = fetch(a)
    # A hit does not open, hash or check the database, so these bytes must go unnoticed.
    database.write_bytes(b"not a database")
    watched = [cache / "state.json", cache / "vA" / "metadata.json", database]
    for path in watched:
        os.utime(path, ns=(OLD, OLD))
    (source / "vA" / ASSET).unlink()
    before = snapshot(cache)

    assert fetch(a) == database
    assert database.read_bytes() == b"not a database"
    assert [path.stat().st_mtime_ns for path in watched] == [OLD, OLD, OLD]
    assert snapshot(cache) == before  # same paths, same bytes, state.json included


def test_new_release_keeps_the_replaced_one_as_previous(fetch: Fetch, cache: Path, source: Path) -> None:
    fetch(release(source, "vA"))
    assert fetch(release(source, "vB")) == cache / "vB" / "f1db.db"
    assert state(cache) == {"current": "vB", "previous": "vA"}
    assert names(cache) == {"state.json", "vA", "vB"}


@pytest.mark.usefixtures("rotated")
def test_at_most_two_snapshots_survive(fetch: Fetch, cache: Path, source: Path) -> None:
    assert fetch(release(source, "vC")) == cache / "vC" / "f1db.db"
    assert state(cache) == {"current": "vC", "previous": "vB"}
    assert names(cache) == {"state.json", "vB", "vC"}


def test_previous_is_kept_on_structure_alone_without_reading_its_database(
    fetch: Fetch, cache: Path, source: Path
) -> None:
    fetch(release(source, "vA"))
    (cache / "vA" / "f1db.db").write_bytes(b"not a database")
    fetch(release(source, "vB"))
    assert state(cache) == {"current": "vB", "previous": "vA"}
    assert (cache / "vA" / "f1db.db").read_bytes() == b"not a database"


@pytest.mark.parametrize(
    "damage",
    [
        lambda snapshot_dir: (snapshot_dir / "f1db.db").unlink(),
        lambda snapshot_dir: (snapshot_dir / "metadata.json").write_text("{not json", encoding="utf-8"),
        lambda snapshot_dir: (snapshot_dir / "metadata.json").write_text('{"version": "vOther"}', encoding="utf-8"),
    ],
    ids=["no database", "unreadable metadata", "metadata names another version"],
)
def test_structurally_invalid_snapshot_is_not_kept_as_previous(
    fetch: Fetch, cache: Path, source: Path, damage: Callable[[Path], object]
) -> None:
    fetch(release(source, "vA"))
    damage(cache / "vA")
    fetch(release(source, "vB"))
    assert state(cache) == {"current": "vB", "previous": None}
    assert names(cache) == {"state.json", "vB"}


@pytest.mark.usefixtures("rotated")
def test_checksum_mismatch_leaves_the_cache_untouched(fetch: Fetch, cache: Path, source: Path) -> None:
    spec = {**release(source, "vC"), "sha256": "0" * 64}
    assert_refused(fetch, cache, spec, ValueError, "SHA-256 mismatch")


@pytest.mark.usefixtures("rotated")
def test_archive_that_is_not_a_zip_leaves_the_cache_untouched(fetch: Fetch, cache: Path, source: Path) -> None:
    spec = publish(source, "vC", b"these bytes are not an archive")
    assert_refused(fetch, cache, spec, zipfile.BadZipFile)


@pytest.mark.usefixtures("rotated")
def test_archive_without_the_database_leaves_the_cache_untouched(fetch: Fetch, cache: Path, source: Path) -> None:
    spec = publish(source, "vC", zipped({"other.db": b"anything"}))
    assert_refused(fetch, cache, spec, KeyError)


@pytest.mark.usefixtures("rotated")
def test_database_that_is_not_sqlite_leaves_the_cache_untouched(fetch: Fetch, cache: Path, source: Path) -> None:
    spec = publish(source, "vC", zipped({"f1db.db": b"not a database" * 100}))
    assert_refused(fetch, cache, spec, sqlite3.DatabaseError)


@pytest.mark.usefixtures("rotated")
def test_database_failing_quick_check_leaves_the_cache_untouched(fetch: Fetch, cache: Path, source: Path) -> None:
    spec = publish(source, "vC", zipped({"f1db.db": corrupt_sqlite_bytes(source)}))
    assert_refused(fetch, cache, spec, ValueError, r"quick_check.*NULL value in t\.a")


# The three cases below each have a healthy previous snapshot at hand. None of them may use it.


def test_requested_snapshot_pinned_to_another_checksum_is_refused(
    fetch: Fetch, cache: Path, rotated: tuple[Spec, Spec]
) -> None:
    _, b = rotated
    assert_refused(fetch, cache, {**b, "sha256": "0" * 64}, ValueError, re.escape(str(cache / "vB")))


def test_requested_snapshot_without_its_database_is_refused(
    fetch: Fetch, cache: Path, rotated: tuple[Spec, Spec]
) -> None:
    _, b = rotated
    (cache / "vB" / "f1db.db").unlink()
    assert_refused(fetch, cache, b, ValueError, re.escape(str(cache / "vB")))


@pytest.mark.usefixtures("rotated")
def test_release_that_cannot_be_downloaded_is_an_error(fetch: Fetch, cache: Path) -> None:
    unpublished = {"version": "vC", "asset": ASSET, "sha256": "0" * 64}
    assert_refused(fetch, cache, unpublished, urllib.error.URLError)


@pytest.mark.parametrize(
    "metadata",
    [
        lambda spec: json.dumps({**spec, "asset": "another.zip"}),
        lambda spec: json.dumps({"version": spec["version"], "asset": spec["asset"]}),
        lambda spec: "{not json",
        lambda spec: "[]",
    ],
    ids=["a field differs", "a field is missing", "invalid JSON", "not an object"],
)
def test_requested_snapshot_with_wrong_metadata_is_refused_not_repaired(
    fetch: Fetch, cache: Path, source: Path, metadata: Callable[[Spec], str]
) -> None:
    a = release(source, "vA")
    fetch(a)
    (cache / "vA" / "metadata.json").write_text(metadata(a), encoding="utf-8")
    # The archive is still published, so only the refusal keeps this from being reinstalled.
    assert_refused(fetch, cache, a, ValueError, re.escape(str(cache / "vA")))


@pytest.mark.parametrize(
    "recorded",
    [
        None,
        "{not json",
        '["vB", "vA"]',
        '{"current": 7, "previous": ["x"]}',
        '{"current": "vA", "previous": 7}',
        '{"current": "vA"}',
    ],
    ids=["missing", "invalid JSON", "not an object", "wrong types", "one wrong type", "a key is missing"],
)
def test_unusable_state_is_treated_as_empty(
    fetch: Fetch, cache: Path, rotated: tuple[Spec, Spec], recorded: str | None
) -> None:
    _, b = rotated
    if recorded is None:
        (cache / "state.json").unlink()
    else:
        write_state(cache, recorded)
    # Nothing is salvaged from it, not even a well-formed "current": vA is forgotten and pruned.
    assert fetch(b) == cache / "vB" / "f1db.db"
    assert state(cache) == {"current": "vB", "previous": None}
    assert names(cache) == {"state.json", "vB"}


@pytest.mark.parametrize("previous", ["vGone", "vA"], ids=["a missing snapshot", "the current snapshot"])
def test_unusable_previous_is_dropped_and_the_correction_written_once(
    fetch: Fetch, cache: Path, source: Path, previous: str
) -> None:
    a = release(source, "vA")
    fetch(a)
    write_state(cache, json.dumps({"current": "vA", "previous": previous}))
    fetch(a)
    assert state(cache) == {"current": "vA", "previous": None}
    assert names(cache) == {"state.json", "vA"}

    os.utime(cache / "state.json", ns=(OLD, OLD))
    fetch(a)
    assert (cache / "state.json").stat().st_mtime_ns == OLD


def test_repinning_to_a_cached_release_needs_no_download(
    fetch: Fetch, cache: Path, source: Path, rotated: tuple[Spec, Spec]
) -> None:
    a, _ = rotated
    shutil.rmtree(source)
    assert fetch(a) == cache / "vA" / "f1db.db"
    assert state(cache) == {"current": "vA", "previous": "vB"}
    assert names(cache) == {"state.json", "vA", "vB"}


def test_snapshot_promoted_before_an_interrupted_run_is_adopted(
    fetch: Fetch, cache: Path, source: Path, rotated: tuple[Spec, Spec], tmp_path: Path
) -> None:
    a, _ = rotated
    fetch(a)
    # vC as an interrupted run leaves it: promoted into the cache, state.json not yet updated.
    c = release(source, "vC")
    ensure(c, tmp_path / "elsewhere", source.as_uri())
    shutil.copytree(tmp_path / "elsewhere" / "vC", cache / "vC")
    shutil.rmtree(source)
    assert state(cache) == {"current": "vA", "previous": "vB"}

    assert fetch(c) == cache / "vC" / "f1db.db"
    assert state(cache) == {"current": "vC", "previous": "vA"}
    assert names(cache) == {"state.json", "vA", "vC"}


def test_stale_entries_are_pruned_on_a_hit(fetch: Fetch, cache: Path, source: Path) -> None:
    a = release(source, "vA")
    fetch(a)
    shutil.copytree(cache / "vA", cache / "vOld")
    (cache / ".incoming-left").mkdir()
    (cache / ".incoming-left" / "f1db.db").write_bytes(b"partial")
    (cache / ".state-left.tmp").write_text("{}", encoding="utf-8")
    assert fetch(a) == cache / "vA" / "f1db.db"
    assert names(cache) == {"state.json", "vA"}


@pytest.mark.usefixtures("rotated")
def test_installs_leave_exactly_the_database_and_metadata_and_no_archive(cache: Path) -> None:
    assert set(snapshot(cache)) == {
        "state.json",
        "vA",
        "vA/f1db.db",
        "vA/metadata.json",
        "vB",
        "vB/f1db.db",
        "vB/metadata.json",
    }
    assert not any(zipfile.is_zipfile(path) for path in cache.rglob("*") if path.is_file())


@pytest.mark.usefixtures("rotated")
def test_prune_failure_is_loud_and_the_next_run_converges(
    fetch: Fetch, cache: Path, source: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    c = release(source, "vC")
    rmtree = shutil.rmtree

    def locked(path: Path, *args: object, **kwargs: object) -> None:
        if Path(path) == cache / "vA":
            raise PermissionError(f"locked: {path}")
        rmtree(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(f1db_cache.shutil, "rmtree", locked)
        with pytest.raises(PermissionError, match="locked"):
            fetch(c)
    # The run failed while pruning, after the state had advanced; all three coexist for now.
    assert state(cache) == {"current": "vC", "previous": "vB"}
    assert names(cache) == {"state.json", "vA", "vB", "vC"}

    assert fetch(c) == cache / "vC" / "f1db.db"
    assert state(cache) == {"current": "vC", "previous": "vB"}
    assert names(cache) == {"state.json", "vB", "vC"}
