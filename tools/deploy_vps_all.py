import paramiko
import os

host = '167.99.77.39'
user = 'root'
pw = '^3b*GakE&SWn+Z'

files_to_upload = [
    "sync.py",
    "dashboard_gen_v3.py",
    "fetch_pool_data.py",
    "fetch_collected_fees.py",
    "update_history.py",
    "server.py",
    "pools.json"
]

print("Connecting to VPS...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=pw, timeout=15)

sftp = client.open_sftp()
remote_dir = "/opt/pool-dashboard/tools"

for filename in files_to_upload:
    local_path = os.path.join("tools", filename)
    remote_path = f"{remote_dir}/{filename}"
    if os.path.exists(local_path):
        print(f"Uploading {filename}...")
        sftp.put(local_path, remote_path)
    else:
        print(f"Warning: Local file {local_path} not found.")

sftp.close()

def run(cmd):
    print(f">>> {cmd}")
    _, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out: print(out)
    if err: print(f"ERR: {err}")

print("Fixing permissions and restarting service...")
run("chown -R www-data:www-data /opt/pool-dashboard")
run("systemctl daemon-reload")
run("systemctl restart pool-dashboard")
run("systemctl status pool-dashboard --no-pager | head -n 10")

# Trigger a sync
print("Triggering sync...")
run("curl -X POST http://localhost:3333/api/sync")

client.close()
print("\nDeployment complete!")
