#!/bin/bash
# Instalação completa para VM GCP Ubuntu
# Cole e rode como: bash setup_vm_dbn.sh

set -e
echo "=== Instalando dependências ==="
sudo apt-get update -q
sudo apt-get install -y ffmpeg python3 python3-pip -q

echo "=== Baixando script de live ==="
mkdir -p ~/noise-live
curl -sL "https://raw.githubusercontent.com/tafita1981novo-dotcom/Repovazio/main/scripts/dbn_live_vm.py" \
     -o ~/noise-live/dbn_live.py

echo "=== Criando systemd service (reinicia automaticamente) ==="
cat > /tmp/dbn-live.service << SERVICE
[Unit]
Description=DBN Live 24/7 Brown Noise
After=network.target
Restart=always

[Service]
User=$USER
WorkingDirectory=/home/$USER/noise-live
Environment="DEEP_BROWN_STREAM_KEY=COLOQUE_SUA_KEY_AQUI"
ExecStart=/usr/bin/python3 /home/$USER/noise-live/dbn_live.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

sudo mv /tmp/dbn-live.service /etc/systemd/system/dbn-live.service

echo ""
echo "=== PRÓXIMO PASSO ==="
echo "1. Edite a stream key:"
echo "   sudo nano /etc/systemd/system/dbn-live.service"
echo "   (troque COLOQUE_SUA_KEY_AQUI pela sua stream key do YouTube)"
echo ""
echo "2. Inicie o serviço:"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable dbn-live"
echo "   sudo systemctl start dbn-live"
echo ""
echo "3. Verifique se está rodando:"
echo "   sudo systemctl status dbn-live"
echo "   journalctl -u dbn-live -f"
