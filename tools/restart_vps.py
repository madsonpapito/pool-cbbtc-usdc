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

# 1. Stop service and kill everything
run("systemctl stop pool-dashboard")
time.sleep(1)
run("killall -9 python3 2>/dev/null; sleep 2; echo killed")

# 2. Upload new server.py with SO_REUSEADDR
sftp = client.open_sftp()
sftp.put("c:/POOL-BTC-USD/tools/server.py", "/opt/pool-dashboard/tools/server.py")
sftp.close()
print("\nUploaded new server.py")
run("chown www-data:www-data /opt/pool-dashboard/tools/server.py")

# 3. Wait for port to clear
time.sleep(3)
run("ss -tlnp | grep 3333 || echo 'Port 3333 is free'")

# 4. Start service
run("systemctl start pool-dashboard")
time.sleep(2)
run("systemctl status pool-dashboard")

# 5. Test sync
print("\n=== TESTING SYNC ===")
run("curl -s -X POST http://localhost:3333/api/sync")
time.sleep(3)
run("curl -s http://localhost:3333/api/sync/status")

client.close()
print("\nDONE.")
