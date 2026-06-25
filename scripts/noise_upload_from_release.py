import requests, os, sys, time, subprocess

CLIENT_ID     = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
RT            = os.environ["REFRESH_TOKEN"]
CANAL         = os.environ["CANAL"]
CHANNEL_ID    = os.environ["CHANNEL_ID"]
TITULO        = TITULOS.get(CANAL, os.environ.get("TITULO", CANAL))
TAGS          = TAGS_MAP.get(CANAL, [t.strip() for t in os.environ.get("TAGS","").split(",") if t.strip()])
GH_TOKEN      = os.environ["GH_TOKEN"]
REPO          = os.environ["REPO"]
ASSET_NAME    = os.environ["ASSET_NAME"]
SB_URL        = os.environ.get("SUPABASE_URL","")
SB_KEY        = os.environ.get("SUPABASE_KEY","")

TITULOS = {
    "dbn": "Brown Noise 12 Hours | Deep Sleep, ADHD Focus & Study Music | Black Screen No Ads",
    "adhd": "ADHD Focus Brown Noise 10 Hours | Concentration, Deep Work & Study | Black Screen No Ads",
    "wnv": "White Noise 8 Hours | Deep Sleep, Baby Sleep & Tinnitus Masking | Black Screen No Ads",
    "bsn": "Baby Sleep White Noise 8 Hours | Newborn, Infant & Toddler Sleep Sounds | Black Screen No Ads",
    "pink": "Pink Noise 10 Hours | Deep Sleep, Memory Boost & Tinnitus Relief | Black Screen No Ads",
    "tinnitus": "Tinnitus Relief 8 Hours | Pink & White Noise Masking for Ringing Ears | Black Screen No Ads",
    "rain": "Rain Sounds 8 Hours | Heavy Rain for Deep Sleep, Study & Relaxation | Black Screen No Ads",
}

TAGS_MAP = {
    "dbn": ["brown noise", "brown noise 12 hours", "brown noise sleep", "brown noise ADHD", "brown noise study", "deep sleep sounds", "ADHD focus music", "focus sounds", "study music", "sleep sounds", "black screen", "sleep aid", "white noise sleep", "tinnitus relief", "stress relief", "relaxation music", "deep focus", "concentration music", "sleep fast", "insomnia relief"],
    "adhd": ["ADHD focus", "ADHD", "brown noise ADHD", "ADHD music", "focus music", "concentration music", "deep work", "study music", "ADHD brown noise", "neurodivergent", "executive function", "flow state", "work music", "adhd sounds", "focus 10 hours", "black screen", "productivity music", "study sounds", "brain focus", "adhd relief"],
    "wnv": ["white noise", "white noise 8 hours", "white noise sleep", "white noise baby", "baby sleep", "sleep sounds", "tinnitus masking", "tinnitus relief", "deep sleep", "insomnia", "black screen", "sleep aid", "newborn sleep", "pure white noise", "sleep fast", "sleep white noise", "relaxing sounds", "ambient noise", "sleep music", "noise for sleep"],
    "bsn": ["baby sleep", "white noise baby", "newborn sleep", "infant sleep", "baby sleep sounds", "womb sounds", "baby calm", "colic baby", "baby white noise", "toddler sleep", "baby sleep aid", "newborn white noise", "baby bedtime", "baby nap", "baby soothing sounds", "black screen", "8 hours", "new parents", "fussy baby", "baby sleep through night"],
    "pink": ["pink noise", "pink noise sleep", "pink noise 10 hours", "deep sleep", "tinnitus relief", "memory boost", "sleep science", "pink noise tinnitus", "sleep better", "slow wave sleep", "anxiety relief", "pure pink noise", "tinnitus masking", "pink noise benefits", "black screen", "sleep sounds", "relaxation", "stress relief", "sleep aid", "concentration"],
    "tinnitus": ["tinnitus", "tinnitus relief", "tinnitus masking", "ringing ears", "ear ringing", "tinnitus sounds", "pink noise tinnitus", "white noise tinnitus", "tinnitus help", "tinnitus therapy", "tinnitus sleep", "tinnitus treatment", "ear noise", "tinnitus habituation", "black screen", "8 hours", "ringing in ears", "tinnitus noise", "hearing noise", "hyperacusis"],
    "rain": ["rain sounds", "rain for sleep", "heavy rain", "rain sounds sleep", "rain sounds 8 hours", "rainy night sleep", "sleep rain", "study rain", "rain ASMR", "relaxing rain", "rain sounds relaxation", "black screen rain", "rain noise", "ambient rain", "deep sleep rain", "anxiety relief rain", "stress relief sounds", "nature sounds sleep", "rain sleep sounds", "rain white noise"],
}

DESCRICOES = {
    "dbn": r"""🟫 BROWN NOISE 12 HOURS — Black Screen | No Ads | Looped

Pure brown noise for deep sleep, ADHD focus, studying, and stress relief.
12 uninterrupted hours. Black screen to save your battery.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ BEST FOR:
• Deep Sleep & Insomnia Relief
• ADHD Focus & Concentration
• Study & Deep Work Sessions
• Tinnitus Masking
• Stress & Anxiety Relief
• Baby Sleep
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Headphones recommended for best effect
⚫ Black screen — screen stays dark all night
🔊 Set volume to a comfortable level
⏰ 12 hours — sleep all night without interruption
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌍 AVAILABLE IN YOUR LANGUAGE:
🇺🇸 Brown noise 12 hours for deep sleep, ADHD focus and study
🇬🇧 Brown noise 12 hours for deep sleep, ADHD focus and study
🇧🇷 🇵🇹 Ruído marrom 12 horas para sono profundo, foco TDAH e estudo
🇪🇸 🇲🇽 🇦🇷 Ruido marrón 12 horas para dormir profundo, enfoque TDAH y estudio
🇫🇷 🇨🇦 Bruit brun 12 heures pour sommeil profond, focus TDAH et étude
🇩🇪 🇦🇹 🇨🇭 Braunes Rauschen 12 Stunden für Tiefschlaf, ADHS-Fokus und Lernen
🇮🇹 Rumore marrone 12 ore per sonno profondo, focus ADHD e studio
🇳🇱 Bruin ruis 12 uur voor diepe slaap, ADHD-focus en studie
🇵🇱 Brązowy szum 12 godzin dla głębokiego snu, skupienia ADHD i nauki
🇷🇺 Коричневый шум 12 часов для глубокого сна, концентрации и учёбы
🇯🇵 ブラウンノイズ 12時間 — 深い眠り・ADHD集中・勉強用
🇰🇷 브라운 노이즈 12시간 — 깊은 수면, ADHD 집중, 공부
🇨🇳 棕色噪音 12小时 — 深度睡眠、ADHD专注、学习
🇹🇼 棕色噪音 12小時 — 深度睡眠、ADHD專注、學習
🇮🇳 ब्राउन नॉइज़ 12 घंटे — गहरी नींद, ADHD फोकस, पढ़ाई
🇧🇩 ব্রাউন নয়েজ ১২ ঘন্টা — গভীর ঘুম, ADHD ফোকাস, পড়াশোনা
🇮🇩 🇲🇾 Kebisingan coklat 12 jam untuk tidur nyenyak, fokus ADHD dan belajar
🇹🇭 เสียงน้ำตาล 12 ชั่วโมง สำหรับการนอนหลับลึก สมาธิ ADHD และการเรียน
🇻🇳 Tiếng ồn nâu 12 giờ cho giấc ngủ sâu, tập trung ADHD và học tập
🇸🇦 🇦🇪 ضجيج بني 12 ساعة للنوم العميق والتركيز ودراسة
🇹🇷 Kahverengi gürültü 12 saat derin uyku, ADHD odağı ve çalışma için
🇮🇱 רעש חום 12 שעות לשינה עמוקה, מיקוד ADHD ולימודים
🇬🇷 Καφέ θόρυβος 12 ώρες για βαθύ ύπνο, εστίαση ADHD και μελέτη
🇸🇪 🇳🇴 🇩🇰 Brunt brus 12 timmar för djup sömn, ADHD-fokus och studier
🇵🇹 Ruído castanho 12 horas para sono profundo, foco TDAH e estudo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#BrownNoise #DeepSleep #ADHDFocus #SleepSounds #BlackScreen #StudyMusic
#WhiteNoise #FocusMusic #Insomnia #SleepAid #12Hours #Concentration
#TinnitusRelief #StressRelief #RelaxingSound #DeepWork
""",
    "adhd": r"""🧠 ADHD FOCUS NOISE 10 HOURS — Black Screen | No Ads

Calibrated brown noise specifically for ADHD brains.
Reduces mental hyperactivity, boosts executive function and sustained attention.
10 uninterrupted hours. Black screen saves battery.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ BEST FOR:
• ADHD Focus & Concentration
• Deep Work & Productivity
• Study Sessions & Homework
• Remote Work
• Anxiety & Restlessness Relief
• Executive Function Support
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Best with headphones or earbuds
⚫ Black screen — no visual distraction
🔊 Medium volume for best focus effect
⏰ 10 hours continuous
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌍 AVAILABLE IN YOUR LANGUAGE:
🇺🇸 🇬🇧 ADHD focus brown noise 10 hours — work and study
🇧🇷 🇵🇹 Ruído marrom para foco TDAH 10 horas — trabalho e estudo
🇪🇸 🇲🇽 🇦🇷 Ruido marrón para enfoque TDAH 10 horas — trabajo y estudio
🇫🇷 🇨🇦 Bruit brun pour focus TDAH 10 heures — travail et étude
🇩🇪 🇦🇹 🇨🇭 Braunes Rauschen für ADHS-Fokus 10 Stunden — Arbeit und Lernen
🇮🇹 Rumore marrone per focus ADHD 10 ore — lavoro e studio
🇳🇱 Bruin ruis voor ADHD-focus 10 uur — werk en studie
🇵🇱 Brązowy szum dla skupienia ADHD 10 godzin — praca i nauka
🇷🇺 Коричневый шум для концентрации СДВГ 10 часов — работа и учёба
🇯🇵 ADHD集中用ブラウンノイズ 10時間 — 勉強・仕事
🇰🇷 ADHD 집중 브라운 노이즈 10시간 — 공부, 작업
🇨🇳 ADHD专注棕色噪音 10小时 — 学习和工作
🇹🇼 ADHD專注棕色噪音 10小時 — 學習和工作
🇮🇳 ADHD फोकस ब्राउन नॉइज़ 10 घंटे — पढ़ाई और काम
🇧🇩 ADHD ফোকাস ব্রাউন নয়েজ ১০ ঘন্টা — পড়াশোনা এবং কাজ
🇮🇩 🇲🇾 Kebisingan coklat fokus ADHD 10 jam — kerja dan belajar
🇹🇭 เสียงน้ำตาล ADHD 10 ชั่วโมง — ทำงานและเรียน
🇻🇳 Tiếng ồn nâu tập trung ADHD 10 giờ — làm việc và học tập
🇸🇦 🇦🇪 ضجيج بني للتركيز ADHD 10 ساعات — عمل ودراسة
🇹🇷 ADHD odak kahverengi gürültü 10 saat — iş ve çalışma
🇸🇪 🇳🇴 🇩🇰 Brunt brus för ADHD-fokus 10 timmar — arbete och studier
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#ADHDFocus #ADHD #BrownNoise #Concentration #DeepWork #StudyMusic
#Neurodivergent #ExecutiveFunction #FlowState #FocusMusic #BlackScreen
#ProductivityMusic #WorkMusic #ADHDRelief #10Hours #BrainFocus
""",
    "wnv": r"""⬜ WHITE NOISE 8 HOURS — Black Screen | No Ads | Looped

Pure uninterrupted white noise for deep sleep, baby sleep, and tinnitus masking.
8 hours. Black screen saves battery all night.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ BEST FOR:
• Deep Sleep & Insomnia
• Baby & Newborn Sleep
• Tinnitus Masking
• Blocking Noisy Neighbors
• Shift Workers & Light Sleepers
• Naps & Travel Sleep
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Medium-low volume recommended for sleep
⚫ Black screen — stays dark all night
👶 Safe for all ages including infants
⏰ 8 hours continuous
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌍 AVAILABLE IN YOUR LANGUAGE:
🇺🇸 🇬🇧 White noise 8 hours for deep sleep, babies and tinnitus
🇧🇷 🇵🇹 Ruído branco 8 horas para sono profundo, bebês e zumbido
🇪🇸 🇲🇽 🇦🇷 Ruido blanco 8 horas para dormir profundo, bebés y tinnitus
🇫🇷 🇨🇦 Bruit blanc 8 heures pour sommeil profond, bébé et acouphènes
🇩🇪 🇦🇹 🇨🇭 Weißes Rauschen 8 Stunden für Tiefschlaf, Baby und Tinnitus
🇮🇹 Rumore bianco 8 ore per sonno profondo, bambino e tinnito
🇳🇱 Wit ruis 8 uur voor diepe slaap, baby en tinnitus
🇵🇱 Biały szum 8 godzin dla głębokiego snu, niemowlęcia i szumów usznych
🇷🇺 Белый шум 8 часов для глубокого сна, малыша и тиннитуса
🇯🇵 ホワイトノイズ 8時間 — 深い眠り・赤ちゃん・耳鳴り
🇰🇷 화이트 노이즈 8시간 — 깊은 수면, 아기 수면, 이명
🇨🇳 白噪音 8小时 — 深度睡眠、婴儿睡眠、耳鸣
🇹🇼 白噪音 8小時 — 深度睡眠、嬰兒睡眠、耳鳴
🇮🇳 सफेद शोर 8 घंटे — गहरी नींद, बच्चे और टिनिटस
🇧🇩 সাদা শব্দ ৮ ঘন্টা — গভীর ঘুম, শিশু এবং টিনিটাস
🇮🇩 🇲🇾 Kebisingan putih 8 jam untuk tidur nyenyak, bayi dan tinnitus
🇹🇭 เสียงขาว 8 ชั่วโมง สำหรับการนอนหลับลึก เด็กทารก และหูอื้อ
🇻🇳 Tiếng ồn trắng 8 giờ cho giấc ngủ sâu, trẻ em và ù tai
🇸🇦 🇦🇪 ضجيج أبيض 8 ساعات للنوم العميق والأطفال والطنين
🇹🇷 Beyaz gürültü 8 saat derin uyku, bebek ve tinnitus için
🇸🇪 🇳🇴 🇩🇰 Vitt brus 8 timmar för djup sömn, baby och tinnitus
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#WhiteNoise #SleepSounds #BabySleep #Tinnitus #BlackScreen #DeepSleep
#Insomnia #SleepAid #NewbornSleep #TinnitusMasking #8Hours #RelaxingSounds
#AmbientNoise #SleepMusic #PureWhiteNoise
""",
    "bsn": r"""👶 BABY SLEEP WHITE NOISE 8 HOURS — Black Screen | No Ads

Gentle white noise specially for babies from birth through toddler years.
Mimics womb sounds to instantly calm and help babies sleep longer.
8 hours. Safe volume. Black screen.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ BEST FOR:
• Newborn & Infant Sleep
• Colic & Fussy Baby Relief
• Bedtime & Nap Time Routine
• Toddler Sleep
• Parents Sleeping Too
• Travel & Hotel Sleep for Babies
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Keep below 50dB for infant ears
⚫ Black screen — safe for nursery
👶 Suitable from birth
⏰ 8 hours — won't stop before morning
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌍 AVAILABLE IN YOUR LANGUAGE:
🇺🇸 🇬🇧 Baby sleep white noise 8 hours — newborn and colic
🇧🇷 🇵🇹 Ruído branco para bebê 8 horas — recém-nascido e cólica
🇪🇸 🇲🇽 🇦🇷 Ruido blanco para bebé 8 horas — recién nacido y cólico
🇫🇷 🇨🇦 Bruit blanc bébé 8 heures — nouveau-né et coliques
🇩🇪 🇦🇹 🇨🇭 Weißes Rauschen Baby 8 Stunden — Neugeborenes und Koliken
🇮🇹 Rumore bianco bambino 8 ore — neonato e coliche
🇳🇱 Baby wit ruis 8 uur — pasgeboren en darmkrampjes
🇵🇱 Biały szum dla niemowlęcia 8 godzin — noworodek i kolka
🇷🇺 Белый шум для малыша 8 часов — новорождённый и колики
🇯🇵 赤ちゃん ホワイトノイズ 8時間 — 新生児・コリック
🇰🇷 아기 화이트 노이즈 8시간 — 신생아 및 영아 수면
🇨🇳 婴儿白噪音 8小时 — 新生儿和婴幼儿睡眠
🇹🇼 嬰兒白噪音 8小時 — 新生兒和嬰幼兒睡眠
🇮🇳 शिशु के लिए सफेद शोर 8 घंटे — नवजात और कोलिक
🇧🇩 শিশুর জন্য সাদা শব্দ ৮ ঘন্টা — নবজাতক এবং কোলিক
🇮🇩 🇲🇾 Kebisingan putih bayi 8 jam — bayi baru lahir dan kolik
🇹🇭 เสียงขาวสำหรับทารก 8 ชั่วโมง — ทารกแรกเกิดและอาการปวดท้อง
🇻🇳 Tiếng ồn trắng cho bé 8 giờ — trẻ sơ sinh và đau bụng
🇸🇦 🇦🇪 ضجيج أبيض للأطفال 8 ساعات — حديث الولادة والمغص
🇹🇷 Bebek beyaz gürültü 8 saat — yenidoğan ve kolik
🇸🇪 🇳🇴 🇩🇰 Baby vitt brus 8 timmar — nyfödd och kolik
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#BabySleep #WhiteNoise #NewbornSleep #WombSounds #BabyCalm #BlackScreen
#InfantSleep #ToddlerSleep #BabySounds #8Hours #NewParents
#FussyBaby #BabyBedtime #BabyNap #SleepThroughTheNight #ColikBaby
""",
    "pink": r"""🩷 PINK NOISE 10 HOURS — Black Screen | No Ads | Science-Backed Sleep

Pink noise is scientifically proven to increase deep sleep and improve memory consolidation.
Research from Northwestern University shows pink noise can boost memory by up to 35%.
10 hours. Black screen.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ BEST FOR:
• Deep Sleep & Slow Wave Sleep
• Memory Consolidation & Learning
• Tinnitus Relief & Masking
• Stress & Anxiety Reduction
• Focus & Study
• Relaxation & Meditation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 Backed by sleep science research
🎧 Headphones enhance the effect
⚫ Full black screen — 10 hour dark mode
⏰ Continuous — no interruptions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌍 AVAILABLE IN YOUR LANGUAGE:
🇺🇸 🇬🇧 Pink noise 10 hours for deep sleep, memory and tinnitus
🇧🇷 🇵🇹 Ruído rosa 10 horas para sono profundo, memória e zumbido
🇪🇸 🇲🇽 🇦🇷 Ruido rosa 10 horas para sueño profundo, memoria y tinnitus
🇫🇷 🇨🇦 Bruit rose 10 heures pour sommeil profond, mémoire et acouphènes
🇩🇪 🇦🇹 🇨🇭 Rosarauschen 10 Stunden für Tiefschlaf, Gedächtnis und Tinnitus
🇮🇹 Rumore rosa 10 ore per sonno profondo, memoria e tinnito
🇳🇱 Roze ruis 10 uur voor diepe slaap, geheugen en tinnitus
🇵🇱 Różowy szum 10 godzin dla głębokiego snu, pamięci i szumów usznych
🇷🇺 Розовый шум 10 часов для глубокого сна, памяти и тиннитуса
🇯🇵 ピンクノイズ 10時間 — 深い眠り・記憶力・耳鳴り
🇰🇷 핑크 노이즈 10시간 — 깊은 수면, 기억력, 이명
🇨🇳 粉红噪音 10小时 — 深度睡眠、记忆力和耳鸣
🇹🇼 粉紅噪音 10小時 — 深度睡眠、記憶力和耳鳴
🇮🇳 गुलाबी शोर 10 घंटे — गहरी नींद, स्मृति और टिनिटस
🇧🇩 গোলাপী শব্দ ১০ ঘন্টা — গভীর ঘুম, স্মৃতি এবং টিনিটাস
🇮🇩 🇲🇾 Kebisingan merah muda 10 jam untuk tidur nyenyak, memori dan tinnitus
🇹🇭 เสียงชมพู 10 ชั่วโมง สำหรับการนอนหลับลึก ความจำ และหูอื้อ
🇻🇳 Tiếng ồn hồng 10 giờ cho giấc ngủ sâu, trí nhớ và ù tai
🇸🇦 🇦🇪 ضجيج وردي 10 ساعات للنوم العميق والذاكرة والطنين
🇹🇷 Pembe gürültü 10 saat derin uyku, hafıza ve tinnitus için
🇸🇪 🇳🇴 🇩🇰 Rosa brus 10 timmar för djup sömn, minne och tinnitus
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#PinkNoise #DeepSleep #Tinnitus #MemoryBoost #SleepScience #BlackScreen
#SlowWaveSleep #TinnitusRelief #AnxietyRelief #10Hours #SleepSounds
#PinkNoiseSleep #SleepBetter #Relaxation #MemoryConsolidation
""",
    "tinnitus": r"""👂 TINNITUS RELIEF 8 HOURS — Black Screen | No Ads

Carefully calibrated blend of pink and white noise designed to mask tinnitus frequencies.
Helps with sleep, relaxation and tinnitus habituation therapy.
8 uninterrupted hours. Black screen.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ BEST FOR:
• Tinnitus Masking & Relief
• Sleeping with Tinnitus
• Tinnitus Habituation Therapy
• Focus & Work with Tinnitus
• Ringing, Buzzing & Hissing Ear Sounds
• Hyperacusis Relief
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 Match volume to your tinnitus level
⚫ Black screen — optimal for sleeping
⏰ 8 hours — covers full sleep cycle
💡 Tip: Use at a volume just below your tinnitus
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌍 AVAILABLE IN YOUR LANGUAGE:
🇺🇸 🇬🇧 Tinnitus relief 8 hours — pink and white noise masking
🇧🇷 🇵🇹 Alívio para zumbido 8 horas — ruído rosa e branco
🇪🇸 🇲🇽 🇦🇷 Alivio para tinnitus 8 horas — ruido rosa y blanco
🇫🇷 🇨🇦 Soulagement acouphènes 8 heures — bruit rose et blanc
🇩🇪 🇦🇹 🇨🇭 Tinnitus-Linderung 8 Stunden — Rosa und weißes Rauschen
🇮🇹 Sollievo tinnito 8 ore — rumore rosa e bianco
🇳🇱 Tinnitus verlichting 8 uur — roze en wit ruis
🇵🇱 Ulga w szumach usznych 8 godzin — różowy i biały szum
🇷🇺 Облегчение тиннитуса 8 часов — розовый и белый шум
🇯🇵 耳鳴り緩和ノイズ 8時間 — ピンク＆ホワイトノイズ
🇰🇷 이명 완화 소리 8시간 — 핑크 및 화이트 노이즈
🇨🇳 耳鸣缓解噪音 8小时 — 粉红色和白色噪音
🇹🇼 耳鳴緩解噪音 8小時 — 粉紅色和白色噪音
🇮🇳 कान बजने से राहत 8 घंटे — गुलाबी और सफेद शोर
🇧🇩 কান বাজার উপশম ৮ ঘন্টা — গোলাপী এবং সাদা শব্দ
🇮🇩 🇲🇾 Pereda tinnitus 8 jam — kebisingan merah muda dan putih
🇹🇭 การบรรเทาหูอื้อ 8 ชั่วโมง — เสียงชมพูและขาว
🇻🇳 Giảm ù tai 8 giờ — tiếng ồn hồng và trắng
🇸🇦 🇦🇪 تخفيف الطنين 8 ساعات — ضجيج وردي وأبيض
🇹🇷 Tinnitus rahatlaması 8 saat — pembe ve beyaz gürültü
🇸🇪 🇳🇴 🇩🇰 Tinnituslindring 8 timmar — rosa och vitt brus
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#Tinnitus #TinnitusRelief #RingingEars #TinnitusMasking #PinkNoise
#WhiteNoise #TinnitusTherapy #SleepWithTinnitus #EarRinging #BlackScreen
#TinnitusHabituation #8Hours #Hyperacusis #TinnitusTreatment #EarNoise
""",
    "rain": r"""🌧️ RAIN SOUNDS 8 HOURS — Black Screen | No Ads | Heavy Rain

Heavy continuous rain sounds for deep sleep, studying, and total relaxation.
No thunder. No gaps. No interruptions.
8 hours. Black screen saves battery.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ BEST FOR:
• Deep Sleep & Insomnia
• Study & Focus Sessions
• Relaxation & Meditation
• Anxiety & Stress Relief
• ASMR & Rain Lovers
• Background Ambience for Work
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌧️ Heavy rain — no thunder
⚫ Black screen — no light pollution
🎧 Headphones for full immersion
⏰ 8 hours — full night coverage
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌍 AVAILABLE IN YOUR LANGUAGE:
🇺🇸 🇬🇧 Rain sounds 8 hours for sleep, study and relaxation
🇧🇷 🇵🇹 Som de chuva 8 horas para dormir, estudar e relaxar
🇪🇸 🇲🇽 🇦🇷 Sonidos de lluvia 8 horas para dormir, estudiar y relajarse
🇫🇷 🇨🇦 Sons de pluie 8 heures pour dormir, étudier et se détendre
🇩🇪 🇦🇹 🇨🇭 Regengeräusche 8 Stunden zum Schlafen, Lernen und Entspannen
🇮🇹 Suoni di pioggia 8 ore per dormire, studiare e rilassarsi
🇳🇱 Regengeluiden 8 uur voor slapen, studeren en ontspannen
🇵🇱 Dźwięki deszczu 8 godzin dla snu, nauki i relaksu
🇷🇺 Звуки дождя 8 часов для сна, учёбы и расслабления
🇯🇵 雨音 8時間 — 深い眠り・勉強・リラックス
🇰🇷 빗소리 8시간 — 깊은 수면, 공부, 휴식
🇨🇳 雨声 8小时 — 深度睡眠、学习和放松
🇹🇼 雨聲 8小時 — 深度睡眠、學習和放鬆
🇮🇳 बारिश की आवाज़ 8 घंटे — नींद, पढ़ाई और विश्राम
🇧🇩 বৃষ্টির শব্দ ৮ ঘন্টা — ঘুম, পড়াশোনা এবং বিশ্রাম
🇮🇩 🇲🇾 Suara hujan 8 jam untuk tidur, belajar dan bersantai
🇹🇭 เสียงฝน 8 ชั่วโมง สำหรับการนอนหลับ การเรียน และการผ่อนคลาย
🇻🇳 Tiếng mưa 8 giờ cho giấc ngủ, học tập và thư giãn
🇸🇦 🇦🇪 أصوات المطر 8 ساعات للنوم والدراسة والاسترخاء
🇹🇷 Yağmur sesleri 8 saat uyku, çalışma ve rahatlama için
🇸🇪 🇳🇴 🇩🇰 Regn ljud 8 timmar för sömn, studier och avkoppling
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#RainSounds #SleepRain #HeavyRain #ASMR #SleepSounds #BlackScreen
#StudyRain #RelaxingRain #DeepSleep #AnxietyRelief #8Hours #NatureSounds
#RainASMR #StressRelief #AmbientRain #RainyNight #Insomnia
""",
}

# 1. BAIXAR do GitHub Release
print(f"[{CANAL.upper()}] Baixando {ASSET_NAME} do GitHub Release...")
GH_H = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}

r = requests.get(
    f"https://api.github.com/repos/{REPO}/releases/tags/noise-videos",
    headers=GH_H, timeout=15)
if r.status_code != 200:
    print(f"ERRO release: {r.status_code} {r.text[:200]}")
    sys.exit(1)

asset_url = None
for asset in r.json().get("assets", []):
    if asset["name"].upper() == ASSET_NAME.upper():
        asset_url = asset["url"]
        size_total = asset["size"]
        print(f"  Encontrado: {asset['name']} ({size_total/(1024**3):.2f} GB)")
        break

if not asset_url:
    disponiveis = [a["name"] for a in r.json().get("assets", [])]
    print(f"ERRO: {ASSET_NAME} nao encontrado. Disponiveis: {disponiveis}")
    sys.exit(1)

path_original = f"/tmp/{CANAL}_original.mp4"
path_final    = f"/tmp/{CANAL}.mp4"

r2 = requests.get(asset_url,
    headers={"Authorization": f"token {GH_TOKEN}", "Accept": "application/octet-stream"},
    stream=True, timeout=3600)
if r2.status_code != 200:
    print(f"ERRO download: {r2.status_code}")
    sys.exit(1)

downloaded = 0
with open(path_original, "wb") as f:
    for chunk in r2.iter_content(chunk_size=32*1024*1024):
        if chunk:
            f.write(chunk)
            downloaded += len(chunk)
            print(f"\r  {downloaded/(1024**3):.2f}/{size_total/(1024**3):.2f} GB", end="", flush=True)
print(f"\n  Download OK: {os.path.getsize(path_original)/(1024**3):.2f} GB")

# 2. FASTSTART — move moov atom para o inicio (sem recodificar audio/video)
print(f"  Aplicando faststart (moov atom para o inicio)...")
result = subprocess.run([
    "ffmpeg", "-y",
    "-i", path_original,
    "-c", "copy",           # copia audio e video sem recodificar
    "-movflags", "+faststart",  # move moov para o inicio
    path_final
], capture_output=True, text=True, timeout=600)

if result.returncode != 0:
    print(f"ERRO ffmpeg: {result.stderr[-300:]}")
    sys.exit(1)

size_orig = os.path.getsize(path_original)
size_fast = os.path.getsize(path_final)
print(f"  Faststart OK: {size_orig/(1024**3):.2f} GB -> {size_fast/(1024**3):.2f} GB")
os.remove(path_original)

# 3. ACCESS TOKEN
r3 = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
    "refresh_token": RT, "grant_type": "refresh_token"}, timeout=15)
at = r3.json().get("access_token")
if not at:
    print(f"ERRO token: {r3.text[:150]}")
    sys.exit(1)
print("  Token OAuth: OK")

# 4. LIMPAR canal
r4 = requests.get("https://www.googleapis.com/youtube/v3/channels",
    params={"part": "contentDetails,statistics", "id": CHANNEL_ID},
    headers={"Authorization": f"Bearer {at}"}, timeout=10)
if r4.status_code == 200 and r4.json().get("items"):
    n = int(r4.json()["items"][0]["statistics"].get("videoCount", 0))
    if n > 0:
        pl = r4.json()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        r5 = requests.get("https://www.googleapis.com/youtube/v3/playlistItems",
            params={"part": "snippet", "playlistId": pl, "maxResults": 50},
            headers={"Authorization": f"Bearer {at}"}, timeout=10)
        for item in r5.json().get("items", []):
            vid = item["snippet"]["resourceId"]["videoId"]
            rd = requests.delete("https://www.googleapis.com/youtube/v3/videos",
                params={"id": vid}, headers={"Authorization": f"Bearer {at}"}, timeout=10)
            print(f"  Apagado {vid}: {rd.status_code}")
            time.sleep(0.5)
    else:
        print("  Canal limpo")

# 5. UPLOAD — part=snippet,status APENAS (sem monetizationDetails)
size = os.path.getsize(path_final)
meta = {
    "snippet": {
        "title": TITULO,
        "description": DESCRICOES.get(CANAL, TITULO),
        "tags": TAGS,
        "categoryId": "22",
        "defaultLanguage": "en",
        "defaultAudioLanguage": "en",
    },
    "status": {
        "privacyStatus": "public",
        "selfDeclaredMadeForKids": False,
        "madeForKids": False,
        "license": "youtube",
        "embeddable": True,
        "publicStatsViewable": True,
        "notifySubscribers": True,
    }
}

print(f"  Iniciando upload ({size/(1024**3):.2f} GB)...")
r6 = requests.post(
    "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
    headers={"Authorization": f"Bearer {at}",
             "Content-Type": "application/json",
             "X-Upload-Content-Type": "video/mp4",
             "X-Upload-Content-Length": str(size)},
    json=meta, timeout=30)

if r6.status_code != 200:
    print(f"ERRO iniciar upload: {r6.status_code} {r6.text[:300]}")
    sys.exit(1)

upload_url = r6.headers["Location"]
CHUNK = 50 * 1024 * 1024
sent, video_id = 0, None

with open(path_final, "rb") as f:
    while sent < size:
        chunk = f.read(CHUNK)
        if not chunk:
            break
        end = sent + len(chunk) - 1
        r7 = requests.put(upload_url,
            headers={"Authorization": f"Bearer {at}",
                     "Content-Range": f"bytes {sent}-{end}/{size}",
                     "Content-Type": "video/mp4"},
            data=chunk, timeout=600)
        sent += len(chunk)
        if r7.status_code in (200, 201):
            video_id = r7.json().get("id")
            print(f"\n  UPLOAD COMPLETO: {video_id}")
            break
        elif r7.status_code == 308:
            print(f"\r  {sent/size*100:.1f}%...", end="", flush=True)
        elif r7.status_code == 503:
            print("\n  503 retry 20s...")
            time.sleep(20)
            sent -= len(chunk)
            f.seek(sent)
        else:
            print(f"\n  ERRO: {r7.status_code} {r7.text[:200]}")
            sys.exit(1)

if not video_id:
    print("ERRO: sem video_id ao final")
    sys.exit(1)

# 6. MONETIZACAO (separado do upload)
time.sleep(5)
r8 = requests.put(
    "https://www.googleapis.com/youtube/v3/videos?part=monetizationDetails,status",
    headers={"Authorization": f"Bearer {at}", "Content-Type": "application/json"},
    json={"id": video_id,
          "monetizationDetails": {"access": {"allowed": True}},
          "status": {"selfDeclaredMadeForKids": False, "madeForKids": False,
                     "license": "youtube", "embeddable": True}},
    timeout=20)
print(f"  Monetizacao: {r8.status_code} {'OK' if r8.status_code==200 else r8.text[:80]}")

# 7. SUPABASE
if SB_KEY and len(SB_KEY) > 20:
    sb_h = {"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}",
            "Content-Type": "application/json"}
    requests.patch(f"{SB_URL}/rest/v1/noise_channels?canal_key=eq.{CANAL}",
        headers=sb_h, json={"video_id": video_id, "video_uploaded": True}, timeout=10)

print(f"\n  URL: https://youtube.com/watch?v={video_id}")
print(f"  DONE {CANAL.upper()} = {video_id}")
