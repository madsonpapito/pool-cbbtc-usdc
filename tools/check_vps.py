import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('167.99.77.39', username='root', password='^3b*GakE&SWn+Z')

# Check sync status
print("=== SYNC STATUS ===")
stdin, stdout, stderr = client.exec_command('curl -s http://localhost:3333/api/sync/status')
print(stdout.read().decode())

# Check recent logs
print("\n=== RECENT LOGS (last 30 lines) ===")
stdin, stdout, stderr = client.exec_command("journalctl -u pool-dashboard -n 30 --no-pager")
print(stdout.read().decode())

# Check if any python processes are running
print("\n=== RUNNING PYTHON PROCESSES ===")
stdin, stdout, stderr = client.exec_command("ps aux | grep python3 | grep -v grep")
print(stdout.read().decode())

# Check fees_data files
print("\n=== FEES DATA FILES ===")
stdin, stdout, stderr = client.exec_command("ls -la /opt/pool-dashboard/data/*/fees_data.json 2>/dev/null; echo '---'; cat /opt/pool-dashboard/data/*/fees_data.json 2>/dev/null | python3 -c \"import sys,json; [print(json.dumps(json.load(open(f)), indent=2)) for f in sys.argv[1:]]\" 2>/dev/null || echo 'No fees data yet'")
print(stdout.read().decode())

# Check fees_data content directly
print("\n=== FEES DATA CONTENT ===")
stdin, stdout, stderr = client.exec_command("for f in /opt/pool-dashboard/data/*/fees_data.json; do echo \"--- $f ---\"; cat \"$f\" 2>/dev/null | python3 -m json.tool 2>/dev/null || echo 'not found'; done")
print(stdout.read().decode())

client.close()
