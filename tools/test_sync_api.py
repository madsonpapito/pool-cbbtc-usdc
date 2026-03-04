import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("167.99.77.39", username="root", password="^3b*GakE&SWn+Z", timeout=15)

lines = []
def run(cmd):
    lines.append(f"\n>>> {cmd}")
    _, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    for line in out.splitlines():
        lines.append(line)
    if err:
        for line in err.splitlines():
            lines.append(f"ERR: {line}")

run("curl -s -X POST http://localhost:3333/api/sync")
run("curl -s http://localhost:3333/api/sync/status")
run("systemctl is-active pool-dashboard")
run("ps aux | grep -E '(sync|fetch)' | grep -v grep")

client.close()

with open("test_result.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("Saved to test_result.txt")
