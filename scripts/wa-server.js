/**
 * scripts/wa-server.js
 * GitHub Actions persistent server — Baileys + Supabase + Vercel webhook
 */
const {
  default: makeWASocket,
  DisconnectReason,
  useMultiFileAuthState,
  fetchLatestBaileysVersion,
  makeCacheableSignalKeyStore,
} = require("@whiskeysockets/baileys");
const { Boom }    = require("@hapi/boom");
const { createClient } = require("@supabase/supabase-js");
const fetch       = require("node-fetch");
const fs          = require("fs");
const path        = require("path");
const pino        = require("pino");
const ws          = require("ws");

const SUPABASE_URL   = process.env.SUPABASE_URL;
const SUPABASE_KEY   = process.env.SUPABASE_SERVICE_KEY;
const WEBHOOK_URL    = process.env.WEBHOOK_URL    || "https://repovazio.vercel.app/api/wa-webhook";
const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET || "";
const SESSION_DIR    = "/tmp/wa-session";
const BUCKET         = "wa-session";

// Supabase com ws explícito (Node 20 fix)
const supabase = createClient(SUPABASE_URL, SUPABASE_KEY, {
  realtime: { transport: ws }
});
const logger = pino({ level: "silent" });

// ── Sessão: download do Supabase Storage ────────────────────────────────────
async function downloadSession() {
  console.log("📥 Carregando sessão...");
  fs.mkdirSync(SESSION_DIR, { recursive: true });
  try {
    const { data: files, error } = await supabase.storage.from(BUCKET).list("session");
    if (error || !files || files.length === 0) {
      console.log("   Sem sessão salva — QR code necessário");
      return;
    }
    for (const f of files) {
      const { data } = await supabase.storage.from(BUCKET).download(`session/${f.name}`);
      if (data) {
        const buf = Buffer.from(await data.arrayBuffer());
        fs.writeFileSync(path.join(SESSION_DIR, f.name), buf);
      }
    }
    console.log(`   ✅ ${files.length} arquivo(s) carregados`);
  } catch (e) {
    console.log("   ⚠️  Erro sessão:", e.message);
  }
}

// ── Sessão: upload para Supabase Storage ────────────────────────────────────
async function uploadSession() {
  if (!fs.existsSync(SESSION_DIR)) return;
  const files = fs.readdirSync(SESSION_DIR);
  for (const f of files) {
    const content = fs.readFileSync(path.join(SESSION_DIR, f));
    await supabase.storage.from(BUCKET).upload(`session/${f}`, content, {
      contentType: "application/octet-stream",
      upsert: true
    });
  }
  console.log(`   💾 Sessão salva (${files.length} arqs)`);
}

// ── Publicar QR code na tabela wa_status ────────────────────────────────────
async function publishQR(qr) {
  try {
    const QRCode = require("qrcode");
    const dataUrl = await QRCode.toDataURL(qr, { scale: 8 });
    await supabase.from("wa_status").update({
      qr_base64: dataUrl,
      connected: false,
      updated_at: new Date().toISOString()
    }).eq("id", "singleton");
    console.log("   📱 QR publicado → repovazio.vercel.app/whatsapp-connect");
  } catch (e) {
    console.log("   ⚠️  QR error:", e.message);
    console.log("   Copie este QR string no https://qr.io :", qr.slice(0,60));
  }
}

// ── Marcar conectado ─────────────────────────────────────────────────────────
async function markConnected(name, num) {
  await supabase.from("wa_status").update({
    qr_base64: null,
    connected: true,
    phone_name: name || "",
    phone_num: num   || "",
    updated_at: new Date().toISOString()
  }).eq("id", "singleton");
  console.log(`   ✅ Conectado: ${name} (${num})`);
}

// ── Disparar webhook Vercel ──────────────────────────────────────────────────
async function dispatchWebhook(msgData) {
  try {
    const resp = await fetch(WEBHOOK_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "apikey": WEBHOOK_SECRET
      },
      body: JSON.stringify({ event: "messages.upsert", data: msgData }),
      timeout: 30000
    });
    const body = await resp.json().catch(() => ({}));
    if (body.saved?.length > 0) {
      console.log(`   🔔 Salvo: ${body.saved.join(", ")}`);
    }
  } catch (e) {
    console.log("   ⚠️  Webhook:", e.message);
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
    browser: ["Claude Knowledge Bot", "Chrome", "1.0.0"]
  });

  sock.ev.on("connection.update", async ({ connection, lastDisconnect, qr }) => {
    if (qr) {
      console.log("📱 QR Code disponível...");
      await publishQR(qr);
    }
    if (connection === "close") {
      const code = (lastDisconnect?.error instanceof Boom)
        ? lastDisconnect.error.output.statusCode : 0;
      console.log(`🔌 Conexão fechada (${code})`);
      if (code !== DisconnectReason.loggedOut) {
        setTimeout(start, 5000);
      } else {
        process.exit(1);
      }
    }
    if (connection === "open") {
      const me = sock.user;
      await markConnected(me?.name || me?.notify || "", me?.id || "");
      await uploadSession();
    }
  });

  sock.ev.on("creds.update", async () => {
    await saveCreds();
    await uploadSession();
  });

  sock.ev.on("messages.upsert", async ({ messages, type }) => {
    if (type !== "notify") return;
    for (const msg of messages) {
      if (msg.key.fromMe) continue;
      const text =
        msg.message?.conversation ||
        msg.message?.extendedTextMessage?.text ||
        msg.message?.imageMessage?.caption ||
        msg.message?.videoMessage?.caption || "";
      if (!text) continue;
      console.log(`📨 ${msg.pushName || "?"}: ${text.slice(0, 70)}`);
      await dispatchWebhook({
        message: msg.message,
        pushName: msg.pushName || "",
        key: msg.key,
        messageTimestamp: msg.messageTimestamp
      });
    }
  });

  // Salva sessão a cada 30min
  setInterval(uploadSession, 30 * 60 * 1000);

  console.log("🚀 Servidor ativo — aguardando mensagens...");
  console.log(`   Status: repovazio.vercel.app/whatsapp-connect`);
}

start().catch(err => {
  console.error("❌ Fatal:", err.message);
  process.exit(1);
});
