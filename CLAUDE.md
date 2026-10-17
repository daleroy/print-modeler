# print-modeler repo

Builds 3D-printable models for a Bambu Lab P2S (single color for now).

- Modeling work goes to the `print-modeler` subagent (or `/model <request>`). Relay its questions to
  the user and pass answers back with SendMessage; do not answer them on the user's behalf.
- When the agent returns preview images (`jobs/<slug>/out/*_views.png`), read and show them.
- Never approve a draft, finalize, or slice without the user saying so.
- Photos of people, especially children, are never copied into the repo, committed, or uploaded.
- `vendor/` holds pinned third-party libraries (git submodules). Don't edit them.
- Python tools run from the repo root with the `.venv` interpreter: `.venv/bin/python tools/<tool>.py`.
