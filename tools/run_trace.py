import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("167.99.77.39", username="root", password="^3b*GakE&SWn+Z", timeout=15)

# Upload trace script
sftp = client.open_sftp()
sftp.put("c:/POOL-BTC-USD/tools/trace_test.py", "/opt/pool-dashboard/tools/trace_test.py")
sftp.close()
print("Uploaded trace_test.py")

# Run trace script
_, stdout, stderr = client.exec_command("cd /opt/pool-dashboard && python3 tools/trace_test.py")

start = time.time()
while time.time() - start < 20:
    if stdout.channel.recv_ready():
        print(stdout.channel.recv(4096).decode(), end="")
    if stdout.channel.recv_stderr_ready():
        print("ERR: " + stderr.channel.recv_stderr(4096).decode(), end="")
    if stdout.channel.exit_status_ready():
        # Drain remaining output
        print(stdout.read().decode(), end="")
        print(stderr.read().decode(), end="")
        break
    time.sleep(0.5)

elapsed = time.time() - start
if not stdout.channel.exit_status_ready():
    print(f"\n[TIMEOUT after {elapsed:.1f}s] Script still running.")
else:
    print(f"\nDone in {elapsed:.1f}s, exit code: {stdout.channel.recv_exit_status()}")

client.close()
