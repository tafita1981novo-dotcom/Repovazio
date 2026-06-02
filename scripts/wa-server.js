/**
 * wa-server.js v2 — GitHub Actions persistent server
 * Baileys latest + configurações atualizadas para compatibilidade 2025
 */
const {
  default: makeWASocket,
  DisconnectReason,
  useMultiFileAuthState,
  fetchLatestBaileysVersion,
  makeCacheableSignalKeyStore,
  PHONENUMBER_MCC,
  Browsers
} = require("@whiskeysockets/baileys");
const { Boom }    = require("@hapi/boom");
const { createClient } = require("@supabase/supabase-js");
const fetch       = require("node-fetch");
const fs          = require("fs");
const path        = require("path");
const pino        = require("pino");
const ws          = require("ws");

const SB_URL     = process.env.SUPABASE_URL;
const SB_KEY     = process.env.SUPABASE_SERVICE_KEY;
const WEBHOOK    = process.env.WEBHOOK_URL || "https://repovazio.vercel.app/api/wa-webhook";
const WH_SECRET  = process.env.WEBHOOK_SECRET || "";
const SESSION    = "/tmp/wa-session";
const BUCKET     = "wa-session";

const sb = createClient(SB_URL, SB_KEY, { realtime: { transport: ws } });
const logger = pino({ level: "warn" });

// ── Estado global ─────────────────────────────────────────────────────────────
let reconnectCount = 0;
let isConnected = false;

// ── Supabase: carregar sessão ─────────────────────────────────────────────────
async function loadSession() {
  console.log("📥 Carregando sessão do Supabase...");
  fs.mkdirSync(SESSION, { recursive: true });
  try {
    const { data: files } = await sb.storage.from(BUCKET).list("creds");
    if (!files || files.length === 0) {
      console.log("   Sem sessão salva — vai gerar QR");
      return;
    }
    for (const f of files) {
      const { data } = await sb.storage.from(BUCKET).download(`creds/${f.name}`);
      if (data) {
        const buf = Buffer.from(await data.arrayBuffer());
        fs.writeFileSync(path.join(SESSION, f.name), buf);
      }
    }
    console.log(`   ✅ ${files.length} arquivo(s) de sessão carregados`);
  } catch (e) {
    console.log("   ⚠️  Erro ao carregar sessão:", e.message);
  }
}

// ── Supabase: salvar sessão ───────────────────────────────────────────────────
async function saveSession() {
  if (!fs.existsSync(SESSION)) return;
  const files = fs.readdirSync(SESSION);
  for (const f of files) {
    try {
      const content = fs.readFileSync(path.join(SESSION, f));
      await sb.storage.from(BUCKET).upload(`creds/${f}`, content, {
        contentType: "application/octet-stream",
        upsert: true
      });
    } catch (e) {}
  }
  console.log(`💾 Sessão salva`);
}

// ── Supabase: publicar QR ─────────────────────────────────────────────────────
async function publishQR(qr) {
  try {
    const QRCode = require("qrcode");
    // Gerar QR de alta resolução
    const dataUrl = await QRCode.toDataURL(qr, {
      scale: 10,
      margin: 2,
      color: { dark: "#000000", light: "#FFFFFF" }
    });
    await sb.from("wa_status").update({
      qr_base64:  dataUrl,
      connected:  false,
      updated_at: new Date().toISOString()
    }).eq("id", "singleton");
    console.log(`📱 QR publicado (${new Date().toLocaleTimeString('pt-BR')} BRT)`);
  } catch (e) {
    console.log("⚠️  Erro ao publicar QR:", e.message);
  }
}

// ── Supabase: marcar conectado ────────────────────────────────────────────────
async function markConnected(name, num) {
  isConnected = true;
  await sb.from("wa_status").update({
    qr_base64:  null,
    connected:  true,
    phone_name: name || "",
    phone_num:  num  || "",
    updated_at: new Date().toISOString()
  }).eq("id", "singleton");
  console.log(`✅ CONECTADO: ${name} (${num})`);
}

// ── Webhook ───────────────────────────────────────────────────────────────────
async function sendWebhook(data) {
  try {
    const r = await fetch(WEBHOOK, {
      method: "POST",
      headers: { "Content-Type": "application/json", "apikey": WH_SECRET },
      body: JSON.stringify({ event: "messages.upsert", data }),
      timeout: 30000
    });
    const b = await r.json().catch(() => ({}));
    if (b.saved?.length) console.log(`🔔 Salvo: ${b.saved.join(", ")}`);
  } catch (e) {
    console.log("⚠️  Webhook:", e.message);
  }
}

// ── Main ──────────────────────────────────────────────────────────────────────
async function start() {
  await loadSession();

  const { version, isLatest } = await fetchLatestBaileysVersion();
  console.log(`🚀 Baileys v${version.join(".")} (latest: ${isLatest})`);

  const { state, saveCreds } = await useMultiFileAuthState(SESSION);

  const sock = makeWASocket({
    version,
    logger,
    auth: {
      creds: state.creds,
      keys:  makeCacheableSignalKeyStore(state.keys, logger)
    },
    printQRInTerminal: true,       // mostra no log do Actions também
    syncFullHistory: false,
    markOnlineOnConnect: false,
    generateHighQualityLinkPreview: false,
    browser: Browsers.ubuntu("Chrome"),
    connectTimeoutMs: 60_000,
    keepAliveIntervalMs: 25_000,
    retryRequestDelayMs: 2000,
    maxMsgRetryCount: 3,
    getMessage: async () => undefined
  });

  // ── Conexão ──────────────────────────────────────────────────────────────────
  sock.ev.on("connection.update", async ({ connection, lastDisconnect, qr }) => {

    if (qr) {
      console.log(`📱 Novo QR gerado [tentativa ${reconnectCount + 1}]`);
      await publishQR(qr);
    }

    if (connection === "open") {
      reconnectCount = 0;
      const me = sock.user;
      await markConnected(me?.name || me?.notify || "Desconhecido", me?.id || "");
      await saveSession();
    }

    if (connection === "close") {
      isConnected = false;
      const statusCode = (lastDisconnect?.error instanceof Boom)
        ? lastDisconnect.error.output.statusCode : 0;
      const reason = DisconnectReason;

      console.log(`🔌 Conexão fechada — código: ${statusCode}`);

      // Marcar desconectado
      await sb.from("wa_status").update({
        connected:  false,
        updated_at: new Date().toISOString()
      }).eq("id", "singleton");

      if (statusCode === reason.loggedOut) {
        console.log("❌ Deslogado — limpando sessão");
        try {
          if (fs.existsSync(SESSION)) {
            fs.readdirSync(SESSION).forEach(f => fs.unlinkSync(path.join(SESSION, f)));
          }
          await sb.storage.from(BUCKET).remove(
            (await sb.storage.from(BUCKET).list("creds")).data?.map(f => `creds/${f.name}`) || []
          );
        } catch(e) {}
        reconnectCount = 0;
        setTimeout(start, 3000);

      } else if (reconnectCount < 10) {
        reconnectCount++;
        const delay = Math.min(reconnectCount * 3000, 15000);
        console.log(`🔄 Reconectando em ${delay/1000}s (tentativa ${reconnectCount}/10)...`);
        setTimeout(start, delay);

      } else {
        console.log("❌ Muitas tentativas. Aguardando 60s...");
        reconnectCount = 0;
        setTimeout(start, 60000);
      }
    }
  });

  // ── Credentials ──────────────────────────────────────────────────────────────
  sock.ev.on("creds.update", async () => {
    await saveCreds();
    await saveSession();
  });

  // ── Mensagens ─────────────────────────────────────────────────────────────────
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
      console.log(`📨 ${msg.pushName||"?"}: ${text.slice(0,80)}`);
      await sendWebhook({
        message: msg.message,
        pushName: msg.pushName || "",
        key: msg.key,
        messageTimestamp: msg.messageTimestamp
      });
    }
  });

  // Keep alive
  setInterval(saveSession, 30 * 60 * 1000);
}

start().catch(e => {
  console.error("❌ Fatal:", e.message);
  process.exit(1);
});
