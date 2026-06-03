#!/usr/bin/env python3
"""🎨 Channel Branding — Banner + Perfil + Descrição SEO semanal"""
import os, json, io, urllib.request, urllib.parse
from datetime import datetime

SBU = os.getenv("SUPABASE_URL",""); SBK = os.getenv("SUPABASE_SERVICE_KEY","")

def get_token():
    rt = os.getenv("YT_REFRESH_TOKEN",""); ci = os.getenv("YT_CLIENT_ID",""); cs = os.getenv("YT_CLIENT_SECRET","")
    if not all([rt,ci,cs]): return ""
    body = urllib.parse.urlencode({"client_id":ci,"client_secret":cs,"refresh_token":rt,"grant_type":"refresh_token"}).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token",data=body)
    with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read()).get("access_token","")

def create_banner_png():
    """Cria banner 2560x1440 com Pillow se disponível"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB",(2560,1440),(6,6,15))
        draw = ImageDraw.Draw(img)
        # Fundo gradiente
        for y in range(1440):
            r = int(6 + (y/1440)*20)
            g = int(6 + (y/1440)*10)
            b = int(15 + (y/1440)*40)
            draw.line([(0,y),(2560,y)], fill=(r,g,b))
        # Símbolo ψ
        draw.text((1280,500),"ψ",fill=(124,58,237))
        draw.text((800,700),"DANIELA COELHO",fill=(255,255,255))
        draw.text((700,820),"Pesquisadora de Comportamento Humano",fill=(200,200,200))
        draw.text((1000,940),"Novo conteúdo toda semana",fill=(124,58,237))
        buf = io.BytesIO(); img.save(buf,"JPEG",quality=90); return buf.getvalue()
    except ImportError:
        return None  # Pillow não disponível

def main():
    print(f"[{datetime.now():%H:%M:%S}] 🎨 Channel Branding iniciado")
    tok = get_token()
    if not tok: print("  ⚠️  Token não disponível"); return
    
    # Atualizar keywords do canal
    update = {
        "id": "UCSH63tBfY6wEIdkC4u4zKdg",
        "brandingSettings": {
            "channel": {
                "title": "Daniela Coelho — Pesquisadora de Comportamento Humano",
                "description": "A ciência explica o que você sente mas não consegue nomear. Narcisismo, trauma, ansiedade, manipulação. @psidanicoelho",
                "keywords": "psicologia,comportamento humano,saude mental,narcisismo,ansiedade,trauma,neurociencia,Daniela Coelho,apego,burnout",
                "country": "BR",
                "unsubscribedTrailer": ""
            }
        }
    }
    
    try:
        body = json.dumps(update).encode()
        req = urllib.request.Request("https://www.googleapis.com/youtube/v3/channels?part=brandingSettings",
            data=body, method="PUT")
        req.add_header("Authorization",f"Bearer {tok}"); req.add_header("Content-Type","application/json")
        with urllib.request.urlopen(req,timeout=20) as r: pass
        print("  ✅ Branding atualizado!")
    except Exception as e:
        print(f"  ⚠️ Branding: {e}")
    
    print("  ✅ Channel Branding completo")

if __name__ == "__main__":
    main()
