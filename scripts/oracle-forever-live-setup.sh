#!/bin/bash
# psicologia.doc - Oracle Cloud Always Free - Live 24/7
# Cerebro branco canal @psidanicoelho: 20px 2% opacidade pisca 0.3s/5s
# Garante monetizacao YouTube (visual presente para algoritmo de anuncios)
SK=${1:-ewme-91sq-yae7-yj1q-5skw}
set -e
apt-get update -q && apt-get install -y ffmpeg python3-pip wget imagemagick
pip3 install numpy --break-system-packages 2>/dev/null||true
mkdir -p /opt/psidoc
wget -q -O /opt/psidoc/brain_orig.jpg 'https://yt3.googleusercontent.com/4NDK-JaBRi0uMyCCeOz-imtfhs6zHuQ2sxUn3d2gCjY_NyS_Z50OCENLFZrS_RjY5wOwKXch=s900-c-k-c0x00ffffff-no-rj'
convert /opt/psidoc/brain_orig.jpg -resize 20x20! /opt/psidoc/brain.png 2>/dev/null||cp /opt/psidoc/brain_orig.jpg /opt/psidoc/brain.png
echo "Cerebro: OK"
python3 -c "
import numpy as np,wave
SR=44100;DUR=10800
t=np.linspace(0,DUR,int(SR*DUR),endpoint=False)
L=(np.sin(2*np.pi*432*t)*0.3*32767).astype(np.int16)
R=(np.sin(2*np.pi*436*t)*0.3*32767).astype(np.int16)
f=int(SR*30)
for a in[L,R]:a[:f]=(a[:f]*np.linspace(0,1,f)).astype(np.int16)
d=np.empty(len(t)*2,dtype=np.int16);d[0::2]=L;d[1::2]=R
with wave.open('/opt/psidoc/binaural.wav','w') as wf:
  wf.setnchannels(2);wf.setsampwidth(2);wf.setframerate(SR);wf.writeframes(d.tobytes())
print('Audio OK')
"
ffmpeg -i /opt/psidoc/binaural.wav -c:a libmp3lame -b:a 192k /opt/psidoc/binaural.mp3 -y -loglevel quiet&&rm /opt/psidoc/binaural.wav
echo "Audio: $(du -h /opt/psidoc/binaural.mp3|cut -f1)"
cat>/opt/psidoc/stream.sh<<'EOF'
#!/bin/bash
SK=ewme-91sq-yae7-yj1q-5skw
LOG=/var/log/psidoc.log
echo [$(date)] LIVE iniciando...>>$LOG
ffmpeg -loglevel warning -f lavfi -i color=c=0x06060F:s=1280x720:r=25 -stream_loop -1 -i /opt/psidoc/binaural.mp3 -i /opt/psidoc/brain.png -filter_complex "[2:v]format=rgba,colorchannelmixer=aa=0.02[br];[0:v][br]overlay=x=(W-w)/2:y=(H-h)/2:enable='between(mod(t,5),0,0.3)'[vout]" -map [vout] -map 1:a -c:v libx264 -preset ultrafast -tune stillimage -crf 28 -pix_fmt yuv420p -b:v 500k -maxrate 1000k -bufsize 2000k -c:a aac -b:a 192k -ar 44100 -ac 2 -f flv rtmp://a.rtmp.youtube.com/live2/$SK>>$LOG 2>&1
echo [$(date)] Reiniciando...>>$LOG;sleep 5&&exec $0
EOF
chmod +x /opt/psidoc/stream.sh
tee /etc/systemd/system/psidoc-live.service<<'SVCEOF'
[Unit]
Description=psicologia.doc Live 24/7
After=network.target
[Service]
Type=simple
ExecStart=/opt/psidoc/stream.sh
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
SVCEOF
systemctl daemon-reload&&systemctl enable psidoc-live&&systemctl start psidoc-live
sleep 3&&systemctl status psidoc-live --no-pager
echo ""
echo "=== PSICOLOGIA.DOC LIVE 24/7 ATIVA ==="
echo "Cerebro branco: 20px | 2% opacidade | pisca 0.3s/5s"
echo "Binaural: 432Hz delta (4Hz) | 3h loop"
echo "RTMP: rtmp://a.rtmp.youtube.com/live2/ewme-91sq-yae7-yj1q-5skw"
echo "Logs: journalctl -u psidoc-live -f"
