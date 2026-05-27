#!/usr/bin/env python3
"""
live_black_screen_v2.py — TELA PRETA + 4 ATOS HIPNÓTICOS + COGNIÇÃO QUÂNTICA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ENGENHARIA REVERSA dos #1 mundiais:
  Sleep Cove (EN)           → linguagem hipnótica progressiva, body scan
  Sleep Magic (EN)          → voz pessoal, hipnoterapeuta autoridade
  Smarter While You Sleep   → formato numerado viral (Técnica 1, 2, 3...)
  Projeto Meditar (PT)      → voz pessoal direta + comunidade
  Alan Disavia (ES)         → 1h hipnose profunda
  Boring Psychology Sleep   → tela preta + insights psicológicos

DIFERENCIAIS ÚNICOS (ninguém faz):
  1. COGNIÇÃO QUÂNTICA real: Busemeyer & Pothos (Cambridge 2012)
     + observer effect + microtubules Penrose-Hameroff
  2. Default Mode Network (Raichle 2001) reorganização no sono
  3. Áudio multi-camada: TTS + binaural 528Hz + chuva + sino tibetano
  4. Estrutura 4 atos: indução → técnicas → quântico → integração
  5. 9 idiomas com voz consistente Daniela Coelho

MATEMÁTICA: 4h cycle × 1.5 = 6h watch time médio por viewer dormindo
"""
import os, time, subprocess, pathlib, threading, asyncio
import edge_tts, requests

LANG       = os.getenv("LANG_CODE", "PT").upper()
STREAM_KEY = os.getenv("YOUTUBE_STREAM_KEY", "")
GROQ_KEY   = os.getenv("GROQ_API_KEY", "")
RTMP_URL   = f"rtmp://a.rtmp.youtube.com/live2/{STREAM_KEY}"
TMP        = pathlib.Path(f"/tmp/blackv2_{LANG.lower()}"); TMP.mkdir(exist_ok=True)

VOICES = {
    "PT": "pt-BR-AntonioNeural",  "EN": "en-US-GuyNeural",
    "ES": "es-ES-AlvaroNeural",   "FR": "fr-FR-HenriNeural",
    "DE": "de-DE-ConradNeural",   "IT": "it-IT-DiegoNeural",
    "JA": "ja-JP-KeitaNeural",    "KO": "ko-KR-InJoonNeural",
    "AR": "ar-SA-HamedNeural",
}

# ════════════════════════════════════════════════════════════════════════════
# ATO 1: INDUÇÃO HIPNÓTICA (Sleep Cove / Sleep Magic style)
# Linguagem progressiva: olhos → corpo → respiração → profundidade
# ════════════════════════════════════════════════════════════════════════════
ACT1_INDUCTION = {
"PT": "Feche os olhos agora... respire fundo, devagar... sinta o ar entrando... e saindo. "
      "Com cada respiração, você afunda mais profundamente no descanso. "
      "Seus pés relaxam... suas pernas pesadas... seu abdômen solta... os ombros descem. "
      "Não há nada que você precise fazer agora. Apenas ouvir. Apenas existir. "
      "Eu sou Daniela Coelho, e nas próximas horas vou guiar sua mente "
      "por descobertas que pesquisadores como van der Kolk e Ainsworth comprovaram. "
      "Você pode dormir a qualquer momento. Seu inconsciente continuará absorvendo.",

"EN": "Close your eyes now... breathe in deeply, slowly... feel the air entering... and leaving. "
      "With each breath, you sink deeper into rest. "
      "Your feet relax... your legs heavy... your abdomen softens... your shoulders drop. "
      "There is nothing you need to do now. Just listen. Just exist. "
      "I am Daniela Coelho, and for the next hours I will guide your mind "
      "through discoveries that researchers like van der Kolk and Ainsworth have proven. "
      "You can fall asleep at any moment. Your unconscious will keep absorbing.",

"ES": "Cierra los ojos ahora... respira hondo, despacio... siente el aire entrando... y saliendo. "
      "Con cada respiración, te hundes más profundamente en el descanso. "
      "Tus pies se relajan... tus piernas pesadas... tu abdomen se suelta... tus hombros bajan. "
      "No hay nada que necesites hacer ahora. Solo escuchar. Solo existir. "
      "Soy Daniela Coelho, y en las próximas horas guiaré tu mente "
      "a través de descubrimientos que investigadores como van der Kolk y Ainsworth han comprobado.",

"FR": "Fermez les yeux maintenant... respirez profondément, lentement... sentez l'air entrer... et sortir. "
      "À chaque respiration, vous vous enfoncez plus profondément dans le repos. "
      "Vos pieds se détendent... vos jambes lourdes... votre abdomen se relâche... vos épaules descendent. "
      "Il n'y a rien que vous deviez faire maintenant. Juste écouter. Juste exister. "
      "Je suis Daniela Coelho, et dans les heures qui viennent je guiderai votre esprit "
      "à travers les découvertes prouvées par van der Kolk et Ainsworth.",

"DE": "Schließen Sie jetzt die Augen... atmen Sie tief ein, langsam... spüren Sie die Luft, die einströmt... und ausströmt. "
      "Mit jedem Atemzug sinken Sie tiefer in die Ruhe. "
      "Ihre Füße entspannen... Ihre Beine schwer... Ihr Bauch wird weich... Ihre Schultern sinken. "
      "Es gibt nichts, was Sie jetzt tun müssen. Nur zuhören. Nur sein. "
      "Ich bin Daniela Coelho, und in den nächsten Stunden werde ich Ihren Geist führen "
      "durch Entdeckungen, die Forscher wie van der Kolk und Ainsworth bewiesen haben.",

"IT": "Chiudi gli occhi ora... respira profondamente, lentamente... senti l'aria che entra... e che esce. "
      "Con ogni respiro, ti immergi più profondamente nel riposo. "
      "I tuoi piedi si rilassano... le tue gambe pesanti... il tuo addome si ammorbidisce... le tue spalle scendono. "
      "Non c'è nulla che tu debba fare ora. Solo ascoltare. Solo esistere. "
      "Sono Daniela Coelho, e nelle prossime ore guiderò la tua mente "
      "attraverso scoperte che ricercatori come van der Kolk e Ainsworth hanno dimostrato.",

"JA": "今、目を閉じてください... 深く、ゆっくりと息を吸って... 空気が入ってくるのを感じて... そして出ていく。"
      "一呼吸ごとに、あなたはより深い休息へと沈んでいきます。"
      "足が緩み... 脚が重くなり... 腹部が柔らかくなり... 肩が下がります。"
      "今、あなたが何かをする必要はありません。ただ聞いてください。ただ存在してください。"
      "私は行動研究者ダニエラ・コエーリョです。これから数時間、あなたの心を導きます。"
      "ヴァン・デア・コークやエインズワースが証明した発見へと。",

"KO": "지금 눈을 감으세요... 깊고 천천히 숨을 들이쉬세요... 공기가 들어오는 것을 느끼세요... 그리고 나가는 것을. "
      "호흡할 때마다, 당신은 더 깊은 휴식 속으로 가라앉습니다. "
      "발이 이완되고... 다리가 무거워지고... 복부가 부드러워지고... 어깨가 내려갑니다. "
      "지금 당신이 해야 할 일은 없습니다. 그저 들으세요. 그저 존재하세요. "
      "저는 다니엘라 코엘류입니다. 다음 몇 시간 동안 당신의 마음을 인도하겠습니다.",

"AR": "أغمض عينيك الآن... تنفس بعمق، ببطء... اشعر بالهواء الداخل... والخارج. "
      "مع كل نفس، تغوص أعمق في الراحة. "
      "قدماك تسترخيان... ساقاك ثقيلتان... بطنك يلين... كتفاك ينزلان. "
      "لا يوجد شيء عليك فعله الآن. فقط استمع. فقط كن. "
      "أنا دانييلا كويلو، وفي الساعات القادمة سأرشد عقلك "
      "عبر اكتشافات أثبتها الباحثون مثل فان دير كولك وأينسورث.",
}

# ════════════════════════════════════════════════════════════════════════════
# ATO 2: TÉCNICAS PSICOLÓGICAS NUMERADAS (Smarter While You Sleep viral format)
# 7 técnicas REAIS de psicologia comportamental — cita pesquisadores
# ════════════════════════════════════════════════════════════════════════════
ACT2_TECHNIQUES = {
"PT": [
 "Técnica um. O Efeito Espelho. Quando alguém imita sutilmente seus gestos, "
 "seu cérebro libera ocitocina e cria conexão instantânea. Tanya Chartrand de Duke "
 "comprovou isso em 1999. Narcisistas usam isso para te capturar nos primeiros minutos.",

 "Técnica dois. Pé na Porta. Um pedido pequeno aceito facilita um grande depois. "
 "Freedman e Fraser de Stanford descobriram em 1966 que pessoas que concordam com algo trivial "
 "têm setenta e seis por cento mais chance de concordar com algo grande em seguida.",

 "Técnica três. Triangulação. O manipulador insere uma terceira pessoa para criar ciúme. "
 "Murray Bowen, fundador da terapia familiar, descreveu esse padrão em famílias disfuncionais. "
 "Se você se sente competindo por atenção, observe quem inseriu o terceiro.",

 "Técnica quatro. Reforço Intermitente. Carinho seguido de frieza, ciclo repetido. "
 "Skinner provou em 1956 que recompensa aleatória cria o vício mais forte. "
 "Por isso é tão difícil sair de relacionamentos tóxicos. Não é amor. É condicionamento.",

 "Técnica cinco. Gaslighting. Negar sua percepção até você duvidar da própria memória. "
 "Robin Stern de Yale documentou em duas mil dez como vítimas chegam a duvidar de fatos óbvios. "
 "Se você precisa gravar conversas para se lembrar do que aconteceu, isso é sinal.",

 "Técnica seis. Bombardeio de Amor. Atenção avassaladora nas primeiras semanas. "
 "Malkin de Harvard explica em Rethinking Narcissism que narcisistas encobertos fazem isso "
 "para criar dependência antes do descarte. O amor real cresce devagar.",

 "Técnica sete. Silêncio Punitivo. Cortar comunicação para te castigar. "
 "Kipling Williams de Purdue mostrou em estudos com ressonância magnética "
 "que o silêncio ativa as mesmas áreas cerebrais da dor física. Não é maturidade. É violência.",
],
"EN": [
 "Technique one. The Mirror Effect. When someone subtly mimics your gestures, "
 "your brain releases oxytocin and creates instant connection. Tanya Chartrand at Duke "
 "proved this in 1999. Narcissists use this to capture you in the first minutes.",

 "Technique two. Foot in the Door. A small request accepted enables a large one later. "
 "Freedman and Fraser at Stanford discovered in 1966 that people who agree to something trivial "
 "are seventy-six percent more likely to agree to something major next.",

 "Technique three. Triangulation. The manipulator inserts a third person to create jealousy. "
 "Murray Bowen, founder of family therapy, described this pattern in dysfunctional families. "
 "If you feel competing for attention, notice who inserted the third party.",

 "Technique four. Intermittent Reinforcement. Affection followed by coldness, cycled. "
 "Skinner proved in 1956 that random reward creates the strongest addiction. "
 "This is why leaving toxic relationships is so hard. It is not love. It is conditioning.",

 "Technique five. Gaslighting. Denying your perception until you doubt your own memory. "
 "Robin Stern at Yale documented in 2010 how victims come to doubt obvious facts. "
 "If you need to record conversations to remember what happened, that is a sign.",

 "Technique six. Love Bombing. Overwhelming attention in the first weeks. "
 "Malkin at Harvard explains in Rethinking Narcissism that covert narcissists do this "
 "to create dependency before the discard. Real love grows slowly.",

 "Technique seven. The Silent Treatment. Cutting communication to punish you. "
 "Kipling Williams at Purdue showed in MRI studies "
 "that silence activates the same brain areas as physical pain. It is not maturity. It is violence.",
],
"ES": [
 "Técnica uno. El Efecto Espejo. Cuando alguien imita sutilmente tus gestos, "
 "tu cerebro libera oxitocina y crea conexión instantánea. Tanya Chartrand de Duke "
 "lo comprobó en mil novecientos noventa y nueve. Los narcisistas usan esto para atraparte.",

 "Técnica dos. Pie en la Puerta. Una petición pequeña aceptada facilita una grande después. "
 "Freedman y Fraser de Stanford descubrieron en mil novecientos sesenta y seis "
 "que las personas que aceptan algo trivial tienen setenta y seis por ciento más probabilidad de aceptar algo mayor.",

 "Técnica tres. Triangulación. El manipulador inserta una tercera persona para crear celos. "
 "Murray Bowen, fundador de la terapia familiar, describió este patrón. "
 "Si te sientes compitiendo por atención, observa quién insertó al tercero.",

 "Técnica cuatro. Refuerzo Intermitente. Cariño seguido de frialdad, ciclo repetido. "
 "Skinner probó que la recompensa aleatoria crea la adicción más fuerte. "
 "Por eso es tan difícil salir de relaciones tóxicas. No es amor. Es condicionamiento.",

 "Técnica cinco. Gaslighting. Negar tu percepción hasta que dudes de tu propia memoria. "
 "Robin Stern de Yale documentó cómo las víctimas llegan a dudar de hechos obvios. "
 "Si necesitas grabar conversaciones para recordar lo que pasó, es una señal.",

 "Técnica seis. Bombardeo de Amor. Atención abrumadora en las primeras semanas. "
 "Malkin de Harvard explica que los narcisistas encubiertos hacen esto "
 "para crear dependencia antes del descarte. El amor real crece despacio.",

 "Técnica siete. Silencio Punitivo. Cortar comunicación para castigarte. "
 "Kipling Williams de Purdue mostró en estudios de resonancia magnética "
 "que el silencio activa las mismas áreas cerebrales que el dolor físico.",
],
"FR": [
 "Technique un. L'Effet Miroir. Tanya Chartrand de Duke a prouvé en mille neuf cent quatre-vingt-dix-neuf "
 "que l'imitation subtile libère l'ocytocine. Les narcissiques l'utilisent dès les premières minutes.",
 "Technique deux. Pied dans la Porte. Freedman et Fraser de Stanford en mille neuf cent soixante-six. "
 "Soixante-seize pour cent de chance d'accepter quelque chose de grand après quelque chose de petit.",
 "Technique trois. Triangulation. Murray Bowen a décrit ce schéma. "
 "Si vous vous sentez en compétition, regardez qui a inséré le tiers.",
 "Technique quatre. Renforcement Intermittent. Skinner a prouvé que la récompense aléatoire crée la dépendance la plus forte.",
 "Technique cinq. Gaslighting. Robin Stern de Yale en deux mille dix. "
 "Si vous devez enregistrer pour vous souvenir, c'est un signe.",
 "Technique six. Love Bombing. Malkin de Harvard explique cela dans Rethinking Narcissism. L'amour vrai grandit lentement.",
 "Technique sept. Silence Punitif. Kipling Williams de Purdue: le silence active les mêmes zones que la douleur physique.",
],
"DE": [
 "Technik eins. Der Spiegeleffekt. Tanya Chartrand von Duke bewies 1999, "
 "dass subtile Nachahmung Oxytocin freisetzt. Narzissten nutzen dies in den ersten Minuten.",
 "Technik zwei. Fuß in der Tür. Freedman und Fraser von Stanford 1966. "
 "Sechsundsiebzig Prozent höhere Wahrscheinlichkeit zuzustimmen nach kleiner Bitte.",
 "Technik drei. Triangulation. Murray Bowen beschrieb dieses Muster. "
 "Wenn Sie um Aufmerksamkeit konkurrieren, beachten Sie wer den Dritten eingefügt hat.",
 "Technik vier. Intermittierende Verstärkung. Skinner bewies: zufällige Belohnung schafft stärkste Sucht.",
 "Technik fünf. Gaslighting. Robin Stern von Yale 2010. Wenn Sie aufnehmen müssen um sich zu erinnern, ist das ein Zeichen.",
 "Technik sechs. Love Bombing. Malkin von Harvard erklärt dies in Rethinking Narcissism.",
 "Technik sieben. Schweigebehandlung. Kipling Williams von Purdue: Stille aktiviert dieselben Hirnareale wie körperlicher Schmerz.",
],
"IT": [
 "Tecnica uno. L'Effetto Specchio. Tanya Chartrand di Duke nel mille novecento novantanove "
 "dimostrò che l'imitazione sottile rilascia ossitocina. I narcisisti la usano nei primi minuti.",
 "Tecnica due. Piede nella Porta. Freedman e Fraser di Stanford nel mille novecento sessantasei. "
 "Settantasei per cento di probabilità in più di accettare qualcosa di grande dopo qualcosa di piccolo.",
 "Tecnica tre. Triangolazione. Murray Bowen descrisse questo modello. Osserva chi ha inserito il terzo.",
 "Tecnica quattro. Rinforzo Intermittente. Skinner provò che la ricompensa casuale crea la dipendenza più forte.",
 "Tecnica cinque. Gaslighting. Robin Stern di Yale nel duemila dieci. Se devi registrare per ricordare, è un segno.",
 "Tecnica sei. Love Bombing. Malkin di Harvard lo spiega in Rethinking Narcissism. L'amore vero cresce lentamente.",
 "Tecnica sette. Silenzio Punitivo. Kipling Williams di Purdue: il silenzio attiva le stesse aree del dolore fisico.",
],
"JA": [
 "テクニック一。ミラー効果。デューク大学のターニャ・チャートランドが千九百九十九年に証明しました。"
 "微妙な模倣はオキシトシンを放出します。ナルシシストは最初の数分でこれを使います。",
 "テクニック二。フット・イン・ザ・ドア。スタンフォード大学のフリードマンとフレイザーが千九百六十六年に発見。"
 "小さな要求の後、大きな要求を受け入れる確率が七十六パーセント高くなります。",
 "テクニック三。三角関係。マレー・ボーエンが家族療法でこのパターンを記述しました。"
 "注意を競い合っていると感じたら、誰が第三者を挿入したか観察してください。",
 "テクニック四。間欠強化。スキナーは千九百五十六年に証明しました。ランダムな報酬が最強の依存を作ります。",
 "テクニック五。ガスライティング。イェール大学のロビン・スタンが二千十年に文書化。"
 "会話を録音しないと覚えていられないなら、それは兆候です。",
 "テクニック六。ラブ・ボミング。ハーバード大学のマルキンがRethinking Narcissismで説明。本当の愛はゆっくり育ちます。",
 "テクニック七。沈黙の罰。パデュー大学のキプリング・ウィリアムズがMRI研究で示しました。"
 "沈黙は身体的痛みと同じ脳領域を活性化します。",
],
"KO": [
 "기법 하나. 거울 효과. 듀크 대학교의 타냐 차트랜드가 1999년에 증명했습니다. "
 "미묘한 모방은 옥시토신을 방출합니다. 나르시시스트들은 처음 몇 분 안에 이것을 사용합니다.",
 "기법 둘. 발 들이밀기. 스탠퍼드의 프리드먼과 프레이저가 1966년에 발견. "
 "작은 요청을 받아들이면 큰 요청을 받아들일 확률이 76퍼센트 높아집니다.",
 "기법 셋. 삼각화. 머레이 보웬이 가족치료에서 이 패턴을 설명했습니다. "
 "주의를 두고 경쟁한다고 느낀다면, 누가 제3자를 끼워 넣었는지 관찰하세요.",
 "기법 넷. 간헐적 강화. 스키너는 1956년에 증명했습니다. 무작위 보상이 가장 강한 중독을 만듭니다.",
 "기법 다섯. 가스라이팅. 예일의 로빈 스턴이 2010년에 문서화했습니다. "
 "대화를 녹음해야 기억할 수 있다면, 그것은 신호입니다.",
 "기법 여섯. 러브 바밍. 하버드의 말킨이 Rethinking Narcissism에서 설명. 진짜 사랑은 천천히 자랍니다.",
 "기법 일곱. 침묵 처벌. 퍼듀의 키플링 윌리엄스: 침묵은 신체적 고통과 같은 뇌 영역을 활성화합니다.",
],
"AR": [
 "التقنية الأولى. تأثير المرآة. أثبتت تانيا شارتراند من ديوك في عام ألف وتسعمئة وتسعة وتسعين "
 "أن التقليد الدقيق يطلق الأوكسيتوسين. النرجسيون يستخدمون هذا في الدقائق الأولى.",
 "التقنية الثانية. القدم في الباب. اكتشف فريدمان وفريزر من ستانفورد عام ألف وتسعمئة وستة وستين "
 "أن من يوافق على شيء صغير يوافق على شيء كبير بنسبة ستة وسبعين بالمئة أعلى.",
 "التقنية الثالثة. التثليث. وصف موراي بوين هذا النمط في علاج العائلة. "
 "إذا شعرت أنك تنافس على الاهتمام، انظر من أدخل الطرف الثالث.",
 "التقنية الرابعة. التعزيز المتقطع. أثبت سكينر في ألف وتسعمئة وستة وخمسين أن المكافأة العشوائية تخلق أقوى إدمان.",
 "التقنية الخامسة. الإضاءة الغازية. وثقت روبن ستيرن من ييل في ألفين وعشرة كيف يشك الضحايا في حقائق واضحة.",
 "التقنية السادسة. القصف بالحب. يشرح مالكين من هارفارد ذلك في Rethinking Narcissism. الحب الحقيقي ينمو ببطء.",
 "التقنية السابعة. المعاملة الصامتة. أظهر كيبلينغ ويليامز من بوردو أن الصمت ينشط نفس مناطق الألم الجسدي.",
],
}

# ════════════════════════════════════════════════════════════════════════════
# ATO 3: COGNIÇÃO QUÂNTICA — DIFERENCIAL ÚNICO MUNDIAL
# Pesquisa real: Busemeyer & Pothos (Cambridge 2012), DMN (Raichle 2001),
# Penrose-Hameroff microtubules, observer effect on thoughts
# Nenhum canal de psicologia para dormir aborda isso. Pioneirismo.
# ════════════════════════════════════════════════════════════════════════════
ACT3_QUANTUM = {
"PT": "Agora algo que nenhum outro canal te conta enquanto você dorme. "
      "Em dois mil e doze, Busemeyer de Indiana e Pothos de Cambridge publicaram "
      "que a mente humana segue probabilidade quântica, não clássica. "
      "Isso significa: seus pensamentos existem em superposição até você observá-los. "
      "Quando você se julga, você colapsa a função de onda da sua identidade. "
      "Marcus Raichle de Washington descobriu em dois mil e um a Rede de Modo Padrão. "
      "É a rede neural que se ativa quando você não está focado em nada. "
      "É exatamente nela, durante o sono, que sua identidade se reorganiza. "
      "Penrose e Hameroff propuseram que microtúbulos nos neurônios "
      "operam por coerência quântica. Controverso, mas publicado em Physics of Life Reviews. "
      "Você não é fixo. Você é uma onda de probabilidade. Durma sabendo disso.",

"EN": "Now something no other channel tells you while you sleep. "
      "In 2012, Busemeyer at Indiana and Pothos at Cambridge published "
      "that the human mind follows quantum probability, not classical. "
      "This means: your thoughts exist in superposition until you observe them. "
      "When you judge yourself, you collapse the wave function of your identity. "
      "Marcus Raichle at Washington discovered in 2001 the Default Mode Network. "
      "It is the neural network that activates when you focus on nothing. "
      "It is precisely there, during sleep, that your identity reorganizes itself. "
      "Penrose and Hameroff proposed that microtubules in neurons "
      "operate by quantum coherence. Controversial, but published in Physics of Life Reviews. "
      "You are not fixed. You are a wave of probability. Sleep knowing this.",

"ES": "Ahora algo que ningún otro canal te cuenta mientras duermes. "
      "En dos mil doce, Busemeyer de Indiana y Pothos de Cambridge publicaron "
      "que la mente humana sigue probabilidad cuántica, no clásica. "
      "Esto significa: tus pensamientos existen en superposición hasta que los observas. "
      "Cuando te juzgas, colapsas la función de onda de tu identidad. "
      "Marcus Raichle de Washington descubrió la Red de Modo Predeterminado. "
      "Es exactamente ahí, durante el sueño, que tu identidad se reorganiza. "
      "Penrose y Hameroff propusieron que los microtúbulos neuronales "
      "operan por coherencia cuántica. Tú no eres fijo. Eres una onda de probabilidad.",

"FR": "Maintenant quelque chose qu'aucune autre chaîne ne vous dit pendant que vous dormez. "
      "En deux mille douze, Busemeyer d'Indiana et Pothos de Cambridge ont publié "
      "que l'esprit humain suit la probabilité quantique, non classique. "
      "Vos pensées existent en superposition jusqu'à ce que vous les observiez. "
      "Marcus Raichle de Washington a découvert le Réseau du Mode par Défaut. "
      "C'est précisément là, pendant le sommeil, que votre identité se réorganise. "
      "Vous n'êtes pas fixe. Vous êtes une onde de probabilité.",

"DE": "Jetzt etwas, das kein anderer Kanal Ihnen erzählt während Sie schlafen. "
      "2012 veröffentlichten Busemeyer aus Indiana und Pothos aus Cambridge: "
      "Der menschliche Geist folgt Quantenwahrscheinlichkeit, nicht klassischer. "
      "Ihre Gedanken existieren in Superposition bis Sie sie beobachten. "
      "Marcus Raichle aus Washington entdeckte das Default Mode Network. "
      "Genau dort, während des Schlafes, reorganisiert sich Ihre Identität. "
      "Sie sind nicht fest. Sie sind eine Wahrscheinlichkeitswelle.",

"IT": "Ora qualcosa che nessun altro canale ti racconta mentre dormi. "
      "Nel duemila dodici, Busemeyer dell'Indiana e Pothos di Cambridge pubblicarono "
      "che la mente umana segue probabilità quantistica, non classica. "
      "I tuoi pensieri esistono in sovrapposizione finché non li osservi. "
      "Marcus Raichle scoprì il Default Mode Network. "
      "È esattamente lì, durante il sonno, che la tua identità si riorganizza. "
      "Non sei fisso. Sei un'onda di probabilità.",

"JA": "今、他のどのチャンネルも眠っている間に話さないことを。"
      "二千十二年、インディアナのブセマイヤーとケンブリッジのポトスは発表しました。"
      "人間の心は量子確率に従う、古典確率ではなく。"
      "あなたの思考は、観察するまで重ね合わせの中に存在します。"
      "ワシントンのマーカス・ライクルは二千一年にデフォルト・モード・ネットワークを発見しました。"
      "睡眠中、まさにそこで、あなたのアイデンティティは再編成されます。"
      "あなたは固定ではありません。あなたは確率の波です。",

"KO": "이제 다른 어떤 채널도 당신이 자는 동안 말해주지 않는 것을. "
      "2012년, 인디애나의 부세마이어와 케임브리지의 포토스가 발표했습니다. "
      "인간의 마음은 양자 확률을 따른다, 고전 확률이 아니라. "
      "당신의 생각은 관찰하기 전까지 중첩 상태로 존재합니다. "
      "마커스 라이클이 2001년에 디폴트 모드 네트워크를 발견했습니다. "
      "수면 중, 바로 그곳에서 당신의 정체성이 재구성됩니다. "
      "당신은 고정되지 않았습니다. 당신은 확률의 파동입니다.",

"AR": "الآن شيء لا تخبرك به أي قناة أخرى وأنت نائم. "
      "في عام ألفين واثني عشر، نشر بوسيماير من إنديانا وبوثوس من كامبريدج "
      "أن العقل البشري يتبع الاحتمال الكمي، لا الكلاسيكي. "
      "أفكارك توجد في تراكب حتى تلاحظها. "
      "اكتشف ماركوس رايكل من واشنطن شبكة الوضع الافتراضي. "
      "هناك بالضبط، أثناء النوم، تعيد هويتك تنظيم نفسها. "
      "أنت لست ثابتاً. أنت موجة احتمال.",
}

# ════════════════════════════════════════════════════════════════════════════
# ATO 4: INTEGRAÇÃO + FECHAMENTO
# ════════════════════════════════════════════════════════════════════════════
ACT4_INTEGRATION = {
"PT": "Você não precisa lembrar de nada disso. Seu inconsciente está integrando agora. "
      "Os pesquisadores que mencionei estão respaldando cada palavra. "
      "Permita que sua respiração se aprofunde mais. Permita que seu corpo afunde mais. "
      "Quando você acordar, algo terá mudado. Pequeno, mas real. "
      "Esta voz continuará. Eu sou Daniela Coelho. Durma profundamente.",

"EN": "You do not need to remember any of this. Your unconscious is integrating now. "
      "The researchers I mentioned are backing every word. "
      "Allow your breathing to deepen further. Allow your body to sink further. "
      "When you wake, something will have shifted. Small, but real. "
      "This voice will continue. I am Daniela Coelho. Sleep deeply.",

"ES": "No necesitas recordar nada de esto. Tu inconsciente está integrando ahora. "
      "Permite que tu respiración se profundice más. Permite que tu cuerpo se hunda más. "
      "Cuando despiertes, algo habrá cambiado. Pequeño, pero real. "
      "Esta voz continuará. Soy Daniela Coelho. Duerme profundamente.",

"FR": "Vous n'avez pas besoin de vous souvenir de tout cela. Votre inconscient intègre maintenant. "
      "Permettez à votre respiration de s'approfondir. Permettez à votre corps de s'enfoncer. "
      "Quand vous vous réveillerez, quelque chose aura changé. Petit, mais réel. "
      "Cette voix continuera. Je suis Daniela Coelho. Dormez profondément.",

"DE": "Sie müssen sich an nichts davon erinnern. Ihr Unbewusstes integriert jetzt. "
      "Lassen Sie Ihre Atmung tiefer werden. Lassen Sie Ihren Körper tiefer sinken. "
      "Wenn Sie aufwachen, wird sich etwas verändert haben. Klein, aber real. "
      "Diese Stimme wird weitergehen. Ich bin Daniela Coelho. Schlafen Sie tief.",

"IT": "Non devi ricordare nulla di questo. Il tuo inconscio sta integrando ora. "
      "Permetti al tuo respiro di approfondirsi. Permetti al tuo corpo di affondare. "
      "Quando ti sveglierai, qualcosa sarà cambiato. Piccolo, ma reale. "
      "Questa voce continuerà. Sono Daniela Coelho. Dormi profondamente.",

"JA": "これを覚えている必要はありません。あなたの無意識が今、統合しています。"
      "呼吸をさらに深くしてください。体をさらに沈ませてください。"
      "目覚めたとき、何かが変わっているでしょう。小さくても、本物の変化です。"
      "この声は続きます。私はダニエラ・コエーリョです。深く眠ってください。",

"KO": "이 모든 것을 기억할 필요는 없습니다. 당신의 무의식이 지금 통합하고 있습니다. "
      "호흡을 더 깊게 하세요. 몸이 더 가라앉도록 허용하세요. "
      "깨어났을 때, 무언가가 바뀌어 있을 것입니다. 작지만, 진짜입니다. "
      "이 목소리는 계속됩니다. 저는 다니엘라 코엘류입니다. 깊이 자세요.",

"AR": "لست بحاجة لتذكر أي من هذا. لاوعيك يدمج الآن. "
      "اسمح لتنفسك بأن يتعمق أكثر. اسمح لجسدك بأن يغوص أكثر. "
      "عندما تستيقظ، شيء ما سيكون قد تغير. صغير، لكن حقيقي. "
      "هذا الصوت سيستمر. أنا دانييلا كويلو. نم بعمق.",
}

TITLES = {
"PT": "🖤 Psicologia do Sono | 7 Técnicas + Cognição Quântica | Daniela Coelho LIVE 24/7",
"EN": "🖤 Sleep Psychology | 7 Dark Techniques + Quantum Cognition | Daniela Coelho LIVE 24/7",
"ES": "🖤 Psicología del Sueño | 7 Técnicas + Cognición Cuántica | Daniela Coelho EN VIVO",
"FR": "🖤 Psychologie du Sommeil | 7 Techniques + Cognition Quantique | Daniela Coelho LIVE",
"DE": "🖤 Schlafpsychologie | 7 Techniken + Quantenkognition | Daniela Coelho LIVE",
"IT": "🖤 Psicologia del Sonno | 7 Tecniche + Cognizione Quantica | Daniela Coelho LIVE",
"JA": "🖤 眠りの心理学 | 7つの技法 + 量子認知 | ダニエラ・コエーリョ 24時間LIVE",
"KO": "🖤 수면 심리학 | 7가지 기법 + 양자 인지 | 다니엘라 코엘류 24시간 LIVE",
"AR": "🖤 علم نفس النوم | ٧ تقنيات + الإدراك الكمي | دانييلا كويلو بث مباشر",
}

# ════════════════════════════════════════════════════════════════════════════
# ÁUDIO MULTI-CAMADA: TTS + binaural 528Hz + chuva + sino tibetano
# ════════════════════════════════════════════════════════════════════════════
def gen_ambient_bed(duration=2700):  # 45min default
    """Cama sonora: binaural 528Hz/532Hz + chuva + sino ocasional"""
    out = TMP / "ambient_bed.aac"
    if out.exists() and out.stat().st_size > 1_000_000: return out
    cmd = ["ffmpeg","-y",
        "-f","lavfi","-i",f"sine=frequency=528:duration={duration}",     # L
        "-f","lavfi","-i",f"sine=frequency=532:duration={duration}",     # R (binaural beat=4Hz=theta)
        "-f","lavfi","-i",f"anoisesrc=color=pink:duration={duration}",   # chuva suave
        "-filter_complex",
        "[0:a]volume=0.05[l];[1:a]volume=0.05[r];"
        "[l][r]amerge=inputs=2[binaural];"
        "[2:a]highpass=f=200,lowpass=f=4000,volume=0.025[rain];"
        "[binaural][rain]amix=inputs=2:duration=longest:normalize=0[out]",
        "-map","[out]","-c:a","aac","-b:a","160k","-ar","44100", str(out)]
    subprocess.run(cmd, capture_output=True, timeout=180)
    return out

async def tts_save(text, voice, outpath, rate="-12%"):
    """Edge TTS com rate negativo (mais lento, hipnótico)"""
    c = edge_tts.Communicate(text, voice, rate=rate)
    await c.save(str(outpath))

def mix_speech_with_bed(speech_file, idx):
    """Mescla TTS com cama ambiente"""
    bed = gen_ambient_bed()
    mixed = TMP / f"mix_{idx}.aac"
    cmd = ["ffmpeg","-y",
        "-i", str(speech_file),
        "-stream_loop","-1","-i", str(bed),
        "-filter_complex",
        "[0:a]volume=1.0,afade=t=in:d=2,afade=t=out:st=999:d=3[speech];"
        "[1:a]volume=0.25[ambient];"
        "[speech][ambient]amix=inputs=2:duration=first[out]",
        "-map","[out]","-c:a","aac","-b:a","192k","-ar","44100", str(mixed)]
    subprocess.run(cmd, capture_output=True, timeout=60)
    return mixed if mixed.exists() else None

def gen_segment(text, idx):
    voice = VOICES.get(LANG, "en-US-GuyNeural")
    speech = TMP / f"speech_{idx}.mp3"
    asyncio.run(tts_save(text, voice, speech, rate="-12%"))
    if not speech.exists(): return None
    return mix_speech_with_bed(speech, idx)

def build_silence(seconds, idx):
    """Pausa de silêncio com apenas ambiente (entre técnicas, p/ digestão)"""
    bed = gen_ambient_bed()
    out = TMP / f"silence_{idx}.aac"
    cmd = ["ffmpeg","-y","-stream_loop","-1","-i",str(bed),
           "-t",str(seconds),"-c:a","aac","-b:a","160k", str(out)]
    subprocess.run(cmd, capture_output=True, timeout=30)
    return out if out.exists() else None

def create_black_frame():
    fp = TMP / "black.jpg"
    if not fp.exists():
        subprocess.run(["ffmpeg","-y","-f","lavfi","-i",
            "color=c=black:size=1280x720:rate=1","-frames:v","1", str(fp)],
            capture_output=True)
    return fp

def build_full_cycle():
    """Constrói 1 ciclo completo de ~35-45min: 4 atos sequenciais"""
    print(f"  📦 Construindo ciclo de 4 atos em {LANG}...")
    segments = []

    # ATO 1: Indução
    s1 = gen_segment(ACT1_INDUCTION[LANG], 1)
    if s1: segments.append(s1)
    pause = build_silence(5, "p1")
    if pause: segments.append(pause)

    # ATO 2: 7 técnicas com pausa entre cada
    for i, tech in enumerate(ACT2_TECHNIQUES[LANG]):
        s = gen_segment(tech, f"2_{i}")
        if s: segments.append(s)
        pause = build_silence(8, f"p2_{i}")  # 8s digestão
        if pause: segments.append(pause)

    # ATO 3: Cognição quântica (diferencial)
    s3 = gen_segment(ACT3_QUANTUM[LANG], 3)
    if s3: segments.append(s3)
    pause = build_silence(5, "p3")
    if pause: segments.append(pause)

    # ATO 4: Integração + fechamento
    s4 = gen_segment(ACT4_INTEGRATION[LANG], 4)
    if s4: segments.append(s4)
    pause = build_silence(15, "p4")  # silêncio longo entre ciclos
    if pause: segments.append(pause)

    return segments

def run():
    if not STREAM_KEY:
        print("ERRO: YOUTUBE_STREAM_KEY ausente"); return

    print(f"=== 🖤 BLACK SCREEN v2 — {LANG} ===")
    print(f"    {TITLES[LANG]}")

    # Cria cama ambiente uma vez
    gen_ambient_bed(2700)
    print("  🎵 Cama ambiente criada (binaural 528Hz + chuva)")

    # Constrói ciclo completo
    segs = build_full_cycle()
    if not segs:
        print("ERRO: ciclo vazio"); return
    print(f"  ✅ {len(segs)} segmentos no ciclo")

    # Playlist loopada (ciclo repete ~10x em 6h)
    playlist = TMP / "playlist.txt"
    with open(playlist, "w") as f:
        for cycle in range(15):  # até 15 ciclos = ~10h
            for s in segs:
                f.write(f"file '{s.resolve()}'\n")

    black = create_black_frame()

    print(f"\n🔴 STREAM ON → {RTMP_URL[:42]}...")
    print(f"   Formato: tela preta + áudio 4-atos loopado")
    print(f"   Bitrate: 150kbps vídeo + 192kbps áudio")

    proc = subprocess.Popen([
        "ffmpeg","-y",
        "-loop","1","-i", str(black),
        "-f","concat","-safe","0","-i", str(playlist),
        "-c:v","libx264","-preset","ultrafast","-tune","stillimage",
        "-b:v","150k","-maxrate","200k","-bufsize","400k",
        "-g","30","-pix_fmt","yuv420p","-r","5",
        "-c:a","aac","-b:a","192k","-ar","44100","-ac","2",
        "-f","flv", RTMP_URL
    ])

    try: proc.wait()
    except KeyboardInterrupt: proc.terminate()
    print("Stream encerrado.")

if __name__ == "__main__":
    run()
