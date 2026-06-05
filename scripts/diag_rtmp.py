#!/usr/bin/env python3
"""Diagnóstico RTMP + fix final"""
import os,json,urllib.request,urllib.parse,subprocess,math,struct,wave,time,pathlib,shutil,sys,threading
from datetime import datetime,timezone,timedelta

YT_CLIENT_ID     = os.environ["YT_CLIENT_ID"]
YT_CLIENT_SECRET = os.environ["YT_CLIENT_SECRET"]
YT_REFRESH_TOKEN = os.environ["YT_REFRESH_TOKEN"]
DURATION_H       = int(os.environ.get("DURATION_H","6"))

ST_KEY    = "ewme-91sq-yae7-yj1q-5skw"
STREAM_ID = "SH63tBfY6wEIdkC4u4zKdg1780543868590330"
BC_ID     = "kNYQd4Vkya4"  # Live criada pela sessão anterior
RTMP      = f"rtmp://a.rtmp.youtube.com/live2/{ST_KEY}"
RTMPS     = f"rtmps://a.rtmps.youtube.com/live2/{ST_KEY}"
TMP       = pathlib.Path("/tmp")

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}",flush=True)

def get_token():
    data=urllib.parse.urlencode({"client_id":YT_CLIENT_ID,"client_secret":YT_CLIENT_SECRET,
        "refresh_token":YT_REFRESH_TOKEN,"grant_type":"refresh_token"}).encode()
    req=urllib.request.Request("https://oauth2.googleapis.com/token",data=data)
    req.add_header("Content-Type","application/x-www-form-urlencoded")
    with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read())["access_token"]

def yt_post(token,url,body=None,method="POST"):
    data=json.dumps(body or {}).encode()
    req=urllib.request.Request(url,data=data,method=method)
    req.add_header("Authorization",f"Bearer {token}")
    req.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req,timeout=15) as r:
            txt=r.read(); return json.loads(txt) if txt else {}
    except Exception as e: return {"error":str(e)}

def yt_delete(token,url):
    req=urllib.request.Request(url,method="DELETE")
    req.add_header("Authorization",f"Bearer {token}")
    try: urllib.request.urlopen(req,timeout=10); return True
    except: return False

def ffm():
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except: pass
    return shutil.which("ffmpeg") or "ffmpeg"

def gerar_wav():
    SR,DUR=44100,5; s=SR*DUR; out=bytearray()
    for i in range(s):
        t=i/SR
        out+=struct.pack("<hh",int(math.sin(2*math.pi*430*t)*22000),int(math.sin(2*math.pi*432*t)*22000))
    p=TMP/"b432.wav"
    with wave.open(str(p),"wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(bytes(out))
    return str(p)

DESC="""🔴 LIVE 24/7 | BLACK SCREEN | BINAURAL BEATS 432Hz | DARK PSYCHOLOGY
Daniela Coelho — Human Behavior Researcher | @psidanicoelho
🖤 PURE BLACK SCREEN 100% dark | TRUE BINAURAL 432Hz | Use HEADPHONES
Perfect: Sleep • Study • Meditation • Focus | #blackscreen #binauralbeats432hz
🔴 LIVE | SCHWARZER BILDSCHIRM | BINAURAL 432Hz [DE] Daniela Coelho @psidanicoelho
🔴 EN DIRECT | ÉCRAN NOIR | BINAURAL 432Hz [FR] Daniela Coelho @psidanicoelho
🔴 EN VIVO | PANTALLA NEGRA | BINAURAL 432Hz [ES] Daniela Coelho @psidanicoelho
🔴 AO VIVO | TELA PRETA | BINAURAL 432Hz [PT] Daniela Coelho @psidanicoelho
🔴 ライブ | ブラックスクリーン | バイノーラル432Hz [JA] ダニエラ @psidanicoelho
🔴 라이브 | 검은화면 | 바이노럴432Hz [KO] 다니엘라 @psidanicoelho
🔴 直播 | 黑屏 | 双耳432Hz [ZH] 达尼埃拉 @psidanicoelho
🔴 LIVE | SCHERMO NERO | BINAURAL 432Hz [IT] Daniela Coelho @psidanicoelho
🔴 LIVE | ZWART SCHERM | BINAURAL 432Hz [NL] Daniela Coelho @psidanicoelho
🔴 NA ŻYWO | CZARNY EKRAN | BINAURAL 432Hz [PL] Daniela Coelho @psidanicoelho
🔴 CANLI | SİYAH EKRAN | BINAURAL 432Hz [TR] Daniela Coelho @psidanicoelho
🔴 LIVE | LAYAR HITAM | BINAURAL 432Hz [ID] Daniela Coelho @psidanicoelho
🔴 लाइव | काली स्क्रीन | बाइनॉरल432Hz [HI] डेनियला @psidanicoelho
🔴 مباشر | شاشة سوداء | ثنائي432Hz [AR] دانييلا @psidanicoelho
#darkpsychology #narcissism #432hz #sleepmusic #danielacoelho #psidanicoelho"""

def main():
    log("="*65)
    log(f"DIAGNÓSTICO RTMP + LIVE FINAL | {datetime.now(timezone.utc):%H:%M} UTC")
    ff=ffm(); log(f"FFmpeg: {ff}")
    wav=gerar_wav(); log(f"WAV: OK")
    
    # ─── TESTE 1: Conectividade porta 1935 ───
    log("\n--- TESTE 1: nc porta 1935 ---")
    r1=subprocess.run(["nc","-z","-w","5","a.rtmp.youtube.com","1935"],capture_output=True,timeout=10)
    log(f"  nc porta 1935: rc={r1.returncode} {'OK ✅' if r1.returncode==0 else 'BLOQUEADO ❌'}")
    
    # ─── TESTE 2: ffmpeg RTMP 10s com stderr visível ───
    log("\n--- TESTE 2: ffmpeg RTMP 10s ---")
    test_cmd=[ff,"-y","-re","-stream_loop","-1","-i",wav,
              "-f","lavfi","-i","color=black:size=1280x720:rate=25",
              "-map","1:v","-map","0:a",
              "-c:v","libx264","-preset","ultrafast","-crf","36",
              "-b:v","150k","-c:a","aac","-b:a","128k",
              "-f","flv","-t","10",RTMP]
    proc=subprocess.Popen(test_cmd,stderr=subprocess.PIPE,text=True)
    stderr_lines=[]
    while True:
        line=proc.stderr.readline()
        if not line and proc.poll() is not None: break
        if line:
            stderr_lines.append(line.strip())
            # Mostrar linhas chave em tempo real
            if any(x in line for x in ["Error","error","Failed","failed","Connection","refused","timeout","Opening","RTMP","rtmp","connect","handshake"]):
                log(f"  ffmpeg: {line.strip()[:120]}")
    rc=proc.returncode
    log(f"  ffmpeg RTMP rc={rc}")
    if rc != 0:
        log("  Últimas linhas stderr:")
        for l in stderr_lines[-8:]: 
            if l: log(f"    {l[:120]}")
    else:
        log("  ✅ RTMP conectou com sucesso!")
    
    # Se porta bloqueada, tentar RTMPS
    if r1.returncode != 0 or rc != 0:
        log("\n--- TESTE 3: nc porta 443 (RTMPS) ---")
        r3=subprocess.run(["nc","-z","-w","5","a.rtmps.youtube.com","443"],capture_output=True,timeout=10)
        log(f"  nc porta 443: rc={r3.returncode} {'OK ✅' if r3.returncode==0 else 'BLOQUEADO ❌'}")
    
    # ─── OAuth e gerenciar broadcast ───
    token=get_token(); log(f"\nToken OAuth ✅")
    
    # Apagar NZpc6TiTH_A (Narcisismo encoberto - resquício)
    ok=yt_delete(token,"https://www.googleapis.com/youtube/v3/liveBroadcasts?id=NZpc6TiTH_A")
    log(f"Delete NZpc6TiTH_A (narcisismo): {'✅' if ok else 'já deletado'}")
    
    # Confirmar broadcast kNYQd4Vkya4 e atualizar SEO
    res=yt_post(token,
        "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status",
        {"id":BC_ID,"snippet":{
            "title":"🔴 LIVE 24/7 | BLACK SCREEN for Sleep & Focus | Binaural Beats 432Hz | Dark Psychology",
            "description":DESC[:4900],
            "scheduledStartTime":(datetime.now(timezone.utc)+timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "categoryId":"22","defaultLanguage":"en"
        }},"PUT")
    log(f"SEO update: {res.get('id','ERRO')}")
    
    # Bind novamente por garantia
    bind_res=yt_post(token,
        f"https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?id={BC_ID}&part=id,contentDetails&streamId={STREAM_ID}",{})
    log(f"Bind: {bind_res.get('contentDetails',{}).get('boundStreamId','?')[:30]}")
    
    # ─── Stream com stderr logado para diagnóstico ───
    log(f"\n✅ Broadcast: https://studio.youtube.com/video/{BC_ID}/livestreaming")
    
    dur_s=DURATION_H*3600; inicio=time.time(); tentativas=0
    while time.time()-inicio<dur_s and tentativas<50:
        restante=int(dur_s-(time.time()-inicio))
        if restante<15: break
        tentativas+=1
        log(f"\n[{tentativas}] 🔴 Streaming {restante//3600}h{restante%3600//60}m")
        
        cmd=[ff,"-y","-re","-stream_loop","-1","-i",wav,
             "-f","lavfi","-i","color=black:size=1920x1080:rate=25",
             "-map","1:v","-map","0:a",
             "-c:v","libx264","-preset","ultrafast","-crf","36",
             "-b:v","150k","-maxrate","200k","-bufsize","400k",
             "-g","50","-r","25","-pix_fmt","yuv420p",
             "-c:a","aac","-b:a","128k","-ac","2","-ar","44100",
             "-f","flv","-t",str(min(restante,120)),  # máx 2min por tentativa para debug
             RTMP]
        
        proc2=subprocess.Popen(cmd,stderr=subprocess.PIPE,text=True)
        errs=[]
        for line in proc2.stderr:
            errs.append(line.strip())
            if any(x in line for x in ["Error","error","Failed","Connection","Opening","RTMP","handshake","Output","frame="]):
                log(f"  ffmpeg: {line.strip()[:120]}")
        rc2=proc2.returncode
        log(f"  rc={rc2}")
        if rc2==0: 
            log("  ✅ 2min OK — continuando sem limite")
            break
        log("  Stderr:")
        for l in errs[-5:]:
            if l: log(f"    {l[:120]}")
        espera=min(30*tentativas,120)
        log(f"  retry em {espera}s"); time.sleep(espera)

if __name__=="__main__": main()
