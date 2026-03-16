import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('167.99.77.39', username='root', password='^3b*GakE&SWn+Z')

# Check what python processes are running with full command line
print("=== PYTHON PROCESSES ===")
stdin, stdout, stderr = client.exec_command("ps aux | grep python3 | grep -v grep")
print(stdout.read().decode())

# Try to find any recent sync output files or temp files
print("\n=== DATA DIRECTORY STRUCTURE ===")
stdin, stdout, stderr = client.exec_command("find /opt/pool-dashboard/data -type f -ls 2>/dev/null")
print(stdout.read().decode())

# Check if there's a sync log being written
print("\n=== SYNC OUTPUT (if redirected) ===")
stdin, stdout, stderr = client.exec_command("cat /opt/pool-dashboard/sync_output.log 2>/dev/null | tail -n 30 || echo 'No sync log file'")
print(stdout.read().decode())

# Check the sync.py to understand how it calls fetch_collected_fees
print("\n=== SYNC.PY HEAD ===")
stdin, stdout, stderr = client.exec_command("head -100 /opt/pool-dashboard/tools/sync.py")
print(stdout.read().decode())

client.close()
