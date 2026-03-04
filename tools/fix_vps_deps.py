import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("167.99.77.39", username="root", password="^3b*GakE&SWn+Z", timeout=15)

def run(cmd, timeout=120):
    print(f"\n>>> {cmd}")
    _, stdout, stderr = client.exec_command(cmd)
    start = time.time()
    while time.time() - start < timeout:
        if stdout.channel.recv_ready():
            print(stdout.channel.recv(4096).decode(), end="")
        if stdout.channel.recv_stderr_ready():
            print(stderr.channel.recv_stderr(4096).decode(), end="")
        if stdout.channel.exit_status_ready():
            print(stdout.read().decode(), end="")
            print(stderr.read().decode(), end="")
            break
        time.sleep(0.5)
    rc = stdout.channel.recv_exit_status()
    elapsed = time.time() - start
    print(f"\n[exit={rc}, {elapsed:.1f}s]")

# 1. Install missing dependencies
run("pip3 install web3 requests", timeout=120)

# 2. Verify they work
run("python3 -c 'from web3 import Web3; print(Web3); import requests; print(requests)'")

# 3. Pull latest code to the VPS
run("cd /opt/pool-dashboard && chown -R root:root . && git pull origin main && chown -R www-data:www-data .")

# 4. Restart service
run("systemctl restart pool-dashboard")
time.sleep(2)
run("systemctl status pool-dashboard")

# 5. Test the API endpoint directly
print("\n--- TESTING SYNC API ---")
run("curl -s -X POST http://localhost:3333/api/sync", timeout=30)

client.close()
print("\n\nALL DONE.")
