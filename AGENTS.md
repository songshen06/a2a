# Repository Guidelines (ACP Version)

## Project Structure & Module Organization
This repository contains an A2A prototype that implements the **Agent Client Protocol (ACP)** via Stdio JSON-RPC:

- `exts/omni.kit.a2a_client/`: Omniverse Kit extension code.
- `exts/omni.kit.a2a_client/config/extension.toml`: extension metadata.
- `exts/omni.kit.a2a_client/python/omni/kit/a2a_client/extension.py`: Core logic for UI, async subprocess management, and JSON-RPC communication.
- `mock_opencode_cli.py`: A Python CLI script that mocks OpenCode's ACP behavior (reads stdin, writes stdout).
- `spec.md` and `README.md`: behavior spec (v1.2) and usage notes.

## Build, Test, and Development Commands
- **No external dependencies** required for the mock server (standard library only).
- `python3 mock_opencode_cli.py`: run the mock CLI interactively (type JSON-RPC requests to stdin).

Manual integration flow:
1. Launch Omniverse Kit and enable `omni.kit.a2a_client`.
2. Open **A2A Client (ACP)** window.
3. Configure the command (default: `python3 .../mock_opencode_cli.py`, or `wsl opencode acp`).
4. Submit an instruction and verify the JSON-RPC log and generated USDA code.

## Coding Style & Naming Conventions
- Use Python with PEP 8 defaults.
- **Async/Await**: Critical for `extension.py` to ensure the Kit UI remains responsive during blocking subprocess calls.
- **Stdio Communication**: 
  - Write to `stdin` as bytes (encoded UTF-8).
  - Read from `stdout` as bytes (decoded UTF-8).
  - Ensure `flush=True` when writing to stdout in mock scripts.

## Testing Guidelines
- Primary test path is the manual end-to-end flow.
- Use `mock_opencode_cli.py` to simulate various agent responses (e.g., "optimize", "material").
- For Windows/WSL testing, ensure paths are handled with `posix=False` in `shlex.split`.

## Commit & Pull Request Guidelines
- Commit format: `type(scope): short summary`.
- Keep commits focused on ACP protocol compliance.
