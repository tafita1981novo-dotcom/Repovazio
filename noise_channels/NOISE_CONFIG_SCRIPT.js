
// ╔═══════════════════════════════════════════════════════════════════╗
// ║  NOISE CHANNELS - SCRIPT DE CONFIGURAÇÃO AUTOMÁTICA              ║
// ║  Cole no DevTools Console no YouTube Studio (F12 → Console)      ║
// ╚═══════════════════════════════════════════════════════════════════╝

const BASE = 'https://raw.githubusercontent.com/tafita1981novo-dotcom/Repovazio/main/noise_assets';

// MAPA: ID do canal → assets corretos
const CANAIS = {
  'UCD4LLFnsiVzA-DeSN6oaUzg': { key: 'dbn',      nome: 'Deep Brown Noise' },
  'UC0mFKp42jfL0ZobYEj7uwUA': { key: 'wnv',      nome: 'White Noise Vault' },
  'UCK3xZDFY84ffNrLEAI1Qmyw': { key: 'adhd',     nome: 'ADHD Focus Noise' },
  'UCZ5pmYA2ESO1vIhtE86l3_Q': { key: 'tinnitus', nome: 'Tinnitus Relief 24h' },
  'UCy4d2yt8eRywJS7PMTDX3xA': { key: 'bsn',      nome: 'Baby Sleep Now' },
  'UCXQ_-FOGTJk17T06gy0bYqQ': { key: 'pink',     nome: 'Pure Pink Noise' },
};

// Detectar canal atual pela URL
function getChannelKey() {
  const m = window.location.href.match(/channel\/(UC[a-zA-Z0-9_-]+)/);
  if (!m) return null;
  const canal = CANAIS[m[1]];
  if (!canal) { console.error('Canal não mapeado:', m[1]); return null; }
  console.log('✅ Canal detectado:', canal.nome, '| Key:', canal.key);
  return canal.key;
}

// Upload de arquivo via file input
async function upload(selector, url, fname, mime) {
  const r = await fetch(url);
  const b = await r.blob();
  const f = new File([b], fname, {type: mime || b.type || 'image/jpeg'});
  const dt = new DataTransfer(); dt.items.add(f);
  
  let inp;
  if (typeof selector === 'number') {
    inp = document.querySelectorAll('input[type="file"]')[selector];
  } else {
    inp = document.querySelector(selector);
  }
  
  if (!inp) { console.error('Input não encontrado:', selector); return 'ERR'; }
  Object.defineProperty(inp, 'files', {value: dt.files, configurable: true});
  inp.dispatchEvent(new Event('change', {bubbles: true}));
  inp.dispatchEvent(new InputEvent('input', {bubbles: true}));
  await new Promise(r => setTimeout(r, 3000));
  return 'OK:' + fname;
}

// Configurar branding (banner + logo + watermark)
async function configureBranding() {
  const key = getChannelKey();
  if (!key) return;
  
  console.log('🚀 Iniciando upload de branding para:', key);
  
  // Aguardar inputs ficarem disponíveis
  await new Promise(r => setTimeout(r, 1000));
  
  const inputs = document.querySelectorAll('input[type="file"]');
  console.log('File inputs encontrados:', inputs.length);
  
  if (inputs.length === 0) {
    console.log('⚠️ Abra studio.youtube.com/channel/ID/editing/profile primeiro!');
    return;
  }
  
  // Upload: banner (idx=0), logo (idx=1), watermark (idx=2)
  const r1 = await upload(0, `${BASE}/${key}_banner.jpg`, `${key}_banner.jpg`);
  console.log('Banner:', r1);
  
  await new Promise(r => setTimeout(r, 2000));
  const r2 = await upload(1, `${BASE}/${key}_logo.jpg`, `${key}_logo.jpg`);
  console.log('Logo:', r2);
  
  await new Promise(r => setTimeout(r, 2000));
  const r3 = await upload(2, `${BASE}/watermark.png`, 'watermark.png', 'image/png');
  console.log('Watermark:', r3);
  
  console.log('✅ Upload concluído! Clique Done em cada modal e depois Publish.');
}

// Configurar descrição multilíngue
async function configureDesc() {
  const key = getChannelKey();
  if (!key) return;
  
  const descs = {
    'dbn': `Brown noise for ADHD, sleep & fan sound. 10h black screen. No ads.
🧠ADHD • 🛌Sleep Fast • 🖤Black Screen • 🌬Fan Sound

🇺🇸Brown noise ADHD sleep fast fan sound 10 hours
🇧🇷Ruído marrom TDAH dormir rápido ventilador 10h
🇩🇪Braunes Rauschen ADHS schlafen Ventilator 10h
🇫🇷Bruit brun TDAH dormir vite ventilateur 10h
🇪🇸Ruido marrón TDAH dormir rápido ventilador 10h
🇯🇵ブラウンノイズ ADHD すぐ眠れる 10時間
🇰🇷갈색소음 ADHD 빠르게잠들기 10시간
🇨🇳棕色噪音 ADHD 快速入睡 10小时
🇸🇦ضجيج بني ADHD نوم سريع 10ساعات
🇮🇳ब्राउन नॉइज़ ADHD जल्दी सोना 10घंटे

📺@WhiteNoiseVault-j5t @ADHDFocusNoise-v2r @RuidoMarrom-p4f`,
    'wnv': `Pure white noise for sleep, study & blocking distractions. 10h black screen.
🛌Sleep Fast • 📚Study • 🖤Black Screen • 👶Baby Sleep

🇺🇸White noise black screen sleep fast study 10 hours
🇧🇷Ruído branco tela preta dormir rápido estudar 10h
🇩🇪Weißes Rauschen schwarzer Bildschirm schlafen lernen 10h
🇫🇷Bruit blanc écran noir dormir vite étude 10h
🇪🇸Ruido blanco pantalla negra dormir rápido estudiar 10h
🇯🇵ホワイトノイズ 黒画面 すぐ眠れる 勉強 10時間
🇰🇷백색소음 블랙스크린 빠르게잠들기 공부 10시간
🇨🇳白噪音 黑屏 快速入睡 学习 10小时
🇸🇦ضجيج أبيض شاشة سوداء نوم سريع دراسة 10ساعات
🇮🇳व्हाइट नॉइज़ ब्लैक स्क्रीन जल्दी सोना 10घंटे

📺@DeepBrownNoise-j6b @BabySleepNow-g7c @TinnitusRelief24h`,
    'adhd': `Brown noise for ADHD focus, hyperfocus & sleep. Like a fan. 10h black screen.
🧠ADHD • 🎯Hyperfocus • 🛌Sleep Fast • 🖤Black Screen

🇺🇸ADHD brown noise focus hyperfocus sleep fast black screen 10 hours
🇧🇷TDAH ruído marrom foco hiperfoco dormir rápido tela preta 10h
🇩🇪ADHS braunes Rauschen Fokus Hyperfokus schlafen 10h
🇫🇷TDAH bruit brun focus hyperfocus dormir vite 10h
🇪🇸TDAH ruido marrón foco hiperfoco dormir rápido 10h
🇯🇵ADHD ブラウンノイズ 集中 過集中 すぐ眠れる 10時間
🇰🇷ADHD 갈색소음 집중 과집중 빠르게잠들기 10시간
🇨🇳ADHD 棕色噪音 专注 过度专注 快速入睡 10小时
🇸🇦ADHD ضجيج بني تركيز نوم سريع 10ساعات
🇮🇳ADHD ब्राउन नॉइज़ ध्यान जल्दी सोना 10घंटे

📺@DeepBrownNoise-j6b @RuidoMarrom-p4f @WhiteNoiseVault-j5t`,
    'tinnitus': `White & pink noise to mask tinnitus & help you sleep fast. 10h black screen.
👂Tinnitus • 🛌Sleep Fast • 🖤Black Screen • 🔇Ear Ringing

🇺🇸Tinnitus relief white noise sleep fast black screen ear ringing 10 hours
🇧🇷Alívio zumbido ruído branco dormir rápido tela preta 10h
🇩🇪Tinnitus Linderung weißes Rauschen Ohrgeräusche schlafen 10h
🇫🇷Acouphènes bruit blanc dormir vite écran noir 10h
🇪🇸Tinnitus alivio ruido blanco dormir rápido pantalla negra 10h
🇯🇵耳鳴り緩和 ホワイトノイズ すぐ眠れる 黒画面 10時間
🇰🇷이명완화 백색소음 빠르게잠들기 블랙스크린 10시간
🇨🇳耳鸣缓解 白噪音 快速入睡 黑屏 10小时
🇸🇦طنين الأذن ضجيج أبيض نوم سريع شاشة سوداء 10ساعات
🇮🇳टिनिटस राहत व्हाइट नॉइज़ जल्दी सोना 10घंटे

📺@PurePinkNoise @WhiteNoiseVault-j5t @DeepBrownNoise-j6b`,
    'bsn': `White & pink noise to help babies and newborns sleep fast. 10h black screen.
👶Newborn • 🛌Sleep Fast • 🖤Black Screen • 🍼Colic Relief

🇺🇸Baby white noise newborn sleep fast colic black screen 10 hours
🇧🇷Ruído branco bebê recém-nascido dormir cólica tela preta 10h
🇩🇪Baby Rauschen Neugeborenes schlafen Koliken schwarzer Bildschirm 10h
🇫🇷Bruit bébé nouveau-né dormir coliques écran noir 10h
🇪🇸Ruido bebé recién nacido dormir cólicos pantalla negra 10h
🇯🇵赤ちゃんノイズ 新生児 すぐ眠れる 黒画面 10時間
🇰🇷아기소음 신생아잠들기 블랙스크린 10시간
🇨🇳婴儿白噪音 新生儿入睡 黑屏 10小时
🇸🇦ضجيج أبيض طفل مولود نوم شاشة سوداء 10ساعات
🇮🇳बेबी नॉइज़ नवजात जल्दी सोना ब्लैक स्क्रीन 10घंटे

📺@WhiteNoiseVault-j5t @PurePinkNoise @TinnitusRelief24h`,
    'pink': `Science-based pink noise for deep sleep, memory & tinnitus. 10h black screen.
🔬Science • 🛌Deep Sleep • 🖤Black Screen • 🧠Memory Boost

🇺🇸Pink noise deep sleep black screen science memory tinnitus 10 hours
🇧🇷Ruído rosa sono profundo tela preta científico memória 10h
🇩🇪Rosa Rauschen Tiefschlaf schwarzer Bildschirm Wissenschaft 10h
🇫🇷Bruit rose sommeil profond écran noir science mémoire 10h
🇪🇸Ruido rosa sueño profundo pantalla negra ciencia 10h
🇯🇵ピンクノイズ 深い睡眠 黒画面 科学 記憶力 10時間
🇰🇷핑크노이즈 깊은수면 블랙스크린 과학 기억력 10시간
🇨🇳粉红噪音 深度睡眠 黑屏 科学 记忆力 10小时
🇸🇦ضجيج وردي نوم عميق شاشة سوداء علم ذاكرة 10ساعات
🇮🇳पिंक नॉइज़ गहरी नींद ब्लैक स्क्रीन विज्ञान 10घंटे

📺@WhiteNoiseVault-j5t @TinnitusRelief24h @BabySleepNow-g7c`,
  };
  
  const desc = descs[key];
  if (!desc) { console.error('Descrição não encontrada para:', key); return; }
  
  // Encontrar o campo de descrição (contenteditable)
  const el = document.querySelector('[contenteditable="true"]');
  if (!el) { console.error('Campo de descrição não encontrado!'); return; }
  
  el.focus();
  el.textContent = '';
  document.execCommand('selectAll', false, null);
  document.execCommand('delete', false, null);
  document.execCommand('insertText', false, desc);
  el.dispatchEvent(new Event('input', {bubbles: true}));
  
  console.log('✅ Descrição configurada! Chars:', desc.length, '/1000');
  console.log('Clique em Publish para salvar.');
}

// Executar tudo automaticamente
async function configureAll() {
  console.log('═══════════════════════════════════');
  console.log('CONFIGURAÇÃO COMPLETA DO CANAL');
  console.log('═══════════════════════════════════');
  
  // 1. Configurar branding
  await configureBranding();
  
  // 2. Configurar descrição (se estiver na aba Profile)
  setTimeout(() => {
    configureDesc();
  }, 2000);
}

// Executar automaticamente
configureAll();

// Funções disponíveis manualmente:
// configureBranding() - faz upload de banner, logo e watermark
// configureDesc()     - preenche descrição com 10 idiomas
// configureAll()      - faz tudo acima
