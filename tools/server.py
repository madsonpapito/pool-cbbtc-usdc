import http.server
import socketserver
import subprocess
import json
import os
import sys
import threading

PORT = 3333
DIRECTORY = "."

# Track sync state
sync_status = {"running": False, "last_result": None}

def run_sync_background():
    """Run sync.py in a background thread."""
    global sync_status
    sync_status["running"] = True
    sync_status["last_result"] = None
    print("Starting sync in background...")
    
    try:
        result = subprocess.run(
            [sys.executable, "tools/sync.py"],
            capture_output=True,
            text=True,
            timeout=600  # 10 min hard limit
        )
        
        if result.returncode == 0:
            print("Sync completed successfully.")
            sync_status["last_result"] = {"success": True, "message": "Sync complete!"}
        else:
            error_msg = result.stderr[:500] if result.stderr else "Unknown error"
            print(f"Sync failed: {error_msg}")
            sync_status["last_result"] = {"success": False, "message": f"Error: {error_msg}"}
    except subprocess.TimeoutExpired:
        print("Sync timed out after 10 minutes.")
        sync_status["last_result"] = {"success": False, "message": "Sync timed out after 10 minutes."}
    except Exception as e:
        print(f"Sync exception: {e}")
        sync_status["last_result"] = {"success": False, "message": str(e)}
    finally:
        sync_status["running"] = False

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/sync':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            if sync_status["running"]:
                response = {"success": True, "message": "Sync already in progress, please wait..."}
            else:
                # Start sync in background thread
                thread = threading.Thread(target=run_sync_background, daemon=True)
                thread.start()
                response = {"success": True, "message": "Sync started! Dashboard will update in a few minutes."}
            
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_error(404)

    def do_GET(self):
        if self.path == '/api/sync/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "running": sync_status["running"],
                "last_result": sync_status["last_result"]
            }
            self.wfile.write(json.dumps(response).encode())
            return
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cwd = os.getcwd()
    print(f"Serving at port {PORT} from {cwd}")
    
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Local dashboard server running at http://localhost:{PORT}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()
