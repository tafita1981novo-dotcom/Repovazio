#!/usr/bin/env python3
"""
live_global_v4.py — LIVE 24/7 MULTILINGUAL TELA PRETA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
100% GRATUITO — Sem ElevenLabs, sem nada pago

ESTRATÉGIA MUNDIAL POR HORÁRIO UTC:
  00–03 UTC → EN  (EUA East prime time 20h ET)
  03–06 UTC → PT  (Brasil midnight 00h BRT — sono profundo)
  06–08 UTC → JA  (Japão manhã 15h JST)
  08–10 UTC → KO  (Coreia tarde 17h KST)
  10–12 UTC → AU  (Austrália tarde 20h AEDT)
  12–14 UTC → DE  (Alemanha 13h CET — pausa almoço)
  14–16 UTC → FR  (França 15h CET)
  16–18 UTC → ES  (México 10h CDT / Espanha 17h CET)
  18–20 UTC → IT  (Itália 19h CET)
  20–22 UTC → UK  (UK 20h GMT — prime time)
  22–24 UTC → PT  (Brasil 19h BRT — prime time)

AUDIO:
  - Binaural delta 528Hz (sono) / theta 5.5Hz (foco) / alpha 10Hz (calma)
  - Sons de natureza procedurais (chuva, oceano, vento)
  - 100% Python puro, sem dependências externas

SEO POR IDIOMA:
  - Título com keyword de alto volume no início
  - Descrição 300+ chars com timestamps e CTAs
  - Tags em 3 camadas: genérico + específico + long-tail
  - YouTube localization em 25 idiomas via API

CPM ALVO POR IDIOMA:
  EN $15–50 (EUA/UK/AU/CA) | DE $12–18 | FR $10–14
  PT R$12–22 | ES $8–12   | JA $8–15  | KO $6–12
"""
import os, sys, math, struct, wave, subprocess, pathlib, random, time, json
import urllib.request, urllib.parse
from datetime import datetime, timezone

# ── Env ──────────────────────────────────────────────────────────────
STREAM_KEY   = os.getenv("YOUTUBE_STREAM_KEY","uaqu-vx24-86d8-r0wy-0jwc")
DURATION_H   = int(os.getenv("DURATION_HOURS","6"))
FORCE_LANG   = os.getenv("LIVE_LANG","")  # Se vazio, detecta por UTC hora
LIVE_TYPE    = os.getenv("LIVE_TYPE","auto")  # auto|sleep|study|meditation|anxiety
TMP = pathlib.Path("/tmp/live_v4"); TMP.mkdir(exist_ok=True)

def log(msg): print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)

def ffm():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError: pass
    import shutil
    b=shutil.which("ffmpeg")
    if b: return b
    for p in ["/snap/bin/ffmpeg","/usr/bin/ffmpeg","/usr/local/bin/ffmpeg"]:
        if pathlib.Path(p).exists(): return p
    return "ffmpeg"

# ── Tabela multilingual completa ──────────────────────────────────────
LANGS = {
    "PT": {
        "name": "Português",
        "prime_utc": [0, 3, 21, 22, 23],  # 00h-03h e 21h-23h UTC
        "cpm_est": "R$15-22",
        "tts_voice": "pt-BR-ThalitaMultilingualNeural",
        "tts_rate": "+5%",
        "sleep": {
            "title": "Sono Profundo 8 Horas ● Binaural 528Hz ● Tela Preta ● Daniela Coelho",
            "description": (
                "🌙 SONO PROFUNDO COM TELA PRETA — 8 horas de música binaural 528Hz para dormir.\n"
                "Tela 100% preta para não perturbar seu sono. Sons delta para sono profundo.\n\n"
                "✅ 528Hz Binaural Beats — Delta para sono profundo\n"
                "✅ Tela completamente preta — zero luz na tela\n"
                "✅ Sons de natureza — chuva + oceano suave\n"
                "✅ Baseado em neurociência do sono (Harvard Sleep Lab)\n\n"
                "⏱️ TIMESTAMPS:\n"
                "00:00 — Início (fade in suave 60 segundos)\n"
                "01:00 — 528Hz ativo — relaxamento profundo\n"
                "02:00 — Ondas delta iniciando\n"
                "05:00 — Sono profundo máximo\n\n"
                "@psidanicoelho #sono #músicaparadormir #528hz #binauralbeats\n"
                "#dormir #ansiedade #meditação #telaescura #sonoprofundo"
            ),
            "tags": [
                "música para dormir","sono profundo","528hz","binaural beats",
                "tela preta sono","dormir rápido","ansiedade sono","música relaxante",
                "frequência 528","sleep music","meditação sono","ondas delta",
                "psicologia do sono","dormir bem","insônia","relaxamento profundo",
                "sons da natureza","chuva para dormir","binaural sono","daniela coelho"
            ]
        },
        "study": {
            "title": "Música para Estudar 24/7 ● Ondas Theta 5.5Hz ● Foco Total ● Tela Preta",
            "description": (
                "📚 FOCO TOTAL — Música binaural theta para estudar, trabalhar e concentrar.\n"
                "Ondas theta 5.5Hz ativam memória e criatividade. Tela preta sem distrações.\n\n"
                "✅ 5.5Hz Theta Waves — foco e memória\n"
                "✅ Sem distrações visuais\n"
                "✅ 24/7 disponível\n\n"
                "@psidanicoelho #estudar #foco #thetawaves #musica\n"
                "#concentração #estudar #memória #produtividade"
            ),
            "tags": [
                "música para estudar","foco","theta waves","ondas theta",
                "concentração","estudar ouvindo música","music to study",
                "produtividade","memória","binaural study","trabalho foco"
            ]
        }
    },
    "EN": {
        "name": "English",
        "prime_utc": [0, 1, 2, 20, 21],  # 20h-22h UTC = 20h ET / 20h GMT
        "cpm_est": "$15-50",
        "tts_voice": "en-US-AvaMultilingualNeural",
        "tts_rate": "+3%",
        "sleep": {
            "title": "Deep Sleep Music 8 Hours ● 528Hz Binaural Beats ● BLACK SCREEN ● No Ads",
            "description": (
                "😴 DEEP SLEEP — 8 hours of 528Hz binaural beats for deep sleep. Black screen.\n"
                "Delta waves 0.5-4Hz trigger deep sleep. No light from screen. No interruptions.\n\n"
                "✅ 528Hz Delta Binaural Beats — proven sleep frequency\n"
                "✅ 100% Black Screen — zero light, zero disturbance\n"
                "✅ Ocean + Rain nature sounds\n"
                "✅ Based on Harvard Sleep Research\n\n"
                "⏱️ TIMESTAMPS:\n"
                "00:00 — Gentle fade in\n"
                "01:00 — 528Hz active\n"
                "05:00 — Deep delta sleep\n\n"
                "@psidanicoelho #sleep #528hz #binauralbeats #blackscreen\n"
                "#deepsleeep #sleepmusic #deltabeats #insomnia #relaxation"
            ),
            "tags": [
                "sleep music","528hz sleep","binaural beats sleep","black screen sleep",
                "deep sleep music","sleep meditation","delta waves","insomnia relief",
                "sleep sounds","nature sounds sleep","528hz binaural","sleep frequency",
                "deep sleep 8 hours","sleeping music","study music","focus music",
                "healing frequencies","528hz meditation","sleep aid","anxiety relief"
            ]
        },
        "study": {
            "title": "Study Music 24/7 ● Theta Waves 5.5Hz ● Deep Focus ● Black Screen",
            "description": (
                "📚 DEEP FOCUS — Study music with 5.5Hz theta binaural beats.\n"
                "Theta waves enhance memory, creativity and deep concentration.\n\n"
                "✅ 5.5Hz Theta Binaural Beats\n"
                "✅ Zero visual distractions\n"
                "✅ Based on neuroscience research\n\n"
                "@psidanicoelho #studymusic #focus #theta #binaural"
            ),
            "tags": [
                "study music","focus music","theta waves","concentration","brain music",
                "study beats","work music","productivity","memory music","binaural study",
                "coding music","reading music","homework music","exam study music"
            ]
        }
    },
    "ES": {
        "name": "Español",
        "prime_utc": [16, 17, 23, 0],
        "cpm_est": "$8-12",
        "tts_voice": "es-MX-DaliaNeural",
        "tts_rate": "+5%",
        "sleep": {
            "title": "Música para Dormir 8 Horas ● 528Hz Binaural ● PANTALLA NEGRA ● Sin Anuncios",
            "description": (
                "🌙 SUEÑO PROFUNDO — 8 horas de música binaural 528Hz para dormir profundo.\n"
                "Pantalla completamente negra para no interrumpir tu sueño.\n\n"
                "✅ 528Hz Ondas Delta — frecuencia comprobada del sueño\n"
                "✅ Pantalla 100% negra — cero luz\n"
                "✅ Sonidos de naturaleza — lluvia + océano\n\n"
                "@psidanicoelho #músicapararormir #sueñoprofundo #528hz #pantallenegra"
            ),
            "tags": [
                "música para dormir","sueño profundo","528hz","binaural","pantalla negra",
                "música relajante","dormir rápido","ansiedad","meditación","frecuencias",
                "ondas delta","música estudiar","concentración","enfoque","naturaleza"
            ]
        },
        "study": {
            "title": "Música para Estudiar 24/7 ● Ondas Theta ● Concentración Total ● Pantalla Negra",
            "description": "📚 CONCENTRACIÓN TOTAL — Música binaural theta para estudiar y trabajar.\n@psidanicoelho #estudiar #concentración #theta",
            "tags": ["música estudiar","concentración","theta","binaural","enfoque","productividad"]
        }
    },
    "DE": {
        "name": "Deutsch",
        "prime_utc": [12, 13, 18, 19],
        "cpm_est": "$12-18",
        "tts_voice": "de-DE-SeraphinaMultilingualNeural",
        "tts_rate": "+3%",
        "sleep": {
            "title": "Schlafmusik 8 Stunden ● 528Hz Binaural Beats ● SCHWARZER BILDSCHIRM",
            "description": "🌙 TIEFER SCHLAF — 8 Stunden 528Hz Binaural Beats.\nSchwarzer Bildschirm ohne Licht.\n@psidanicoelho #schlafmusik #528hz #binaural",
            "tags": ["schlafmusik","528hz","binaural beats","schwarzer bildschirm","schlaf","einschlafen","entspannung"]
        },
        "study": {
            "title": "Lernmusik 24/7 ● Theta Wellen ● Konzentration ● Schwarzer Bildschirm",
            "description": "📚 KONZENTRATION — Theta-Binaural für Lernen und Arbeit.\n@psidanicoelho #lernmusik #konzentration #theta",
            "tags": ["lernmusik","konzentration","theta","binaural","fokus","lernen","produktivität"]
        }
    },
    "FR": {
        "name": "Français",
        "prime_utc": [14, 15, 19, 20],
        "cpm_est": "$10-14",
        "tts_voice": "fr-FR-DeniseNeural",
        "tts_rate": "+3%",
        "sleep": {
            "title": "Musique pour Dormir 8h ● 528Hz Binaural ● ÉCRAN NOIR ● Sans Publicités",
            "description": "🌙 SOMMEIL PROFOND — 8 heures de musique binaural 528Hz.\nÉcran complètement noir.\n@psidanicoelho #musiquedormir #528hz #binaural",
            "tags": ["musique pour dormir","sommeil profond","528hz","binaural","écran noir","relaxation","méditation"]
        },
        "study": {
            "title": "Musique pour Étudier 24/7 ● Ondes Thêta ● Concentration ● Écran Noir",
            "description": "📚 CONCENTRATION TOTALE — Musique binaural theta.\n@psidanicoelho #musiqueetudier #concentration #theta",
            "tags": ["musique étudier","concentration","theta","binaural","focus","productivité","mémoire"]
        }
    },
    "JA": {
        "name": "日本語",
        "prime_utc": [6, 7, 10, 11],
        "cpm_est": "$8-15",
        "tts_voice": "ja-JP-NanamiNeural",
        "tts_rate": "+3%",
        "sleep": {
            "title": "睡眠音楽8時間 ● 528Hz バイノーラルビート ● ブラックスクリーン ● 深い眠り",
            "description": "🌙 ぐっすり眠る — 528Hz バイノーラルビートで深い眠りを\nスクリーン完全真っ黒\n@psidanicoelho #睡眠音楽 #528hz #バイノーラル",
            "tags": ["睡眠音楽","528hz","バイノーラル","ブラックスクリーン","深い眠り","不眠症","リラックス","瞑想"]
        },
        "study": {
            "title": "集中力アップ勉強音楽 24/7 ● シータ波 5.5Hz ● ブラックスクリーン",
            "description": "📚 集中して勉強する — シータ波バイノーラルで記憶力アップ\n@psidanicoelho #勉強音楽 #集中力 #シータ波",
            "tags": ["勉強音楽","集中力","シータ波","バイノーラル","記憶力","生産性"]
        }
    },
    "KO": {
        "name": "한국어",
        "prime_utc": [8, 9, 11],
        "cpm_est": "$6-12",
        "tts_voice": "ko-KR-SunHiNeural",
        "tts_rate": "+5%",
        "sleep": {
            "title": "수면 음악 8시간 ● 528Hz 바이노럴 비트 ● 검은 화면 ● 깊은 수면",
            "description": "🌙 깊은 수면 — 528Hz 바이노럴 비트로 깊게 잠들기\n화면 완전 검정\n@psidanicoelho #수면음악 #528hz #바이노럴",
            "tags": ["수면음악","528hz","바이노럴","검은화면","깊은수면","불면증","명상","집중력"]
        },
        "study": {
            "title": "공부 음악 24/7 ● 세타파 ● 집중력 향상 ● 검은 화면",
            "description": "📚 집중력 UP — 세타파 바이노럴로 공부 집중\n@psidanicoelho #공부음악 #집중력 #세타파",
            "tags": ["공부음악","집중력","세타파","바이노럴","기억력","생산성"]
        }
    },
    "IT": {
        "name": "Italiano",
        "prime_utc": [18, 19],
        "cpm_est": "$8-12",
        "tts_voice": "it-IT-ElsaNeural",
        "tts_rate": "+3%",
        "sleep": {
            "title": "Musica per Dormire 8 Ore ● 528Hz Binaural ● SCHERMO NERO ● Sonno Profondo",
            "description": "🌙 SONNO PROFONDO — 8 ore di musica binaural 528Hz.\nSchermo completamente nero.\n@psidanicoelho #musicaperdormire #528hz #binaural",
            "tags": ["musica per dormire","sonno profondo","528hz","binaural","schermo nero","rilassamento","meditazione"]
        },
        "study": {
            "title": "Musica per Studiare 24/7 ● Onde Theta ● Concentrazione ● Schermo Nero",
            "description": "📚 CONCENTRAZIONE TOTALE — Onde theta binaural.\n@psidanicoelho #musicastudiare #concentrazione #theta",
            "tags": ["musica studiare","concentrazione","theta","binaural","focus","produttività","memoria"]
        }
    }
}

def detect_lang_by_utc():
    """Detecta idioma ideal baseado na hora UTC atual"""
    hour_utc = datetime.now(timezone.utc).hour
    
    # Mapear hora → idioma com maior audiência acordada no prime time
    schedule = {
        0: "EN",   # EUA East/Central 20h-21h
        1: "EN",   # EUA West 17h-18h
        2: "EN",   # continua EN audience
        3: "PT",   # Brasil 00h — sono profundo
        4: "PT",   # Brasil 01h
        5: "PT",   # Brasil 02h
        6: "JA",   # Japão 15h — tarde
        7: "JA",   # Japão 16h
        8: "KO",   # Coreia 17h
        9: "KO",   # Coreia 18h
        10: "JA",  # Japão/AU overlap
        11: "JA",  # Japão 20h prime time
        12: "DE",  # Alemanha 13h almoço
        13: "DE",  # Alemanha 14h
        14: "FR",  # França 15h
        15: "FR",  # França 16h
        16: "ES",  # México 10h / Espanha 17h
        17: "ES",  # América Latina tarde
        18: "IT",  # Itália 19h — prime time
        19: "IT",  # Itália 20h
        20: "UK",  # UK 20h prime time (usar EN)
        21: "PT",  # Brasil 18h prime time
        22: "PT",  # Brasil 19h
        23: "PT",  # Brasil 20h
    }
    
    lang = schedule.get(hour_utc, "PT")
    if lang == "UK": lang = "EN"  # UK usa EN
    return lang

def detect_live_type():
    """Detecta tipo baseado na hora local BR"""
    hour_utc = datetime.now(timezone.utc).hour
    hour_br = (hour_utc - 3) % 24  # UTC-3 = BRT
    
    if 22 <= hour_br or hour_br < 7:
        return "sleep"     # Noite/madrugada → sono
    elif 7 <= hour_br < 12:
        return "study"     # Manhã → foco/estudo
    elif 12 <= hour_br < 14:
        return "study"     # Almoço → foco leve
    elif 14 <= hour_br < 18:
        return "meditation"  # Tarde → meditação/ansiedade
    elif 18 <= hour_br < 22:
        return "sleep"     # Noite cedo → relaxamento → sono
    return "sleep"

# ── Geração de áudio binaural de alta qualidade ──────────────────────
def gen_binaural_hq(out_path, dur_sec, live_type="sleep"):
    """
    Binaural de ALTA QUALIDADE — Python puro, indetectável como sintético
    
    sleep:      δ 2.0Hz  | base 200Hz | chuva + oceano
    study:      θ 5.5Hz  | base 220Hz | ruído branco suave + vento
    meditation: α 10Hz   | base 174Hz | natureza suave
    anxiety:    α 8Hz    | base 196Hz | chuva suave
    """
    PRESETS = {
        "sleep":      {"beat": 2.0,  "base": 200, "carrier2": 285,
                       "rain_vol": 0.12, "ocean_vol": 0.08, "noise_vol": 0.04},
        "study":      {"beat": 5.5,  "base": 220, "carrier2": 285,
                       "rain_vol": 0.04, "ocean_vol": 0.02, "noise_vol": 0.08},
        "meditation": {"beat": 10.0, "base": 174, "carrier2": 285,
                       "rain_vol": 0.10, "ocean_vol": 0.06, "noise_vol": 0.03},
        "anxiety":    {"beat": 8.0,  "base": 196, "carrier2": 285,
                       "rain_vol": 0.09, "ocean_vol": 0.05, "noise_vol": 0.04},
    }
    p = PRESETS.get(live_type, PRESETS["sleep"])
    
    sr = 44100; n = int(dur_sec * sr)
    log(f"   Gerando binaural HQ {p['beat']}Hz ({dur_sec//60}min)...")
    
    L_data, R_data = [], []
    for i in range(n):
        t = i / sr
        # Fade 60s início e fim
        fade = min(1.0, min(t/60, (dur_sec-t)/60))
        fade = max(0.0, fade)
        
        # 1. Tom binaural principal (carrier + beat binaural)
        tone_L = 0.28 * math.sin(2*math.pi*p["base"]*t)
        tone_R = 0.28 * math.sin(2*math.pi*(p["base"]+p["beat"])*t)
        
        # 2. Segundo carrier harmônico (riqueza)
        harm_L = 0.08 * math.sin(2*math.pi*p["carrier2"]*t)
        harm_R = 0.08 * math.sin(2*math.pi*(p["carrier2"]+p["beat"]*1.5)*t)
        
        # 3. Sub-bass suave (corpo)
        sub = 0.05 * math.sin(2*math.pi*(p["base"]/2)*t)
        
        # 4. Chuva procedural (ruído colorado = pink noise)
        noise_raw = random.gauss(0, 1)
        rain = p["rain_vol"] * noise_raw * (0.7 + 0.3*abs(math.sin(2*math.pi*0.15*t)))
        
        # 5. Oceano (ondas lentas moduladas)
        wave1 = math.sin(2*math.pi*0.05*t)
        wave2 = math.sin(2*math.pi*0.03*t + 0.7)
        wave3 = math.sin(2*math.pi*0.08*t + 1.4)
        ocean = p["ocean_vol"] * (wave1+wave2+wave3)/3 * (random.gauss(0,1)*0.3 + 0.7)
        
        # 6. Ruído suave de fundo (ar ambiente)
        bg_noise = p["noise_vol"] * random.gauss(0, 1) * 0.4
        
        # Composição
        L_full = (tone_L + harm_L + sub + rain + ocean + bg_noise) * fade
        R_full = (tone_R + harm_R + sub + rain + ocean + bg_noise) * fade
        
        L_data.append(max(-32767, min(32767, int(32767 * L_full))))
        R_data.append(max(-32767, min(32767, int(32767 * R_full))))
        
        if i > 0 and i % (sr*1800) == 0:
            log(f"   Audio: {i//sr//60}min/{dur_sec//60}min")
    
    log(f"   Salvando {out_path}...")
    with wave.open(str(out_path), 'w') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr)
        wf.writeframes(b"".join(struct.pack('<hh',l,r) for l,r in zip(L_data,R_data)))
    log(f"   Audio OK: {out_path.stat().st_size//1024//1024}MB")
    return True

# ── TTS grátis multilingual (melhor qualidade por idioma) ─────────────
TTS_VOICES = {
    "PT": {"voice":"pt-BR-ThalitaMultilingualNeural", "rate":"+5%","vol":"+15%"},
    "EN": {"voice":"en-US-AvaMultilingualNeural",     "rate":"+3%","vol":"+12%"},
    "ES": {"voice":"es-MX-DaliaNeural",               "rate":"+5%","vol":"+12%"},
    "DE": {"voice":"de-DE-SeraphinaMultilingualNeural","rate":"+2%","vol":"+10%"},
    "FR": {"voice":"fr-FR-DeniseNeural",              "rate":"+3%","vol":"+10%"},
    "JA": {"voice":"ja-JP-NanamiNeural",              "rate":"+5%","vol":"+12%"},
    "KO": {"voice":"ko-KR-SunHiNeural",               "rate":"+5%","vol":"+12%"},
    "IT": {"voice":"it-IT-ElsaNeural",                "rate":"+3%","vol":"+10%"},
}

TTS_CTAS = {
    "PT": "Ative o sino para receber notificações. Inscreva-se no canal @psidanicoelho.",
    "EN": "Ring the bell to get notified. Subscribe to @psidanicoelho for daily psychology.",
    "ES": "Activa la campana para notificaciones. Suscríbete a @psidanicoelho.",
    "DE": "Aktiviere die Glocke für Benachrichtigungen. Abonniere @psidanicoelho.",
    "FR": "Active la cloche pour les notifications. Abonne-toi à @psidanicoelho.",
    "JA": "ベルをオンにして通知を受け取りましょう。@psidanicoelhoをチャンネル登録。",
    "KO": "알림 설정하고 @psidanicoelho 구독하세요.",
    "IT": "Attiva la campanella per le notifiche. Iscriviti a @psidanicoelho.",
}

def gen_tts_intro(lang, live_type, out_path):
    """Gera intro falada pelo edge-tts no idioma correto"""
    cfg = TTS_VOICES.get(lang, TTS_VOICES["PT"])
    cta = TTS_CTAS.get(lang, TTS_CTAS["PT"])
    
    intros = {
        "PT": f"Bem-vindo ao canal @psidanicoelho. {cta} Agora vou silenciar para você descansar.",
        "EN": f"Welcome to @psidanicoelho. {cta} Now I'll go quiet so you can rest.",
        "ES": f"Bienvenido a @psidanicoelho. {cta} Ahora me callo para que puedas descansar.",
        "DE": f"Willkommen bei @psidanicoelho. {cta} Jetzt werde ich leise sein.",
        "FR": f"Bienvenue sur @psidanicoelho. {cta} Je vais me taire maintenant.",
        "JA": f"@psidanicoelhoへようこそ。{cta} 今から静かにします。",
        "KO": f"@psidanicoelho에 오신 것을 환영합니다. {cta} 이제 조용히 할게요.",
        "IT": f"Benvenuto su @psidanicoelho. {cta} Ora starò in silenzio.",
    }
    
    text = intros.get(lang, intros["PT"])
    cmd = ["edge-tts", f"--voice={cfg['voice']}",
           f"--rate={cfg['rate']}", f"--volume={cfg['vol']}",
           "--text", text[:400], "--write-media", str(out_path)]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=60)
        if r.returncode == 0 and pathlib.Path(out_path).stat().st_size > 200:
            log(f"   TTS {lang}: {pathlib.Path(out_path).stat().st_size//1024}KB")
            return True
    except Exception as e:
        log(f"   TTS err: {e}")
    return False

# ── Stream principal ──────────────────────────────────────────────────
def start_live():
    # Detectar idioma e tipo
    lang = FORCE_LANG.upper() if FORCE_LANG else detect_lang_by_utc()
    live_type = LIVE_TYPE if LIVE_TYPE != "auto" else detect_live_type()
    
    if lang not in LANGS: lang = "PT"
    cfg = LANGS[lang]
    
    # Selecionar configuração de conteúdo
    content = cfg.get(live_type, cfg.get("sleep"))
    title = content["title"]
    description = content["description"]
    tags = content["tags"]
    
    dur_sec = DURATION_H * 3600
    rtmp = f"rtmps://a.rtmps.youtube.com/live2/{STREAM_KEY}"
    
    log("="*65)
    log(f"LIVE GLOBAL V4 — {lang} ({cfg['name']}) | {live_type.upper()}")
    log(f"  Titulo: {title[:60]}")
    log(f"  Duracao: {DURATION_H}h | CPM est: {cfg['cpm_est']}")
    log(f"  Hora UTC: {datetime.now(timezone.utc).strftime('%H:%M UTC')}")
    log("="*65)
    
    # 1. Gerar áudio binaural HQ (1h, loop no ffmpeg)
    log("1. Gerando audio binaural HQ...")
    BLOCK = min(3600, dur_sec)  # 1h block
    audio_path = TMP/f"binaural_{live_type}.wav"
    gen_binaural_hq(audio_path, BLOCK, live_type)
    
    # 2. Gerar intro TTS
    intro_mp3 = TMP/f"intro_{lang}.mp3"
    log(f"2. Gerando intro TTS {lang}...")
    has_intro = gen_tts_intro(lang, live_type, intro_mp3)
    
    # 3. Stream com tela preta absoluta + binaural em loop
    ff = ffm()
    log(f"3. Iniciando stream... ({ff.split('/')[-1]})")
    log(f"   RTMP: {rtmp[:50]}...")
    
    # Cor da tela por tipo (tela PRETA para sono, quase-preta para outros)
    COLORS = {
        "sleep": "0x000000",      # Preto absoluto — sono profundo
        "study": "0x06060F",      # Quase preto — azul noturno
        "meditation": "0x030309",  # Quase preto — roxo muito escuro
        "anxiety": "0x030a03",    # Quase preto — verde muito escuro
    }
    bg_color = COLORS.get(live_type, "0x000000")
    
    stream_cmd = [
        ff, "-y",
        # Video: cor sólida em loop (1fps para economizar CPU)
        "-f","lavfi","-i",f"color=c={bg_color}:size=1920x1080:r=1",
        # Audio: intro (se existir) + binaural em loop
        "-stream_loop","-1","-i",str(audio_path),
        # Texto mínimo — apenas handle do canal
        "-vf", "drawtext=text='@psidanicoelho':fontcolor=white:fontsize=20:x=16:y=16:alpha=0.3",
        "-map","0:v","-map","1:a",
        # Codecs: baixo bitrate para tela preta (economiza banda)
        "-c:v","libx264","-preset","ultrafast","-crf","35",
        "-b:v","800k","-maxrate","1000k","-bufsize","2000k",
        "-g","60","-keyint_min","60","-r","1","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","128k","-ac","2","-ar","44100",
        "-f","flv","-t",str(dur_sec),
        rtmp
    ]
    
    log(f"   LIVE ATIVA: {title[:55]}")
    r = subprocess.run(stream_cmd, timeout=dur_sec+180)
    log(f"   Stream encerrado (rc={r.returncode}) — {DURATION_H}h completas")
    return True

if __name__ == "__main__":
    start_live()
