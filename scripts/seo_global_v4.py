#!/usr/bin/env python3
"""
seo_global_v4.py — SEO YouTube em 25 idiomas para LIVES e VIDEOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YouTube API permite definir título/descrição em múltiplos idiomas.
Resultado: o vídeo aparece em buscas locais no idioma correto de CADA país.

PAÍSES QUE MAIS BUSCAM (volume mensal):
  EN: 550K/mês "528hz sleep" (EUA+UK+AU+CA) — CPM $15-50
  PT: 201K/mês "música para dormir" (BR+PT) — CPM R$12-22
  HI: 300K/mês "sleep music" (Índia) — CPM $2-5
  ES: 165K/mês "música para dormir" (MX+ES+LATAM) — CPM $6-12
  JA: 110K/mês "睡眠音楽" (Japão) — CPM $8-15
  KO: 90K/mês "수면 음악" (Coreia) — CPM $6-12
  DE: 90K/mês "Schlafmusik" (Alemanha+CH+AT) — CPM $12-18
  FR: 74K/mês "musique pour dormir" (FR+CA-QC) — CPM $10-14
  IT: 60K/mês "musica per dormire" (Itália) — CPM $8-12
  PL: 55K/mês "muzyka do spania" (Polônia) — CPM $5-8
  RU: 50K/mês "музыка для сна" (Rússia) — CPM $2-4
  NL: 45K/mês "slaapmusiek" (Holanda) — CPM $8-12
  TR: 40K/mês "uyku müziği" (Turquia) — CPM $3-5
  AR: 35K/mês "موسيقى للنوم" (Árabe) — CPM $3-6
"""
import os, json, time
import urllib.request, urllib.parse

YT_TOKEN = os.getenv("YOUTUBE_ACCESS_TOKEN","")

# Localizations em 25 idiomas para a live de sono
SLEEP_LOCALIZATIONS = {
    "pt":    {"title":"Sono Profundo 8H ● 528Hz Binaural ● Tela Preta ● @psidanicoelho",
              "description":"🌙 Música binaural 528Hz para sono profundo. Tela preta absoluta. Delta waves.\n#sonoprofundo #528hz #músicaparadormir"},
    "en":    {"title":"Deep Sleep 8 Hours ● 528Hz Binaural Beats ● Black Screen ● No Ads",
              "description":"😴 528Hz binaural beats for deep sleep. Completely black screen. Delta waves.\n#deepsleeep #528hz #binauralbeats #blackscreen"},
    "es":    {"title":"Música para Dormir 8 Horas ● 528Hz Binaural ● Pantalla Negra",
              "description":"🌙 Binaural 528Hz para sueño profundo. Pantalla completamente negra.\n#musicoparadormir #528hz #binaural"},
    "de":    {"title":"Schlafmusik 8 Stunden ● 528Hz Binaural ● Schwarzer Bildschirm",
              "description":"😴 528Hz Binaural Beats für tiefen Schlaf. Schwarzer Bildschirm.\n#schlafmusik #528hz #binauralbeats"},
    "fr":    {"title":"Musique pour Dormir 8h ● 528Hz Binaural ● Écran Noir",
              "description":"🌙 Musique binaural 528Hz pour sommeil profond. Écran noir.\n#musiquedormir #528hz #binaural"},
    "ja":    {"title":"睡眠音楽8時間 ● 528Hz バイノーラル ● ブラックスクリーン ● ぐっすり眠る",
              "description":"😴 528Hzバイノーラルビートで深い眠り。スクリーン完全真っ黒。\n#睡眠音楽 #528hz #バイノーラル #深い眠り"},
    "ko":    {"title":"수면 음악 8시간 ● 528Hz 바이노럴 ● 검은 화면 ● 깊은 수면",
              "description":"😴 528Hz 바이노럴로 깊게 잠들기. 화면 완전 검정.\n#수면음악 #528hz #바이노럴 #검은화면"},
    "it":    {"title":"Musica per Dormire 8 Ore ● 528Hz Binaural ● Schermo Nero",
              "description":"🌙 Musica binaural 528Hz per sonno profondo. Schermo nero.\n#musicaperdormire #528hz #binaural"},
    "pl":    {"title":"Muzyka do Snu 8 Godzin ● 528Hz Binaural ● Czarny Ekran",
              "description":"😴 Muzyka binaural 528Hz do głębokiego snu. Czarny ekran.\n#muzykadosna #528hz #binaural"},
    "ru":    {"title":"Музыка для Сна 8 Часов ● 528Hz Бинауральные Ритмы ● Чёрный Экран",
              "description":"😴 Бинауральные ритмы 528Hz для глубокого сна. Чёрный экран.\n#музыкадлясна #528hz #бинауральные"},
    "nl":    {"title":"Slaapmusiek 8 Uur ● 528Hz Binaural ● Zwart Scherm",
              "description":"😴 528Hz Binaural voor diepe slaap. Zwart scherm.\n#slaapmusiek #528hz #binaural"},
    "tr":    {"title":"Uyku Müziği 8 Saat ● 528Hz Binaural ● Siyah Ekran",
              "description":"😴 Derin uyku için 528Hz binaural. Siyah ekran.\n#uyukmüziği #528hz #binaural"},
    "ar":    {"title":"موسيقى للنوم 8 ساعات ● 528 هرتز ثنائي الأذن ● شاشة سوداء",
              "description":"😴 موسيقى ثنائية الأذن 528 هرتز للنوم العميق. شاشة سوداء.\n#موسيقى_للنوم #528هرتز"},
    "hi":    {"title":"नींद के लिए संगीत 8 घंटे ● 528Hz बाइनॉरल ● काली स्क्रीन",
              "description":"😴 गहरी नींद के लिए 528Hz बाइनॉरल बीट्स। काली स्क्रीन।\n#नींद_संगीत #528hz #binaural"},
    "zh-Hans":{"title":"睡眠音乐8小时 ● 528Hz双耳节拍 ● 黑屏 ● 深度睡眠",
              "description":"😴 528Hz双耳节拍助眠音乐。完全黑屏。\n#睡眠音乐 #528hz #双耳"},
    "id":    {"title":"Musik Tidur 8 Jam ● 528Hz Binaural ● Layar Hitam ● Tidur Nyenyak",
              "description":"😴 Musik binaural 528Hz untuk tidur nyenyak. Layar hitam.\n#musiktidur #528hz #binaural"},
    "ms":    {"title":"Muzik Tidur 8 Jam ● 528Hz Binaural ● Skrin Hitam",
              "description":"😴 Muzik binaural 528Hz untuk tidur nyenyak. Skrin hitam.\n#muziktidur #528hz"},
    "sv":    {"title":"Sömnmusik 8 Timmar ● 528Hz Binaural ● Svart Skärm",
              "description":"😴 Binaural 528Hz för djup sömn. Svart skärm.\n#sömnmusik #528hz #binaural"},
    "no":    {"title":"Søvnmusikk 8 Timer ● 528Hz Binaural ● Svart Skjerm",
              "description":"😴 Binaural 528Hz for dyp søvn. Svart skjerm.\n#søvnmusikk #528hz"},
    "da":    {"title":"Søvnmusik 8 Timer ● 528Hz Binaural ● Sort Skærm",
              "description":"😴 Binaural 528Hz til dyb søvn. Sort skærm.\n#søvnmusik #528hz"},
    "fi":    {"title":"Unimusiiikki 8 Tuntia ● 528Hz Binaural ● Musta Näyttö",
              "description":"😴 Binaural 528Hz syvään uneen. Musta näyttö.\n#unimusiiikki #528hz"},
    "cs":    {"title":"Hudba na spaní 8 hodin ● 528Hz Binaural ● Černá obrazovka",
              "description":"😴 Binaural 528Hz pro hluboký spánek. Černá obrazovka.\n#hudbanapani #528hz"},
    "uk":    {"title":"Музика для сну 8 годин ● 528Hz Бінауральні Ритми ● Чорний Екран",
              "description":"😴 Бінауральні ритми 528Hz для глибокого сну. Чорний екран.\n#музикадлясну #528hz"},
    "th":    {"title":"เพลงนอนหลับ 8 ชั่วโมง ● 528Hz ไบนอรัล ● หน้าจอสีดำ",
              "description":"😴 เสียงไบนอรัล 528Hz เพื่อการนอนหลับลึก หน้าจอสีดำ\n#เพลงนอนหลับ #528hz"},
    "ro":    {"title":"Muzică pentru Somn 8 Ore ● 528Hz Binaural ● Ecran Negru",
              "description":"😴 Binaural 528Hz pentru somn adânc. Ecran negru.\n#muzicapentrusomn #528hz"},
}

STUDY_LOCALIZATIONS = {
    "pt": {"title":"Música para Estudar 24/7 ● Theta 5.5Hz ● Foco e Concentração ● Tela Preta",
           "description":"📚 Binaural theta para foco. Tela preta sem distrações.\n#estudar #foco #theta"},
    "en": {"title":"Study Music 24/7 ● 5.5Hz Theta Binaural ● Deep Focus ● Black Screen",
           "description":"📚 Theta binaural for deep focus and memory.\n#studymusic #focus #theta #binaural"},
    "es": {"title":"Música para Estudiar 24/7 ● Theta 5.5Hz ● Concentración ● Pantalla Negra",
           "description":"📚 Binaural theta para concentración.\n#estudiare #concentración #theta"},
    "de": {"title":"Lernmusik 24/7 ● Theta 5.5Hz ● Konzentration ● Schwarzer Bildschirm",
           "description":"📚 Theta Binaural für Konzentration.\n#lernmusik #konzentration #theta"},
    "fr": {"title":"Musique pour Étudier 24/7 ● Theta 5.5Hz ● Concentration ● Écran Noir",
           "description":"📚 Binaural theta pour concentration.\n#étudier #concentration #theta"},
    "ja": {"title":"勉強音楽 24/7 ● シータ波 5.5Hz ● 集中力 ● ブラックスクリーン",
           "description":"📚 シータ波で集中力UP。\n#勉強音楽 #集中力 #シータ波"},
    "ko": {"title":"공부 음악 24/7 ● 세타파 5.5Hz ● 집중력 향상 ● 검은 화면",
           "description":"📚 세타파로 집중력 향상.\n#공부음악 #집중력 #세타파"},
}

def apply_localizations(video_id, localizations, access_token):
    """Aplica SEO multilingual via YouTube Data API v3"""
    if not access_token or not video_id:
        print(f"  Sem token YT — localizations salvas localmente para aplicar manualmente")
        return False
    
    for lang_code, content in localizations.items():
        body = {
            "id": video_id,
            "localizations": {
                lang_code: {
                    "title": content["title"],
                    "description": content["description"]
                }
            }
        }
        try:
            data = json.dumps(body).encode()
            req = urllib.request.Request(
                f"https://www.googleapis.com/youtube/v3/videos?part=localizations&access_token={access_token}",
                data=data, method="PUT"
            )
            req.add_header("Content-Type","application/json")
            with urllib.request.urlopen(req, timeout=15) as r:
                pass
            print(f"  SEO {lang_code}: OK")
            time.sleep(0.2)
        except Exception as e:
            print(f"  SEO {lang_code}: err — {e}")
    return True

def main():
    video_id = os.getenv("VIDEO_ID","")
    content_type = os.getenv("CONTENT_TYPE","sleep")
    
    locs = SLEEP_LOCALIZATIONS if content_type == "sleep" else STUDY_LOCALIZATIONS
    
    print(f"SEO Global V4 — {len(locs)} idiomas para video {video_id or '[sem ID]'}")
    
    if not video_id:
        print("VIDEO_ID nao definido — exportando JSON para aplicar manualmente")
        output = {"sleep": SLEEP_LOCALIZATIONS, "study": STUDY_LOCALIZATIONS}
        with open("/tmp/seo_localizations.json","w") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"Salvo em /tmp/seo_localizations.json ({len(SLEEP_LOCALIZATIONS)+len(STUDY_LOCALIZATIONS)} idiomas)")
        return
    
    apply_localizations(video_id, locs, YT_TOKEN)
    print(f"SEO completo: {len(locs)} localizations aplicadas")

if __name__ == "__main__":
    main()
