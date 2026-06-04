#!/bin/bash
# psicologia.doc - Oracle Cloud Free Tier Forever Live
# Run on Ubuntu 22.04 ARM instance
# Usage: bash oracle-forever-live-setup.sh YOUR_YOUTUBE_STREAM_KEY
STREAM_KEY="${1:-STREAM_KEY}"
set -e
apt-get update -q && apt-get install -y ffmpeg python3-pip
pip3 install numpy --break-system-packages 2>/dev/null || true
mkdir -p /opt/psidoc
python3 - << 'GENPYEOF'
import numpy as np, wave, os
SR=44100; DUR=3*3600
t=np.linspace(0,DUR,int(SR*DUR),endpoint=False)
L=(np.sin(2*np.pi*432*t)*0.3*32767).astype(np.int16)
R=(np.sin(2*np.pi*436*t)*0.3*32767).astype(np.int16)
fade=int(SR*30)
for arr in [L,R]:
    arr[:fade]=(arr[:fade]*np.linspace(0,1,fade)).astype(np.int16)
data=np.empty(len(t)*2,dtype=np.int16); data[0::2]=L; data[1::2]=R
with wave.open('/opt/psidoc/binaural.wav','w') as f:
    f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR); f.writeframes(data.tobytes())
print('Audio gerado:', os.path.getsize('/opt/psidoc/binaural.wav')//1000000, 'MB')
GENPYEOF
ffmpeg -i /opt/psidoc/binaural.wav -c:a libmp3lame -b:a 192k /opt/psidoc/binaural.mp3 -y -loglevel quiet && rm /opt/psidoc/binaural.wav
cat > /opt/psidoc/stream.sh << STREAMEOF
#!/bin/bash
RTMP="rtmp://a.rtmp.youtube.com/live2/${STREAM_KEY}"
ffmpeg -loglevel warning -f lavfi -i "color=c=0x06060F:s=1280x720:r=25" -stream_loop -1 -i /opt/psidoc/binaural.mp3 -filter_complex "[0:v]drawtext=text=psi:fontsize=180:fontcolor=white@0.03:x=(w-tw)/2:y=(h-th)/2[v]" -map "[v]" -map "1:a" -c:v libx264 -preset ultrafast -tune stillimage -crf 28 -pix_fmt yuv420p -b:v 400k -c:a aac -b:a 128k -ar 44100 -ac 2 -f flv "\$RTMP" 2>/var/log/psidoc.log
sleep 5; exec \$0
STREAMEOF
chmod +x /opt/psidoc/stream.sh
tee /etc/systemd/system/psidoc-live.service << SVCEOF
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
systemctl daemon-reload && systemctl enable psidoc-live && systemctl start psidoc-live
echo '=== LIVE ATIVA 24/7 - psicologia.doc ==='
echo 'Logs: journalctl -u psidoc-live -f'
