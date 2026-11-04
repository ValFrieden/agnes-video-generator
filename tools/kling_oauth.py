import base64
import hashlib
import json
import os
import secrets
import subprocess
import sys
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8089
REDIRECT_URI = f"http://localhost:{PORT}/callback"
REGISTRATION_ENDPOINT = "https://kling.ai/auth/register"
AUTHORIZE_ENDPOINT = "https://kling.ai/auth/authorize"
TOKEN_ENDPOINT = "https://kling.ai/auth/token"
SCOPES = "generation.create generation.read account.credit.read"

GEMINI_DIR = os.path.expanduser(r"~\.gemini")
CONFIG_PATH = os.path.join(GEMINI_DIR, "config", "mcp_config.json")
SAVED_CREDS_PATH = os.path.join(GEMINI_DIR, "kling_oauth.json")
AGY_EXE = os.path.join(GEMINI_DIR, "bin", "agy.exe")

def generate_pkce():
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge

def register_client():
    payload = {
        "client_name": "Antigravity MCP Client",
        "redirect_uris": [REDIRECT_URI]
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        REGISTRATION_ENDPOINT,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res["client_id"]

def update_mcp_config(access_token):
    # Method 1: Using agy.exe if available
    if os.path.exists(AGY_EXE):
        try:
            cmd = [
                AGY_EXE, "mcp", "add",
                "--header", f"Authorization: Bearer {access_token}",
                "kling", "https://kling.ai/mcp"
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("[OAuth] agy.exe updated kling MCP server with Authorization header.")
        except Exception as e:
            print(f"[OAuth] Warning: agy.exe update failed: {e}")

    # Method 2: Direct update of mcp_config.json
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if "mcpServers" not in cfg:
                cfg["mcpServers"] = {}
            cfg["mcpServers"]["kling"] = {
                "disabled": False,
                "serverUrl": "https://kling.ai/mcp",
                "headers": {
                    "Authorization": f"Bearer {access_token}"
                }
            }
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
            print(f"[OAuth] Successfully updated {CONFIG_PATH}")
        except Exception as e:
            print(f"[OAuth] Warning: direct config update failed: {e}")

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    client_id = None
    code_verifier = None
    expected_state = None
    server_instance = None

    def log_message(self, format, *args):
        # Suppress default noisy console logs
        sys.stderr.write(f"[HTTP] {format % args}\n")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            return

        params = urllib.parse.parse_qs(parsed.query)
        code = params.get("code", [None])[0]
        state = params.get("state", [None])[0]
        error = params.get("error", [None])[0]

        if error:
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            err_html = f"<h2>Authorization Error</h2><p>{error}</p>"
            self.wfile.write(err_html.encode("utf-8"))
            return

        if not code or state != self.expected_state:
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h2>Invalid authorization state or code missing.</h2>")
            return

        # Exchange code for token
        try:
            token_data = urllib.parse.urlencode({
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "code_verifier": self.code_verifier,
            }).encode("utf-8")

            req = urllib.request.Request(
                TOKEN_ENDPOINT,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                token_resp = json.loads(resp.read().decode("utf-8"))

            access_token = token_resp.get("access_token")
            refresh_token = token_resp.get("refresh_token")
            expires_in = token_resp.get("expires_in")

            if not access_token:
                raise ValueError(f"No access token returned: {token_resp}")

            # Save full tokens
            creds = {
                "client_id": self.client_id,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": expires_in,
                "token_endpoint": TOKEN_ENDPOINT,
                "scopes": SCOPES
            }
            with open(SAVED_CREDS_PATH, "w", encoding="utf-8") as f:
                json.dump(creds, f, indent=2)
            print(f"[OAuth] Credentials saved to {SAVED_CREDS_PATH}")

            # Update MCP config
            update_mcp_config(access_token)

            # Send success response
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Kling AI Connected</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
    .card { background: #1e293b; padding: 40px 50px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); text-align: center; max-width: 480px; border: 1px solid #334155; }
    h1 { color: #38bdf8; margin-top: 0; font-size: 1.8rem; }
    p { color: #94a3b8; font-size: 1.05rem; line-height: 1.5; }
    .badge { display: inline-block; background: #065f46; color: #34d399; padding: 6px 14px; border-radius: 20px; font-weight: 600; font-size: 0.9rem; margin-bottom: 15px; }
  </style>
</head>
<body>
  <div class="card">
    <div class="badge">&#10003; Успешно</div>
    <h1>Kling AI MCP подключен!</h1>
    <p>Авторизация успешно завершена. MCP-сервер настроен в Antigravity.<br><br>Вы можете закрыть эту вкладку и вернуться в чат.</p>
  </div>
</body>
</html>"""
            self.wfile.write(html.encode("utf-8"))
            print("[OAuth] SUCCESS! Kling AI MCP server authorized successfully.")
            # Trigger clean shutdown
            self.server_instance.should_stop = True

        except Exception as e:
            print(f"[OAuth] Error exchanging token: {e}")
            self.send_response(500)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            err_html = f"<h2>Token Exchange Error</h2><p>{e}</p>"
            self.wfile.write(err_html.encode("utf-8"))

def main():
    print("[OAuth] Registering client with Kling AI...", flush=True)
    client_id = register_client()
    print(f"[OAuth] Registered client_id: {client_id}", flush=True)

    verifier, challenge = generate_pkce()
    state = secrets.token_urlsafe(16)

    # Persist state so it survives any transient issues
    state_file = os.path.join(os.path.dirname(__file__), ".oauth_state.json")
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump({
            "client_id": client_id,
            "code_verifier": verifier,
            "state": state
        }, f)

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state
    }
    auth_url = f"{AUTHORIZE_ENDPOINT}?{urllib.parse.urlencode(params)}"

    OAuthCallbackHandler.client_id = client_id
    OAuthCallbackHandler.code_verifier = verifier
    OAuthCallbackHandler.expected_state = state

    server = HTTPServer(("127.0.0.1", PORT), OAuthCallbackHandler)
    server.should_stop = False
    OAuthCallbackHandler.server_instance = server

    print("\n" + "="*70, flush=True)
    print("KLING AI MCP AUTHORIZATION URL:", flush=True)
    print(auth_url, flush=True)
    print("="*70 + "\n", flush=True)

    # Try opening browser automatically
    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    print(f"[OAuth] Waiting for authorization callback on {REDIRECT_URI}...", flush=True)
    server.timeout = 300 # 5 minutes timeout
    while not server.should_stop:
        server.handle_request()

    print("[OAuth] Server stopped. All done!")

if __name__ == "__main__":
    main()
