#!/usr/bin/env python3
"""
live_universal_v2.py — 9 idiomas × horário prime time × CTA inscrição
Canal: @psidanicoelho (UCSH63tBfY6wEIdkC4u4zKdg)
Todos os streams usam YOUTUBE_STREAM_KEY — acumulam no mesmo canal
"""
import os, time, subprocess, pathlib, requests, textwrap, hashlib, threading
from datetime import datetime, timezone, timedelta

LANG_CODE  = os.getenv("LANG_CODE", "EN").upper()
STREAM_KEY = os.getenv(f"YOUTUBE_STREAM_KEY_{LANG_CODE}", os.getenv("YOUTUBE_STREAM_KEY", ""))
GROQ_KEY   = os.getenv("GROQ_API_KEY", "")
RTMP_URL   = f"rtmp://a.rtmp.youtube.com/live2/{STREAM_KEY}"
CHANNEL    = "@psidanicoelho"
W, H = 1280, 720
TMP = pathlib.Path(f"/tmp/live_{LANG_CODE.lower()}"); TMP.mkdir(exist_ok=True)

# ── FUSO + SAUDAÇÃO por idioma ─────────────────────────────────────────────
TZ_OFFSETS = {
    "PT": -3, "EN": -5, "ES": -4, "FR": 1,
    "DE": 1,  "IT": 1,  "JA": 9, "KO": 9, "AR": 3, "HI": 5.5, "RU": 3, "ZH": 8
}

def get_greeting(lang):
    h = (datetime.now(timezone.utc) + timedelta(hours=TZ_OFFSETS.get(lang, 0))).hour
    greetings = {
        "PT": {(5,12):"Bom dia ☀️",(12,18):"Boa tarde 🌤",(18,24):"Boa noite 🌙",(0,5):"Madrugada 🌃"},
        "EN": {(5,12):"Good morning ☀️",(12,18):"Good afternoon 🌤",(18,24):"Good evening 🌙",(0,5):"Late night 🌃"},
        "ES": {(5,12):"Buenos días ☀️",(12,18):"Buenas tardes 🌤",(18,24):"Buenas noches 🌙",(0,5):"Madrugada 🌃"},
        "FR": {(5,12):"Bonjour ☀️",(12,18):"Bon après-midi 🌤",(18,24):"Bonsoir 🌙",(0,5):"Bonne nuit 🌃"},
        "DE": {(5,12):"Guten Morgen ☀️",(12,18):"Guten Tag 🌤",(18,24):"Guten Abend 🌙",(0,5):"Gute Nacht 🌃"},
        "IT": {(5,12):"Buongiorno ☀️",(12,18):"Buon pomeriggio 🌤",(18,24):"Buona sera 🌙",(0,5):"Notte 🌃"},
        "JA": {(5,12):"おはよう ☀️",(12,18):"こんにちは 🌤",(18,24):"こんばんは 🌙",(0,5):"深夜 🌃"},
        "KO": {(5,12):"좋은 아침 ☀️",(12,18):"안녕하세요 🌤",(18,24):"좋은 저녁 🌙",(0,5):"늦은 밤 🌃"},
        "AR": {(5,12):"صباح الخير ☀️",(12,18):"مساء النور 🌤",(18,24):"مساء الخير 🌙",(0,5):"منتصف الليل 🌃"},
        "HI": {(5,12):"सुप्रभात ☀️",(12,18):"नमस्ते 🌤",(18,24):"शुभ संध्या 🌙",(0,5):"रात 🌃"},
        "RU": {(5,12):"Доброе утро ☀️",(12,18):"Добрый день 🌤",(18,24):"Добрый вечер 🌙",(0,5):"Поздняя ночь 🌃"},
        "ZH": {(5,12):"早上好 ☀️",(12,18):"下午好 🌤",(18,24):"晚上好 🌙",(0,5):"深夜 🌃"},
    }
    tbl = greetings.get(lang, greetings["EN"])
    for (s,e), txt in tbl.items():
        if s <= h < e: return txt
    return list(tbl.values())[-1]

# ── CONTEÚDO POR IDIOMA ────────────────────────────────────────────────────
CONTENT = {
    "PT": {
        "brand": "Daniela Coelho · Pesquisadora de Comportamento Humano",
        "cta":   "▶ Inscreva-se: @psidanicoelho",
        "sleep": ("528Hz SONO PROFUNDO", "#050515", "#818CF8", [
            ("Apego Ansioso","Apego ansioso hiperativa a amígdala durante o sono — explicando ruminação às 3h. Biologia, não fraqueza. — Ainsworth"),
            ("Cortisol e Insônia","Ansiedade crônica eleva cortisol e suprime melatonina. O ciclo por trás de 40% das insônias ansiosas. — Sapolsky"),
            ("Trauma e Sono","Trauma não processado fragmenta os ciclos REM. O corpo ensaia ameaças enquanto dorme. — van der Kolk"),
            ("Narcisismo Encoberto","O narcisista mais perigoso não parece arrogante. Parece a maior vítima da sala. — Malkin/Harvard"),
            ("Vício em Validação","Curtidas ativam o mesmo circuito de recompensa que a cocaína. Razão variável — o mais viciante. — Skinner"),
        ]),
        "prime": ("963Hz LIBERTAÇÃO", "#120008", "#FB7185", [
            ("Gaslight","Quando você confia mais na realidade deles do que na sua, o gaslighting já funcionou. — Freyd/Oregon"),
            ("Fronteiras","Dizer não sem culpa é habilidade aprendida, não traço de personalidade. — Brown/U.Texas"),
            ("Síndrome do Impostor","Quanto mais competente você é, mais sabe o que não sabe. Metacognição, não fraqueza."),
            ("Dopamina","O scroll infinito foi projetado por engenheiros de vício. Você não é fraco — o sistema é viciante. — Alter"),
            ("Amor e Destruição","62% dos adultos têm apego inseguro. A maioria nunca soube. — Dados globais Ainsworth"),
        ]),
    },
    "EN": {
        "brand": "Sarah Mitchell · Behavioral Research & Psychology",
        "cta":   "▶ Subscribe: @psidanicoelho",
        "sleep": ("528Hz DEEP SLEEP", "#050515", "#818CF8", [
            ("Anxious Attachment","Anxious attachment hyperactivates the amygdala during sleep — explaining 3am rumination. Biology, not weakness. — Ainsworth"),
            ("Cortisol & Insomnia","Chronic anxiety elevates cortisol and suppresses melatonin. The cycle behind 40% of anxious insomnia. — Sapolsky"),
            ("Trauma & REM","Unprocessed trauma disrupts REM cycles. The body rehearses threats during sleep. — van der Kolk"),
            ("528Hz & Healing","528Hz frequency linked to reduced stress hormones in peer-reviewed research. — NCBI 2019"),
            ("Covert Narcissism","The most dangerous narcissist doesn't seem arrogant. They seem like the biggest victim. — Malkin/Harvard"),
        ]),
        "prime": ("963Hz LIBERATION", "#120008", "#FB7185", [
            ("Gaslighting Signs","When you trust their reality more than yours, gaslighting already worked. — Freyd/Oregon"),
            ("Validation Addiction","Likes activate the same reward circuit as cocaine. Variable ratio — the most addictive. — Skinner/Alter"),
            ("Impostor Syndrome","The more competent you are, the more you know what you don't know. Metacognition, not weakness."),
            ("Healthy Boundaries","Saying no without guilt is a learned skill, not a personality trait. — Brown/U.Texas"),
            ("Anxious Attachment","62% of adults have insecure attachment. Most never knew. — Global Ainsworth Data"),
        ]),
    },
    "ES": {
        "brand": "Daniela Coelho · Investigadora de Comportamiento Humano",
        "cta":   "▶ Suscríbete: @psidanicoelho",
        "sleep": ("528Hz SUEÑO PROFUNDO", "#050515", "#818CF8", [
            ("Apego Ansioso","El apego ansioso hiperactivala amígdala durante el sueño — explicando la rumia a las 3am. Biología, no debilidad. — Ainsworth"),
            ("Cortisol e Insomnio","La ansiedad crónica eleva el cortisol y suprime la melatonina. El ciclo detrás del 40% del insomnio. — Sapolsky"),
            ("Trauma y Sueño","El trauma no procesado fragmenta los ciclos REM. El cuerpo ensaya amenazas mientras duerme. — van der Kolk"),
            ("Narcisismo Encubierto","El narcisista más peligroso no parece arrogante. Parece la mayor víctima. — Malkin/Harvard"),
            ("Adicción a Validación","Los likes activan el mismo circuito de recompensa que la cocaína. Razón variable — la más adictiva. — Skinner"),
        ]),
        "prime": ("963Hz LIBERACIÓN", "#120008", "#FB7185", [
            ("Gaslighting","Cuando confías más en su realidad que en la tuya, el gaslighting ya funcionó. — Freyd/Oregon"),
            ("Límites Sanos","Decir no sin culpa es una habilidad aprendida, no un rasgo de personalidad. — Brown/U.Texas"),
            ("Síndrome del Impostor","Cuanto más competente eres, más sabes lo que no sabes. Metacognición, no debilidad."),
            ("Dopamina","El scroll infinito fue diseñado por ingenieros de adicción. No eres débil — el sistema es adictivo."),
            ("Apego Inseguro","El 62% de los adultos tiene apego inseguro. La mayoría nunca lo supo. — Datos globales Ainsworth"),
        ]),
    },
    "FR": {
        "brand": "Daniela Coelho · Chercheuse en Comportement Humain",
        "cta":   "▶ Abonnez-vous: @psidanicoelho",
        "sleep": ("528Hz SOMMEIL PROFOND", "#050515", "#818CF8", [
            ("Attachement Anxieux","L'attachement anxieux hyperactive l'amygdale pendant le sommeil — expliquant les ruminations à 3h du matin. Biologie, pas faiblesse. — Ainsworth"),
            ("Cortisol et Insomnie","L'anxiété chronique élève le cortisol et supprime la mélatonine. Le cycle derrière 40% des insomnies. — Sapolsky"),
            ("Trauma et Sommeil","Le trauma non traité fragmente les cycles REM. Le corps répète les menaces pendant le sommeil. — van der Kolk"),
            ("Narcissisme Masqué","Le narcissiste le plus dangereux ne semble pas arrogant. Il semble être la plus grande victime. — Malkin/Harvard"),
            ("528Hz et Guérison","Fréquence 528Hz liée à la réduction des hormones de stress dans des recherches évaluées par des pairs. — NCBI 2019"),
        ]),
        "prime": ("963Hz LIBÉRATION", "#120008", "#FB7185", [
            ("Gaslighting","Quand vous faites plus confiance à leur réalité qu'à la vôtre, le gaslighting a déjà fonctionné. — Freyd/Oregon"),
            ("Limites Saines","Dire non sans culpabilité est une compétence apprise, pas un trait de personnalité. — Brown/U.Texas"),
            ("Syndrome de l'Imposteur","Plus vous êtes compétent, plus vous savez ce que vous ne savez pas. Métacognition, pas faiblesse."),
            ("Addiction à la Validation","Les likes activent le même circuit de récompense que la cocaïne. Ratio variable — le plus addictif. — Skinner"),
            ("Attachement Insécure","62% des adultes ont un attachement insécure. La plupart ne l'ont jamais su. — Données mondiales Ainsworth"),
        ]),
    },
    "DE": {
        "brand": "Sarah Mitchell · Verhaltensforschung & Psychologie",
        "cta":   "▶ Abonnieren: @psidanicoelho",
        "sleep": ("528Hz TIEFER SCHLAF", "#050515", "#818CF8", [
            ("Ängstliche Bindung","Ängstliche Bindung überaktiviert die Amygdala im Schlaf — erklärt nächtliches Grübeln um 3 Uhr. Biologie, keine Schwäche. — Ainsworth"),
            ("Kortisol & Schlaflosigkeit","Chronische Angst erhöht Kortisol und unterdrückt Melatonin. Der Kreislauf hinter 40% der Schlaflosigkeit. — Sapolsky"),
            ("Trauma & REM","Unverarbeitetes Trauma stört REM-Zyklen. Der Körper probt Bedrohungen im Schlaf. — van der Kolk"),
            ("Verdeckter Narzissmus","Der gefährlichste Narzisst wirkt nicht arrogant. Er wirkt wie das größte Opfer. — Malkin/Harvard"),
            ("Dopamin & Social Media","Likes aktivieren denselben Belohnungskreislauf wie Kokain. Variables Verhältnis — das Suchterzeugende. — Skinner"),
        ]),
        "prime": ("963Hz BEFREIUNG", "#120008", "#FB7185", [
            ("Gaslighting erkennen","Wenn Sie ihrer Realität mehr vertrauen als Ihrer eigenen, hat Gaslighting bereits funktioniert. — Freyd"),
            ("Gesunde Grenzen","Nein zu sagen ohne Schuldgefühle ist eine erlernte Fähigkeit, kein Persönlichkeitsmerkmal. — Brown"),
            ("Hochstapler-Syndrom","Je kompetenter Sie sind, desto mehr wissen Sie, was Sie nicht wissen. Metakognition, keine Schwäche."),
            ("Unsichere Bindung","62% der Erwachsenen haben unsichere Bindung. Die meisten wussten es nie. — Globale Ainsworth-Daten"),
            ("Burnout","Burnout ist keine Schwäche — es ist der Beweis, dass Sie zu lange zu viel versucht haben."),
        ]),
    },
    "IT": {
        "brand": "Daniela Coelho · Ricercatrice di Comportamento Umano",
        "cta":   "▶ Iscriviti: @psidanicoelho",
        "sleep": ("528Hz SONNO PROFONDO", "#050515", "#818CF8", [
            ("Attaccamento Ansioso","L'attaccamento ansioso iperattiva l'amigdala durante il sonno — spiegando la ruminazione alle 3am. Biologia, non debolezza. — Ainsworth"),
            ("Cortisolo e Insonnia","L'ansia cronica eleva il cortisolo e sopprime la melatonina. Il ciclo dietro il 40% dell'insonnia. — Sapolsky"),
            ("Trauma e Sonno","Il trauma non elaborato frammenta i cicli REM. Il corpo prova le minacce durante il sonno. — van der Kolk"),
            ("Narcisismo Mascherato","Il narcisista più pericoloso non sembra arrogante. Sembra la vittima più grande. — Malkin/Harvard"),
            ("528Hz e Guarigione","La frequenza 528Hz è collegata alla riduzione degli ormoni dello stress nella ricerca scientifica. — NCBI 2019"),
        ]),
        "prime": ("963Hz LIBERAZIONE", "#120008", "#FB7185", [
            ("Gaslighting","Quando ti fidi della loro realtà più che della tua, il gaslighting ha già funzionato. — Freyd/Oregon"),
            ("Confini Sani","Dire no senza senso di colpa è un'abilità appresa, non un tratto della personalità. — Brown/U.Texas"),
            ("Sindrome dell'Impostore","Più sei competente, più sai quello che non sai. Metacognizione, non debolezza."),
            ("Dipendenza da Validazione","I like attivano lo stesso circuito di ricompensa della cocaina. Rapporto variabile — il più dipendente. — Skinner"),
            ("Attaccamento Insicuro","Il 62% degli adulti ha un attaccamento insicuro. La maggior parte non lo sapeva mai. — Dati Ainsworth"),
        ]),
    },
    "JA": {
        "brand": "行動研究者 ダニエラ・コエーリョ",
        "cta":   "▶ 登録: @psidanicoelho",
        "sleep": ("528Hz 深い睡眠", "#050515", "#818CF8", [
            ("不安型愛着","不安型愛着は睡眠中に扁桃体を過活性化する — 夜3時の反芻を説明する。生物学、弱さではない。— Ainsworth"),
            ("コルチゾールと不眠","慢性的な不安はコルチゾールを上昇させ、メラトニンを抑制する。不眠の40%の原因。— Sapolsky"),
            ("トラウマと睡眠","処理されていないトラウマはREMサイクルを乱す。身体は睡眠中に脅威をリハーサルする。— van der Kolk"),
            ("隠れたナルシシズム","最も危険なナルシシストは傲慢には見えない。最大の被害者に見える。— Malkin/Harvard"),
            ("ドーパミンとSNS","いいねはコカインと同じ報酬回路を活性化する。可変比率 — 最も依存性が高い。— Skinner"),
        ]),
        "prime": ("963Hz 解放", "#120008", "#FB7185", [
            ("ガスライティング","彼らの現実を自分のものより信頼するとき、ガスライティングはすでに機能している。— Freyd/Oregon"),
            ("健全な境界線","罪悪感なしにノーと言うことは学習したスキルであり、性格特性ではない。— Brown/U.Texas"),
            ("インポスター症候群","能力が高いほど、自分が知らないことを知っている。メタ認知、弱さではない。"),
            ("不健全な依存","62%の成人が不安全な愛着を持っている。ほとんどが知らなかった。— Ainsworth"),
            ("燃え尽き症候群","バーンアウトは弱さではない — 長すぎる間、多すぎることをしようとした証拠。"),
        ]),
    },
    "KO": {
        "brand": "행동 연구원 다니엘라 코엘류",
        "cta":   "▶ 구독: @psidanicoelho",
        "sleep": ("528Hz 깊은 수면", "#050515", "#818CF8", [
            ("불안 애착","불안 애착은 수면 중 편도체를 과활성화한다 — 새벽 3시의 반추를 설명한다. 생물학, 나약함이 아니다. — Ainsworth"),
            ("코르티솔과 불면증","만성 불안은 코르티솔을 높이고 멜라토닌을 억제한다. 불면증의 40% 뒤에 있는 사이클. — Sapolsky"),
            ("트라우마와 수면","처리되지 않은 트라우마는 REM 주기를 방해한다. 몸은 잠자는 동안 위협을 연습한다. — van der Kolk"),
            ("은밀한 나르시시즘","가장 위험한 나르시시스트는 오만해 보이지 않는다. 가장 큰 피해자처럼 보인다. — Malkin/Harvard"),
            ("도파민과 SNS","좋아요는 코카인과 같은 보상 회로를 활성화한다. 변동 비율 — 가장 중독성이 강하다. — Skinner"),
        ]),
        "prime": ("963Hz 해방", "#120008", "#FB7185", [
            ("가스라이팅","당신이 자신의 현실보다 그들의 현실을 더 신뢰할 때, 가스라이팅은 이미 작동했다. — Freyd/Oregon"),
            ("건강한 경계","죄책감 없이 거절하는 것은 배운 기술이지 성격 특성이 아니다. — Brown/U.Texas"),
            ("사기꾼 증후군","능력이 높을수록 자신이 모르는 것을 더 많이 안다. 메타인지, 나약함이 아니다."),
            ("불안 애착","성인의 62%가 불안전한 애착을 가지고 있다. 대부분은 몰랐다. — Ainsworth"),
            ("번아웃","번아웃은 나약함이 아니다 — 너무 오래 너무 많이 하려 했다는 증거다."),
        ]),
    },
    "AR": {
        "brand": "دانييلا كويلو · باحثة في السلوك البشري",
        "cta":   "▶ اشترك: @psidanicoelho",
        "sleep": ("528Hz نوم عميق", "#050515", "#818CF8", [
            ("القلق والتعلق","التعلق القلق يفرط في تنشيط اللوزة الدماغية أثناء النوم — يفسر التفكير المفرط في الساعة 3 صباحاً. علم الأحياء، ليس ضعفاً. — Ainsworth"),
            ("الكورتيزول والأرق","القلق المزمن يرفع الكورتيزول ويقمع الميلاتونين. الدورة التي تقف وراء 40% من الأرق. — Sapolsky"),
            ("الصدمة والنوم","الصدمة غير المعالجة تعطل دورات النوم العميق. الجسم يتدرب على التهديدات أثناء النوم. — van der Kolk"),
            ("النرجسية الخفية","أخطر النرجسيين لا يبدو متغطرساً. يبدو الضحية الكبرى. — Malkin/Harvard"),
            ("الدوبامين والإعلام","الإعجابات تنشط نفس دائرة المكافأة كالكوكايين. النسبة المتغيرة — الأكثر إدماناً. — Skinner"),
        ]),
        "prime": ("963Hz تحرر", "#120008", "#FB7185", [
            ("الغاز لايتينج","عندما تثق بواقعهم أكثر من واقعك، فإن الغاز لايتينج قد نجح بالفعل. — Freyd/Oregon"),
            ("الحدود الصحية","قول لا دون ذنب مهارة مكتسبة، وليست سمة شخصية. — Brown/U.Texas"),
            ("متلازمة المحتال","كلما كنت أكثر كفاءة، كلما عرفت ما لا تعرفه. وعي ذاتي، وليس ضعفاً."),
            ("التعلق غير الآمن","62% من البالغين لديهم تعلق غير آمن. معظمهم لم يعرفوا ذلك أبداً. — Ainsworth"),
            ("الاحتراق الوظيفي","الاحتراق الوظيفي ليس ضعفاً — إنه دليل على أنك حاولت الكثير لفترة طويلة."),
        ]),
    },
    "HI": {
        "brand": "डैनिएला कोएलो · मानव व्यवहार शोधकर्ता",
        "cta":   "▶ सब्सक्राइब करें: @psidanicoelho",
        "sleep": ("528Hz गहरी नींद", "#050515", "#818CF8", [
            ("चिंतित लगाव","चिंतित लगाव नींद में अमिग्डाला को सक्रिय करता है — सुबह 3 बजे की चिंता। जीव विज्ञान, कमजोरी नहीं। — Ainsworth"),
            ("कोर्टिसोल और अनिद्रा","पुरानी चिंता कोर्टिसोल बढ़ाती है और मेलाटोनिन दबाती है। 40% अनिद्रा का कारण। — Sapolsky"),
            ("आघात और नींद","अनसुलझा आघात REM चक्र बाधित करता है। शरीर नींद में खतरों का अभ्यास करता है। — van der Kolk"),
            ("छिपा नार्सिसिज़्म","सबसे खतरनाक नार्सिसिस्ट घमंडी नहीं दिखता। सबसे बड़ा पीड़ित दिखता है। — Malkin/Harvard"),
            ("मान्यता की लत","लाइक कोकीन जैसा इनाम सर्किट सक्रिय करते हैं। परिवर्तनशील अनुपात — सबसे लती। — Skinner"),
        ]),
        "prime": ("963Hz मुक्ति", "#120008", "#FB7185", [
            ("गैसलाइटिंग","जब आप अपनी से अधिक उनकी वास्तविकता पर भरोसा करते हैं, गैसलाइटिंग काम कर चुकी। — Freyd/Oregon"),
            ("स्वस्थ सीमाएं","बिना अपराधबोध के ना कहना सीखा हुआ कौशल है, व्यक्तित्व गुण नहीं। — Brown/U.Texas"),
            ("इम्पोस्टर सिंड्रोम","जितने सक्षम, उतना जानते हैं कि क्या नहीं जानते। मेटाकॉग्निशन, कमजोरी नहीं।"),
            ("असुरक्षित लगाव","62% वयस्कों में असुरक्षित लगाव है। ज्यादातर को कभी पता नहीं चला। — Ainsworth"),
            ("बर्नआउट","बर्नआउट कमजोरी नहीं — यह प्रमाण है कि आपने बहुत लंबे समय तक बहुत कुछ किया।"),
        ]),
    },
    "RU": {
        "brand": "Даниэла Коэльо · Исследователь поведения человека",
        "cta":   "▶ Подписаться: @psidanicoelho",
        "sleep": ("528Hz ГЛУБОКИЙ СОН", "#050515", "#818CF8", [
            ("Тревожная привязанность","Тревожная привязанность гиперактивирует миндалину во сне — руминация в 3 ночи. Биология, не слабость. — Ainsworth"),
            ("Кортизол и бессонница","Хроническая тревога повышает кортизол и подавляет мелатонин. Цикл за 40% бессонницы. — Sapolsky"),
            ("Травма и сон","Непроработанная травма нарушает циклы быстрого сна. Тело репетирует угрозы во сне. — van der Kolk"),
            ("Скрытый нарциссизм","Самый опасный нарцисс не кажется высокомерным. Он кажется главной жертвой. — Malkin/Harvard"),
            ("Зависимость от одобрения","Лайки активируют ту же систему вознаграждения, что и кокаин. Переменный коэффициент. — Skinner"),
        ]),
        "prime": ("963Hz ОСВОБОЖДЕНИЕ", "#120008", "#FB7185", [
            ("Газлайтинг","Когда вы доверяете их реальности больше, чем своей, газлайтинг уже сработал. — Freyd/Oregon"),
            ("Здоровые границы","Говорить нет без вины — это навык, а не черта характера. — Brown/U.Texas"),
            ("Синдром самозванца","Чем вы компетентнее, тем больше знаете, чего не знаете. Метапознание, не слабость."),
            ("Небезопасная привязанность","62% взрослых имеют небезопасную привязанность. Большинство не знали. — Ainsworth"),
            ("Выгорание","Выгорание — не слабость, а доказательство того, что вы слишком долго делали слишком много."),
        ]),
    },
    "ZH": {
        "brand": "行为研究员 达妮埃拉·科埃略",
        "cta":   "▶ 订阅: @psidanicoelho",
        "sleep": ("528Hz 深度睡眠", "#050515", "#818CF8", [
            ("焦虑型依恋","焦虑型依恋在睡眠中过度激活杏仁核——解释凌晨3点的反刍。是生物学，不是软弱。— Ainsworth"),
            ("皮质醇与失眠","慢性焦虑升高皮质醇并抑制褪黑素。40%失眠背后的循环。— Sapolsky"),
            ("创伤与睡眠","未处理的创伤扰乱深睡周期。身体在睡眠中演练威胁。— van der Kolk"),
            ("隐性自恋","最危险的自恋者并不显得傲慢。他们看起来像最大的受害者。— Malkin/Harvard"),
            ("认可成瘾","点赞激活与可卡因相同的奖赏回路。可变比率——最易成瘾。— Skinner"),
        ]),
        "prime": ("963Hz 解放", "#120008", "#FB7185", [
            ("煤气灯操纵","当你更相信他们的现实而非自己时，操纵已经奏效。— Freyd/Oregon"),
            ("健康界限","无愧疚地说不是习得的技能，而非性格特质。— Brown/U.Texas"),
            ("冒名顶替综合征","你越有能力，越知道自己不知道什么。元认知，不是软弱。"),
            ("不安全依恋","62%的成年人有不安全依恋。大多数人从不知道。— Ainsworth"),
            ("倦怠","倦怠不是软弱——而是你太久尝试太多的证据。"),
        ]),
    },
}

def select_stream(lang):
    tz = TZ_OFFSETS.get(lang, 0)
    h = (datetime.now(timezone.utc) + timedelta(hours=tz)).hour
    return "prime" if 6 <= h < 23 else "sleep"

def gen_audio(hz, mins=30):
    out = TMP / f"aud_{hz}.aac"
    if out.exists() and out.stat().st_size > 50000: return out
    dur = mins * 60
    hz2 = hz + 4
    cmd = ["ffmpeg", "-y",
        "-f","lavfi","-i",f"sine=frequency={hz}:duration={dur}",
        "-f","lavfi","-i",f"sine=frequency={hz2}:duration={dur}",
        "-f","lavfi","-i",f"anoisesrc=color=pink:duration={dur}",
        "-filter_complex",
        "[0:a]volume=0.035[l];[1:a]volume=0.035[r];[2:a]volume=0.004[p];"
        "[l][r]amerge=inputs=2[bin];[bin][p]amix=inputs=2:duration=longest[out]",
        "-map","[out]","-c:a","aac","-b:a","192k","-ar","44100", str(out)]
    subprocess.run(cmd, capture_output=True, timeout=120)
    return out if out.exists() else None

def get_img(topic, color, seed):
    p = (f"masterpiece, ultra HD cinematic dark {color} background, {topic} psychology concept, "
         f"aurora borealis healing light particles, no text no people, calming 8k detail")
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(p[:380])}?model=flux&width={W}&height={H}&seed={seed}&nologo=true"
    try:
        r = requests.get(url, timeout=60)
        if r.status_code == 200 and len(r.content) > 10000: return r.content
    except: pass
    return None

def make_slide(img_p, hz_str, tema, insight, tc, brand, cta, greeting, idx, total, out):
    lines = textwrap.wrap(insight, 42)[:2]
    l1 = (lines[0] if lines else "").replace("'", r"\'")
    l2 = (lines[1] if len(lines) > 1 else "").replace("'", r"\'")
    brand_e = brand.replace("'", r"\'")
    hz_e    = hz_str.replace("'", r"\'")
    cta_e   = cta.replace("'", r"\'")
    greet_e = greeting.replace("'", r"\'")
    pw = max(4, int(W * idx / max(total, 1)))

    vf = (
        f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
        f"colorchannelmixer=rr=0.6:gg=0.6:bb=0.6,"
        # Header bar
        f"drawbox=y=0:color=black@0.9:width=iw:height=70:t=fill,"
        # Footer bar
        f"drawbox=y=ih-72:color=black@0.93:width=iw:height=72:t=fill,"
        # Progress bar (colored)
        f"drawbox=y=ih-4:color={tc}@0.9:width={pw}:height=4:t=fill,"
        # LIVE indicator
        f"drawbox=x=12:y=18:color=#EF4444:width=10:height=10:t=fill,"
        f"drawtext=text='LIVE':fontsize=13:fontcolor=white:x=28:y=14:bold=1,"
        # Hz label (top center)
        f"drawtext=text='{hz_e}':fontsize=17:fontcolor={tc}:x=(w-text_w)/2:y=14:bold=1:shadowcolor=black:shadowx=1:shadowy=1,"
        # Greeting (top right)
        f"drawtext=text='{greet_e}':fontsize=13:fontcolor=#94A3B8:x=w-text_w-14:y=16,"
        # Topic
        f"drawtext=text='{tema[:38]}':fontsize=15:fontcolor={tc}@0.9:x=(w-text_w)/2:y=h*0.36:shadowcolor=black:shadowx=1:shadowy=1,"
        # Line 1
        f"drawtext=text='{l1}':fontsize=25:fontcolor=white:x=(w-text_w)/2:y=h*0.43:bold=1:shadowcolor=#000:shadowx=2:shadowy=2,"
    )
    if l2:
        vf += f"drawtext=text='{l2}':fontsize=25:fontcolor=white:x=(w-text_w)/2:y=h*0.43+38:bold=1:shadowcolor=#000:shadowx=2:shadowy=2,"
    # CTA subscribe (destaque amarelo)
    vf += (
        f"drawtext=text='{cta_e}':fontsize=15:fontcolor=#F59E0B:x=(w-text_w)/2:y=ih-52:bold=1:shadowcolor=black:shadowx=1:shadowy=1,"
        f"drawtext=text='{brand_e}':fontsize=11:fontcolor=#64748B:x=(w-text_w)/2:y=ih-28"
    )

    cmd = ["ffmpeg","-y","-loop","1","-i",str(img_p),"-vf",vf,
           "-t","60","-c:v","libx264","-preset","fast","-tune","stillimage",
           "-pix_fmt","yuv420p","-r","30","-an", str(out)]
    subprocess.run(cmd, capture_output=True, timeout=180)
    return out.exists() and out.stat().st_size > 10000

def run():
    if not STREAM_KEY:
        print(f"ERRO: YOUTUBE_STREAM_KEY não configurado"); return

    lang_data = CONTENT.get(LANG_CODE, CONTENT["EN"])
    sk        = select_stream(LANG_CODE)
    hz_str, color, tc, items = lang_data[sk]
    brand     = lang_data["brand"]
    cta       = lang_data["cta"]
    greeting  = get_greeting(LANG_CODE)

    hz_num = 528 if "528" in hz_str else 963
    print(f"=== 🌍 LIVE {LANG_CODE} | {hz_str} | {greeting} ===")

    audio = gen_audio(hz_num)
    slides, concat_f = [], TMP / f"pl_{LANG_CODE.lower()}.txt"

    for i in range(3):
        tema, insight = items[i % len(items)]
        seed = int(hashlib.md5(f"{LANG_CODE}_{sk}_{i}".encode()).hexdigest()[:8], 16)
        img_data = get_img(tema, color, seed)
        if not img_data: continue
        img_p = TMP / f"bg_{seed}.jpg"; img_p.write_bytes(img_data)
        sl = TMP / f"sl_{sk}_{i}.mp4"
        if make_slide(img_p, hz_str, tema, insight, tc, brand, cta, greeting, i, len(items), sl):
            slides.append(sl)
            print(f"  ✅ [{i+1}] {tema[:40]}")
        time.sleep(2)

    if not slides: print("Sem slides gerados"); return
    with open(concat_f,"w") as f: [f.write(f"file '{s.resolve()}'\n") for s in slides]

    audio_src = (["-stream_loop","-1","-i",str(audio)] if audio and audio.exists()
                 else ["-f","lavfi","-i",f"sine=frequency={hz_num}:duration=999999"])

    proc = subprocess.Popen([
        "ffmpeg","-y",
        "-f","concat","-safe","0","-stream_loop","-1","-i",str(concat_f),
        *audio_src,
        "-c:v","libx264","-preset","veryfast","-tune","stillimage",
        "-b:v","3000k","-maxrate","3000k","-bufsize","6000k",
        "-g","60","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","192k","-ar","44100","-ac","2",
        "-f","flv", RTMP_URL
    ])

    def bg(start=3):
        idx=start
        while proc.poll() is None:
            time.sleep(55)
            tema, insight = items[idx % len(items)]
            greet = get_greeting(LANG_CODE)
            seed = int(hashlib.md5(f"{LANG_CODE}_{sk}_{idx}".encode()).hexdigest()[:8], 16)
            img_data = get_img(tema, color, seed)
            if img_data:
                img_p = TMP/f"bg_{seed}.jpg"; img_p.write_bytes(img_data)
                sl = TMP/f"sl_{sk}_{idx}.mp4"
                if make_slide(img_p, hz_str, tema, insight, tc, brand, cta, greet, idx%len(items), len(items), sl):
                    with open(concat_f,"a") as f: f.write(f"file '{sl.resolve()}'\n")
                    print(f"  + {tema[:35]}")
            for old in sorted(TMP.glob(f"sl_{sk}_*.mp4"))[:-6]: old.unlink(missing_ok=True)
            idx += 1

    threading.Thread(target=bg, daemon=True).start()
    try: proc.wait()
    except KeyboardInterrupt: proc.terminate()

if __name__ == "__main__":
    run()
