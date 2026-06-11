#!/bin/bash
# ============================================================
# DEPLOY MEMORY STACK — Oracle Cloud ARM (sa-saopaulo-1)
# Execute este script NA VM Oracle como ubuntu user
# Tempo estimado: 5-8 minutos
# ============================================================
set -e

echo "🚀 Deploy Quantum Brain Memory Stack"
echo "======================================"

# ── 1. INSTALAR DOCKER ───────────────────────────────────────────────────────
if ! command -v docker &> /dev/null; then
  echo "📦 Instalando Docker..."
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker ubuntu
  echo "✅ Docker instalado"
else
  echo "✅ Docker já instalado"
fi

# ── 2. INSTALAR DOCKER COMPOSE ───────────────────────────────────────────────
if ! command -v docker-compose &> /dev/null; then
  echo "📦 Instalando Docker Compose..."
  sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose
  echo "✅ Docker Compose instalado"
fi

# ── 3. CRIAR ESTRUTURA ───────────────────────────────────────────────────────
echo "📁 Criando estrutura de diretórios..."
mkdir -p /home/ubuntu/memory-stack
mkdir -p /home/ubuntu/obsidian-mcp
mkdir -p /home/ubuntu/vault/{channels,affiliates,rules,infra,milestones,memory}

# ── 4. COPIAR ARQUIVOS (já copiados via scp ou git pull) ─────────────────────
# Se veio via git:
# cd /home/ubuntu && git clone https://github.com/tafita81/Repovazio && cd Repovazio

# Copiar server obsidian
if [ -f /home/ubuntu/Repovazio/memory-stack/obsidian_mcp_server.js ]; then
  cp /home/ubuntu/Repovazio/memory-stack/obsidian_mcp_server.js /home/ubuntu/obsidian-mcp/server.js
  echo "✅ obsidian server copiado do Repovazio"
fi

# ── 5. CRIAR .ENV ────────────────────────────────────────────────────────────
echo "⚙️  Criando .env..."
cat > /home/ubuntu/memory-stack/.env << ENV
# Graphiti MCP
GROQ_API_KEY2=${GROQ_API_KEY2:-COLOQUE_AQUI}

# Obsidian Vault
GITHUB_TOKEN=${GITHUB_TOKEN:-COLOQUE_AQUI}
ENV

echo ""
echo "⚠️  EDITE /home/ubuntu/memory-stack/.env com suas chaves antes de continuar!"
echo "   GROQ_API_KEY2 = chave do Groq (obter em console.groq.com, grátis)"
echo "   GITHUB_TOKEN  = token GitHub com permissão repo (para sync vault)"
echo ""

# ── 6. INSTALAR DEPS DO OBSIDIAN MCP ─────────────────────────────────────────
echo "📦 Instalando dependências Obsidian MCP..."
cd /home/ubuntu/obsidian-mcp
cat > package.json << PKG
{
  "name": "obsidian-mcp",
  "version": "1.0.0",
  "main": "server.js",
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.9.0",
    "gray-matter": "^4.0.3",
    "glob": "^11.0.0"
  }
}
PKG
npm install --quiet
echo "✅ Dependências instaladas"

# ── 7. SUBIR STACK ───────────────────────────────────────────────────────────
echo ""
echo "🐳 Iniciando Docker Compose..."
cd /home/ubuntu/memory-stack
docker-compose up -d falkordb graphiti-mcp

echo ""
echo "⏳ Aguardando FalkorDB ficar pronto..."
sleep 15

# ── 8. INICIAR OBSIDIAN MCP (diretamente com node, mais leve) ────────────────
echo "🗒️  Iniciando Obsidian MCP..."
pkill -f "node.*server.js" 2>/dev/null || true
nohup node /home/ubuntu/obsidian-mcp/server.js \
  > /var/log/obsidian-mcp.log 2>&1 &
echo "✅ Obsidian MCP iniciado (PID: $!)"

# ── 9. VERIFICAR SAÚDE ───────────────────────────────────────────────────────
echo ""
echo "🔍 Verificando saúde dos serviços..."
sleep 10

GRAPHITI_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8765/health || echo "000")
OBSIDIAN_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8766/health || echo "000")
FALKOR_OK=$(redis-cli -p 6379 ping 2>/dev/null || echo "FAIL")

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "RESULTADO DO DEPLOY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "FalkorDB (6379):    $([ "$FALKOR_OK" = "PONG" ] && echo "✅ OK" || echo "❌ FALHOU")"
echo "Graphiti MCP (8765): $([ "$GRAPHITI_OK" = "200" ] && echo "✅ OK" || echo "⚠️  $GRAPHITI_OK (pode demorar mais)")"
echo "Obsidian MCP (8766): $([ "$OBSIDIAN_OK" = "200" ] && echo "✅ OK" || echo "⚠️  $OBSIDIAN_OK (pode demorar mais)")"
echo ""
echo "📌 IPs para configurar nos GitHub Secrets:"
PUBLIC_IP=$(curl -s ifconfig.me || echo "OBTER_MANUALMENTE")
echo "GRAPHITI_MCP_URL=http://${PUBLIC_IP}:8765/sse"
echo "OBSIDIAN_MCP_URL=http://${PUBLIC_IP}:8766/sse"
echo ""
echo "⚠️  ABRIR PORTAS NO ORACLE CLOUD:"
echo "   Console Oracle → Networking → VCN → Security Lists"
echo "   Adicionar: TCP 8765, TCP 8766, TCP 6379 (APENAS para IP seu)"
echo ""
echo "✅ Deploy completo!"
