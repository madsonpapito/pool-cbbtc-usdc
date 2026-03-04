import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("167.99.77.39", username="root", password="^3b*GakE&SWn+Z", timeout=15)

script = """
echo "--- Finding index.html ---"
find /opt/pool-dashboard -name "index.html" -ls
echo "--- Latest JSON files ---"
ls -alt /opt/pool-dashboard/tools/*.json | head -10
echo "--- Dashboard Generator Output Constant ---"
grep "OUTPUT_FILE =" /opt/pool-dashboard/tools/dashboard_gen_v3.py
echo "--- Sync script Dashboard call ---"
grep -A 5 "dashboard_gen_v3" /opt/pool-dashboard/tools/sync.py
echo "--- Current Date ---"
date
"""

_, stdout, _ = client.exec_command(script)
print(stdout.read().decode())
client.close()
