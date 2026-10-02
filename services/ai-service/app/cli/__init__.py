"""CLI package for the AI Service.

Provides the manual, on-demand pipeline runner (app.cli.pipeline)
that executes the full scheduler flow — ML jobs plus analytics
jobs — outside of APScheduler.

The CLI runs in CLI mode: all repository writes and file-system
writes go to CLI-isolated targets (``*_cli`` tables and the
``cli_data/`` directory), never to production.

Entry point:
    python -m app.cli.pipeline <subcommand>

See app/cli/pipeline.py for the subcommand list.
"""