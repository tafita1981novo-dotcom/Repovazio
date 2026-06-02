// api/wa-webhook.js — Edge Runtime Vercel
// Evolution API webhook → filtra Claude → YT/IG → Supabase
export const config = { runtime: 'edge' };

const SUPABASE_URL  = process.env.SUPABASE_URL  || process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_KEY  = process.env.SUPABASE_SERVICE_KEY;
const GROQ_API_KEY  = process.env.GROQ_API_KEY;
const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET;

const CLAUDE_KW = ["claude","anthropic","claude.ai","claude 3","claude 4",
  "sonnet","claude opus","claude haiku","claude sonnet"];
const YT_RE = /https?:\/\/(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/)([\w\-]{11})/g;
const IG_RE = /https?:\/\/(?:www\.)?instagram\.com\/(?:p|reel|tv)\/([\w\-]+)\/?/g;

function mentionsClaude(t=""){const l=t.toLowerCase();return CLAUDE_KW.some(k=>l.includes(k));}
function extractLinks(t=""){
  const yt=[...t.matchAll(YT_RE)].map(m=>m[1]);
  const ig=[...t.matchAll(IG_RE)].map(m=>m[1]);
  return{yt:[...new Set(yt)],ig:[...new Set(ig)]};
}

async function sbInsert(item){
  const r = await fetch(`${SUPABASE_URL}/rest/v1/claude_knowledge`,{
    method:"POST",
    headers:{"apikey":SUPABASE_KEY,"Authorization":`Bearer ${SUPABASE_KEY}`,
      "Content-Type":"application/json","Prefer":"return=minimal"},
    body:JSON.stringify(item)
  });
  if(!r.ok) console.error("Supabase error:",await r.text());
}

async function groqSummarize(text,src){
  try {
    const r = await fetch("https://api.groq.com/openai/v1/chat/completions",{
      method:"POST",
      headers:{"Authorization":`Bearer ${GROQ_API_KEY}`,"Content-Type":"application/json"},
      body:JSON.stringify({
        model:"llama-3.3-70b-versatile",
        messages:[{role:"user",content:`Analise este conteúdo sobre Claude (IA da Anthropic).\nRetorne JSON:\n- "resumo": resumo do que fala sobre Claude (2-4 frases)\n- "conceitos_claude": lista de recursos/limitações mencionados\n- "relevancia": nota 1-10\n- "tipo_conteudo": tutorial|comparacao|critica|caso_uso|noticia|discussao|outro\nSe não fala de Claude, relevancia:1.\nFonte: ${src}\nConteúdo: ${text.slice(0,4000)}\nRetorne APENAS JSON.`}],
        response_format:{type:"json_object"},temperature:0.1
      }),
      signal:AbortSignal.timeout(15000)
    });
    if(!r.ok) return null;
    const d = await r.json();
    return JSON.parse(d.choices[0].message.content);
  } catch(e){ return null; }
}

async function getYtTranscript(id){
  try {
    const meta = await fetch(`https://www.youtube.com/oembed?url=https://youtu.be/${id}&format=json`,
      {signal:AbortSignal.timeout(6000)});
    const m = meta.ok ? await meta.json() : {};
    for(const lang of ["pt","en"]){
      const tt = await fetch(`https://www.youtube.com/api/timedtext?lang=${lang}&v=${id}`,
        {signal:AbortSignal.timeout(6000)});
      if(tt.ok){
        const xml = await tt.text();
        const text = xml.replace(/<[^>]+>/g," ").replace(/&amp;/g,"&").replace(/\s+/g," ").trim();
        if(text.length>50) return {title:m.title||"",author:m.author_name||"",transcript:text.slice(0,8000)};
      }
    }
    return{title:m.title||"",author:m.author_name||"",transcript:""};
  } catch(e){ return null; }
}

async function getIgCaption(id){
  try {
    const r = await fetch(`https://www.instagram.com/p/${id}/embed/`,
      {headers:{"User-Agent":"Mozilla/5.0"},signal:AbortSignal.timeout(6000)});
    if(!r.ok) return null;
    const html = await r.text();
    const match = html.match(/<div class="Caption"[^>]*>([\s\S]*?)<\/div>/);
    return match ? match[1].replace(/<[^>]+>/g,"").trim().slice(0,2000) : null;
  } catch(e){ return null; }
}

export default async function handler(req){
  if(req.method==="OPTIONS") return new Response(null,{status:200});
  if(req.method!=="POST") return new Response("Method not allowed",{status:405});

  const secret = req.headers.get("apikey")||req.headers.get("x-webhook-secret");
  if(WEBHOOK_SECRET && secret!==WEBHOOK_SECRET)
    return new Response("Unauthorized",{status:401});

  try {
    const body = await req.json();
    if(body.event!=="messages.upsert")
      return Response.json({ok:true,skip:true});

    const data = body.data;
    if(!data?.message) return Response.json({ok:true,skip:true});

    const msg = data.message;
    const text = msg.conversation||msg.extendedTextMessage?.text||
      msg.imageMessage?.caption||msg.videoMessage?.caption||"";
    const pushName  = data.pushName||"";
    const sender    = data.key?.remoteJid||"unknown";
    const timestamp = new Date((data.messageTimestamp||Date.now()/1000)*1000).toISOString();

    if(!mentionsClaude(text)) return Response.json({ok:true,filtered:true});

    const{yt,ig}=extractLinks(text);
    const saved=[];

    // Texto puro
    const clean=text.replace(/https?:\/\/\S+/g,"").trim();
    if(clean.length>20){
      const s=await groqSummarize(clean,"whatsapp_texto");
      if(s&&s.relevancia>=4){
        await sbInsert({fonte:"whatsapp_texto",url:null,conteudo:clean.slice(0,8000),
          resumo:s.resumo,conceitos:s.conceitos_claude||[],relevancia:s.relevancia,
          tipo_conteudo:s.tipo_conteudo,origem_arquivo:"realtime_webhook",
          autor_wa:pushName||sender,data_wa:timestamp});
        saved.push("texto");
      }
    }

    // YouTube
    for(const id of yt){
      const d=await getYtTranscript(id);
      if(!d) continue;
      const c=[d.title?`Título: ${d.title}`:"",d.author?`Canal: ${d.author}`:"",
        d.transcript||"(sem transcrição)"].filter(Boolean).join("\n\n");
      const s=await groqSummarize(c,"youtube");
      if(s) await sbInsert({fonte:"youtube",url:`https://youtu.be/${id}`,
        conteudo:c.slice(0,10000),resumo:s.resumo,conceitos:s.conceitos_claude||[],
        relevancia:s.relevancia,tipo_conteudo:s.tipo_conteudo,
        origem_arquivo:"realtime_webhook",autor_wa:pushName||sender,data_wa:timestamp});
      saved.push(`yt:${id}`);
    }

    // Instagram
    for(const id of ig){
      const caption=await getIgCaption(id);
      if(!caption) continue;
      const s=await groqSummarize(caption,"instagram");
      if(s) await sbInsert({fonte:"instagram",url:`https://www.instagram.com/p/${id}/`,
        conteudo:caption,resumo:s.resumo,conceitos:s.conceitos_claude||[],
        relevancia:s.relevancia,tipo_conteudo:s.tipo_conteudo,
        origem_arquivo:"realtime_webhook",autor_wa:pushName||sender,data_wa:timestamp});
      saved.push(`ig:${id}`);
    }

    return Response.json({ok:true,saved});
  } catch(err){
    return new Response(JSON.stringify({error:err.message}),
      {status:500,headers:{"Content-Type":"application/json"}});
  }
}
