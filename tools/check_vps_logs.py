import paramiko

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

run("cat /etc/nginx/sites-available/pool-dashboard")
run("tail -n 10 /var/log/nginx/error.log")
run("journalctl -u pool-dashboard -n 20 --no-pager")
run("ls -la /opt/pool-dashboard/index.html")

client.close()
