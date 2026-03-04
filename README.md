# A2A Client Extension & Mock Server (ACP Version)

This project implements the A2A (Agent-to-Agent) Client Extension for NVIDIA Omniverse Kit, communicating with OpenCode via the **Agent Client Protocol (ACP)** over Stdio JSON-RPC.

## Directory Structure

```text
.
├── exts/
│   └── omni.kit.a2a_client/
│       ├── config/
│       │   └── extension.toml       # Extension configuration
│       ├── python/
│       │   └── omni/kit/a2a_client/
│       │       └── extension.py     # Core Extension Logic (ACP, UI, Async)
│       └── data/
│           └── icons/
├── mock_opencode_cli.py             # Mock OpenCode ACP Server (CLI)
└── spec.md                          # Project Specification (v1.2 ACP)
```

## Connecting to OpenCode (ACP)

To connect the A2A Client to a real OpenCode instance:

1.  **Locate OpenCode CLI**:
    - Ensure you have OpenCode installed.
    - Find the path to the `opencode` executable (or `code` if using VS Code compatible fork).
    - The extension needs to run the command: `opencode acp` (or equivalent that starts the JSON-RPC server on stdio).

2.  **Configure A2A Client**:
    - Open the "A2A Client (ACP)" window in Omniverse Kit.
    - In the **OpenCode ACP Command** field, enter the full command to start the ACP server.
      - **Windows + WSL** (Your setup): `wsl /usr/bin/opencode acp`
        - Note: Ensure `opencode` is installed inside WSL.
      - **Windows Native**: `C:\Users\YourName\AppData\Local\Programs\OpenCode\bin\opencode.cmd acp`
      - **macOS/Linux**: `/usr/local/bin/opencode acp`
      - **Mock**: `python3 /path/to/mock_opencode_cli.py` (Default)

3.  **Verify Connection**:
    - Enter a simple instruction like "create a cube".
    - Click "Generate Code".
    - Check the "ACP Log" area. You should see `-> { "method": "agent/generateCode", ... }` and `<- { "result": ... }`.

## How to Run with Mock Server

The extension is pre-configured to use the included `mock_opencode_cli.py` for testing without a real OpenCode instance.

1.  **Ensure Python 3 is available** in your environment.
2.  **Load the Extension** in Omniverse Kit.
3.  The default command will automatically point to `mock_opencode_cli.py` inside the extension workspace.
4.  **Test**:
    - Input "optimize scene" -> Returns a sample optimized USDA code.
    - Input "change material" -> Returns a sample material USDA code.

## Extension Logic

The `omni.kit.a2a_client` extension is designed to run within NVIDIA Omniverse Kit:

- **ACP Integration**: Uses `asyncio.create_subprocess_exec` to spawn the OpenCode agent process and communicate via standard input/output (Stdin/Stdout).
- **Protocol**: Speaks JSON-RPC 2.0.
- **UI**: Provides a window to configure the ACP command, input instructions, and preview generated USD code.
- **Async**: Non-blocking communication ensures the Kit UI remains responsive while the agent is generating code.
