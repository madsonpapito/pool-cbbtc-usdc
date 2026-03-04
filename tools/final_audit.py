import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("167.99.77.39", username="root", password="^3b*GakE&SWn+Z", timeout=15)

script = """
echo "--- Checking Index Files ---"
ls -l /opt/pool-dashboard/index.html
ls -l /opt/pool-dashboard/tools/index.html

echo "--- Checking Running Data Processes ---"
ps aux | grep -v grep | grep -E "python3 tools/(sync|fetch|dashboard_gen)"

echo "--- Current Server Time ---"
date

echo "--- Force Dashboard Update (Final Run) ---"
cd /opt/pool-dashboard && python3 tools/dashboard_gen_v3.py
ls -l /opt/pool-dashboard/index.html
"""

_, stdout, stderr = client.exec_command(script)
print(stdout.read().decode())
print(stderr.read().decode())
client.close()
