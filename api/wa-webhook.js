/**
 * api/wa-webhook.js — Vercel Serverless (Next.js)
 * Evolution API webhook → filtra Claude → YT/IG → Supabase
 */
import { createClient } from "@supabase/supabase-js";
import Groq from "groq-sdk";

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_KEY
);
const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

const CLAUDE_KW = ["claude","anthropic","claude.ai","claude 3","claude 4",
  "sonnet","claude opus","claude haiku","claude sonnet"];

const YT_RE = /https?:\/\/(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/)([\w\-]{11})/g;
const IG_RE = /https?:\/\/(?:www\.)?instagram\.com\/(?:p|reel|tv)\/([\w\-]+)\/?/g;

function mentionsClaude(text=""){
  const l = text.toLowerCase();
  return CLAUDE_KW.some(k => l.includes(k));
}
function extractLinks(text=""){
  const yt = [...text.matchAll(YT_RE)].map(m=>m[1]);
  const ig = [...text.matchAll(IG_RE)].map(m=>m[1]);
  return {yt:[...new Set(yt)], ig:[...new Set(ig)]};
}

async function getYoutubeTranscript(videoId){
  try {
    const meta = await fetch(`https://www.youtube.com/oembed?url=https://youtu.be/${videoId}&format=json`,{signal:AbortSignal.timeout(8000)});
    const m = meta.ok ? await meta.json() : {};
    for(const lang of ["pt","en"]){
      const tt = await fetch(`https://www.youtube.com/api/timedtext?lang=${lang}&v=${videoId}`,{signal:AbortSignal.timeout(8000)});
      if(tt.ok){
        const xml = await tt.text();
        const text = xml.replace(/<[^>]+>/g," ").replace(/&amp;/g,"&").replace(/&#39;/g,"'").replace(/\s+/g," ").trim();
        if(text.length>50) return {title:m.title||"",author:m.author_name||"",transcript:text.slice(0,10000)};
      }
    }
    return {title:m.title||"",author:m.author_name||"",transcript:""};
  } catch(e){ return null; }
}

async function getInstagramCaption(postId){
  try {
    const r = await fetch(`https://www.instagram.com/p/${postId}/embed/`,{headers:{"User-Agent":"Mozilla/5.0"},signal:AbortSignal.timeout(8000)});
    if(!r.ok) return null;
    const html = await r.text();
    const m = html.match(/<div class="Caption"[^>]*>([\s\S]*?)<\/div>/);
    return m ? m[1].replace(/<[^>]+>/g,"").trim().slice(0,2000) : null;
  } catch(e){ return null; }
}

async function summarize(text, sourceType){
  try {
    const resp = await groq.chat.completions.create({
      model:"llama-3.3-70b-versatile",
      messages:[{role:"user",content:`Analise este conteúdo sobre Claude (IA da Anthropic).\nRetorne JSON:\n- "resumo": resumo do que fala sobre Claude (2-4 frases)\n- "conceitos_claude": lista de recursos/limitações/casos de uso do Claude mencionados\n- "relevancia": nota 1-10\n- "tipo_conteudo": tutorial|comparacao|critica|caso_uso|noticia|discussao|outro\nSe não fala de Claude, coloque relevancia: 1.\nFonte: ${sourceType}\nConteúdo: ${text.slice(0,4000)}\nRetorne APENAS JSON válido.`}],
      response_format:{type:"json_object"},
      temperature:0.1
    });
    return JSON.parse(resp.choices[0].message.content);
  } catch(e){
    return {resumo:text.slice(0,200),conceitos_claude:[],relevancia:5,tipo_conteudo:"outro"};
  }
}

async function save(item){
  const {error} = await supabase.from("claude_knowledge").insert(item);
  if(error) console.error("Supabase:",error.message);
}

export default async function handler(req, res){
  if(req.method==="OPTIONS") return res.status(200).end();
  if(req.method!=="POST") return res.status(405).json({error:"Method not allowed"});

  const secret = req.headers["apikey"]||req.headers["x-webhook-secret"];
  if(process.env.WEBHOOK_SECRET && secret!==process.env.WEBHOOK_SECRET)
    return res.status(401).json({error:"Unauthorized"});

  try {
    const body = req.body;
    if(body.event!=="messages.upsert") return res.status(200).json({ok:true,skip:true});

    const data = body.data;
    if(!data?.message) return res.status(200).json({ok:true,skip:true});

    const msg = data.message;
    const text = msg.conversation||msg.extendedTextMessage?.text||msg.imageMessage?.caption||msg.videoMessage?.caption||"";
    const sender    = data.key?.remoteJid||"unknown";
    const pushName  = data.pushName||"";
    const timestamp = new Date((data.messageTimestamp||Date.now()/1000)*1000).toISOString();

    console.log(`📨 ${pushName}: ${text.slice(0,80)}`);
    if(!mentionsClaude(text)) return res.status(200).json({ok:true,filtered:true});
    console.log("✅ Menciona Claude!");

    const {yt,ig} = extractLinks(text);
    const saved = [];

    // Texto puro
    const clean = text.replace(/https?:\/\/\S+/g,"").trim();
    if(clean.length>20){
      const s = await summarize(clean,"whatsapp_texto");
      if(s.relevancia>=4){
        await save({fonte:"whatsapp_texto",url:null,conteudo:clean.slice(0,8000),resumo:s.resumo,conceitos:s.conceitos_claude||[],relevancia:s.relevancia,tipo_conteudo:s.tipo_conteudo,origem_arquivo:"realtime_webhook",autor_wa:pushName||sender,data_wa:timestamp});
        saved.push("texto");
      }
    }

    // YouTube
    for(const id of yt){
      const d = await getYoutubeTranscript(id);
      if(!d) continue;
      const c = [d.title?`Título: ${d.title}`:"",d.author?`Canal: ${d.author}`:"",d.transcript||"(sem transcrição)"].filter(Boolean).join("\n\n");
      const s = await summarize(c,"youtube");
      await save({fonte:"youtube",url:`https://youtu.be/${id}`,conteudo:c.slice(0,10000),resumo:s.resumo,conceitos:s.conceitos_claude||[],relevancia:s.relevancia,tipo_conteudo:s.tipo_conteudo,origem_arquivo:"realtime_webhook",autor_wa:pushName||sender,data_wa:timestamp});
      saved.push(`yt:${id}`);
    }

    // Instagram
    for(const id of ig){
      const caption = await getInstagramCaption(id);
      if(!caption) continue;
      const s = await summarize(caption,"instagram");
      await save({fonte:"instagram",url:`https://www.instagram.com/p/${id}/`,conteudo:caption,resumo:s.resumo,conceitos:s.conceitos_claude||[],relevancia:s.relevancia,tipo_conteudo:s.tipo_conteudo,origem_arquivo:"realtime_webhook",autor_wa:pushName||sender,data_wa:timestamp});
      saved.push(`ig:${id}`);
    }

    return res.status(200).json({ok:true,saved});
  } catch(err){
    console.error("Webhook error:",err);
    return res.status(500).json({error:err.message});
  }
}
