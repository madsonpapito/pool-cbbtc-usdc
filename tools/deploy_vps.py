import paramiko
import sys

host = '167.99.77.39'
user = 'root'
pw = '^3b*GakE&SWn+Z'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=pw, timeout=15)

def run(cmd, timeout=60):
    short = cmd.split('\n')[0][:80]
    print(f'>>> {short}')
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out: print(out[-500:])
    if err and 'warning' not in err.lower(): print(f'ERR: {err[-200:]}')
    print()
    return out

# 1. Write nginx config
nginx_conf = """server {
    listen 80;
    server_name _;
    
    root /opt/pool-dashboard;
    index index.html;
    
    location / {
        try_files $uri $uri/ =404;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:3333;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300;
    }
}
"""
run(f"cat > /etc/nginx/sites-available/pool-dashboard << 'EOF'\n{nginx_conf}EOF")

# 2. Enable nginx site
run('rm -f /etc/nginx/sites-enabled/default')
run('ln -sf /etc/nginx/sites-available/pool-dashboard /etc/nginx/sites-enabled/')
run('nginx -t')
run('systemctl restart nginx')
run('systemctl enable nginx')

# 3. Write systemd service
systemd_svc = """[Unit]
Description=Pool Dashboard API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/pool-dashboard
ExecStart=/usr/bin/python3 /opt/pool-dashboard/tools/server.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""
run(f"cat > /etc/systemd/system/pool-dashboard.service << 'EOF'\n{systemd_svc}EOF")

# 4. Enable and start service
run('systemctl daemon-reload')
run('systemctl enable pool-dashboard')
run('systemctl restart pool-dashboard')
run('sleep 2 && systemctl status pool-dashboard --no-pager -l')

# 5. Firewall
run('ufw allow 80/tcp 2>/dev/null; ufw allow 22/tcp 2>/dev/null; echo firewall_ok')

# 6. Verify
run('curl -s http://localhost/ | head -3')

client.close()
print('\n=== DEPLOY COMPLETE ===')
print(f'Dashboard: http://{host}/')
