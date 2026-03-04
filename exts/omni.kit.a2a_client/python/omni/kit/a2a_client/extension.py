import asyncio
import json
import uuid
import shlex
import os
from datetime import datetime

import omni.ext
import omni.kit.undo
import omni.ui as ui
import omni.usd


class A2AClientExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        self._window = ui.Window("A2A Client (ACP)", width=760, height=680)
        
        # Try to locate mock_opencode_cli.py relative to this file
        # extension.py is in .../python/omni/kit/a2a_client/extension.py
        # We want .../a2a/mock_opencode_cli.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up 6 levels: a2a_client -> kit -> omni -> python -> omni.kit.a2a_client -> exts -> a2a
        project_root = os.path.abspath(os.path.join(current_dir, "../../../../../.."))
        mock_cli_path = os.path.join(project_root, "mock_opencode_cli.py")
        
        if not os.path.exists(mock_cli_path):
             # Fallback to CWD
             mock_cli_path = os.path.join(os.getcwd(), "mock_opencode_cli.py")

        self._server_command = f"python3 {mock_cli_path}"
        self._task_priority = "normal"
        self._latest_generated_code = ""
        self._last_instruction = ""
        self._is_processing = False
        self._log_lines = []
        self._build_ui()
        print(f"[omni.kit.a2a_client] startup ({ext_id})")

    def on_shutdown(self):
        print("[omni.kit.a2a_client] shutdown")
        if self._window:
            self._window.destroy()
            self._window = None

    def _build_ui(self):
        with self._window.frame:
            with ui.VStack(spacing=6):
                ui.Label("OpenCode ACP Command:", height=20)
                self._command_field = ui.StringField(height=20)
                self._command_field.model.set_value(self._server_command)
                ui.Label("(e.g., 'wsl opencode acp' or 'C:\\path\\to\\opencode.exe acp')", height=15, style={"color": 0xAAAAAA})

                ui.Label("Task Priority:", height=20)
                self._priority_field = ui.ComboBox(0, "normal", "high", "low")

                ui.Label("Instruction:", height=20)
                self._instruction_field = ui.StringField(height=20)

                with ui.HStack(height=30, spacing=6):
                    ui.Button("Generate Code", clicked_fn=self._on_send_task)
                    ui.Button("Apply", clicked_fn=self._on_apply_task)
                    ui.Button("Retry Last", clicked_fn=self._on_retry_last)

                ui.Label("Status:", height=20)
                self._status_label = ui.Label("Ready", height=20)
                ui.Label("Generated USDA Preview:", height=20)
                with ui.ScrollingFrame(height=300):
                    self._code_preview_label = ui.Label(
                        "No generated code yet.",
                        alignment=ui.Alignment.LEFT_TOP,
                    )
                ui.Label("ACP Log (JSON-RPC):", height=20)
                with ui.ScrollingFrame(height=180):
                    self._log_label = ui.Label(
                        "No logs yet.",
                        alignment=ui.Alignment.LEFT_TOP,
                    )

    def _on_send_task(self):
        if self._is_processing:
            self._status_label.text = "A request is already running."
            return

        instruction = self._instruction_field.model.get_value_as_string().strip()
        if not instruction:
            self._status_label.text = "Please enter an instruction."
            return

        self._server_command = self._command_field.model.get_value_as_string().strip()
        priority_idx = self._priority_field.model.get_item_value_model().as_int
        self._task_priority = ["normal", "high", "low"][priority_idx]
        self._last_instruction = instruction
        self._latest_generated_code = ""
        self._set_code_preview("Waiting for generated code...")
        asyncio.ensure_future(self._process_task_acp(instruction))

    def _on_retry_last(self):
        if self._is_processing:
            self._status_label.text = "A request is already running."
            return
        if not self._last_instruction:
            self._status_label.text = "No previous instruction to retry."
            return
        self._server_command = self._command_field.model.get_value_as_string().strip()
        priority_idx = self._priority_field.model.get_item_value_model().as_int
        self._task_priority = ["normal", "high", "low"][priority_idx]
        self._set_code_preview("Retrying previous instruction...")
        asyncio.ensure_future(self._process_task_acp(self._last_instruction))

    def _on_apply_task(self):
        if not self._latest_generated_code:
            self._status_label.text = "No generated code to apply. Generate first."
            return
        self._apply_changes(self._latest_generated_code)
        self._status_label.text = "Applied generated code."

    async def _process_task_acp(self, instruction):
        self._status_label.text = "Processing (ACP)..."
        self._is_processing = True

        stage = omni.usd.get_context().get_stage()
        if not stage:
            usd_content = '#usda 1.0\n(doc = "Mock Stage")\n'
        else:
            usd_content = stage.GetRootLayer().ExportToString()

        # Construct JSON-RPC Request
        request_id = 1
        rpc_request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "agent/generateCode",
            "params": {
                "instruction": instruction,
                "context": {
                    "code": usd_content,
                    "selection": [] # Todo: get real selection
                },
                "extraParams": {
                    "enableSyntaxCheck": True, 
                    "mode": "incremental",
                    "priority": self._task_priority
                },
            },
        }
        
        rpc_json = json.dumps(rpc_request)
        self._append_log(f"-> {rpc_json}")

        try:
            # Parse command
            # On Windows (nt), use posix=False to support backslashes in paths properly
            cmd_parts = shlex.split(self._server_command, posix=(os.name != "nt"))
            
            # Start Subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Send Request
            stdout, stderr = await process.communicate(input=rpc_json.encode())

            if stderr:
                err_msg = stderr.decode()
                print(f"[A2A] ACP Stderr: {err_msg}")
                # self._append_log(f"STDERR: {err_msg}") # Optional: show stderr in UI

            if stdout:
                response_line = stdout.decode().strip()
                self._append_log(f"<- {response_line}")
                
                try:
                    response = json.loads(response_line)
                    if "error" in response:
                        raise RuntimeError(f"RPC Error: {response['error']}")
                    
                    result = response.get("result", {})
                    generated_code = result.get("generatedCode", "")
                    self._latest_generated_code = generated_code
                    self._set_code_preview(generated_code or "<empty generatedCode>")
                    self._status_label.text = "Code generated via ACP. Click Apply."

                except json.JSONDecodeError:
                     raise RuntimeError(f"Invalid JSON response: {response_line}")
            else:
                 raise RuntimeError("Empty response from ACP process")

        except Exception as exc:
            self._status_label.text = f"ACP Failed: {exc}"
            self._append_log(f"Error: {exc}")
            print(f"[A2A] ACP Error: {exc}")
        finally:
            self._is_processing = False

    def _append_log(self, message):
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_lines.append(f"[{ts}] {message}")
        self._log_lines = self._log_lines[-40:]
        self._log_label.text = "\n".join(self._log_lines)

    def _set_code_preview(self, text):
        self._code_preview_label.text = text

    def _apply_changes(self, usda_code):
        # Placeholder for real USD patch application with undo grouping.
        self._append_log(f"Apply clicked, code_size={len(usda_code)}")
        print(f"[A2A] Applying changes:\n{usda_code}")
