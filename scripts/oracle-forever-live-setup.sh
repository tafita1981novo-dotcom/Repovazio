#!/bin/bash
# psicologia.doc - Oracle Cloud Free Tier Forever Live
# Cerebro do canal: 20px, 2% opacidade, pisca 0.3s/5s - garante anuncios YouTube
STREAM_KEY="${1:-uaqu-vx24-86d8-r0wy-0jwc}"
BRAIN_URL='https://yt3.googleusercontent.com/4NDK-JaBRi0uMyCCeOz-imtfhs6zHuQ2sxUn3d2gCjY_NyS_Z50OCENLFZrS_RjY5wOwKXch=s900-c-k-c0x00ffffff-no-rj'
set -e
apt-get update -q && apt-get install -y ffmpeg python3-pip wget imagemagick
pip3 install numpy --break-system-packages 2>/dev/null || true
mkdir -p /opt/psidoc

# Baixar cerebro branco do canal YouTube
wget -q -O /opt/psidoc/brain_orig.jpg "$BRAIN_URL"
convert /opt/psidoc/brain_orig.jpg -resize 20x20! -alpha set -background none /opt/psidoc/brain.png 2>/dev/null || cp /opt/psidoc/brain_orig.jpg /opt/psidoc/brain.png
echo "Cerebro baixado"

# Gerar audio binaural 432Hz (canal esq=432Hz, dir=436Hz = 4Hz delta)
python3 -c "
import numpy as np, wave
SR=44100; DUR=10800
t=__import__('numpy').linspace(0,DUR,int(SR*DUR),endpoint=False)
L=(np.sin(2*np.pi*432*t)*0.3*32767).astype(np.int16)
R=(np.sin(2*np.pi*436*t)*0.3*32767).astype(np.int16)
fade=int(SR*30)
for a in[L,R]: a[:fade]=(a[:fade]*np.linspace(0,1,fade)).astype(np.int16)
d=np.empty(len(t)*2,dtype=np.int16); d[0::2]=L; d[1::2]=R
f=wave.open('/opt/psidoc/binaural.wav','w'); f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR); f.writeframes(d.tobytes()); f.close()
print('audio ok')"

ffmpeg -i /opt/psidoc/binaural.wav -c:a libmp3lame -b:a 192k /opt/psidoc/binaural.mp3 -y -loglevel quiet && rm /opt/psidoc/binaural.wav
echo "Audio OK: $(du -h /opt/psidoc/binaural.mp3 | cut -f1)"

# Script de stream - cerebro 20px 2% opacidade pisca 0.3s/5s
cat > /opt/psidoc/stream.sh << 'STREAMEOF'
#!/bin/bash
RTMP=rtmp://a.rtmp.youtube.com/live2/uaqu-vx24-86d8-r0wy-0jwc
LOG=/var/log/psidoc.log
echo [$(date)] psicologia.doc LIVE 24/7 iniciando... >> $LOG
ffmpeg -loglevel warning \
  -f lavfi -i color=c=0x06060F:s=1280x720:r=25 \
  -stream_loop -1 -i /opt/psidoc/binaural.mp3 \
  -i /opt/psidoc/brain.png \
  -filter_complex "[2:v]format=rgba,colorchannelmixer=aa=0.02[br];[0:v][br]overlay=x=(W-w)/2:y=(H-h)/2:enable='between(mod(t,5),0,0.3)'[vout]" \
  -map [vout] -map 1:a \
  -c:v libx264 -preset ultrafast -tune stillimage -crf 28 -pix_fmt yuv420p \
  -b:v 500k -maxrate 1000k -bufsize 2000k \
  -c:a aac -b:a 192k -ar 44100 -ac 2 \
  -f flv $RTMP >> $LOG 2>&1
echo [$(date)] Reiniciando em 5s... >> $LOG
sleep 5 && exec $0
STREAMEOF
chmod +x /opt/psidoc/stream.sh

# Servico systemd eterno com auto-restart
tee /etc/systemd/system/psidoc-live.service << 'SVCEOF'
[Unit]
Description=psicologia.doc Live 24/7 Forever
After=network.target
[Service]
Type=simple
ExecStart=/opt/psidoc/stream.sh
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload && systemctl enable psidoc-live && systemctl start psidoc-live
sleep 3 && systemctl status psidoc-live --no-pager
echo "=== LIVE 24/7 ATIVA - psicologia.doc ==="
echo "Stream: rtmp://a.rtmp.youtube.com/live2/uaqu-vx24-86d8-r0wy-0jwc"
echo "Logs: journalctl -u psidoc-live -f"