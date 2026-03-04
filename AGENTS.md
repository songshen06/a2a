# Repository Guidelines

## Project Structure & Module Organization
This repository contains a small A2A prototype with two main parts:

- `exts/omni.kit.a2a_client/`: Omniverse Kit extension code.
- `exts/omni.kit.a2a_client/config/extension.toml`: extension metadata and dependencies.
- `exts/omni.kit.a2a_client/python/scripts/extension.py`: UI, async task dispatch, retry logic, and USD-apply stubs.
- `mock_server.py`: FastAPI mock endpoint (`POST /tasks/send`) used for local integration testing.
- `requirements.txt`: Python dependencies for the mock server.
- `spec.md` and `README.md`: behavior spec and usage notes.

## Build, Test, and Development Commands
- `pip install -r requirements.txt`: install server dependencies.
- `python mock_server.py`: run the mock server on `0.0.0.0:8000`.
- `uvicorn mock_server:app --reload --host 0.0.0.0 --port 8000`: optional autoreload dev server.

Manual integration flow:
1. Start the mock server.
2. Launch Omniverse Kit and enable `omni.kit.a2a_client`.
3. Open **A2A Client**, submit an instruction, and verify status/output.

## Coding Style & Naming Conventions
- Use Python with PEP 8 defaults: 4-space indentation, clear function boundaries, and minimal inline comments.
- Naming patterns:
- Classes: `PascalCase` (example: `A2AClientExtension`).
- Functions/variables: `snake_case` (example: `_process_task`, `base_delay`).
- Constants/config values: uppercase only when true constants; otherwise keep module-level settings explicit and localized.
- Keep async/network logic non-blocking (`async`/`await`) in extension code.

## Testing Guidelines
There is no committed automated test suite yet. Current validation is integration-focused:

- Primary test path is the manual end-to-end flow described above.
- When adding logic-heavy code, add `pytest` unit tests under a new `tests/` directory (e.g., `tests/test_retry_logic.py`).
- Prefer deterministic tests by isolating random/time behavior behind injectable helpers.

## Commit & Pull Request Guidelines
Git history is not available in this workspace snapshot, so follow this baseline convention:

- Commit format: `type(scope): short summary` (for example, `feat(extension): add retry status messaging`).
- Keep commits focused and reversible; avoid mixing extension and server refactors in one commit.
- PRs should include:
- What changed and why.
- How to test locally (commands + expected result).
- Screenshots/log snippets for UI or runtime behavior changes.
- Linked issue/spec section when applicable.
