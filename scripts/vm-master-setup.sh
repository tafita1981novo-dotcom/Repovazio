#!/bin/bash
# ============================================================
# PSIDOC VM MASTER SETUP — Oracle A1.Flex Ubuntu 22.04
# Roda uma vez após criar a VM
# ============================================================
set -e

echo "======================================"
echo " PSIDOC VM SETUP — Rafael Oliveira"
echo "======================================"

# --- VARIÁVEIS INJETADAS PELO WORKFLOW ---
GROQ_API_KEY="${GROQ_API_KEY}"
GEMINI_API_KEY="${GEMINI_API_KEY}"
NVIDIA_API_KEY="${NVIDIA_API_KEY}"
DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY}"
GH_PAT="${GH_PAT}"
YOUTUBE_STREAM_KEY="${YOUTUBE_STREAM_KEY}"
SUPABASE_URL="https://tpjvalzwkqwttvmszvie.supabase.co"
SUPABASE_ANON_KEY="${SUPABASE_ANON_KEY}"
YOUTUBE_CHANNEL_ID="UCSH63tBfY6wEIdkC4u4zKdg"
YOUTUBE_REFRESH_TOKEN="${YOUTUBE_REFRESH_TOKEN}"
YOUTUBE_CLIENT_ID="${YOUTUBE_CLIENT_ID}"
YOUTUBE_CLIENT_SECRET="${YOUTUBE_CLIENT_SECRET}"
VERCEL_TOKEN="${VERCEL_TOKEN}"

# --- 1. SISTEMA BASE ---
echo "[1/8] Sistema base..."
sudo apt-get update -q
sudo apt-get install -y \
  curl wget git vim htop \
  ffmpeg python3 python3-pip python3-venv \
  nodejs npm docker.io nginx certbot \
  ufw fail2ban \
  build-essential -q

# Docker sem sudo
sudo usermod -aG docker ubuntu
sudo systemctl enable docker
sudo systemctl start docker

# --- 2. FIREWALL ---
echo "[2/8] Firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 11434/tcp # Ollama LLM
sudo ufw allow 8080/tcp  # Backend API
sudo ufw allow 3000/tcp  # Apps adicionais
sudo ufw --force enable

# --- 3. OLLAMA (LLM LOCAL GRATUITO) ---
echo "[3/8] Ollama + Llama 3.1 8B..."
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl enable ollama
sudo systemctl start ollama
sleep 5

# Baixar modelo Llama 3.1 8B (gratuito, roda em 24GB RAM)
ollama pull llama3.1:8b &
# Baixar Mistral 7B como alternativa
ollama pull mistral:7b &

# --- 4. ENV GLOBAL ---
echo "[4/8] Variáveis de ambiente..."
sudo tee /etc/environment << ENV_EOF
GROQ_API_KEY="${GROQ_API_KEY}"
GEMINI_API_KEY="${GEMINI_API_KEY}"
NVIDIA_API_KEY="${NVIDIA_API_KEY}"
DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY}"
GH_PAT="${GH_PAT}"
YOUTUBE_STREAM_KEY="${YOUTUBE_STREAM_KEY}"
YOUTUBE_CHANNEL_ID="${YOUTUBE_CHANNEL_ID}"
YOUTUBE_REFRESH_TOKEN="${YOUTUBE_REFRESH_TOKEN}"
YOUTUBE_CLIENT_ID="${YOUTUBE_CLIENT_ID}"
YOUTUBE_CLIENT_SECRET="${YOUTUBE_CLIENT_SECRET}"
SUPABASE_URL="${SUPABASE_URL}"
SUPABASE_ANON_KEY="${SUPABASE_ANON_KEY}"
VERCEL_TOKEN="${VERCEL_TOKEN}"
OLLAMA_HOST="0.0.0.0"
ENV_EOF

# .env para apps
mkdir -p /opt/psidoc
cat > /opt/psidoc/.env << ENV2_EOF
GROQ_API_KEY=${GROQ_API_KEY}
GEMINI_API_KEY=${GEMINI_API_KEY}
NVIDIA_API_KEY=${NVIDIA_API_KEY}
DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
GH_PAT=${GH_PAT}
YOUTUBE_STREAM_KEY=${YOUTUBE_STREAM_KEY}
YOUTUBE_CHANNEL_ID=${YOUTUBE_CHANNEL_ID}
YOUTUBE_REFRESH_TOKEN=${YOUTUBE_REFRESH_TOKEN}
YOUTUBE_CLIENT_ID=${YOUTUBE_CLIENT_ID}
YOUTUBE_CLIENT_SECRET=${YOUTUBE_CLIENT_SECRET}
SUPABASE_URL=${SUPABASE_URL}
SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
VERCEL_TOKEN=${VERCEL_TOKEN}
OLLAMA_BASE_URL=http://localhost:11434
ENV2_EOF
chmod 600 /opt/psidoc/.env

# --- 5. NGINX REVERSE PROXY ---
echo "[5/8] Nginx API gateway..."
sudo tee /etc/nginx/sites-available/psidoc << NGINX_EOF
server {
    listen 80;
    server_name _;

    # Ollama LLM
    location /llm/ {
        proxy_pass http://127.0.0.1:11434/;
        proxy_set_header Host \$host;
        add_header Access-Control-Allow-Origin "*";
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8080/;
        proxy_set_header Host \$host;
        add_header Access-Control-Allow-Origin "*";
    }

    # Health check
    location /health {
        return 200 '{"status":"ok","vm":"psidoc-oracle"}';
        add_header Content-Type application/json;
    }
}
NGINX_EOF
sudo ln -sf /etc/nginx/sites-available/psidoc /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# --- 6. BACKEND API (FastAPI) ---
echo "[6/8] Backend API..."
pip3 install fastapi uvicorn httpx python-dotenv requests -q --break-system-packages

cat > /opt/psidoc/api.py << 'API_EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx, os
from dotenv import load_dotenv

load_dotenv("/opt/psidoc/.env")
app = FastAPI(title="PSIDOC AI Gateway")

app.add_middleware(CORSMiddleware, allow_origins=["*"],
    allow_methods=["*"], allow_headers=["*"])

OLLAMA = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
GROQ   = "https://api.groq.com/openai/v1"

@app.get("/health")
def health():
    return {"status": "ok", "vm": "psidoc-oracle-arm"}

@app.post("/chat/local")
async def chat_local(payload: dict):
    """Llama 3.1 8B local — 100% gratuito, sem API key"""
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(f"{OLLAMA}/api/generate", json={
            "model": payload.get("model", "llama3.1:8b"),
            "prompt": payload.get("prompt", ""),
            "stream": False
        })
    return r.json()

@app.post("/chat/groq")
async def chat_groq(payload: dict):
    """Llama 3.1 70B via Groq — gratuito via API key"""
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(f"{GROQ}/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"},
            json={"model": "llama-3.1-70b-versatile",
                  "messages": payload.get("messages", [])})
    return r.json()

@app.get("/models")
async def list_models():
    """Lista modelos disponíveis localmente"""
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{OLLAMA}/api/tags")
    return r.json()
API_EOF

# Systemd service para API
sudo tee /etc/systemd/system/psidoc-api.service << SVC_EOF
[Unit]
Description=PSIDOC AI API Gateway
After=network.target ollama.service

[Service]
User=ubuntu
WorkingDirectory=/opt/psidoc
EnvironmentFile=/opt/psidoc/.env
ExecStart=/usr/bin/python3 -m uvicorn api:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVC_EOF

sudo systemctl daemon-reload
sudo systemctl enable psidoc-api
sudo systemctl start psidoc-api

# --- 7. STREAM YOUTUBE 24/7 ---
echo "[7/8] Stream YouTube 24/7..."
wget -qO /opt/psidoc/stream.sh \
  https://raw.githubusercontent.com/tafita81/Repovazio/main/scripts/oracle-forever-live-setup.sh
chmod +x /opt/psidoc/stream.sh
cd /opt/psidoc && STREAM_KEY="${YOUTUBE_STREAM_KEY}" bash stream.sh &

# --- 8. SWAP (evitar OOM com LLM) ---
echo "[8/8] Swap 8GB..."
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# --- AGUARDAR OLLAMA BAIXAR MODELOS ---
echo "Aguardando download dos modelos LLM..."
wait

# --- SALVAR IP E ENDPOINTS NO SUPABASE ---
MY_IP=$(curl -s ifconfig.me)
curl -s -X POST "${SUPABASE_URL}/rest/v1/ia_cache" \
  -H "apikey: ${SUPABASE_ANON_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_ANON_KEY}" \
  -H "Content-Type: application/json" \
  -H "Prefer: resolution=merge-duplicates" \
  -d "{\"cache_key\":\"vm_master_config\",\"value\":\"{\\\"ip\\\":\\\"${MY_IP}\\\",\\\"api\\\":\\\"http://${MY_IP}:8080\\\",\\\"llm\\\":\\\"http://${MY_IP}:11434\\\",\\\"health\\\":\\\"http://${MY_IP}/health\\\"}\",\"expires_at\":null}"

echo ""
echo "======================================"
echo " SETUP COMPLETO!"
echo " IP: ${MY_IP}"
echo " API:    http://${MY_IP}:8080"
echo " LLM:    http://${MY_IP}:11434"
echo " Health: http://${MY_IP}/health"
echo " Chat local: POST http://${MY_IP}:8080/chat/local"
echo " Chat Groq:  POST http://${MY_IP}:8080/chat/groq"
echo "======================================"
