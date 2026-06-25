import requests, os, sys, time

CID = os.environ["CLIENT_ID"]
CSC = os.environ["CLIENT_SECRET"]
RT  = os.environ["REFRESH_TOKEN"]
CANAL = os.environ["CANAL"].lower()

def get_at():
    r = requests.post("https://oauth2.googleapis.com/token",
        data={"client_id":CID,"client_secret":CSC,"refresh_token":RT,"grant_type":"refresh_token"},
        timeout=10)
    d = r.json()
    at = d.get("access_token")
    if not at:
        print(f"ERRO token: {d}"); sys.exit(1)
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
    "dbn": """Brown Noise 12 Hours - Black Screen | No Ads | All Night

Pure brown noise for deep sleep, ADHD focus and study.
12 uninterrupted hours. Battery-saving black screen.

BEST FOR: Deep Sleep | ADHD Focus | Study | Tinnitus | Stress Relief

LISTEN IN YOUR LANGUAGE:
EN: Brown noise 12 hours for deep sleep, ADHD focus and study
PT/BR: Ruido marrom 12 horas para sono profundo, foco TDAH e estudo
ES: Ruido marron 12 horas para dormir, enfoque TDAH y estudio
FR: Bruit brun 12 heures pour sommeil profond, TDAH et etude
DE: Braunes Rauschen 12 Stunden fur Tiefschlaf, ADHS und Lernen
IT: Rumore marrone 12 ore per sonno, ADHD e studio
NL: Bruin ruis 12 uur voor slaap, ADHD en studie
PL: Brazowy szum 12 godzin sen ADHD nauka
RU: Korichnevyy shum 12 chasov son SDVG ucheba
JP: Brown noise 12 jikan suimin ADHD shuchu benkyou
KR: Brown noise 12 sigan sunyeon ADHD jipjung gongbu
CN: Zongse zaosheng 12 xiaoshi shenmian ADHD zhuanzhu xuexi
TW: Zongse zaosheng 12 xiaoshi shenmian ADHD zhuanzhu xuexi
IN: Brown noise 12 ghante gehri neend ADHD focus padhai
BD: Brown noise 12 ghonta gabhir ghum ADHD focus porasona
ID/MY: Kebisingan coklat 12 jam tidur ADHD belajar
TH: Siang nam tan 12 chuamong non ADHD rianru
VN: Tieng on nau 12 gio ngu sau ADHD hoc
SA/AE: Dawsha bunni 12 saah nawm tarkiz dirasa
TR: Kahverengi gurultu 12 saat uyku ADHD calisma
SE/NO/DK: Brunt brus 12 timmar somn ADHD studier
GR: Kafe thoryvos 12 ores ypnos ADHD meleti
PT: Ruido castanho 12 horas sono TDAH estudo

#BrownNoise #DeepSleep #ADHDFocus #SleepSounds #BlackScreen #StudyMusic #12Hours #NoAds""",

    "adhd": """ADHD Focus Noise 10 Hours - Black Screen | No Ads

Brown noise calibrated for ADHD brains. Reduces mental hyperactivity,
boosts executive function and sustained attention.
10 uninterrupted hours. No visual distraction.

BEST FOR: ADHD Focus | Deep Work | Study | Remote Work | Executive Function

LISTEN IN YOUR LANGUAGE:
EN: ADHD focus brown noise 10 hours - deep work and study
PT/BR: Ruido marrom para foco TDAH 10 horas - trabalho e estudo
ES: Ruido marron enfoque TDAH 10 horas - trabajo y estudio
FR: Bruit brun focus TDAH 10 heures - travail et etude
DE: Braunes Rauschen ADHS Fokus 10 Stunden - Arbeit und Lernen
IT: Rumore marrone ADHD 10 ore - lavoro e studio
NL: Bruin ruis ADHD 10 uur - werk en studie
PL: Brazowy szum ADHD 10 godzin praca nauka
RU: Korichnevyy shum SDVG 10 chasov rabota ucheba
JP: ADHD focus brown noise 10 jikan shigoto benkyou
KR: ADHD jipjung brown noise 10 sigan ileul gongbu
CN: ADHD zhuanzhu zongse zaosheng 10 xiaoshi gongzuo xuexi
TW: ADHD zhuanzhu zongse zaosheng 10 xiaoshi gongzuo xuexi
IN: ADHD focus 10 ghante kaam aur padhai
BD: ADHD focus 10 ghonta kaj porasona
ID/MY: ADHD fokus 10 jam kerja dan belajar
TH: ADHD samathi 10 chuamong thamgan rianru
VN: ADHD tap trung 10 gio lam viec hoc tap
SA/AE: ADHD tarkiz 10 saah amal wa dirasa
TR: ADHD odak 10 saat is ve calisma
SE/NO/DK: ADHD fokus 10 timmar arbete studier
GR: ADHD estivasi 10 ores ergasia meleti
PT: TDAH foco 10 horas trabalho e estudo

#ADHDFocus #ADHD #BrownNoise #Concentration #DeepWork #StudyMusic #10Hours #BlackScreen #NoAds""",

    "bsn": """Baby Sleep White Noise 8 Hours - Black Screen | No Ads | Safe Volume

Gentle white noise for babies from newborn through toddler age.
Mimics womb sounds. Pediatrician-approved. 8 continuous hours.

BEST FOR: Newborn | Infant | Toddler | Colic | Bedtime | Naps

LISTEN IN YOUR LANGUAGE:
EN: Baby sleep white noise 8 hours - newborn infant and colic
PT/BR: Ruido branco para bebe 8 horas - recem-nascido e colica
ES: Ruido blanco para bebe 8 horas - recien nacido y colico
FR: Bruit blanc bebe 8 heures - nouveau-ne et coliques
DE: Baby Weisses Rauschen 8 Stunden - Neugeborenes und Koliken
IT: Rumore bianco bambino 8 ore - neonato e coliche
NL: Baby wit ruis 8 uur - pasgeboren en darmkrampjes
PL: Bialy szum niemowle 8 godzin noworodek i kolka
RU: Belyy shum malysh 8 chasov novorozhdennyy i koliki
JP: Akachan white noise 8 jikan shinsei-ji korikku
KR: Agi hwaiteu noiseu 8 sigan sinsengi suyeon
CN: Yinger bai zaosheng 8 xiaoshi xinsheng'er shui mian
TW: Yinger bai zaosheng 8 xiaoshi xinsheng'er shui mian
IN: Shishu ke liye safed shor 8 ghante navajaata aur kolik
BD: Sisur janya sada shobdo 8 ghonta navajata kolika
ID/MY: Kebisingan putih bayi 8 jam bayi baru lahir dan kolik
TH: Siang khao samrap tharo 8 chuamong taro raek kerd
VN: Tieng on trang cho be 8 gio tre so sinh
SA/AE: Dawsha baida lil-atfal 8 saah mawlud hadith
TR: Bebek beyaz gurultu 8 saat yenidogan ve kolik
SE/NO/DK: Baby vitt brus 8 timmar nyfodd och kolik
GR: Leykos thoryvos morou 8 ores neogynnito kai kolikos
PT: Ruido branco bebe 8 horas recem-nascido e colicas

#BabySleep #WhiteNoise #NewbornSleep #WombSounds #BabyCalm #BlackScreen #8Hours #NoAds""",

    "pink": """Pink Noise 10 Hours - Black Screen | No Ads | Science-Backed Sleep

Pink noise is scientifically proven to increase deep sleep and boost memory.
Northwestern University: pink noise improves memory by up to 35%.
10 continuous hours. Black screen.

BEST FOR: Deep Sleep | Memory Boost | Tinnitus Relief | Anxiety | Study

LISTEN IN YOUR LANGUAGE:
EN: Pink noise 10 hours for deep sleep, memory and tinnitus
PT/BR: Ruido rosa 10 horas - sono profundo, memoria e zumbido
ES: Ruido rosa 10 horas - sueno profundo, memoria y tinnitus
FR: Bruit rose 10 heures - sommeil profond, memoire et acouphenes
DE: Rosarauschen 10 Stunden - Tiefschlaf, Gedachtnis und Tinnitus
IT: Rumore rosa 10 ore - sonno profondo, memoria e tinnito
NL: Roze ruis 10 uur - slaap, geheugen en tinnitus
PL: Rozowy szum 10 godzin sen pamiec szumy uszne
RU: Rozovyy shum 10 chasov son pamyat' tinniteus
JP: Pink noise 10 jikan suimin kioku mimi nari
KR: Pink noise 10 sigan sunyeon gieok iimyeong
CN: Fenhong zaosheng 10 xiaoshi shenmian jiyi erming
TW: Fenhong zaosheng 10 xiaoshi shenmian jiyi erming
IN: Gulabi shor 10 ghante gehri neend smriti tinnitus
BD: Golapi shobdo 10 ghonta ghum smriti kaner awaj
ID/MY: Kebisingan merah muda 10 jam tidur memori tinnitus
TH: Siang chomphoo 10 chuamong non khwamjam huaue
VN: Tieng on hong 10 gio ngu sau tri nho u tai
SA/AE: Dawsha wardiyya 10 saah nawm dhakira tanin
TR: Pembe gurultu 10 saat derin uyku hafiza tinnitus
SE/NO/DK: Rosa brus 10 timmar djup somn minne tinnitus
GR: Roz thoryvos 10 ores ypnos mnimis emvoes
PT: Ruido rosa 10 horas sono profundo memoria zumbidos

#PinkNoise #DeepSleep #Tinnitus #MemoryBoost #SleepScience #BlackScreen #10Hours #NoAds""",

    "rain": """Rain Sounds 8 Hours - Black Screen | No Ads | Heavy Rain All Night

Pure heavy rain sounds for deep sleep, study and relaxation.
Continuous rain - no abrupt changes or thunder loops. 8 hours.

BEST FOR: Deep Sleep | Study | Stress Relief | Meditation | Focus

LISTEN IN YOUR LANGUAGE:
EN: Rain sounds 8 hours for deep sleep, study and relaxation
PT/BR: Sons de chuva 8 horas - sono profundo, estudo, relaxamento
ES: Sonidos de lluvia 8 horas - dormir, estudiar y relajarse
FR: Sons de pluie 8 heures - dormir, etudier et se detendre
DE: Regengerausche 8 Stunden - Schlafen, Lernen und Entspannen
IT: Suoni di pioggia 8 ore - sonno, studio e relax
NL: Regengeluiden 8 uur - slaap, studie en ontspanning
PL: Dzwieki deszczu 8 godzin sen nauka relaks
RU: Zvuki dozhdya 8 chasov son ucheba rasslableniye
JP: Ame no oto 8 jikan fukai nemuri benkyou rirakusu
KR: Bisori 8 sigan gipheun sunyeon gongbu hyugsik
CN: Yu sheng 8 xiaoshi shen du shui mian xuexi fang song
TW: Yu sheng 8 xiaoshi shen du shui mian xuexi fang song
IN: Barish ki awaz 8 ghante gehri neend padhai aur aaram
BD: Bristir shobdo 8 ghonta ghum padhna o bishramer
ID/MY: Suara hujan 8 jam tidur belajar dan relaksasi
TH: Siang fon 8 chuamong non rianru phon klai
VN: Tieng mua 8 gio ngu sau hoc tap thu gian
SA/AE: Aswat almatar 8 saah nawm dirasa wa raha
TR: Yagmur sesleri 8 saat uyku calisma ve rahatlama
SE/NO/DK: Regnsljud 8 timmar somn studie avslappning
GR: Ichos vrochis 8 ores ypnos meleti kai xekourasmeno
PT: Sons de chuva 8 horas sono profundo estudo relaxamento

#RainSounds #SleepSounds #HeavyRain #BlackScreen #DeepSleep #StudyMusic #8Hours #NoAds"""
}

# Aguardar até 5 min e aplicar quando vídeo aparecer
for attempt in range(1, 6):
    print(f"Attempt {attempt}/5 — canal: {CANAL}")
    at = get_at()
    
    # Buscar via playlist de uploads do canal
    ch_id = os.environ["CHANNEL_ID"]
    r = requests.get("https://www.googleapis.com/youtube/v3/channels",
        params={"part":"contentDetails,statistics","id":ch_id},
        headers={"Authorization":f"Bearer {at}"},timeout=10)
    
    if r.ok and r.json().get("items"):
        n = int(r.json()["items"][0]["statistics"].get("videoCount",0))
        if n > 0:
            pl = r.json()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            r2 = requests.get("https://www.googleapis.com/youtube/v3/playlistItems",
                params={"part":"snippet","playlistId":pl,"maxResults":1},
                headers={"Authorization":f"Bearer {at}"},timeout=10)
            items = r2.json().get("items",[])
            if items:
                vid = items[0]["snippet"]["resourceId"]["videoId"]
                t   = items[0]["snippet"].get("title","?")
                print(f"Video encontrado: {vid} | {t[:40]}")
                
                # Aplicar metadados completos
                titulo = TITULOS[CANAL]
                tags   = TAGS[CANAL]
                desc   = DESCS[CANAL]
                
                r3 = requests.put(
                    "https://www.googleapis.com/youtube/v3/videos?part=snippet,status",
                    headers={"Authorization":f"Bearer {at}","Content-Type":"application/json"},
                    json={"id":vid,
                          "snippet":{"title":titulo,"description":desc,"tags":tags,
                                     "categoryId":"22","defaultLanguage":"en","defaultAudioLanguage":"en"},
                          "status":{"selfDeclaredMadeForKids":False,"madeForKids":False,
                                    "license":"youtube","embeddable":True,"publicStatsViewable":True}},
                    timeout=30)
                
                if r3.ok:
                    print(f"METADATA OK: {titulo[:50]}")
                    sys.exit(0)
                else:
                    print(f"METADATA ERRO {r3.status_code}: {r3.text[:150]}")
                    sys.exit(1)
        
        print(f"  Canal tem {n} video(s) — aguardando...")
    
    if attempt < 5:
        time.sleep(60)

print("Video nao apareceu em 5 tentativas — YouTube ainda processando")
sys.exit(0)
