#!/usr/bin/env python3
"""
tts_v5.py — Cerebro V5 — O PADRAO ETERNO
Voz: Fish Audio (gratuita, masculina, cinematografica)
Fallback: ElevenLabs George → Edge TTS
ZERO branding na voz — narrador anonimo, intelectual, contemplativo
"""
import os, asyncio, requests, time, json
from supabase import create_client

SB_URL = os.environ["SUPABASE_URL"]
SB_KEY = os.environ["SUPABASE_KEY"]
sb = create_client(SB_URL, SB_KEY)

EL_KEY   = os.environ.get("ELEVENLABS_API_KEY","")
FISH_KEY = os.environ.get("FISHAUDIO_API_KEY","")
EL_MODEL = "eleven_multilingual_v2"

# Fish Audio — vozes masculinas intelectuais (IDs do catalogo publico)
# Fallback para ElevenLabs George se Fish Audio falhar
FISH_VOICES = [
    "54a5170264694bfc8e9ad98df7bd89c3",  # Alan — voz masculina profunda
    "0eb22a6a2e954f6aae5b39b955b0fef8",  # modelo narrativo masculino
]

def gerar_fish_audio(script, video_id):
    """Fish Audio API — gratuita, vozes cinematograficas"""
    if not FISH_KEY:
        print("    Fish Audio key ausente")
        return None, None
    for voice_id in FISH_VOICES:
        try:
            r = requests.post(
                "https://api.fish.audio/v1/tts",
                headers={"Authorization": "Bearer " + FISH_KEY,
                         "Content-Type": "application/json"},
                json={
                    "text": script,
                    "reference_id": voice_id,
                    "format": "mp3",
                    "mp3_bitrate": 192,
                    "normalize": True,
                    "latency": "normal"
                }, timeout=180)
            print("    Fish Audio " + voice_id[:8] + ": " + str(r.status_code))
            if r.status_code == 200:
                path = "/tmp/fish_" + str(video_id) + ".mp3"
                with open(path,"wb") as f: f.write(r.content)
                size = os.path.getsize(path)
                if size > 10000:
                    print("    OK Fish Audio: " + str(size) + "B")
                    return path, "FishAudio_" + voice_id[:8]
            elif r.status_code == 401:
                print("    Fish Audio: key invalida")
                break
            else:
                try: print("    Fish Audio err: " + str(r.json())[:100])
                except: print("    Fish Audio err: " + r.text[:100])
        except Exception as e:
            print("    Fish Audio exc: " + str(e)[:80])
    return None, None

def gerar_elevenlabs(script, video_id):
    """ElevenLabs George — fallback principal"""
    if not EL_KEY: return None, None
    try:
        r = requests.post(
            "https://api.elevenlabs.io/v1/text-to-speech/JBFqnCBsd6RMkjVDRZzb",
            headers={"xi-api-key": EL_KEY, "Content-Type": "application/json"},
            json={"text": script, "model_id": EL_MODEL, "language_code": "pt",
                  "voice_settings": {"stability": 0.42, "similarity_boost": 0.82,
                                     "style": 0.28, "use_speaker_boost": True},
                  "output_format": "mp3_44100_192"},
            timeout=180)
        print("    ElevenLabs George: " + str(r.status_code))
        if r.status_code == 200:
            p = "/tmp/el_" + str(video_id) + ".mp3"
            with open(p,"wb") as f: f.write(r.content)
            print("    OK George: " + str(os.path.getsize(p)) + "B")
            return p, "ElevenLabs_George"
        try: print("    EL err: " + str(r.json().get("detail",""))[:100])
        except: pass
    except Exception as e:
        print("    EL exc: " + str(e)[:80])
    return None, None

async def gerar_edge(script, video_id):
    try:
        import edge_tts
        p = "/tmp/edge_" + str(video_id) + ".mp3"
        tts = edge_tts.Communicate(script, voice="pt-BR-ThalitaMultilingualNeural", rate="-5%")
        await tts.save(p)
        print("    Edge TTS fallback: " + str(os.path.getsize(p)) + "B")
        return p, "Edge_Thalita"
    except Exception as e:
        print("    Edge falhou: " + str(e))
    return None, None

def upload_audio(path, video_id):
    fname = "audios/v" + str(video_id) + "_v5.mp3"
    with open(path,"rb") as f: data = f.read()
    r = requests.post(SB_URL+"/storage/v1/object/videos/"+fname,
        headers={"apikey":SB_KEY,"Authorization":"Bearer "+SB_KEY,
                 "Content-Type":"audio/mpeg","x-upsert":"true"}, data=data)
    if r.status_code in [200,201]:
        return SB_URL+"/storage/v1/object/public/videos/"+fname
    print("    upload err: " + str(r.status_code))
    return None

def main():
    print("=== TTS V5 — Fish Audio + ElevenLabs George ===")
    print("Fish: " + ("OK" if FISH_KEY else "ausente") + " | EL: " + ("OK" if EL_KEY else "ausente"))
    r = sb.table("content_pipeline").select(
        "id,title,script,duracao_min,pub_order"
    ).eq("status","mp4_ready").is_("audio_url",None).order("pub_order").limit(5).execute()
    videos = r.data or []
    print("Videos sem audio: " + str(len(videos)))
    for v in videos:
        vid_id = v["id"]
        script = (v.get("script") or "").strip()
        if not script: continue
        print("\n  #" + str(vid_id) + " " + str(v.get("title",""))[:50])
        # 1. Fish Audio (gratuito)
        path, voz = gerar_fish_audio(script, vid_id)
        # 2. ElevenLabs George (fallback)
        if not path:
            path, voz = gerar_elevenlabs(script, vid_id)
        # 3. Edge TTS (ultimo recurso)
        if not path:
            path, voz = asyncio.run(gerar_edge(script, vid_id))
            voz = "Edge_Thalita"
        if not path: continue
        url = upload_audio(path, vid_id)
        if url:
            sb.table("content_pipeline").update(
                {"audio_url":url,"voice_name":voz}
            ).eq("id",vid_id).execute()
            print("    OK (" + str(voz) + ")")

if __name__ == "__main__":
    main()
