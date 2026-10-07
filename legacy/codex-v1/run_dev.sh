#!/usr/bin/env bash
set -u

fail() {
    printf '%s\nSee SETUP.md for setup instructions.\n' "$1" >&2
    exit 1
}

system=$(uname -s) || fail 'Cannot determine the operating system.'
case "$system" in
    MINGW*|MSYS*|CYGWIN*)
        printf 'This launcher is intended for macOS/Linux.\nOn Windows, use run_dev.bat.\n'
        exit 1
        ;;
esac

# Resolve paths from this script, independently of the caller's directory.
repo_root=$(CDPATH= cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P) || fail 'Cannot resolve the repository root.'
python="$repo_root/.venv/bin/python"
backend="$repo_root/apps/backend"
frontend="$repo_root/apps/frontend"
url='http://127.0.0.1:5173/'

[ -x "$python" ] || fail 'Missing executable .venv/bin/python.'
[ -f "$repo_root/data/f1db.db" ] || fail 'Missing canonical data/f1db.db.'
[ -d "$backend" ] || fail 'Missing apps/backend/.'
[ -d "$frontend" ] || fail 'Missing apps/frontend/.'
command -v node >/dev/null 2>&1 || fail 'Node.js is missing from PATH.'
command -v npm >/dev/null 2>&1 || fail 'npm is missing from PATH.'
[ -x "$frontend/node_modules/.bin/vite" ] || fail 'Frontend dependencies are missing.'
PYTHONPATH="$backend/src" "$python" -B -c 'import fastapi, uvicorn, f1_eras.api.http' || fail 'Backend dependencies are unavailable.'
node -e 'for (const name of ["vite", "react", "react-dom", "plotly.js"]) require.resolve(name, {paths: [process.argv[1]]})' "$frontend" || fail 'Frontend dependencies are incomplete.'

backend_pid=
frontend_pid=
timer_pid=
pause() {
    # Waiting on a background timer keeps the launcher in the foreground
    # process group, so Ctrl+C reaches its trap when job control is enabled.
    sleep "$1" &
    timer_pid=$!
    wait "$timer_pid" || true
    timer_pid=
}
cleanup() {
    trap '' INT TERM
    for pid in "$backend_pid" "$frontend_pid" "$timer_pid"; do
        [ -z "$pid" ] || kill -TERM -- "-$pid" 2>/dev/null || true
    done
    # Allow graceful shutdown, then remove any remaining service descendants.
    sleep 2
    for pid in "$backend_pid" "$frontend_pid" "$timer_pid"; do
        if [ -n "$pid" ]; then
            kill -KILL -- "-$pid" 2>/dev/null || true
            wait "$pid" 2>/dev/null || true
        fi
    done
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Bash job control gives each service its own process group, including Vite
# children started by npm. This is supported by macOS's older Bash too.
set -m
printf 'Backend: http://127.0.0.1:8000\nFrontend: %s\nPress Ctrl+C to stop both services.\n' "$url"
"$python" -B -m uvicorn f1_eras.api.http:create_default_app --factory --app-dir "$backend/src" --host 127.0.0.1 --port 8000 &
backend_pid=$!
(
    cd "$frontend" || exit 1
    exec npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
) &
frontend_pid=$!

pause 4
if kill -0 "$backend_pid" 2>/dev/null && kill -0 "$frontend_pid" 2>/dev/null; then
    if [ "$system" = Darwin ] && command -v open >/dev/null 2>&1; then
        (open "$url" || printf 'Open %s in your browser.\n' "$url") &
    elif command -v xdg-open >/dev/null 2>&1; then
        (xdg-open "$url" || printf 'Open %s in your browser.\n' "$url") &
    else
        printf '%s\n' "$url"
    fi
fi

# Bash 3.2 has no wait -n; watch both children and stop the other on exit.
while kill -0 "$backend_pid" 2>/dev/null && kill -0 "$frontend_pid" 2>/dev/null; do
    pause 1
done
if ! kill -0 "$backend_pid" 2>/dev/null; then
    wait "$backend_pid"
    status=$?
    printf 'Backend exited with status %s; stopping development services.\n' "$status" >&2
else
    wait "$frontend_pid"
    status=$?
    printf 'Frontend exited with status %s; stopping development services.\n' "$status" >&2
fi
exit "$status"
