import re

path = '/opt/pool-dashboard/tools/dashboard_gen_v3.py'

with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# Remove the isVercel block
code = re.sub(
    r'const isVercel = !window.*?return;\s*?}',
    '// Removed localhost restriction for VPS',
    code,
    flags=re.DOTALL
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print('Fixed dashboard_gen_v3.py on VPS')
