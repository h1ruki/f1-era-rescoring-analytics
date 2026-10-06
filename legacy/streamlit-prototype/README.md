# Original Streamlit prototype

These files are the original Streamlit prototype, retained as project-history
and reference material to show the evolution of F1 ERAs.

The active application lives in [backend/](../../backend/README.md) and
[frontend/](../../frontend/README.md). Use the root
[development launcher](../../run_dev.bat) to run that implementation.

This archive is not maintained as a runnable application. Its database-location
assumptions are preserved, and `run_app.bat` contains obsolete machine-specific
local-development paths. It is not a supported entry point. The active canonical
database now lives at `data/f1db.db`, relative to the repository root; the archived
code is preserved without adapting it to that location.
