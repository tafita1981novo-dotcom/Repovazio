import requests, os, sys, time

CID   = os.environ["CLIENT_ID"]
CSC   = os.environ["CLIENT_SECRET"]
RT    = os.environ["REFRESH_TOKEN"]
CANAL = os.environ["CANAL"].lower()
VID   = os.environ.get("VIDEO_ID", "")   # ID confirmado nos logs do upload

def get_at():
    r = requests.post("https://oauth2.googleapis.com/token",
        data={"client_id":CID,"client_secret":CSC,"refresh_token":RT,"grant_type":"refresh_token"},
        timeout=10)
    d = r.json()
    at = d.get("access_token")
    if not at:
        print(f"ERRO token: {d}")
        sys.exit(1)
    return at

TITULOS = {
    "dbn":  "Brown Noise 12 Hours | Deep Sleep, ADHD Focus & Study Music | Black Screen No Ads",
    "adhd": "ADHD Focus Brown Noise 10 Hours | Concentration, Deep Work & Study | Black Screen No Ads",
    "bsn":  "Baby Sleep White Noise 8 Hours | Newborn, Infant & Toddler Sleep Sounds | Black Screen No Ads",
    "pink": "Pink Noise 10 Hours | Deep Sleep, Memory Boost & Tinnitus Relief | Black Screen No Ads",
    "rain": "Rain Sounds 8 Hours | Heavy Rain for Deep Sleep, Study & Relaxation | Black Screen No Ads",
}
TAGS = {
    "dbn":  ["brown noise","brown noise 12 hours","brown noise sleep","brown noise ADHD","ADHD focus","deep sleep sounds","sleep sounds","black screen","sleep aid","concentration music","study music","tinnitus relief","stress relief","insomnia","focus music","deep work","neurodivergent","noise for sleep","relax music","brown noise study"],
    "adhd": ["ADHD focus","ADHD","brown noise ADHD","ADHD music","focus music","concentration music","deep work","study music","neurodivergent","executive function","flow state","work music","focus 10 hours","black screen","productivity music","brain focus","ADHD relief","adhd sounds","adhd studying","adhd brown noise"],
    "bsn":  ["baby sleep","white noise baby","newborn sleep","infant sleep","baby sleep sounds","womb sounds","baby calm","colic baby","baby white noise","toddler sleep","baby sleep aid","newborn white noise","baby bedtime","baby nap","baby soothing sounds","black screen","8 hours","new parents","fussy baby","baby sleep through night"],
    "pink": ["pink noise","pink noise sleep","pink noise 10 hours","deep sleep","tinnitus relief","memory boost","sleep science","pink noise tinnitus","sleep better","slow wave sleep","anxiety relief","pure pink noise","tinnitus masking","pink noise benefits","black screen","sleep sounds","relaxation","stress relief","sleep aid","concentration"],
    "rain": ["rain sounds","rain sounds for sleeping","rain sounds 8 hours","heavy rain","rain sleep","rain study","rain relaxation","rain ASMR","rainstorm sounds","rain white noise","sleeping rain","rain sounds black screen","rain night","thunderstorm sleep","rain focus","8 hours rain","cozy rain","rain meditation","ambient rain","deep sleep rain"],
}
DESCS = {
    "dbn":  "Brown Noise 12 Hours | Black Screen | No Ads\n\nPure brown noise for deep sleep, ADHD focus and study. 12 uninterrupted hours.\n\nBEST FOR: Deep Sleep | ADHD Focus | Study | Tinnitus | Stress Relief\n\nEN: Brown noise 12 hours for deep sleep, ADHD focus and study\nPT/BR: Ruido marrom 12 horas para sono profundo, foco TDAH e estudo\nES: Ruido marron 12 horas para dormir, enfoque TDAH y estudio\nFR: Bruit brun 12 heures pour sommeil profond, TDAH et etude\nDE: Braunes Rauschen 12 Stunden Tiefschlaf ADHS Lernen\nIT: Rumore marrone 12 ore sonno ADHD studio\nNL: Bruin ruis 12 uur slaap ADHD studie\nPL: Brazowy szum 12 godzin sen ADHD nauka\nRU: Korichnevyy shum 12 chasov son SDVG ucheba\nJP: Brown noise 12 jikan suimin ADHD benkyou\nKR: Brown noise 12 sigan sunyeon ADHD gongbu\nCN: Zongse zaosheng 12 xiaoshi shenmian ADHD xuexi\nIN: Brown noise 12 ghante neend ADHD padhai\nBD: Brown noise 12 ghonta ghum ADHD porasona\nID/MY: Kebisingan coklat 12 jam tidur ADHD belajar\nTH: Siang nam tan 12 chuamong non ADHD rianru\nVN: Tieng on nau 12 gio ngu sau ADHD hoc\nAR: Dawsha bunni 12 saah nawm tarkiz dirasa\nTR: Kahverengi gurultu 12 saat uyku ADHD calisma\nSE/NO/DK: Brunt brus 12 timmar somn ADHD studier\nGR: Kafe thoryvos 12 ores ypnos ADHD meleti\nPT: Ruido castanho 12 horas sono TDAH estudo\n\n#BrownNoise #DeepSleep #ADHDFocus #SleepSounds #BlackScreen #StudyMusic #12Hours #NoAds",
    "adhd": "ADHD Focus Noise 10 Hours | Black Screen | No Ads\n\nBrown noise calibrated for ADHD brains. 10 uninterrupted hours.\n\nBEST FOR: ADHD Focus | Deep Work | Study | Remote Work | Executive Function\n\nEN: ADHD focus brown noise 10 hours deep work and study\nPT/BR: Ruido marrom TDAH foco 10 horas trabalho e estudo\nES: Ruido marron TDAH enfoque 10 horas trabajo y estudio\nFR: Bruit brun TDAH focus 10 heures travail et etude\nDE: Braunes Rauschen ADHS 10 Stunden Arbeit und Lernen\nIT: Rumore marrone ADHD 10 ore lavoro e studio\nNL: Bruin ruis ADHD 10 uur werk en studie\nPL: Brazowy szum ADHD 10 godzin praca nauka\nRU: Korichnevyy shum SDVG 10 chasov rabota ucheba\nJP: ADHD focus brown noise 10 jikan shigoto benkyou\nKR: ADHD jipjung brown noise 10 sigan ileul gongbu\nCN: ADHD zhuanzhu zongse zaosheng 10 xiaoshi gongzuo xuexi\nIN: ADHD focus 10 ghante kaam padhai\nBD: ADHD focus 10 ghonta kaj porasona\nID/MY: ADHD fokus 10 jam kerja dan belajar\nTH: ADHD samathi 10 chuamong thamgan rianru\nVN: ADHD tap trung 10 gio lam viec hoc tap\nAR: ADHD tarkiz 10 saah amal dirasa\nTR: ADHD odak 10 saat is ve calisma\nSE/NO/DK: ADHD fokus 10 timmar arbete studier\nGR: ADHD estivasi 10 ores ergasia meleti\nPT: TDAH foco 10 horas trabalho e estudo\n\n#ADHDFocus #ADHD #BrownNoise #Concentration #DeepWork #StudyMusic #10Hours #BlackScreen #NoAds",
    "bsn":  "Baby Sleep White Noise 8 Hours | Black Screen | No Ads\n\nGentle white noise for babies from newborn through toddler. 8 hours.\n\nBEST FOR: Newborn | Infant | Toddler | Colic | Bedtime | Naps\n\nEN: Baby sleep white noise 8 hours newborn infant and colic\nPT/BR: Ruido branco bebe 8 horas recem-nascido e colica\nES: Ruido blanco bebe 8 horas recien nacido y colico\nFR: Bruit blanc bebe 8 heures nouveau-ne et coliques\nDE: Baby Weisses Rauschen 8 Stunden Neugeborenes und Koliken\nIT: Rumore bianco bambino 8 ore neonato e coliche\nNL: Baby wit ruis 8 uur pasgeboren en darmkrampjes\nPL: Bialy szum niemowle 8 godzin noworodek i kolka\nRU: Belyy shum malysh 8 chasov novorozhdennyy i koliki\nJP: Akachan white noise 8 jikan shinsei-ji korikku\nKR: Agi hwaiteu noiseu 8 sigan sinsengi suyeon\nCN: Yinger bai zaosheng 8 xiaoshi xinsheng-er shuimian\nIN: Shishu ke liye safed shor 8 ghante navajaata aur kolik\nBD: Sisur janya sada shobdo 8 ghonta navajata kolika\nID/MY: Kebisingan putih bayi 8 jam bayi baru lahir dan kolik\nTH: Siang khao samrap tharo 8 chuamong taro raek kerd\nVN: Tieng on trang cho be 8 gio tre so sinh\nAR: Dawsha baida lil-atfal 8 saah mawlud hadith\nTR: Bebek beyaz gurultu 8 saat yenidogan ve kolik\nSE/NO/DK: Baby vitt brus 8 timmar nyfodd och kolik\nGR: Leykos thoryvos morou 8 ores neogynnito kai kolikos\nPT: Ruido branco bebe 8 horas recem-nascido e colicas\n\n#BabySleep #WhiteNoise #NewbornSleep #WombSounds #BabyCalm #BlackScreen #8Hours #NoAds",
    "pink": "Pink Noise 10 Hours | Black Screen | No Ads | Science-Backed\n\nPink noise proven to increase deep sleep and boost memory by up to 35% (Northwestern University). 10 hours.\n\nBEST FOR: Deep Sleep | Memory Boost | Tinnitus Relief | Anxiety | Study\n\nEN: Pink noise 10 hours for deep sleep, memory and tinnitus\nPT/BR: Ruido rosa 10 horas sono profundo, memoria e zumbido\nES: Ruido rosa 10 horas sueno profundo, memoria y tinnitus\nFR: Bruit rose 10 heures sommeil profond, memoire et acouphenes\nDE: Rosarauschen 10 Stunden Tiefschlaf, Gedachtnis und Tinnitus\nIT: Rumore rosa 10 ore sonno profondo, memoria e tinnito\nNL: Roze ruis 10 uur slaap, geheugen en tinnitus\nPL: Rozowy szum 10 godzin sen pamiec szumy uszne\nRU: Rozovyy shum 10 chasov son pamyat tinniteus\nJP: Pink noise 10 jikan suimin kioku mimi nari\nKR: Pink noise 10 sigan sunyeon gieok iimyeong\nCN: Fenhong zaosheng 10 xiaoshi shenmian jiyi erming\nIN: Gulabi shor 10 ghante gehri neend smriti tinnitus\nBD: Golapi shobdo 10 ghonta ghum smriti kaner awaj\nID/MY: Kebisingan merah muda 10 jam tidur memori tinnitus\nTH: Siang chomphoo 10 chuamong non khwamjam huaue\nVN: Tieng on hong 10 gio ngu sau tri nho u tai\nAR: Dawsha wardiyya 10 saah nawm dhakira tanin\nTR: Pembe gurultu 10 saat derin uyku hafiza tinnitus\nSE/NO/DK: Rosa brus 10 timmar djup somn minne tinnitus\nGR: Roz thoryvos 10 ores ypnos mnimis emvoes\nPT: Ruido rosa 10 horas sono profundo memoria zumbidos\n\n#PinkNoise #DeepSleep #Tinnitus #MemoryBoost #SleepScience #BlackScreen #10Hours #NoAds",
    "rain": "Rain Sounds 8 Hours | Black Screen | No Ads | Heavy Rain All Night\n\nPure heavy rain for deep sleep, study and relaxation. Continuous rain. 8 hours.\n\nBEST FOR: Deep Sleep | Study | Stress Relief | Meditation | Focus\n\nEN: Rain sounds 8 hours for deep sleep, study and relaxation\nPT/BR: Sons de chuva 8 horas sono profundo, estudo, relaxamento\nES: Sonidos de lluvia 8 horas dormir, estudiar y relajarse\nFR: Sons de pluie 8 heures dormir, etudier et se detendre\nDE: Regengerausche 8 Stunden Schlafen, Lernen und Entspannen\nIT: Suoni di pioggia 8 ore sonno, studio e relax\nNL: Regengeluiden 8 uur slaap, studie en ontspanning\nPL: Dzwieki deszczu 8 godzin sen nauka relaks\nRU: Zvuki dozhdya 8 chasov son ucheba rasslableniye\nJP: Ame no oto 8 jikan fukai nemuri benkyou rirakusu\nKR: Bisori 8 sigan gipheun sunyeon gongbu hyugsik\nCN: Yu sheng 8 xiaoshi shenmian xuexi fangsong\nIN: Barish ki awaz 8 ghante gehri neend padhai aur aaram\nBD: Bristir shobdo 8 ghonta ghum padha o bishramer\nID/MY: Suara hujan 8 jam tidur belajar dan relaksasi\nTH: Siang fon 8 chuamong non rianru phon klai\nVN: Tieng mua 8 gio ngu sau hoc tap thu gian\nAR: Aswat almatar 8 saah nawm dirasa wa raha\nTR: Yagmur sesleri 8 saat uyku calisma ve rahatlama\nSE/NO/DK: Regnsljud 8 timmar somn studie avslappning\nGR: Ichos vrochis 8 ores ypnos meleti kai xekourasmeno\nPT: Sons de chuva 8 horas sono profundo estudo relaxamento\n\n#RainSounds #SleepSounds #HeavyRain #BlackScreen #DeepSleep #StudyMusic #8Hours #NoAds",
}

def apply_metadata(at, vid):
    titulo = TITULOS[CANAL]
    tags   = TAGS[CANAL]
    desc   = DESCS[CANAL]
    r = requests.put(
        "https://www.googleapis.com/youtube/v3/videos?part=snippet,status",
        headers={"Authorization": f"Bearer {at}", "Content-Type": "application/json"},
        json={"id": vid,
              "snippet": {"title": titulo, "description": desc, "tags": tags,
                          "categoryId": "22", "defaultLanguage": "en", "defaultAudioLanguage": "en"},
              "status": {"selfDeclaredMadeForKids": False, "madeForKids": False,
                         "license": "youtube", "embeddable": True, "publicStatsViewable": True}},
        timeout=30)
    return r.ok, r.status_code, r.text[:200] if not r.ok else ""

CH_ID = os.environ["CHANNEL_ID"]

print(f"Canal: {CANAL} | Video ID hint: {VID or 'N/A'}")

for attempt in range(1, 9):
    print(f"Attempt {attempt}/8")
    at = get_at()

    # Estrategia 1: usar o VIDEO_ID direto se fornecido
    if VID:
        r = requests.get("https://www.googleapis.com/youtube/v3/videos",
            params={"part": "snippet,status", "id": VID},
            headers={"Authorization": f"Bearer {at}"}, timeout=10)
        if r.ok and r.json().get("items"):
            vid = VID
            title_now = r.json()["items"][0]["snippet"].get("title","?")[:30]
            print(f"  Video encontrado por ID: {vid} | {title_now}")
            ok, code, err = apply_metadata(at, vid)
            if ok:
                print(f"  METADATA OK: {TITULOS[CANAL][:50]}")
                sys.exit(0)
            else:
                print(f"  METADATA ERRO {code}: {err}")
                sys.exit(1)
        else:
            print(f"  Video {VID} nao acessivel ainda (processing) — aguardando...")

    # Estrategia 2: buscar via playlist de uploads
    r2 = requests.get("https://www.googleapis.com/youtube/v3/channels",
        params={"part": "contentDetails,statistics", "id": CH_ID},
        headers={"Authorization": f"Bearer {at}"}, timeout=10)
    if r2.ok and r2.json().get("items"):
        n = int(r2.json()["items"][0]["statistics"].get("videoCount", 0))
        if n > 0:
            pl = r2.json()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            r3 = requests.get("https://www.googleapis.com/youtube/v3/playlistItems",
                params={"part": "snippet", "playlistId": pl, "maxResults": 1},
                headers={"Authorization": f"Bearer {at}"}, timeout=10)
            items = r3.json().get("items", [])
            if items:
                vid = items[0]["snippet"]["resourceId"]["videoId"]
                print(f"  Video encontrado via playlist: {vid}")
                ok, code, err = apply_metadata(at, vid)
                if ok:
                    print(f"  METADATA OK: {TITULOS[CANAL][:50]}")
                    sys.exit(0)
                else:
                    print(f"  METADATA ERRO {code}: {err}")
                    sys.exit(1)
        print(f"  Canal com {n} video(s) mas nenhum acessivel")

    if attempt < 8:
        time.sleep(60)

print(f"Video nao ficou disponivel em 8 tentativas (8 min). Roda de novo em ~10min.")
sys.exit(0)
