#!/bin/bash
cd /root/pool-cbbtc-usdc || exit 1

# Criar Dockerfile
cat << 'EOF' > Dockerfile
FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential curl software-properties-common git && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir python-dotenv
COPY . .
EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
EOF

# Criar docker-compose.yml
cat << 'EOF' > docker-compose.yml
version: '3.8'
services:
  streamlit:
    build: .
    container_name: pool-tracker-app
    ports:
      - "8501:8501"
    volumes:
      - .:/app
    environment:
      - RPC_URL=${RPC_URL:-https://mainnet.base.org}
    restart: always

  sync:
    build: .
    container_name: pool-tracker-sync
    volumes:
      - .:/app
    environment:
      - RPC_URL=${RPC_URL:-https://mainnet.base.org}
    entrypoint: ["/bin/sh", "-c", "while true; do python tools/sync.py; sleep 3600; done"]
    restart: always
EOF

# Criar .env
echo "RPC_URL=https://mainnet.base.org" > .env

# Iniciar containers
docker-compose up -d --build
