import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("167.99.77.39", username="root", password="^3b*GakE&SWn+Z", timeout=15)

lines = []

def run(cmd):
    lines.append(f"\n>>> {cmd}")
    _, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode()
    for line in out.splitlines():
        lines.append(line)

run("ls -la /opt/")
run("ls -la /var/www/")
run("ls -la /root/")
run("systemctl list-units --type=service --state=running")
run("ps aux --sort=-%mem | head -20")
run("cat /etc/nginx/sites-enabled/* 2>/dev/null || echo 'no sites-enabled'")
run("ls /etc/nginx/sites-available/")

client.close()

with open("vps_inventory.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("Saved to vps_inventory.txt")
