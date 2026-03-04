import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("167.99.77.39", username="root", password="^3b*GakE&SWn+Z", timeout=15)

def run(cmd):
    print(f"\n>>> {cmd}")
    _, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    for line in out.splitlines():
        print(line)
    if err:
        for line in err.splitlines():
            print(f"ERR: {line}")

# 1. Upload the new server.py
sftp = client.open_sftp()
sftp.put("c:/POOL-BTC-USD/tools/server.py", "/opt/pool-dashboard/tools/server.py")
sftp.close()
print("Uploaded server.py")

# 2. Fix permissions
run("chown www-data:www-data /opt/pool-dashboard/tools/server.py")

# 3. Restart the service
run("systemctl restart pool-dashboard")
time.sleep(2)
run("systemctl status pool-dashboard")

# 4. Quick test the API
run("curl -s -X POST http://localhost:3333/api/sync")

# 5. Check status endpoint
time.sleep(2)
run("curl -s http://localhost:3333/api/sync/status")

client.close()
print("\nDEPLOY DONE.")
