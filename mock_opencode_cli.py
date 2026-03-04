import sys
import json
import time
import random
import threading

def log(msg):
    # Log to stderr to avoid interfering with stdout JSON-RPC
    sys.stderr.write(f"[MockACP] {msg}\n")
    sys.stderr.flush()

def handle_request(line):
    try:
        request = json.loads(line)
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        log(f"Received request: {method} (id={request_id})")

        # Simulate processing delay
        time.sleep(random.uniform(0.1, 0.5))

        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "serverInfo": {"name": "MockOpenCode", "version": "1.0"},
                    "capabilities": {}
                }
            }
        elif method == "agent/generateCode":
            instruction = params.get("instruction", "").lower()
            
            if "optimize" in instruction:
                generated_code = "#usda 1.0\n(doc = \"Optimized Stage\")\ndef Xform \"World\" {\n    def Sphere \"Ball\" {\n        double radius = 2.0\n    }\n}"
            elif "material" in instruction:
                generated_code = "#usda 1.0\ndef Material \"MyMaterial\" {\n    token outputs:surface.connect = </MyMaterial/PBRShader.outputs:surface>\n    def Shader \"PBRShader\" {\n        uniform token info:id = \"UsdPreviewSurface\"\n        color3f inputs:diffuseColor = (1, 0, 0)\n    }\n}"
            else:
                generated_code = "#usda 1.0\n(doc = \"Default Response\")\ndef Scope \"Generated\" {}"

            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "generatedCode": generated_code,
                    "status": "completed",
                    "message": "Task completed successfully"
                }
            }
        else:
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": "Method not found"
                }
            }

        # Write response to stdout
        print(json.dumps(response), flush=True)
        log(f"Sent response for id={request_id}")

    except json.JSONDecodeError:
        log("Error: Invalid JSON received")
    except Exception as e:
        log(f"Error: {str(e)}")

def main():
    log("Starting Mock OpenCode ACP Server...")
    # ACP usually waits for commands on stdin
    for line in sys.stdin:
        if not line:
            break
        handle_request(line.strip())

if __name__ == "__main__":
    main()
