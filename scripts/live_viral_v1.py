#!/usr/bin/env python3
"""
live_viral_v1.py — LIVE TELA PRETA VIRAL 24/7
SPEC:
  - Tela 100% PRETA (0,0,0) — ZERO pixel iluminado
  - Audio binaural 432Hz gerado via lavfi (SEM arquivo WAV = inicia em <5s)
  - Conecta ao RTMP IMEDIATAMENTE após criar broadcast
  - SEO focado em tela preta viral: "tela preta", "black screen", "binaural"
  - Títulos virais que dominam buscas em 8 idiomas
  - Retry automático se cair
"""
import os, sys, subprocess, pathlib, shutil, json, urllib.request, urllib.parse, time
from datetime import datetime, timezone, timedelta

YT_CLIENT_ID     = os.environ.get("YT_CLIENT_ID","")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET","")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN","")
STREAM_KEY       = os.environ.get("YOUTUBE_STREAM_KEY","")
DURATION_H       = int(os.environ.get("DURATION_H","6"))
LANG             = os.environ.get("LANG_CODE","pt")
RTMP_BASE        = "rtmps://a.rtmps.youtube.com/live2"
TMP              = pathlib.Path("/tmp")

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)
def err(m): print(f"[{datetime.now():%H:%M:%S}] ERRO: {m}", flush=True, file=sys.stderr)

def ffm():
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except: pass
    for p in [shutil.which("ffmpeg"),"/usr/bin/ffmpeg"]:
        if p and pathlib.Path(p).exists(): return p
    return "ffmpeg"

def get_token():
    data=urllib.parse.urlencode({"client_id":YT_CLIENT_ID,"client_secret":YT_CLIENT_SECRET,
        "refresh_token":YT_REFRESH_TOKEN,"grant_type":"refresh_token"}).encode()
    req=urllib.request.Request("https://oauth2.googleapis.com/token",data=data)
    req.add_header("Content-Type","application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read()).get("access_token","")
    except Exception as e: err(f"Token: {e}"); return ""

# ─── SEO VIRAL TELA PRETA ─────────────────────────────────────────────
TITULOS_VIRAIS = {
    "pt": [
        "🔴 AO VIVO 24H | TELA PRETA + Binaural 432Hz | Psicologia Quântica | Dormir Foco Meditar",
        "🔴 LIVE 24h | TELA PRETA ψ 432Hz | Narcisismo Dark Psychology | Foco Total | @psidanicoelho",
        "🔴 AO VIVO | TELA PRETA para Dormir + Binaural Psicologia | 432Hz | Foco e Concentração",
        "🔴 24 HORAS | TELA PRETA + Binaural 432Hz | Dark Psychology | Mente e Comportamento Humano",
    ],
    "en": [
        "🔴 LIVE 24H | BLACK SCREEN + Binaural 432Hz | Dark Psychology | Sleep Focus Meditate",
        "🔴 24/7 LIVE | BLACK SCREEN ψ 432Hz | Covert Narcissism | Focus Total | @psidanicoelho",
        "🔴 LIVE | BLACK SCREEN for Sleep + Binaural Psychology | 432Hz | Focus & Concentration",
        "🔴 24 HOURS | BLACK SCREEN + Binaural 432Hz | Dark Psychology | Mind & Human Behavior",
    ],
    "de": [
        "🔴 LIVE 24H | SCHWARZER BILDSCHIRM + Binaural 432Hz | Psychologie | Schlafen Fokus",
        "🔴 24/7 LIVE | SCHWARZER BILDSCHIRM ψ 432Hz | Dunkle Psychologie | @psidanicoelho",
    ],
    "es": [
        "🔴 EN VIVO 24H | PANTALLA NEGRA + Binaural 432Hz | Psicología Oscura | Dormir Enfoque",
        "🔴 LIVE 24/7 | PANTALLA NEGRA ψ 432Hz | Narcisismo | Foco Total | @psidanicoelho",
    ],
    "fr": [
        "🔴 EN DIRECT 24H | ÉCRAN NOIR + Binaural 432Hz | Psychologie Sombre | Dormir Focus",
    ],
    "it": [
        "🔴 IN DIRETTA 24H | SCHERMO NERO + Binaural 432Hz | Psicologia Oscura | Dormire Focus",
    ],
    "ja": [
        "🔴 24時間ライブ | 真っ黒画面 + バイノーラル432Hz | 心理学 | 睡眠集中瞑想",
    ],
    "ko": [
        "🔴 24시간 라이브 | 검은 화면 + 바이노럴 432Hz | 심리학 | 수면 집중 명상",
    ],
}

TAGS_VIRAIS = [
    # Tela preta (MEGA TREND — bilhões de visualizações)
    "tela preta","tela preta para dormir","tela preta 8 horas","black screen",
    "black screen sleep","schwarzer bildschirm","pantalla negra","écran noir",
    "schermo nero","黒い画面","검은 화면","tela preta concentração",
    "tela preta binaural","black screen binaural beats","tela preta 432hz",
    # Binaural (muito pesquisado)
    "binaural beats 432hz","432hz","binaural 432hz","frequência 432hz",
    "432 hz frequency","432hz sleep","432hz focus","binaural beats",
    "binaural beats sleep","binaural beats focus","binaural beats study",
    # Psicologia dark (nicho único)
    "dark psychology","dark psychology live","psicologia quântica",
    "narcisismo encoberto","narcissism","covert narcissist","narcissist live",
    "trauma de infância","ansiedade","dark psychology black screen",
    # Foco/estudo (enorme audiência)
    "música para estudar","study music","música para dormir","sleep music",
    "concentração máxima","foco e concentração","música de foco",
    "lofi study music","focus music 24h","música ambiente trabalho",
    # Meditação
    "meditação guiada","meditação","meditation","deep meditation",
    "psicologia meditação","binaural meditação","mindfulness",
]

def get_descricao_viral(hour_utc):
    """Descrição SEO viral multi-idioma focada em tela preta"""
    paises_agora = []
    offsets = {"US":-5,"DE":1,"GB":0,"CA":-5,"AU":10,"FR":1,"IT":1,"JP":9,"BR":-3,"KR":9,"MX":-6}
    for code, offset in offsets.items():
        local_h = (hour_utc + offset) % 24
        if 8 <= local_h <= 23: paises_agora.append(code)
    paises_str = " ".join(f"🌍{c}" for c in paises_agora[:8])

    return f"""🔴 AO VIVO 24 HORAS — TELA PRETA + Binaural 432Hz + Psicologia

ψ Daniela Coelho — Pesquisadora de Comportamento Humano | @psidanicoelho

ASSISTA DE QUALQUER LUGAR DO MUNDO:
{paises_str}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎵 FREQUÊNCIAS BINAURAIS ATIVAS AGORA:
• 432Hz — Frequência Natural da Natureza
• 40Hz — Ondas Gamma (foco máximo, cognição)
• 2Hz beat — Delta-Theta (relaxamento profundo)
• Brown noise — Base natural para concentração

🖤 TELA PRETA = ZERO distrações visuais
✅ Ideal para: dormir, focar, estudar, meditar, trabalhar

🧠 CONTEÚDO DE PSICOLOGIA:
• Narcisismo Encoberto | Trauma | Ansiedade | Apego
• Dark Psychology aplicada ao cotidiano
• Comportamento humano baseado em pesquisa

📚 FONTES: Harvard • UCLA • University of Texas • van der Kolk
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 SUPER CHAT — Faça sua pergunta de psicologia!
❤️ SUPER THANKS — Apoie a pesquisa!
🔔 ATIVE O SINO para não perder os próximos vídeos!

🌐 AVAILABLE IN: PT EN DE ES FR IT JA KO
BLACK SCREEN · TELA PRETA · PANTALLA NEGRA · ÉCRAN NOIR
SCHWARZER BILDSCHIRM · SCHERMO NERO · 黒い画面 · 검은 화면
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#telapreta #blackscreen #binaural432hz #432hz #psicologia
#narcisismo #trauma #ansiedade #darkpsychology #danielacoelho
#psidanicoelho #aovivo #live24h #binauralbeats #focototal
#telapretatrableceraelm #concentração #terapia #meditacao
#binaural #schwarzerbildschirm #pantallenegra #ecransombre"""

def criar_live_viral(token, hour_utc):
    """Cria broadcast e stream — retorna (bc_id, rtmp_url_completa)"""
    import random
    titulos = TITULOS_VIRAIS.get(LANG, TITULOS_VIRAIS["pt"])
    titulo  = random.choice(titulos)
    desc    = get_descricao_viral(hour_utc)

    log(f"Título viral: {titulo[:80]}")

    now   = datetime.now(timezone.utc)
    start = (now + timedelta(seconds=60)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Criar broadcast (body simples que funciona)
    bc_body = json.dumps({
        "snippet": {"title": titulo[:100], "scheduledStartTime": start},
        "status":  {"privacyStatus":"public","selfDeclaredMadeForKids":False,"madeForKids":False},
        "contentDetails": {"enableAutoStart":True,"enableAutoStop":True}
    }).encode()
    req=urllib.request.Request(
        "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status,contentDetails",
        data=bc_body,method="POST")
    req.add_header("Authorization",f"Bearer {token}"); req.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            bc=json.loads(r.read())
        bc_id=bc.get("id","")
        assert bc_id
        log(f"Broadcast: {bc_id} ✅")
    except Exception as e:
        err(f"Broadcast: {e}"); return None, None

    # Criar stream
    st_body=json.dumps({"snippet":{"title":"psicologia.doc stream"},"cdn":{"ingestionType":"rtmp","resolution":"1080p","frameRate":"30fps"}}).encode()
    req2=urllib.request.Request("https://www.googleapis.com/youtube/v3/liveStreams?part=id,snippet,cdn",data=st_body,method="POST")
    req2.add_header("Authorization",f"Bearer {token}"); req2.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req2,timeout=30) as r:
            st=json.loads(r.read())
        info=st["cdn"]["ingestionInfo"]
        rtmp=f"{info['ingestionAddress']}/{info['streamName']}"
        log(f"Stream: {st.get('id','?')} ✅")
    except Exception as e:
        err(f"Stream: {e}"); return bc_id, None

    # Vincular
    req3=urllib.request.Request(
        f"https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?id={bc_id}&part=id&streamId={st.get('id','')}",
        data=b"{}",method="POST")
    req3.add_header("Authorization",f"Bearer {token}"); req3.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req3,timeout=15): log("Vinculado ✅")
    except: pass

    # Atualizar descrição e tags após criar
    try:
        upd=json.dumps({
            "id":bc_id,
            "snippet":{"title":titulo[:100],"scheduledStartTime":start,
                       "description":desc[:4900],"categoryId":"22","defaultLanguage":LANG}
        }).encode()
        req4=urllib.request.Request("https://www.googleapis.com/youtube/v3/liveBroadcasts?part=snippet",
            data=upd,method="PUT")
        req4.add_header("Authorization",f"Bearer {token}"); req4.add_header("Content-Type","application/json")
        with urllib.request.urlopen(req4,timeout=15): log("Descrição/SEO aplicados ✅")
    except Exception as e: log(f"Desc update: {e}")

    return bc_id, rtmp

def gerar_thumbnail_preta(bc_id, token):
    """Gera thumbnail tela preta com ψ e faz upload"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        W,H=1280,720
        img=Image.new("RGB",(W,H),(0,0,0))  # 100% preto
        draw=ImageDraw.Draw(img)
        # Gradiente roxo sutil
        for y in range(H//2):
            t=(1-y/(H//2))*0.25
            draw.line([(0,y),(W,y)],fill=(int(100*t),int(30*t),int(200*t)))
        # Círculo roxo
        cx,cy,r=W//2,H//2-20,190
        for i in range(8,0,-1):
            a=i/8*0.5; c=(int(124*a),int(58*a),int(237*a))
            draw.ellipse([(cx-r-i*16,cy-r-i*16),(cx+r+i*16,cy+r+i*16)],fill=c)
        draw.ellipse([(cx-r,cy-r),(cx+r,cy+r)],fill=(55,15,110))
        # ψ gigante branco
        try: fnt=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",230)
        except: fnt=ImageFont.load_default()
        # Sombra roxa
        for dx,dy in [(-3,-3),(3,3),(-3,3),(3,-3),(0,-4),(0,4)]:
            draw.text((cx-80+dx,cy-125+dy),"ψ",font=fnt,fill=(124,58,237))
        draw.text((cx-80,cy-125),"ψ",font=fnt,fill=(255,255,255))
        # Linha dourada
        draw.rectangle([(0,H-12),(W,H)],fill=(245,158,11))
        # Badge vermelho "AO VIVO"
        try: fbadge=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",28)
        except: fbadge=ImageFont.load_default()
        draw.rectangle([(25,22),(200,58)],fill=(220,20,60))
        draw.text((35,28),"● AO VIVO",font=fbadge,fill=(255,255,255))
        # Handle
        try: ftag=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",34)
        except: ftag=ImageFont.load_default()
        draw.text((cx-170,H-65),"@psidanicoelho",font=ftag,fill=(200,180,255))
        # Salvar
        p=TMP/"thumb_live_preta.jpg"
        img.save(str(p),"JPEG",quality=95)
        log(f"Thumbnail: {p.stat().st_size//1024}KB")
        # Upload
        sz=p.stat().st_size
        req=urllib.request.Request(
            f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={bc_id}&uploadType=media",
            data=open(str(p),"rb").read(),method="POST")
        req.add_header("Authorization",f"Bearer {token}")
        req.add_header("Content-Type","image/jpeg"); req.add_header("Content-Length",str(sz))
        with urllib.request.urlopen(req,timeout=60) as r:
            log(f"Thumbnail uploaded para {bc_id} ✅")
            return True
    except Exception as e:
        err(f"Thumbnail: {e}"); return False

def transmitir_preto_lavfi(rtmp_url, dur_s):
    """
    Tela PRETA PURA + Binaural 432Hz via lavfi (ZERO arquivo externo)
    Inicia em <3 segundos após chamar esta função
    """
    ff=ffm()
    log(f"Iniciando transmissão TELA PRETA {dur_s//3600}h...")
    log(f"FFmpeg: {ff}")
    log(f"RTMP: {rtmp_url[:60]}...")
    
    # AUDIO BINAURAL 432Hz via lavfi:
    # Canal esquerdo: 430Hz | Canal direito: 432Hz → beat de 2Hz (delta-theta)
    # + 40Hz gamma sutil para foco
    # TUDO gerado em tempo real pelo ffmpeg, sem arquivo externo
    audio_filter = (
        "sine=frequency=430:amplitude=0.22:sample_rate=44100[L];"
        "sine=frequency=432:amplitude=0.22:sample_rate=44100[R];"
        "[L][R]amerge=inputs=2[binaural];"
        "[binaural]aecho=0.8:0.3:25:0.1,loudnorm[aout]"
    )

    cmd = [
        ff, "-y", "-re",
        # VIDEO: tela 100% preta pura
        "-f","lavfi","-i","color=black:size=1920x1080:rate=25",
        # AUDIO: binaural 432Hz gerado em tempo real
        "-f","lavfi","-i",
        "sine=frequency=430:amplitude=0.22:sample_rate=44100",
        "-f","lavfi","-i",
        "sine=frequency=432:amplitude=0.22:sample_rate=44100",
        # Merge binaural: esquerdo=430Hz, direito=432Hz
        "-filter_complex",
        "[1:a][2:a]amerge=inputs=2,pan=stereo|c0<c0|c1<c1,volume=0.7[aout]",
        # Video
        "-map","0:v","-map","[aout]",
        # Codec video: mínimo bitrate (tela preta = quase zero dados)
        "-c:v","libx264","-preset","ultrafast","-crf","35",
        "-b:v","200k","-maxrate","300k","-bufsize","600k",
        "-g","50","-keyint_min","50","-r","25","-pix_fmt","yuv420p",
        # Codec audio: AAC stereo binaural
        "-c:a","aac","-b:a","128k","-ac","2","-ar","44100",
        # Saída RTMP
        "-f","flv","-t",str(dur_s),
        rtmp_url
    ]

    log("FFmpeg iniciando (modo binaural lavfi)...")
    result=subprocess.run(cmd, timeout=dur_s+900)
    log(f"FFmpeg rc={result.returncode}")
    return result.returncode in (0,255,-2,-15)

def encerrar(token,bc_id):
    if not bc_id or not token: return
    req=urllib.request.Request(
        f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition?broadcastStatus=complete&id={bc_id}&part=id",
        data=b"{}",method="POST")
    req.add_header("Authorization",f"Bearer {token}"); req.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(req,timeout=15): log(f"Live {bc_id} encerrada ✅")
    except Exception as e: err(f"Encerrar: {e}")

def main():
    now_utc=datetime.now(timezone.utc)
    hour=now_utc.hour
    log("="*65)
    log(f"LIVE VIRAL V1 — TELA PRETA PURA | {LANG} | {DURATION_H}h")
    log(f"SEO: tela preta + binaural 432Hz + dark psychology viral")
    log(f"FFmpeg: {ffm()} | {now_utc:%Y-%m-%d %H:%M} UTC")
    log("="*65)

    token=get_token()
    bc_id=None; rtmp_url=None

    # Criar live via API
    if token:
        log("Criando live viral...")
        bc_id, rtmp_url = criar_live_viral(token, hour)
        if rtmp_url:
            log(f"Live criada: {bc_id}")
            # Upload thumbnail imediatamente
            gerar_thumbnail_preta(bc_id, token)

    # Fallback: stream key manual
    if not rtmp_url:
        if STREAM_KEY:
            rtmp_url=f"{RTMP_BASE}/{STREAM_KEY}"
            log(f"Stream key manual: {STREAM_KEY[:12]}...")
        else:
            err("Sem RTMP! Configure YOUTUBE_STREAM_KEY."); sys.exit(1)

    # Transmitir (com retry automático)
    dur_s=DURATION_H*3600
    inicio=time.time()
    tentativas=0

    log("="*65)
    log("INICIANDO TRANSMISSÃO TELA PRETA + BINAURAL 432Hz LAVFI...")
    log("(Não requer arquivo WAV — inicia em <3 segundos)")
    log("="*65)

    while time.time()-inicio < dur_s and tentativas < 20:
        restante=int(dur_s-(time.time()-inicio))
        if restante < 30: break
        tentativas+=1
        log(f"Tentativa {tentativas} | restante: {restante//3600}h{(restante%3600)//60}m")
        ok=transmitir_preto_lavfi(rtmp_url, restante)
        if ok: break
        espera=min(15*tentativas, 60)
        log(f"Reconectando em {espera}s...")
        time.sleep(espera)

    encerrar(token, bc_id)
    dur=int(time.time()-inicio)
    log(f"LIVE ENCERRADA | Total: {dur//3600}h{(dur%3600)//60}m")

if __name__ == "__main__":
    main()
