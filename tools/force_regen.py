import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("167.99.77.39", username="root", password="^3b*GakE&SWn+Z", timeout=15)

# O segredo é rodar o script de dentro da pasta correta e garantir as permissões
script = """
set -e
echo "--- Regenerating Dashboard ---"
cd /opt/pool-dashboard
python3 tools/dashboard_gen_v3.py

echo "--- Fixing Permissions ---"
chown www-data:www-data /opt/pool-dashboard/index.html
chmod 644 /opt/pool-dashboard/index.html

echo "--- Verifying Result ---"
ls -l /opt/pool-dashboard/index.html
grep "Last Updated" /opt/pool-dashboard/index.html | head -n 1 || echo "No date found in HTML"
date
"""

_, stdout, stderr = client.exec_command(script)
print(stdout.read().decode())
print(stderr.read().decode())
client.close()
