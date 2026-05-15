#!/usr/bin/env python3
"""
tts_v3.py — Cerebro V3 CINEMATOGRAFICO
Voz: ElevenLabs Sarah, contemplativa, 0.88x velocidade, pausas estrategicas
Padrao: documentario psicologico cinematografico premium
"""
import os, asyncio, requests, time, subprocess, re
from supabase import create_client

SB_URL = os.environ["SUPABASE_URL"]
SB_KEY = os.environ["SUPABASE_KEY"]
sb = create_client(SB_URL, SB_KEY)
SB_ANON = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRwanZhbHp3a3F3dHR2bXN6dmllIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYwMzUyOTMsImV4cCI6MjA5MTYxMTI5M30.UEgUo0Mw15ihQZykLAY5QApRzgTXkfIewZFzIgwao3Q"

EL_KEY   = os.environ.get("ELEVENLABS_API_KEY","")
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Sarah multilingual — voz contemplativa
MODEL    = "eleven_multilingual_v2"

def adicionar_pausas_cinematograficas(script):
    """Insere pausas estrategicas para o padrao contemplativo/documentario."""
    texto = script
    gatilhos = [
        " porque"," porem"," contudo"," entretanto"," na verdade",
        " o que"," isso significa"," isso quer dizer"," a questao",
        " o motivo"," a razao"," o problema"," a verdade"
    ]
    for g in gatilhos:
        texto = texto.replace(g, "..." + g)
    # Quebra de paragrafo entre frases longas
    texto = re.sub(r"(\.\s+)([A-Z])", r".\n\n\2", texto)
    # Limitar reticencias multiplas
    texto = re.sub(r"\.{4,}", "...", texto)
    return texto

def gerar_elevenlabs(script, video_id):
    if not EL_KEY:
        print("    ElevenLabs key ausente")
        return None
    script_com_pausas = adicionar_pausas_cinematograficas(script)
    try:
        r = requests.post(
            "https://api.elevenlabs.io/v1/text-to-speech/" + VOICE_ID,
            headers={"xi-api-key": EL_KEY, "Content-Type": "application/json"},
            json={
                "text": script_com_pausas,
                "model_id": MODEL,
                "language_code": "pt",
                "voice_settings": {
                    "stability": 0.52,
                    "similarity_boost": 0.80,
                    "style": 0.12,
                    "use_speaker_boost": True
                },
                "output_format": "mp3_44100_192"
            },
            timeout=180
        )
        print("    ElevenLabs: " + str(r.status_code))
        if r.status_code == 200:
            raw = "/tmp/el_raw_" + str(video_id) + ".mp3"
            with open(raw, "wb") as f:
                f.write(r.content)
            # Aplicar 0.88x — voz contemplativa (referencia: canais de doc psicologico)
            slow = "/tmp/el_" + str(video_id) + ".mp3"
            resultado = subprocess.run(
                ["ffmpeg","-y","-i",raw,
                 "-filter:a","atempo=0.88",
                 "-codec:a","libmp3lame","-b:a","192k",slow],
                capture_output=True, timeout=60
            )
            if resultado.returncode == 0 and os.path.exists(slow):
                print("    OK Sarah 0.88x: " + str(os.path.getsize(slow)) + "B")
                return slow
            else:
                print("    slowdown falhou, usando raw")
                return raw
        try:
            err = r.json().get("detail","")[:150]
        except:
            err = r.text[:150]
        print("    erro: " + str(err))
    except Exception as e:
        print("    EL exc: " + str(e))
    return None

async def gerar_edge(script, video_id):
    try:
        import edge_tts
        raw = "/tmp/edge_raw_" + str(video_id) + ".mp3"
        tts = edge_tts.Communicate(script, voice="pt-BR-ThalitaMultilingualNeural", rate="-12%")
        await tts.save(raw)
        slow = "/tmp/edge_" + str(video_id) + ".mp3"
        subprocess.run(
            ["ffmpeg","-y","-i",raw,
             "-filter:a","atempo=0.90",
             "-codec:a","libmp3lame","-b:a","192k",slow],
            capture_output=True, timeout=60
        )
        p = slow if os.path.exists(slow) else raw
        print("    Edge TTS 0.90x: " + str(os.path.getsize(p)) + "B")
        return p
    except Exception as e:
        print("    Edge falhou: " + str(e))
    return None

def upload_audio(path, video_id):
    fname = "audios/v" + str(video_id) + "_cinem.mp3"
    with open(path, "rb") as f:
        data = f.read()
    r = requests.post(
        SB_URL + "/storage/v1/object/videos/" + fname,
        headers={
            "apikey": SB_ANON, "Authorization": "Bearer " + SB_ANON,
            "Content-Type": "audio/mpeg", "x-upsert": "true"
        },
        data=data
    )
    if r.status_code in [200,201]:
        return SB_URL + "/storage/v1/object/public/videos/" + fname
    print("    upload err: " + str(r.status_code))
    return None

def main():
    print("=== TTS V3 CINEMATOGRAFICO — ElevenLabs Sarah 0.88x ===")
    el_status = "OK" if EL_KEY else "AUSENTE fallback Edge"
    print("ElevenLabs: " + el_status)
    r = sb.table("content_pipeline").select(
        "id,title,script,duracao_min,pub_order"
    ).eq("status","mp4_ready").is_("audio_url",None).order("pub_order").limit(5).execute()
    videos = r.data or []
    print("Videos sem audio: " + str(len(videos)))
    for v in videos:
        vid_id = v["id"]
        script = (v.get("script") or "").strip()
        if not script:
            print("  #" + str(vid_id) + ": sem script")
            continue
        print("\n  #" + str(vid_id) + " " + str(v.get("title",""))[:50])
        path = gerar_elevenlabs(script, vid_id)
        if not path:
            path = asyncio.run(gerar_edge(script, vid_id))
        if not path:
            print("    todos TTS falharam")
            continue
        url = upload_audio(path, vid_id)
        if url:
            vname = "ElevenLabs_Sarah_0.88x" if "el_" in path else "Edge_Thalita_0.90x"
            sb.table("content_pipeline").update(
                {"audio_url": url, "voice_name": vname}
            ).eq("id", vid_id).execute()
            print("    OK audio (" + vname + ")")

if __name__ == "__main__":
    main()
