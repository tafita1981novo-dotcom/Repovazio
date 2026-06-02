
/**
 * scripts/wa-server.js
 * Roda no GitHub Actions como processo persistente (até 6h)
 * Baileys → recebe msgs WhatsApp → dispara webhook → Vercel → Supabase
 * Sessão salva no Supabase Storage (sem QR na reinicialização)
 */
const {
  default: makeWASocket,
  DisconnectReason,
  useMultiFileAuthState,
  fetchLatestBaileysVersion,
  makeCacheableSignalKeyStore,
  makeInMemoryStore
} = require("@whiskeysockets/baileys");
const { Boom } = require("@hapi/boom");
const { createClient } = require("@supabase/supabase-js");
const fetch = require("node-fetch");
const fs   = require("fs");
const path = require("path");
const pino = require("pino");

const SUPABASE_URL    = process.env.SUPABASE_URL;
const SUPABASE_KEY    = process.env.SUPABASE_SERVICE_KEY;
const WEBHOOK_URL     = process.env.WEBHOOK_URL || "https://repovazio.vercel.app/api/wa-webhook";
const WEBHOOK_SECRET  = process.env.WEBHOOK_SECRET;
const SESSION_DIR     = "/tmp/wa-baileys-session";
const SESSION_BUCKET  = "wa-session";

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);
const logger   = pino({ level: "silent" });

// ── Supabase: carregar sessão ────────────────────────────────────────────────
async function downloadSession() {
  console.log("📥 Carregando sessão do Supabase...");
  fs.mkdirSync(SESSION_DIR, { recursive: true });
  try {
    const { data: files } = await supabase.storage.from(SESSION_BUCKET).list("session");
    if (!files || files.length === 0) {
      console.log("   Nenhuma sessão salva. QR code necessário na primeira vez.");
      return;
    }
    for (const f of files) {
      const { data } = await supabase.storage.from(SESSION_BUCKET).download(`session/${f.name}`);
      if (data) {
        const buf = Buffer.from(await data.arrayBuffer());
        fs.writeFileSync(path.join(SESSION_DIR, f.name), buf);
      }
    }
    console.log(`   ✅ ${files.length} arquivo(s) de sessão carregados`);
  } catch (e) {
    console.log("   ⚠️  Erro ao carregar sessão:", e.message);
  }
}

// ── Supabase: salvar sessão ──────────────────────────────────────────────────
async function uploadSession() {
  if (!fs.existsSync(SESSION_DIR)) return;
  const files = fs.readdirSync(SESSION_DIR);
  for (const f of files) {
    const content = fs.readFileSync(path.join(SESSION_DIR, f));
    await supabase.storage.from(SESSION_BUCKET).upload(`session/${f}`, content, {
      contentType: "application/octet-stream",
      upsert: true
    });
  }
  console.log(`   💾 Sessão salva (${files.length} arquivos)`);
}

// ── Supabase: publicar QR code para visualização ─────────────────────────────
async function publishQR(qr) {
  // Converte QR string para base64 PNG via qrcode lib
  try {
    const QRCode = require("qrcode");
    const dataUrl = await QRCode.toDataURL(qr, { scale: 8 });
    await supabase.from("wa_status").update({
      qr_base64:  dataUrl,
      connected:  false,
      updated_at: new Date().toISOString()
    }).eq("id", "singleton");
    console.log("   📱 QR publicado → acesse repovazio.vercel.app/whatsapp-connect");
  } catch (e) {
    console.log("   ⚠️  QR error:", e.message);
    // fallback: só logar o QR como texto
    console.log("   QR string:", qr.slice(0, 50) + "...");
  }
}

// ── Supabase: marcar como conectado ──────────────────────────────────────────
async function markConnected(name, num) {
  await supabase.from("wa_status").update({
    qr_base64:  null,
    connected:  true,
    phone_name: name || "",
    phone_num:  num  || "",
    updated_at: new Date().toISOString()
  }).eq("id", "singleton");
  console.log(`   ✅ Conectado: ${name} (${num})`);
}

// ── Webhook para Vercel ────────────────────────────────────────────────────────
async function dispatchWebhook(msgData) {
  try {
    const resp = await fetch(WEBHOOK_URL, {
      method:  "POST",
      headers: {
        "Content-Type": "application/json",
        "apikey": WEBHOOK_SECRET
      },
      body:    JSON.stringify({ event: "messages.upsert", data: msgData }),
      signal:  AbortSignal.timeout(30000)
    });
    const body = await resp.json().catch(() => ({}));
    console.log(`   🔔 Webhook → ${resp.status} | saved: ${JSON.stringify(body.saved || [])}`);
  } catch (e) {
    console.log("   ⚠️  Webhook error:", e.message);
  }
}

// ── Main ─────────────────────────────────────────────────────────────────────
async function start() {
  await downloadSession();

  const { version } = await fetchLatestBaileysVersion();
  const { state, saveCreds } = await useMultiFileAuthState(SESSION_DIR);

  const sock = makeWASocket({
    version,
    logger,
    auth: {
      creds: state.creds,
      keys:  makeCacheableSignalKeyStore(state.keys, logger)
    },
    printQRInTerminal: false,
    generateHighQualityLinkPreview: false,
    browser: ["Claude Knowledge", "Chrome", "1.0.0"]
  });

  // ── Eventos de conexão ─────────────────────────────────────────────────────
  sock.ev.on("connection.update", async ({ connection, lastDisconnect, qr }) => {
    if (qr) {
      console.log("📱 QR Code gerado — publicando...");
      await publishQR(qr);
    }

    if (connection === "close") {
      const code = (lastDisconnect?.error instanceof Boom)
        ? lastDisconnect.error.output.statusCode
        : 0;
      const shouldReconnect = code !== DisconnectReason.loggedOut;
      console.log(`🔌 Conexão fechada (${code}) — ${shouldReconnect ? "reconectando..." : "deslogado"}`);

      if (shouldReconnect) {
        setTimeout(start, 5000);
      } else {
        // Limpar sessão se deslogado
        await supabase.storage.from(SESSION_BUCKET).remove(
          fs.existsSync(SESSION_DIR)
            ? fs.readdirSync(SESSION_DIR).map(f => `session/${f}`)
            : []
        );
        process.exit(1);
      }
    }

    if (connection === "open") {
      const me = sock.user;
      await markConnected(me?.name || me?.notify || "", me?.id || "");
      await uploadSession();
    }
  });

  // ── Salvar credentials ─────────────────────────────────────────────────────
  sock.ev.on("creds.update", async () => {
    await saveCreds();
    await uploadSession();
  });

  // ── Receber mensagens ──────────────────────────────────────────────────────
  sock.ev.on("messages.upsert", async ({ messages, type }) => {
    if (type !== "notify") return;

    for (const msg of messages) {
      if (msg.key.fromMe) continue; // ignora mensagens próprias

      const text =
        msg.message?.conversation ||
        msg.message?.extendedTextMessage?.text ||
        msg.message?.imageMessage?.caption  ||
        msg.message?.videoMessage?.caption  || "";

      if (!text) continue;

      console.log(`📨 ${msg.pushName || msg.key.remoteJid}: ${text.slice(0, 80)}`);

      // Verifica se menciona Claude (deixa o webhook filtrar, mas log aqui)
      const hasClaude = ["claude","anthropic","sonnet","claude opus","claude haiku"]
        .some(k => text.toLowerCase().includes(k));

      if (hasClaude || true) { // envia tudo, o webhook filtra
        await dispatchWebhook({
          message:          msg.message,
          pushName:         msg.pushName || "",
          key:              msg.key,
          messageTimestamp: msg.messageTimestamp
        });
      }
    }
  });

  // ── Keep alive: salvar sessão a cada 30min ─────────────────────────────────
  setInterval(uploadSession, 30 * 60 * 1000);

  console.log("🚀 WhatsApp server ativo — aguardando mensagens...");
  console.log(`   Webhook: ${WEBHOOK_URL}`);
  console.log("   Status: repovazio.vercel.app/whatsapp-connect");
}

start().catch(err => {
  console.error("❌ Fatal:", err.message);
  process.exit(1);
});
