#!/usr/bin/env python3
"""
gen_psych2go.py — Formato Psych2Go (10.5M subs, $80K/mês)
Listicles de psicologia: "10 Signs of Covert Narcissism"
CTR típico: 12-18% — algoritmo favorece muito
Duração: 4-7 min | CPM: $8-20
"""
import os, subprocess, requests, pathlib, textwrap, time

IDIOMA = os.getenv("CANAL_IDIOMA","EN")
GROQ   = os.getenv("GROQ_API_KEY","")
TMP    = pathlib.Path(f"/tmp/psych2go_{IDIOMA}"); TMP.mkdir(exist_ok=True)
W, H   = 1920, 1080

# Listicles top — baseados nos vídeos mais virais do Psych2Go
LISTICLES = {
"EN": [
  {"num":10,"tema":"Signs You're Dealing with a Covert Narcissist",
   "items":["They always play the victim","Your reality gets constantly questioned","They use silence as punishment","Compliments come with hidden stings","They monitor your reactions closely","Guilt trips are their superpower","They need constant validation","Your achievements trigger their jealousy","They rewrite history conveniently","You feel drained after every interaction"]},
  {"num":7,"tema":"Signs of Anxious Attachment You Might Miss",
   "items":["You check your phone obsessively after sending a message","You apologize when you have nothing to apologize for","You catastrophize silence","You feel responsible for other people's emotions","Conflict feels like abandonment","You need constant reassurance","You lose yourself in relationships"]},
  {"num":8,"tema":"Signs You Have Silent Depression",
   "items":["You function perfectly but feel completely empty","You laugh genuinely but cry alone","You're productive but don't care about any of it","You isolate to avoid explaining yourself","Sleep is an escape, not rest","You forget what you used to enjoy","Small tasks feel monumental","You fantasize about disappearing but not dying"]},
  {"num":5,"tema":"Manipulation Tactics Narcissists Use",
   "items":["Future faking — promising things they never intend to deliver","DARVO — Deny, Attack, Reverse Victim and Offender","Love bombing followed by sudden withdrawal","Triangulation — using others to create jealousy","The silent treatment as punishment and control"]},
],
"PT": [
  {"num":10,"tema":"Sinais de que Você Está com um Narcisista Encoberto",
   "items":["Sempre se colocam como vítima","Questionam sua realidade constantemente","Usam o silêncio como punição","Elogios vêm com críticas disfarçadas","Monitoram suas reações de perto","A culpa é sempre sua","Precisam de validação constante","Suas conquistas os deixam com inveja","Reescrevem a história convenientemente","Você se sente esgotado após cada interação"]},
  {"num":7,"tema":"Sinais de Apego Ansioso que Você Pode Estar Ignorando",
   "items":["Você checa o celular obsessivamente depois de mandar mensagem","Pede desculpas quando não fez nada errado","Catastrofiza o silêncio","Se sente responsável pelas emoções dos outros","Conflito parece abandono","Precisa de reasseguramento constante","Você se perde nos relacionamentos"]},
  {"num":8,"tema":"Sinais de Depressão Silenciosa",
   "items":["Funciona perfeitamente mas se sente completamente vazio","Ri de verdade mas chora sozinho","É produtivo mas não se importa com nada","Se isola para evitar explicações","O sono é fuga, não descanso","Esqueceu o que costumava curtir","Tarefas pequenas parecem monumentais","Fantasias de desaparecer mas não de morrer"]},
],
"ES": [
  {"num":10,"tema":"Señales de que Estás con un Narcisista Encubierto",
   "items":["Siempre se presentan como víctimas","Cuestionan tu realidad constantemente","Usan el silencio como castigo","Los elogios vienen con críticas disfrazadas","Monitorean tus reacciones de cerca","La culpa siempre es tuya","Necesitan validación constante","Tus logros les provocan envidia","Reescriben la historia convenientemente","Te sientes agotado después de cada interacción"]},
  {"num":7,"tema":"Señales de Apego Ansioso",
   "items":["Revisas tu teléfono obsesivamente después de enviar un mensaje","Te disculpas cuando no hiciste nada malo","Catastrofizas el silencio","Te sientes responsable por las emociones de otros","El conflicto se siente como abandono","Necesitas reaseguramiento constante","Te pierdes en las relaciones"]},
],
"DE": [
  {"num":10,"tema":"Zeichen für einen verdeckten Narzissten",
   "items":["Sie spielen immer das Opfer","Deine Realität wird ständig in Frage gestellt","Sie nutzen Schweigen als Strafe","Komplimente kommen mit versteckten Stacheln","Sie überwachen deine Reaktionen genau","Schuldgefühle sind ihre Superkraft","Sie brauchen ständige Bestätigung","Deine Erfolge wecken ihren Neid","Sie schreiben Geschichte bequem um","Du fühlst dich nach jeder Interaktion ausgelaugt"]},
],
"FR": [
  {"num":10,"tema":"Signes d'un Narcissique Masqué",
   "items":["Il joue toujours la victime","Votre réalité est constamment remise en question","Il utilise le silence comme punition","Les compliments cachent des piques","Il surveille vos réactions de près","Les manipulations par la culpabilité sont son super-pouvoir","Il a besoin de validation constante","Vos succès déclenchent sa jalousie","Il réécrit l'histoire à sa convenance","Vous vous sentez épuisé après chaque interaction"]},
],
"JA": [
  {"num":10,"tema":"隠れた自己愛者と付き合っているサイン",
   "items":["常に被害者を演じる","あなたの現実を常に疑問視する","沈黙を罰として使う","褒め言葉に隠れたトゲがある","あなたの反応を注意深く監視する","罪悪感の植え付けが得意","絶え間ない承認を必要とする","あなたの成功に嫉妬する","都合よく歴史を書き換える","交流するたびに疲弊する"]},
],
"KO": [
  {"num":10,"tema":"은밀한 나르시시스트와 함께하고 있다는 징후",
   "items":["항상 피해자를 연기한다","당신의 현실을 끊임없이 의심한다","침묵을 벌로 사용한다","칭찬 뒤에 숨겨진 가시가 있다","당신의 반응을 면밀히 관찰한다","죄책감 유발이 그들의 초능력","끊임없는 검증이 필요하다","당신의 성취에 질투한다","역사를 편리하게 다시 쓴다","모든 상호작용 후 지쳐있다"]},
],
}
# Adicionar versões simplificadas para IT, ZH, AR, RU, HI
for idioma in ["IT","ZH","AR","RU","HI"]:
    LISTICLES[idioma] = LISTICLES["EN"][:1]  # Usa EN como fallback

def groq_narrar(item_num, item_texto, idioma):
    """Gera narração de 1 frase para cada item — via Groq"""
    if not GROQ: return item_texto
    lang_map = {"EN":"English","PT":"Portuguese Brazilian","ES":"Spanish","DE":"German",
                "FR":"French","JA":"Japanese","KO":"Korean","IT":"Italian","ZH":"Chinese","AR":"Arabic","RU":"Russian","HI":"Hindi"}
    lang = lang_map.get(idioma,"English")
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization":f"Bearer {GROQ}","Content-Type":"application/json"},
            json={"model":"llama-3.3-70b-versatile",
                  "messages":[{"role":"user","content":
                    f"In {lang}, write ONE powerful sentence (max 15 words) expanding on this psychology sign: '{item_texto}'. "
                    f"No numbering. Direct, impactful, evidence-based tone."}],
                  "max_tokens":60,"temperature":0.7},
            timeout=10)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
    except: pass
    return item_texto

def gerar_slide_item(num_total, item_num, item_texto, narr_texto, tema, out_path):
    """Cria 1 slide com o item da lista — estilo Psych2Go"""
    prog_w = max(4, int(W * item_num / num_total))
    cor    = ["#7C3AED","#3B82F6","#10B981","#F59E0B","#EF4444",
              "#8B5CF6","#06B6D4","#84CC16","#F97316","#EC4899"][item_num % 10]
    
    num_esc  = f"#{item_num}".replace("'",r"\'")
    item_esc = item_texto[:50].replace("'",r"\'")
    narr_esc = narr_texto[:80].replace("'",r"\'")
    tema_esc = tema[:55].replace("'",r"\'")
    
    vf = (
        f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
        f"colorchannelmixer=rr=0.5:gg=0.5:bb=0.5,"
        # Barra progresso no topo
        f"drawbox=y=0:color={cor}:width={prog_w}:height=8:t=fill,"
        f"drawbox=y=8:color=black@0.9:width=iw:height=92:t=fill,"
        # Título do vídeo
        f"drawtext=text='{num_total} {tema_esc}':fontsize=22:fontcolor=#94A3B8:x=20:y=20,"
        # Número do item em destaque (como Psych2Go faz)
        f"drawbox=x=iw/2-200:y=ih/2-140:color={cor}:width=400:height=100:t=fill,"
        f"drawtext=text='{num_esc}':fontsize=60:fontcolor=white:x=(w-text_w)/2:y=h/2-130:bold=1,"
        # Item texto
        f"drawbox=y=ih/2-20:color=black@0.75:width=iw:height=130:t=fill,"
        f"drawtext=text='{item_esc}':fontsize=38:fontcolor=white:x=(w-text_w)/2:y=h/2-10:bold=1:shadowcolor=#000:shadowx=2:shadowy=2,"
        # Narração
        f"drawbox=y=ih/2+130:color=black@0.6:width=iw:height=80:t=fill,"
        f"drawtext=text='{narr_esc}':fontsize=22:fontcolor=#CBD5E1:x=(w-text_w)/2:y=h/2+145,"
        # Barra inferior
        f"drawbox=y=ih-80:color=black@0.85:width=iw:height=80:t=fill,"
        f"drawtext=text='Psychology Frequencies':fontsize=18:fontcolor={cor}:x=20:y=h-52,"
        f"drawtext=text='Evidence-Based Science':fontsize=16:fontcolor=#64748B:x=20:y=h-28"
    )
    subprocess.run([
        "ffmpeg","-y","-loop","1","-i",str(out_path.parent/f"bg_{item_num % 4}.jpg"),
        "-vf",vf,"-t","12",
        "-c:v","libx264","-preset","fast","-pix_fmt","yuv420p","-r","30","-an",
        str(out_path)
    ], capture_output=True, timeout=60)
    return out_path.exists()

def run():
    if IDIOMA not in LISTICLES or not LISTICLES[IDIOMA]:
        print(f"Sem listicles para {IDIOMA}")
        return
    
    listicle = LISTICLES[IDIOMA][0]
    print(f"=== PSYCH2GO FORMAT | {IDIOMA} | {listicle['num']} {listicle['tema'][:40]} ===")
    
    # Gerar 4 imagens base variadas
    for i in range(4):
        seeds = [9001, 9078, 9155, 9232]
        prompts = [
            "masterpiece, dark minimalist background, purple gradient, abstract particles, psychology concept, no text no people",
            "masterpiece, dark blue background, neural network visualization, brain concept, abstract, no text no people",
            "masterpiece, dark background, geometric mandala purple blue, meditation concept, no text no people",
            "masterpiece, dark cosmic background, stars and nebula, consciousness concept, no text no people",
        ]
        p = prompts[i]
        url = (f"https://image.pollinations.ai/prompt/{requests.utils.quote(p)}"
               f"?model=flux&width={W}&height={H}&seed={seeds[i]}&nologo=true")
        try:
            ri = requests.get(url, timeout=60)
            if ri.status_code == 200 and len(ri.content) > 10000:
                (TMP/f"bg_{i}.jpg").write_bytes(ri.content)
                print(f"  ✅ Bg {i+1}/4")
        except: pass
        time.sleep(2)
    
    # Gerar slide de cada item
    slides = []
    for j, item in enumerate(listicle["items"], 1):
        narr = groq_narrar(j, item, IDIOMA)
        sl   = TMP/f"slide_{j:02d}.mp4"
        if gerar_slide_item(len(listicle["items"]), j, item, narr, listicle["tema"], sl):
            slides.append(sl)
            print(f"  ✅ Item {j}/{len(listicle['items'])}: {item[:40]}")
        time.sleep(1)
    
    if not slides: return
    
    # Concatenar
    pl = TMP/"pl.txt"
    with open(pl,"w") as f:
        [f.write(f"file '{s.resolve()}'\n") for s in slides]
    
    out = TMP/f"psych2go_{IDIOMA}_{listicle['num']}signs.mp4"
    subprocess.run([
        "ffmpeg","-y","-f","concat","-safe","0","-i",str(pl),
        "-f","lavfi","-i","sine=frequency=432:duration=300",
        "-c:v","copy","-c:a","aac","-b:a","128k","-shortest",str(out)
    ], capture_output=True, timeout=300)
    
    if out.exists():
        print(f"\n✅ PRONTO: {out} ({out.stat().st_size//1024//1024}MB)")
        print(f"   Título: {listicle['num']} Signs {listicle['tema']}")

if __name__ == "__main__":
    run()
