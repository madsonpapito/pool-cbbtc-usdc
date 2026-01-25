import http.server
import socketserver
import subprocess
import json
import os
import sys

PORT = 3333
DIRECTORY = "."

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/sync':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            try:
                # Run the sync script
                print("Received sync request...")
                result = subprocess.run(
                    [sys.executable, "tools/sync.py"], 
                    capture_output=True, 
                    text=True
                )
                
                output = result.stdout
                error = result.stderr
                
                response = {
                    "success": result.returncode == 0,
                    "message": output if result.returncode == 0 else f"Error: {error}"
                }
                
                if result.returncode == 0:
                    print("Sync successful.")
                else:
                    print(f"Sync failed: {error}")
                    
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                self.wfile.write(json.dumps({"success": False, "message": str(e)}).encode())
        else:
            self.send_error(404)

    def do_GET(self):
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

if __name__ == "__main__":
    # Change into the project directory ensure relative paths in sync.py work
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # Actually, the file path above assumes server.py is in tools/server.py
    # So dirname is 'tools', and dirname(dirname) is project root.
    # Let's double check where we are running from. 
    # The command usually is python tools/server.py from project root.
    cwd = os.getcwd()
    print(f"Serving at port {PORT} from {cwd}")
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Local dashboard server running at http://localhost:{PORT}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()
