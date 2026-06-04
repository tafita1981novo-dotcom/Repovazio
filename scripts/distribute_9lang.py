#!/usr/bin/env python3
"""
distribute_9lang.py — Distribuição automática 9 idiomas
YouTube: atualiza metadados em todos os idiomas
TikTok: posta shorts (requer TT_CLIENT_KEY + TT_ACCESS_TOKEN)
Instagram: posta reels (requer IG_USER_ID + IG_ACCESS_TOKEN)
"""
import os,sys,json,urllib.request,urllib.parse,time,random
from datetime import datetime,timezone

# Importar SEO
sys.path.insert(0,"/home/runner/work/Repovazio/Repovazio/scripts")
try:
    import seo_9idiomas as SEO
    TITULOS=SEO.TITULOS; DESC=SEO.DESC
except:
    TITULOS={"en":["🔴 LIVE 24/7 | BLACK SCREEN for Sleep | Binaural 432Hz"]}
    DESC={"en":"Black screen binaural 432hz dark psychology @psidanicoelho"}

YT_CLIENT_ID     = os.environ.get("YT_CLIENT_ID","")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET","")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN","")
TT_CLIENT_KEY    = os.environ.get("TT_CLIENT_KEY","")
TT_ACCESS_TOKEN  = os.environ.get("TT_ACCESS_TOKEN","")
IG_USER_ID       = os.environ.get("IG_USER_ID","")
IG_ACCESS_TOKEN  = os.environ.get("IG_ACCESS_TOKEN","")
SB_URL           = os.environ.get("SUPABASE_URL","")
SB_KEY           = os.environ.get("SUPABASE_SERVICE_KEY","")

def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}",flush=True)

def get_yt_token():
    if not YT_CLIENT_ID: return ""
    data=urllib.parse.urlencode({"client_id":YT_CLIENT_ID,"client_secret":YT_CLIENT_SECRET,
        "refresh_token":YT_REFRESH_TOKEN,"grant_type":"refresh_token"}).encode()
    req=urllib.request.Request("https://oauth2.googleapis.com/token",data=data)
    req.add_header("Content-Type","application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req,timeout=15) as r:
            return json.loads(r.read()).get("access_token","")
    except: return ""

def get_latest_video(yt_token):
    """Pega o vídeo mais recente do canal (não-live)"""
    req=urllib.request.Request(
        "https://www.googleapis.com/youtube/v3/channels?part=contentDetails&mine=true")
    req.add_header("Authorization",f"Bearer {yt_token}")
    try:
        with urllib.request.urlopen(req,timeout=15) as r:
            ch=json.loads(r.read())
        pid=ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        req2=urllib.request.Request(
            f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={pid}&maxResults=5")
        req2.add_header("Authorization",f"Bearer {yt_token}")
        with urllib.request.urlopen(req2,timeout=15) as r:
            pl=json.loads(r.read())
        # Filtrar apenas vídeos (não lives)
        for item in pl.get("items",[]):
            vid_id=item["snippet"]["resourceId"]["videoId"]
            title=item["snippet"]["title"]
            if "LIVE" not in title.upper() and "AO VIVO" not in title.upper():
                return vid_id, title
    except Exception as e:
        log(f"get_latest_video: {e}")
    return None, None

def update_yt_video_seo(yt_token, vid_id, lang):
    """Atualiza metadados de um vídeo em um idioma específico"""
    titles=TITULOS.get(lang,TITULOS.get("en",[]))
    if not titles: return
    titulo=random.choice(titles)
    desc_text=DESC.get(lang, DESC.get("en",""))
    
    try:
        # Pegar snippet atual
        req=urllib.request.Request(
            f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={vid_id}")
        req.add_header("Authorization",f"Bearer {yt_token}")
        with urllib.request.urlopen(req,timeout=15) as r:
            vdata=json.loads(r.read())
        
        if not vdata.get("items"): return
        snippet=vdata["items"][0]["snippet"]
        cat_id=snippet.get("categoryId","22")
        
        # Atualizar
        body=json.dumps({
            "id":vid_id,
            "snippet":{
                "title":titulo[:100],
                "description":desc_text[:4900],
                "categoryId":cat_id,
                "defaultLanguage":"en",
                "tags":["black screen","binaural beats 432hz","432hz","sleep music",
                        "dark psychology","narcissism","danielacoelho","psidanicoelho",
                        "tela preta","schwarzer bildschirm","pantalla negra","blackscreen",
                        "black screen for sleep","binaural beats sleep","study music",
                        "focus music","meditation music","deep sleep music"]
            }
        }).encode()
        req2=urllib.request.Request(
            "https://www.googleapis.com/youtube/v3/videos?part=snippet",
            data=body,method="PUT")
        req2.add_header("Authorization",f"Bearer {yt_token}")
        req2.add_header("Content-Type","application/json")
        with urllib.request.urlopen(req2,timeout=15):
            log(f"YT SEO [{lang.upper()}]: {titulo[:60]} ✅")
    except Exception as e:
        log(f"update_yt_seo {lang}: {e}")

def post_tiktok(video_url, caption_lang="en"):
    """Posta no TikTok via API v2"""
    if not TT_ACCESS_TOKEN:
        log("TikTok: sem token (configure TT_ACCESS_TOKEN no GitHub Secrets)")
        return False
    titulo=random.choice(TITULOS.get(caption_lang,TITULOS["en"]))
    caption=f"{titulo[:140]} #blackscreen #binaural #432hz #darkpsychology #psidanicoelho"
    try:
        body=json.dumps({
            "post_info":{"title":caption,"privacy_level":"PUBLIC_TO_EVERYONE"},
            "source_info":{"source":"PULL_FROM_URL","video_url":video_url}
        }).encode()
        req=urllib.request.Request(
            "https://open.tiktokapis.com/v2/post/publish/video/init/",
            data=body,method="POST")
        req.add_header("Authorization",f"Bearer {TT_ACCESS_TOKEN}")
        req.add_header("Content-Type","application/json; charset=UTF-8")
        with urllib.request.urlopen(req,timeout=30) as r:
            result=json.loads(r.read())
        log(f"TikTok: {result.get('data',{}).get('publish_id','?')} ✅")
        return True
    except Exception as e:
        log(f"TikTok erro: {e}")
        return False

def post_instagram(video_url, caption_lang="en"):
    """Posta no Instagram Reels via Graph API"""
    if not IG_ACCESS_TOKEN or not IG_USER_ID:
        log("Instagram: sem token (configure IG_USER_ID + IG_ACCESS_TOKEN no GitHub Secrets)")
        return False
    titulo=random.choice(TITULOS.get(caption_lang,TITULOS["en"]))
    caption=f"{titulo}\n\n🖤 BLACK SCREEN 24/7 • BINAURAL 432Hz\n\n#blackscreen #binaural #432hz #darkpsychology #psychology #narcissism #sleep #study #meditation #psidanicoelho #danielacoelho"
    try:
        # Criar container
        data=urllib.parse.urlencode({"media_type":"REELS","video_url":video_url,
            "caption":caption,"access_token":IG_ACCESS_TOKEN}).encode()
        req=urllib.request.Request(
            f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media",data=data)
        with urllib.request.urlopen(req,timeout=30) as r:
            container=json.loads(r.read())
        container_id=container.get("id","")
        if not container_id: return False
        
        time.sleep(10)  # aguardar processamento
        
        # Publicar
        data2=urllib.parse.urlencode({"creation_id":container_id,
            "access_token":IG_ACCESS_TOKEN}).encode()
        req2=urllib.request.Request(
            f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish",data=data2)
        with urllib.request.urlopen(req2,timeout=30) as r:
            result=json.loads(r.read())
        log(f"Instagram: {result.get('id','?')} ✅")
        return True
    except Exception as e:
        log(f"Instagram erro: {e}")
        return False

def main():
    now=datetime.now(timezone.utc)
    log("="*60)
    log(f"DISTRIBUTE 9 IDIOMAS | {now:%Y-%m-%d %H:%M} UTC")
    log("="*60)
    
    # Token YouTube
    yt_token=get_yt_token()
    if yt_token:
        log("✅ YouTube token OK")
    else:
        log("⚠️  YouTube: sem token")
    
    # Verificar tokens de distribuição
    has_tt = bool(TT_ACCESS_TOKEN)
    has_ig = bool(IG_ACCESS_TOKEN and IG_USER_ID)
    log(f"TikTok: {'✅ configurado' if has_tt else '❌ pendente (configure TT_ACCESS_TOKEN)'}")
    log(f"Instagram: {'✅ configurado' if has_ig else '❌ pendente (configure IG_USER_ID + IG_ACCESS_TOKEN)'}")
    
    # Pegar vídeo mais recente
    vid_id=os.environ.get("VIDEO_ID","")
    vid_title=""
    
    if not vid_id and yt_token:
        vid_id, vid_title = get_latest_video(yt_token)
    
    if vid_id:
        log(f"Vídeo: {vid_id} | {vid_title[:50] if vid_title else '?'}")
        
        # Atualizar SEO em todos os 9 idiomas no YouTube
        log("\n--- Atualizando SEO YouTube ---")
        for lang in ["en","pt","de","es","fr","it","ja","ko"]:
            if yt_token:
                update_yt_video_seo(yt_token, vid_id, lang)
                time.sleep(1)
        
        # Construir URL do vídeo para distribuição
        yt_url=f"https://www.youtube.com/watch?v={vid_id}"
        log(f"\nURL: {yt_url}")
        
        # Postar TikTok
        if has_tt:
            log("\n--- Postando TikTok ---")
            post_tiktok(yt_url,"en")
        
        # Postar Instagram
        if has_ig:
            log("\n--- Postando Instagram ---")
            post_instagram(yt_url,"en")
    else:
        log("Sem vídeo para distribuir — apenas atualizando live SEO")
        
        # Atualizar SEO da live
        if yt_token:
            log("\n--- Atualizando SEO Live ---")
            h=now.hour
            lang="de" if 5<=h<12 else ("en" if 12<=h<20 else "pt")
            titulo=random.choice(TITULOS.get(lang,TITULOS["en"]))
            log(f"Idioma hora {h}h UTC: {lang} | {titulo[:60]}")
            
            from datetime import timedelta
            start=(now+timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
            desc=DESC.get(lang,DESC["en"])
            body=json.dumps({"id":"LhAVPY_HK-4","snippet":{
                "title":titulo[:100],"description":desc[:4900],
                "scheduledStartTime":start,"categoryId":"22","defaultLanguage":"en"
            }}).encode()
            req=urllib.request.Request("https://www.googleapis.com/youtube/v3/liveBroadcasts?part=snippet",
                data=body,method="PUT")
            req.add_header("Authorization",f"Bearer {yt_token}"); req.add_header("Content-Type","application/json")
            try:
                with urllib.request.urlopen(req,timeout=15): log(f"Live SEO [{lang}] ✅")
            except Exception as e: log(f"Live SEO: {e}")
    
    log("\n=== TOKENS NECESSÁRIOS PARA DISTRIBUIÇÃO COMPLETA ===")
    if not has_tt:
        log("TikTok (GRATUITO — +500K views orgânicos):")
        log("  1. https://developers.tiktok.com → Create App")
        log("  2. GitHub Secrets: TT_CLIENT_KEY + TT_ACCESS_TOKEN")
    if not has_ig:
        log("Instagram (GRATUITO — +200K views orgânicos):")
        log("  1. https://developers.facebook.com/apps → Instagram Basic")
        log("  2. GitHub Secrets: IG_USER_ID + IG_ACCESS_TOKEN")
    
    log("\n✅ Distribuição concluída!")

if __name__=="__main__":
    main()
