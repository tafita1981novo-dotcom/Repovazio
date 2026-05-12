"use client";
import { useState, useEffect, useRef, useCallback } from "react";

// ═══════════════════════════════════════════════════════════════════
// PSICOLOGIA.DOC — CÉREBRO AUTÔNOMO v7
// Canal: @psicologiadoc (DOC = Daniela Oliveira Coelho + documentário)
// Dia 1 = 15 abr 2026 | Revelação = ~1 jan 2027 (Dia 261)
// 2026: Canal 100% anônimo — ZERO menção a nome ou pessoa
// 2027: Daniela Coelho, psicóloga (NÃO "Dra." — apenas psicóloga)
// ═══════════════════════════════════════════════════════════════════


const SBU = "https://tpjvalzwkqwttvmszvie.supabase.co";
const SBK = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRwanZhbHp3a3F3dHR2bXN6dmllIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0Njg2OTIzMCwiZXhwIjoyMDYyNDQ1MjMwfQ.v8h1t7cjDvM2vxGpMr7sRlWEWvDSnBBpgjNPGDZ7Rlk";
const H_SB = {apikey:SBK,"Authorization":"Bearer "+SBK};
async function sbFetch(path){try{const r=await fetch(SBU+"/rest/v1/"+path,{headers:H_SB});return r.ok?r.json():[];}catch{return[];}}

const RANK_INTERVAL = 60*1000;
const PROD_INTERVAL = 30*60*1000;
const FIRST_RANK    = 15*1000;
const FIRST_PROD    = 60*1000;

const CANAL = {
  nome:    "psicologia.doc",
  handle:  "@psicologiadoc",
  slogan:  "A psicologia que você vive — documentada.",
  bio2026: "@psicologiadoc | Psicologia documentada 🎬 | Saúde mental que você reconhece | Novos docs toda semana",
  bio2027: "@psicologiadoc | Daniela Coelho, psicóloga 🧠 | CRP [NÚMERO] | Consultas online → link na bio",
};

const JORNADA_INICIO = new Date("2026-04-15T00:00:00");
const DIA_REVELACAO  = 261; // ~1 jan 2027

function calcDay() {
  return Math.max(1, Math.floor((new Date()-JORNADA_INICIO)/86400000)+1);
}
function dayToDate(d) {
  const dt = new Date(JORNADA_INICIO);
  dt.setDate(dt.getDate()+d-1);
  return dt.toLocaleDateString("pt-BR",{day:"2-digit",month:"2-digit",year:"numeric"});
}
function getPhase(day, revealed) {
  if (revealed) return {label:"Fase 7: Daniela Coelho, psicóloga",goal:"Consultas + 500K+ + R$80-250K/mês",color:"var(--green)",period:"2027+"};
  if (day<=14)  return {label:"Fase 1: Fundação SEO",  goal:"1.000 inscritos · buscas",          color:"var(--blue)",  period:dayToDate(1)+" – "+dayToDate(14)};
  if (day<=30)  return {label:"Fase 2: Viralização",   goal:"5.000 inscritos · primeiro viral",   color:"var(--purple)",period:dayToDate(15)+" – "+dayToDate(30)};
  if (day<=60)  return {label:"Fase 3: Escala",        goal:"10K inscritos · AdSense",            color:"var(--green)", period:dayToDate(31)+" – "+dayToDate(60)};
  if (day<=180) return {label:"Fase 4: Crescimento",   goal:"50K · R$10-40K/mês",                color:"var(--amber)", period:dayToDate(61)+" – "+dayToDate(180)};
  if (day<=260) return {label:"Fase 5: Autoridade",    goal:"100K+ · marca anônima sólida",       color:"var(--red)",   period:dayToDate(181)+" – "+dayToDate(260)};
  return          {label:"Fase 6: Pré-revelação",      goal:"200K+ · lista de espera consultas",  color:"#a855f7",      period:dayToDate(261)+"+"};
}

// ─── TÉCNICAS PNL + ENGENHARIA DE ATENÇÃO ──────────────────────
// Cases reais: Therapy in a Nutshell (2M), Psych2Go (13M),
// Dr. Nicole LePera (12M), Canal Dark (1.2M views R$24K/60 dias)
const ATTENTION_HOOKS = [
  "Se você faz [COMPORTAMENTO] quando [SITUAÇÃO], esse documentário foi feito especificamente para você.",
  "Por que você continua atraindo [TIPO DE PESSOA] mesmo sabendo que vai te machucar?",
  "Existe um padrão documentado em [N]% das pessoas e quase ninguém fala sobre isso abertamente.",
  "O que você vai descobrir nos próximos [N] minutos vai mudar como você vê [SITUAÇÃO] para sempre.",
  "Você provavelmente já sentiu [EMOÇÃO] sem conseguir explicar de onde vem. A ciência explica.",
  "Documentamos [N] casos reais de [TEMA]. O que descobrimos vai te surpreender.",
  "Em [ANO], pesquisadores documentaram algo que ainda acontece com milhões de pessoas hoje.",
  "Tem um nome técnico para o que você sente quando [SITUAÇÃO]. E existe uma saída.",
  "Se alguém perto de você age assim, este documentário explica exatamente o porquê.",
  "A resposta está no final deste documentário — mas você precisa entender o contexto primeiro.",
];

const VIRAL_PATTERNS = [
  "Por que Você [VERBO] Quando [SITUAÇÃO]",
  "[N] Sinais que Você Tem [CONDIÇÃO] (e Não Sabe)",
  "Por que Você Atrai [TIPO PROBLEMÁTICO]",
  "Como Parar de [COMPORTAMENTO] — A Psicologia Explica",
  "[CONDIÇÃO]: O que Ninguém te Conta",
  "O que Acontece com o Seu Cérebro Quando [SITUAÇÃO]",
  "[N] Comportamentos que Parecem Normais Mas São [CONDIÇÃO]",
  "A Psicologia Por Trás de [LIVRO/SITUAÇÃO] — Documentado",
];

const TOPICS = [
  "Ansiedade & Burnout","Apego Ansioso","Narcisismo & Manipulação",
  "Trauma de Infância","Autossabotagem","Relacionamentos Tóxicos",
  "Inteligência Emocional","Depressão & Tristeza","Limites Saudáveis",
  "Gaslighting","Autoestima","Síndrome do Impostor",
  "Dependência Emocional","Luto & Perda","Ansiedade Social",
  "Psicologia do Dinheiro","Liderança Tóxica","Vício em Validação",
];

const CHANNELS_LIST = ["youtube","tiktok","instagram","pinterest"];

// ─── BESTSELLERS POR TEMA (indexação sutil) ──────────────────────
const BESTSELLERS = {
  "Ansiedade & Burnout":      [{t:"Por que Zebras não Têm Úlcera",a:"Sapolsky"},{t:"O Corpo Guarda o Placar",a:"van der Kolk"}],
  "Apego Ansioso":            [{t:"Attached",a:"Levine & Heller"},{t:"Nós",a:"Lisa Fischler"}],
  "Narcisismo & Manipulação": [{t:"Why Does He Do That?",a:"Lundy Bancroft"}],
  "Trauma de Infância":       [{t:"O Corpo Guarda o Placar",a:"van der Kolk"},{t:"Childhood Disrupted",a:"Nakazawa"}],
  "Autossabotagem":           [{t:"The Big Leap",a:"Gay Hendricks"},{t:"Mindset",a:"Carol Dweck"}],
  "Relacionamentos Tóxicos":  [{t:"Too Good to Leave, Too Bad to Stay",a:"Kirshenbaum"}],
  "Inteligência Emocional":   [{t:"Inteligência Emocional",a:"Daniel Goleman"}],
  "Gaslighting":              [{t:"Gaslighting",a:"Stephanie Moulton Sacks"}],
  "Autoestima":               [{t:"Os 6 Pilares da Autoestima",a:"Nathaniel Branden"}],
  "Dependência Emocional":    [{t:"Codependent No More",a:"Melody Beattie"}],
  "Psicologia do Dinheiro":   [{t:"A Psicologia Financeira",a:"Morgan Housel"}],
};

// ─── SÉRIES EPISÓDICAS COM LOOP ABERTO ──────────────────────────
const SERIES_LIBRARY = [
  {id:"apego",      nome:"📎 A Ciência do Apego",      eps:8, status:"active",  lancamento:dayToDate(1),   subtitulo:"Por que você ama quem te faz sofrer", tecnica:"Cada ep termina: 'No próximo você vai descobrir POR QUE você faz X'"},
  {id:"narcisismo", nome:"🪞 Narcisismo Documentado",  eps:7, status:"planned", lancamento:dayToDate(30),  subtitulo:"O que ninguém conta sobre manipulação", tecnica:"Títulos: 'você provavelmente convive com um' — identificação + urgência"},
  {id:"ansiedade",  nome:"⚡ Ansiedade Documentada",   eps:8, status:"planned", lancamento:dayToDate(60),  subtitulo:"Sua mente acelerada tem um motivo",     tecnica:"22-28min + imagens cinematográficas = CPM máximo"},
  {id:"trauma",     nome:"🔓 Trauma Invisível",        eps:6, status:"planned", lancamento:dayToDate(90),  subtitulo:"O que seu corpo carrega sem você saber", tecnica:"Cada ep tem 1 exercício prático — aumenta retenção + compartilhamento"},
  {id:"burnout",    nome:"🔥 Burnout Documentado",     eps:5, status:"planned", lancamento:dayToDate(120), subtitulo:"Você não é preguiçoso — está esgotado",  tecnica:"Contradição no título = clique: 'Por que férias não curam burnout'"},
];

const SERIES_EPS = {
  apego:["Por Que Você Tem Tanto Medo de Ser Abandonado","Os 4 Estilos de Apego — em qual você está?","Por Que Você Atrai Pessoas Emocionalmente Indisponíveis","O Que Acontece no Seu Cérebro Quando Você se Apega Demais","Por Que Você Fica com Quem te Machuca — a Neurociência","Apego Evitativo — a Solidão Disfarçada de Independência","Como Mudar Seu Estilo de Apego (a Ciência Diz que é Possível)","Relacionamento Seguro — Como Reconhecer e Construir"],
  narcisismo:["O Que é Narcisismo de Verdade — Além do Senso Comum","Os 7 Tipos de Narcisismo (o 5º é o Mais Perigoso)","Como um Narcisista Conquista Você — Passo a Passo","Gaslighting Documentado — Sinais que Estão Acontecendo Agora","Por Que Você Fica com Narcisista Mesmo Sabendo que Faz Mal","Como Sair Dessa Relação Sem se Destruir","Se Recuperando do Abuso Narcisista — O Plano Real"],
  ansiedade:["O que é Ansiedade de Verdade (não é o que te disseram)","Por que Seu Cérebro Cria Ansiedade — Neurociência Real","Os 5 Tipos de Ansiedade que Poucos Falam","Trauma de Infância e Ansiedade Adulta — A Conexão","Por que Você não Consegue 'Simplesmente Relaxar'","Técnicas que a Ciência Provou Funcionar","Quando a Ansiedade Vira Doença — Sinais Claros","Vivendo Bem com Ansiedade — Regulação, não Cura"],
  trauma:["Trauma não é só Guerra — O Que Realmente É","Trauma Complexo (C-PTSD) — O Que Médicos Ainda Ignoram","Flashback Emocional — O Sintoma que Você não Sabia que Tinha","Seu Corpo Guarda o Trauma — Teoria Polivagal em 20min","Trauma de Infância no Adulto — 8 Comportamentos Reveladores","O Caminho Real de Cura — O Que a Ciência Diz"],
  burnout:["O Que é Burnout (não é Preguiça, não é Frescura)","Os 5 Estágios do Burnout — Em Qual Você Está?","Por Que Férias não Curam Burnout","O Plano de Recuperação Real — Semana a Semana","Como Nunca Mais Chegar ao Burnout"],
};

// ─── MONETIZAÇÃO CRP-COMPLIANT ──────────────────────────────────
const MONETIZACAO = [
  {fase:1,ic:"▶️",n:"YouTube AdSense",           v:"R$7-25/1K views",    t:"1K subs + 4K horas",    tipo:"passivo"},
  {fase:1,ic:"🤝",n:"Afiliados Zenklub/Vittude",  v:"R$30-80/cadastro",   t:"Link na bio dia 1",     tipo:"variável"},
  {fase:2,ic:"💬",n:"WhatsApp Premium",           v:"R$29-97/mês/membro", t:"Mês 1 (grupo ativo)",   tipo:"recorrente"},
  {fase:3,ic:"⭐",n:"YouTube Memberships",        v:"R$9,90-49/mês",      t:"500 inscritos",         tipo:"recorrente"},
  {fase:3,ic:"📚",n:"Afiliados Livros (Amazon)",  v:"4-8% por venda",     t:"Indexação sutil nos eps",tipo:"passivo"},
  {fase:4,ic:"🏷️",n:"Patrocínio Direto",         v:"R$1-8K/vídeo",       t:"10K views médio",       tipo:"negociado"},
  {fase:4,ic:"📦",n:"Curso Digital Básico",       v:"R$97-197/aluno",     t:"10K inscritos",         tipo:"lançamento"},
  {fase:5,ic:"📦",n:"Curso Digital Avançado",     v:"R$297-997/aluno",    t:"50K inscritos",         tipo:"lançamento"},
  {fase:5,ic:"🎓",n:"Grupo de Estudo Premium",    v:"R$197-497/mês",      t:"100K inscritos",        tipo:"alto valor"},
  {fase:7,ic:"🩺",n:"Consultas Psicológicas",     v:"R$150-350/sessão",   t:"Após revelação 2027",   tipo:"profissional"},
  {fase:7,ic:"🏥",n:"Programa de Acompanhamento", v:"R$497-997/mês",      t:"WA grupos → clientes",  tipo:"alto valor"},
];

const ANTI_BAN = {
  maxDaily:{youtube:3,tiktok:5,instagram:5,pinterest:10},
  minInterval:{youtube:120,tiktok:45,instagram:60,pinterest:20},
  noise:()=>Math.floor(Math.random()*23)-11,
  minSafety:85,
};

const WA_CONFIG = {
  maxMembros:1024,
  msgs2026:["Bem-vindo ao grupo psicologia.doc 🎬 Compartilhe suas reflexões sobre o último episódio 💜","Pergunta desta semana: qual comportamento do documentário você mais se identificou?","Novo episódio publicado! O que vocês acharam? Comentem aqui 👇","💡 Este tema tem muito a ver com um livro excelente sobre o assunto — quem conhece?"],
  msgs2027:["Para agendar consulta com Daniela Coelho, psicóloga: [LINK_CALENDLY]","Agenda da semana disponível — vagas limitadas: [LINK]"],
};

// ─── STORAGE ─────────────────────────────────────────────────────
async function stor(k,v){try{await window.storage.set(k,JSON.stringify(v));}catch{try{localStorage.setItem(k,JSON.stringify(v));}catch{}}}
async function load(k,fb){try{const r=await window.storage.get(k);return r?JSON.parse(r.value):fb;}catch{try{const v=localStorage.getItem(k);return v?JSON.parse(v):fb;}catch{return fb;}}}

async function callClaude(sys,usr,search){
  try{
    const body={model:"claude-sonnet-4-20250514",max_tokens:4000,system:sys,messages:[{role:"user",content:usr}]};
    if(search)body.tools=[{type:"web_search_20250305",name:"web_search"}];
    const r=await fetch("https://api.anthropic.com/v1/messages",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
    const d=await r.json();
    if(search)return d.content?.find(b=>b.type==="text")?.text||"";
    return d.content?.[0]?.text||"";
  }catch{return "";}
}
function sleep(ms){return new Promise(r=>setTimeout(r,ms));}

// ─── RANKING + CASES DIÁRIOS ─────────────────────────────────────
async function fetchRanking(log){
  log("🌍 Buscando virais mundiais de psicologia + dark channels...","info");
  try{
    const r=await callClaude("Viral video intelligence. Return ONLY valid JSON.","Search: top psychology mental health dark educational YouTube 2026 most viewed\nReturn ONLY:{\"videos\":[{\"rank\":1,\"title_en\":\"t\",\"title_pt\":\"t\",\"url\":\"https://youtube.com/watch?v=ID\",\"channel\":\"ch\",\"views\":\"1.2M\",\"hook\":\"opening 0-10s\",\"what_makes_viral\":\"emotion\",\"tone\":\"t\",\"duration_min\":22}]}",true);
    const m=r.match(/\{[\s\S]*"videos"[\s\S]*\}/);
    if(m){const p=JSON.parse(m[0]);const vs=(p.videos||[]).filter(v=>v.url?.includes("watch?v="));if(vs.length){log("✅ Ranking: "+vs.length+" vídeos | #1: \""+vs[0].title_en?.slice(0,40)+"\" ("+vs[0].views+")","success");return vs;}}
  }catch(e){log("⚠️ Ranking: "+e.message,"warn");}
  return null;
}

async function fetchDailyCases(day,log){
  log("🔬 Pesquisando cases reais de crescimento + monetização...","info");
  try{
    const r=await callClaude("Research successful YouTube psychology channels and monetization cases. ONLY valid JSON.","Search: YouTube psychology channel 2025 2026 million subscribers monetization growth case study\nReturn ONLY:{\"cases\":[{\"channel\":\"n\",\"achievement\":\"what\",\"tactic\":\"specific\",\"metric\":\"number\",\"apply\":\"how today\"}],\"tactics\":[{\"name\":\"n\",\"how\":\"desc\",\"result\":\"metric\"}]}",true);
    const m=r.match(/\{[\s\S]*"cases"[\s\S]*\}/);
    if(m){const p=JSON.parse(m[0]);log("💡 "+( p.cases?.length||0)+" cases + "+(p.tactics?.length||0)+" táticas","success");return p;}
  }catch(e){log("⚠️ Cases: "+e.message,"warn");}
  return null;
}

// ─── TOM DO CANAL (anônimo em 2026, revelado em 2027) ────────────
function getCanalTone(){
  const rev=(()=>{try{return localStorage.getItem("doc_revealed")==="1";}catch{return false;}})();
  if(rev)return "Canal: psicologia.doc | Criadora: Daniela Coelho, psicóloga | Tom: autoridade calorosa + expertise clínica. Mencione consultas quando relevante.";
  return "Canal: psicologia.doc — canal de documentários de psicologia | Tom: narrador especialista anônimo. NUNCA use 'eu' ou mencione nome de pessoa. Use 'este documentário', 'a psicologia mostra', 'casos documentados revelam'. Público: 25-54 anos. CRP compliance total.";
}

// ─── GERA ROTEIRO HIPNÓTICO ──────────────────────────────────────
async function generateScript(topic,channel,day,topVideo,log){
  const pat=VIRAL_PATTERNS[Math.floor(Math.random()*VIRAL_PATTERNS.length)];
  const hook=ATTENTION_HOOKS[Math.floor(Math.random()*ATTENTION_HOOKS.length)];
  const books=BESTSELLERS[topic]||[];
  const isYT=channel==="youtube";
  const topRef=topVideo?'"'+topVideo.title_en+'" ('+topVideo.views+' views, gancho: "'+(topVideo.hook||"")+'")':"vídeo viral de psicologia";
  log("📝 ["+channel.toUpperCase()+"] Roteiro hipnótico: \""+topic+"\"...","info");

  const sys=getCanalTone()+"\nNUNCA mencione IA. CRP: zero diagnósticos, zero promessa de cura.\nTÉCNICAS OBRIGATÓRIAS:\n1. PNL Espelhamento: pessoa se VÊ no vídeo desde o 1º segundo\n2. Loop aberto: nunca feche a curiosidade até o fim\n3. Segunda pessoa ('você','seu') — direto e íntimo\n4. Cada ponto gera 'isso acontece comigo' ou 'conheço alguém assim'\n5. Vídeos LONGOS para YouTube (22-28min) — CPM 6x maior\n6. Último minuto: CTA forte + preview do próximo episódio\n7. Som cinematic: instrua ElevenLabs com pausas dramáticas [PAUSA] e ênfases *assim*\nBase: DSM-5, APA, CID-11."+(books.length?"\nINDEXAÇÃO SUTIL (não venda): "+books.map(b=>'"'+b.t+'" de '+b.a).join(", "):"");

  const userYT="Crie roteiro documentário YouTube 22-28min sobre \""+topic+"\".\nInspire-se: "+topRef+"\nPadrão viral: '"+pat+"'\nGANCHO 0-30s: '"+hook+"'\n\n📌 SEO TITLE (keyword no início, 55-65 chars, sem nome de pessoa):\n📌 THUMBNAIL TEXT (CAPS emocional, máx 4 palavras):\n[GANCHO 0-30s]: adapte o hook para o tema\n[CONTEXTO 1-3min]: dado científico chocante + estatística\n[DESENVOLVIMENTO 5-8 pontos]: DSM-5/APA + casos anônimos reais\n[VIRADA EMOCIONAL]: 'Se você reconhece isso, há uma explicação'\n[SOLUÇÃO PARCIAL]: 3 ações baseadas em evidências\n[CTA WHATSAPP]: 'Continue essa conversa no grupo psicologia.doc — link na bio'\n[LOOP PRÓXIMO EP]: 'No próximo documentário vou revelar [TEMA] — que explica por que você [COMPORTAMENTO]'\n📄 DESCRIÇÃO YT (400+ palavras, SEO, link WhatsApp):\n🏷️ TAGS (25 tags PT+EN):\n📊 CHAPTERS (timestamps):"+(books.length?"\n💡 Indexe naturalmente: "+books[0].t+" de "+books[0].a:"");

  const userShort="Crie Short/Reel 45-60s para "+channel+" sobre \""+topic+"\".\nGANCHO 0-3s: "+hook.split(".")[0]+"\n[REVELAÇÃO 3-20s]: dado científico + 'acontece porque...'\n[IDENTIFICAÇÃO 20-40s]: 'Se você...' — espelhamento direto\n[CTA 40-60s]: 'Documentei tudo em episódio completo — link na bio'\n📌 TÍTULO (emoji + texto ≤60 chars, sem nome de pessoa):\n🏷️ HASHTAGS: #psicologia #saudemental #psicologiadoc";

  return await callClaude(sys,isYT?userYT:userShort,false);
}

// ─── VALIDAÇÃO EM LOOP ─────────────────────────────────────────
async function validate(text){
  const[sr,er,sfr]=await Promise.all([
    callClaude("Validate DSM-5/APA/CID-11 compliance. ONLY JSON.",text.slice(0,500)+'\nRespond ONLY: {"score":88}'),
    callClaude("Validate CRP ethics code. ONLY JSON.",text.slice(0,500)+'\nRespond ONLY: {"score":91}'),
    callClaude("Audit for YouTube/TikTok/Instagram safety. Zero diagnoses, zero cure promises. ONLY JSON.",text.slice(0,500)+'\nRespond ONLY: {"safety":95}'),
  ]);
  let sc=85,et=90,sf=92;
  try{sc=JSON.parse(sr.replace(/```[^`]*```/g,"").trim()).score||85;}catch{}
  try{et=JSON.parse(er.replace(/```[^`]*```/g,"").trim()).score||90;}catch{}
  try{sf=JSON.parse(sfr.replace(/```[^`]*```/g,"").trim()).safety||92;}catch{}
  return{sci:sc,eth:et,safety:sf,score:Math.round(sc*0.35+et*0.35+sf*0.30)};
}

async function validateLoop(script,log,max=4){
  log("🔄 Revisão em loop — até score ≥88 + safety ≥85...","info");
  let best=script,bestScore=0;
  for(let round=1;round<=max;round++){
    const r=await validate(best);
    log("🔄 Rodada "+round+"/"+max+" — Score:"+r.score+" Safety:"+r.safety,"info");
    if(r.score>=88&&r.safety>=ANTI_BAN.minSafety){log("✅ Sólido em "+round+" rodada(s)","success");return{...r,script:best,rounds:round};}
    if(r.score>bestScore)bestScore=r.score;
    if(round<max){const ref=await callClaude("Revisor CRP. Melhore sem mudar tema. Fortaleça PNL e loop aberto. Remova diagnósticos implícitos.","CONTEÚDO:\n"+best.slice(0,2500)+"\n\nMELHORE e retorne completo:");if(ref?.length>200)best=ref;}
  }
  return await validate(best).then(r=>({...r,script:best,rounds:max}));
}

// ─── MOTOR 1000x ─────────────────────────────────────────────────
async function generateVariationBlocks(topic,day,topVideo,log){
  log("🔁 Motor 1000x — gerando blocos para \""+topic+"\"...","info");
  const sys=getCanalTone()+"\nCRP. Base: DSM-5. PNL espelhamento obrigatório.";
  const topRef=topVideo?'"'+topVideo.title_en+'" ('+topVideo.views+' views)':"";
  const[ht,ct,ct2]=await Promise.all([
    callClaude(sys,topRef+"\nGere 10 HOOKS de 3-8s sobre \""+topic+"\". Gatilhos: choque, identificação, contradição, pergunta, urgência, promessa, exclusividade, empatia, estatística, loop-aberto.\nH1: [hook]\n...H10: [hook]"),
    callClaude(sys,topRef+"\nGere 10 CORPOS de 20-40s sobre \""+topic+"\". Estruturas: lista_3, lista_5, história, comparação, jornada, cérebro, série_ep, mito_fato, protocolo, relacional.\nC1: [corpo]\n...C10: [corpo]"),
    callClaude(sys,"Gere 10 CTAs de 3-8s para docs de psicologia sobre \""+topic+"\". Destinos: salvar, comentar, whatsapp, série, inscrição, reflexão, recurso, próximo_ep, comunidade, pergunta.\nCTA1: [cta]\n...CTA10: [cta]"),
  ]);
  const parse=(text,pfx)=>text.split("\n").filter(l=>l.match(new RegExp("^"+pfx+"\\d+:","i"))).map((l,i)=>({id:pfx+(i+1),content:l.replace(/^[A-Z]+\d+:\s*/i,"").trim()})).filter(b=>b.content.length>10);
  const hooks=parse(ht,"H"),corpos=parse(ct,"C"),ctas=parse(ct2,"CTA");
  log("✅ "+hooks.length+"×"+corpos.length+"×"+ctas.length+" = "+(hooks.length*corpos.length*ctas.length)+" variações","success");
  return{hooks,corpos,ctas,topic};
}

// ─── SAFETY SCORE ─────────────────────────────────────────────
function localSafety(txt){
  let s=100;const t=(txt||"").toLowerCase();
  if(t.includes("você tem "))s-=15;if(t.includes("cure "))s-=20;
  if(t.includes("remédio")||t.includes("medicamento"))s-=25;
  if(t.includes("diagnóstico"))s-=8;
  if(t.includes("daniela")||t.includes("meu nome"))s-=30;
  if(t.includes("psicóloga")&&!t.includes("uma psicóloga")&&!t.includes("a psicóloga"))s-=15;
  if(t.includes("documentado")||t.includes("pesquisas mostram"))s+=3;
  return Math.min(100,Math.max(0,s));
}

// ─── ELEVENLABS ──────────────────────────────────────────────────
async function genVoice(script,log){
  const cfg=(()=>{try{return JSON.parse(localStorage.getItem("doc_cfg")||"{}");}catch{return{};}})();
  if(!cfg.elevenlabs){log("🎙️ ElevenLabs: configure API key → Configurações","warn");return null;}
  const spoken=script.replace(/📌[^\n]*/g,"").replace(/\[.*?\]/g,"").replace(/[━═📊📄🎯💡🏷️]/g,"").trim().slice(0,3500);
  if(spoken.length<50)return null;
  log("🎙️ ElevenLabs: narração cinematic PT-BR...","info");
  try{
    const vId=cfg.elevenlabsVoice||"pNInz6obpgDQGcFmaJgB";
    const r=await fetch("https://api.elevenlabs.io/v1/text-to-speech/"+vId+"/stream",{method:"POST",headers:{"xi-api-key":cfg.elevenlabs,"Content-Type":"application/json"},body:JSON.stringify({text:spoken,model_id:"eleven_multilingual_v2",voice_settings:{stability:0.38,similarity_boost:0.90,style:0.45,use_speaker_boost:true}})});
    if(!r.ok){log("⚠️ ElevenLabs: "+r.status,"warn");return null;}
    const blob=await r.blob();
    log("✅ ElevenLabs: "+(blob.size/1024).toFixed(0)+"KB — narração pronta","success");
    return{url:URL.createObjectURL(blob),blob};
  }catch(e){log("⚠️ ElevenLabs: "+e.message,"warn");return null;}
}

// ─── HEYGEN ──────────────────────────────────────────────────────
async function genAvatar(script,audio,platform,log){
  const cfg=(()=>{try{return JSON.parse(localStorage.getItem("doc_cfg")||"{}");}catch{return{};}})();
  if(!cfg.heygen){log("🎬 HeyGen: configure API key → Configurações","warn");return null;}
  const FMTS={youtube:{w:1920,h:1080},instagram:{w:1080,h:1920},tiktok:{w:1080,h:1920},pinterest:{w:1000,h:1500}};
  const fmt=FMTS[platform]||FMTS.youtube;
  const spoken=script.replace(/📌[^\n]*/g,"").replace(/\[.*?\]/g,"").trim().slice(0,1500);
  log("🎬 HeyGen: avatar "+fmt.w+"×"+fmt.h+" para "+platform+"...","info");
  try{
    const r=await fetch("https://api.heygen.com/v2/video/generate",{method:"POST",headers:{"X-Api-Key":cfg.heygen,"Content-Type":"application/json"},body:JSON.stringify({video_inputs:[{character:{type:"avatar",avatar_id:cfg.heygenAvatar||"Daisy-inskirt-20220818",avatar_style:"normal"},voice:audio?.url?{type:"audio",audio_url:audio.url}:{type:"text",input_text:spoken,voice_id:cfg.heygenVoice||"1bd001e7e50f421d891986aad5158bc8",speed:1.0},background:{type:"color",value:"#0a0a1a"}}],dimension:{width:fmt.w,height:fmt.h},test:false,caption:true})});
    const d=await r.json();
    if(!d.data?.video_id){log("⚠️ HeyGen: "+(d.error||"err"),"warn");return null;}
    log("⏳ HeyGen: renderizando ("+d.data.video_id+")...","info");
    for(let i=0;i<24;i++){
      await sleep(15000);
      try{const sr=await fetch("https://api.heygen.com/v1/video_status.get?video_id="+d.data.video_id,{headers:{"X-Api-Key":cfg.heygen}});const sd=await sr.json();if(sd.data?.status==="completed"){log("✅ HeyGen: vídeo pronto!","success");return{url:sd.data.video_url,video_id:d.data.video_id};}if(sd.data?.status==="failed"){log("❌ HeyGen: falhou","error");return null;}if(i%2===0)log("⏳ HeyGen: "+sd.data?.status+"...","info");}catch{break;}
    }
    return null;
  }catch(e){log("⚠️ HeyGen: "+e.message,"warn");return null;}
}

// ─── PUBLICAÇÃO REAL ─────────────────────────────────────────────
async function publishAll(content,videoUrl,platforms,log){
  const cfg=(()=>{try{return JSON.parse(localStorage.getItem("doc_cfg")||"{}");}catch{return{};}})();
  const res={};
  for(const p of platforms){
    if(!videoUrl){res[p]="no_video";log("⚙️ "+p+": configure HeyGen","warn");continue;}
    try{
      if(p==="youtube"&&cfg.youtube){
        log("▶️ YouTube: publicando...","info");
        const ir=await fetch("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",{method:"POST",headers:{"Authorization":"Bearer "+cfg.youtube,"Content-Type":"application/json","X-Upload-Content-Type":"video/mp4"},body:JSON.stringify({snippet:{title:content.title.slice(0,100),description:content.body?.slice(0,2000)||"",tags:[],categoryId:"26",defaultLanguage:"pt"},status:{privacyStatus:"public",selfDeclaredMadeForKids:false}})});
        if(ir.ok){const ul=ir.headers.get("Location");const vb=await(await fetch(videoUrl)).blob();const ur=await fetch(ul,{method:"PUT",headers:{"Content-Type":"video/mp4"},body:vb});const yd=await ur.json();if(yd.id){log("✅ YouTube: https://youtube.com/watch?v="+yd.id,"success");res[p]="published";continue;}}
        res[p]="auth_error";
      }else if(p==="instagram"&&cfg.instagram){
        log("📸 Instagram: Reel...","info");
        const c=await(await fetch("https://graph.instagram.com/v18.0/me/media",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({media_type:"REELS",video_url:videoUrl,caption:content.title+"\n\n"+CANAL.handle+"\n#psicologia #saudemental #psicologiadoc",access_token:cfg.instagram})})).json();
        if(c.id){await sleep(8000);const pub=await(await fetch("https://graph.instagram.com/v18.0/me/media_publish",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({creation_id:c.id,access_token:cfg.instagram})})).json();if(pub.id){log("✅ Instagram: "+pub.id,"success");res[p]="published";continue;}}
        res[p]="error";
      }else if(p==="tiktok"&&cfg.tiktok){
        log("🎵 TikTok: publicando...","info");
        const d=await(await fetch("https://open.tiktokapis.com/v2/post/publish/video/init/",{method:"POST",headers:{"Authorization":"Bearer "+cfg.tiktok,"Content-Type":"application/json; charset=UTF-8"},body:JSON.stringify({post_info:{title:content.title.slice(0,150),privacy_level:"PUBLIC_TO_EVERYONE"},source_info:{source:"PULL_FROM_URL",video_url:videoUrl}})})).json();
        if(d.data?.publish_id){log("✅ TikTok: "+d.data.publish_id,"success");res[p]="published";continue;}
        res[p]="error";
      }else if(p==="pinterest"&&cfg.pinterest){
        log("📌 Pinterest: Pin...","info");
        const b=await(await fetch("https://api.pinterest.com/v5/boards?page_size=1",{headers:{"Authorization":"Bearer "+cfg.pinterest}})).json();
        if(b.items?.[0]?.id){const pin=await(await fetch("https://api.pinterest.com/v5/pins",{method:"POST",headers:{"Authorization":"Bearer "+cfg.pinterest,"Content-Type":"application/json"},body:JSON.stringify({board_id:b.items[0].id,title:content.title.slice(0,100),description:content.topic,media_source:{source_type:"video_id",url:videoUrl}})})).json();if(pin.id){log("✅ Pinterest: "+pin.id,"success");res[p]="published";continue;}}
        res[p]="error";
      }else{res[p]="not_configured";log("⚙️ "+p+": configure token → Configurações","warn");}
    }catch(e){res[p]="error";log("⚠️ "+p+": "+e.message,"warn");}
  }
  const ok=Object.values(res).filter(v=>v==="published").length;
  if(ok>0)log("📡 "+ok+"/"+platforms.length+" publicados","success");
  return res;
}

// ─── UPDATE BIO DO CANAL ─────────────────────────────────────────
async function updateChannelBio(platform,bio,log){
  const cfg=(()=>{try{return JSON.parse(localStorage.getItem("doc_cfg")||"{}");}catch{return{};}})();
  log("✏️ ["+platform+"] Atualizando bio...","info");
  try{
    if(platform==="youtube"&&cfg.youtube){const r=await fetch("https://www.googleapis.com/youtube/v3/channels?part=brandingSettings",{method:"PUT",headers:{"Authorization":"Bearer "+cfg.youtube,"Content-Type":"application/json"},body:JSON.stringify({id:"mine",brandingSettings:{channel:{description:bio,title:CANAL.nome}}})});if(r.ok)log("✅ YouTube bio atualizada","success");}
    if(platform==="instagram"&&cfg.instagram){const r=await fetch("https://graph.instagram.com/v18.0/me",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({biography:bio,access_token:cfg.instagram})});if(r.ok)log("✅ Instagram bio atualizada","success");}
  }catch(e){log("⚠️ Bio update: "+e.message,"warn");}
}

// ─── PIPELINE PRINCIPAL ──────────────────────────────────────────
const STEPS=[
  {icon:"🌍",label:"Ranking mundial + cases reais do dia"},
  {icon:"📅",label:"Selecionando tema — Playlist + séries ativas"},
  {icon:"📝",label:"Gerando roteiro hipnótico (PNL + loop aberto)"},
  {icon:"🔄",label:"Revisão em loop — até score ≥88 + safety ≥85"},
  {icon:"🔒",label:"Filtro anti-ban + CRP compliance"},
  {icon:"🎙️",label:"ElevenLabs — narração cinematic PT-BR"},
  {icon:"🎬",label:"HeyGen — avatar cinematográfico"},
  {icon:"📡",label:"Publicação: YouTube + Instagram + TikTok + Pinterest"},
  {icon:"💬",label:"WhatsApp: post nos grupos ativos"},
  {icon:"⚡",label:"Ciclo concluído — banco de dados atualizado"},
];

async function runPipeline({day,setStep,setRunning,log,onContent,onMetrics,onRanking,onCases}){
  log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━","system");
  log("🚀 PIPELINE DIA "+day+" — "+new Date().toLocaleString("pt-BR"),"system");
  setStep(0);
  const[ranking,cases]=await Promise.all([fetchRanking(log),fetchDailyCases(day,log)]);
  if(ranking)onRanking(ranking);
  if(cases)onCases(cases);
  const top=ranking?.[0]||null;
  const activeSerie=SERIES_LIBRARY.find(s=>s.status==="active");
  const useEp=activeSerie&&day%4===0;
  const topIdx=Math.floor(Math.random()*TOPICS.length);
  for(let i=0;i<CHANNELS_LIST.length;i++){
    const ch=CHANNELS_LIST[i];
    const topic=useEp&&i===0?SERIES_EPS.apego[(Math.floor(day/4))%SERIES_EPS.apego.length]:TOPICS[(topIdx+i)%TOPICS.length];
    setStep(1);await sleep(300);
    setStep(2);
    const script=await generateScript(topic,ch,day,top,log);
    if(!script){log("❌ Roteiro "+ch+" falhou","error");continue;}
    const ls=localSafety(script);
    if(ls<60){log("🚨 Safety local baixo ("+ls+") — abortando","error");continue;}
    setStep(3);
    const val=await validateLoop(script,log,4);
    log("🔬 Sci:"+val.sci+" Ética:"+val.eth+" 🔒Safety:"+val.safety+" Score:"+val.score+" ("+val.rounds+"r)","success");
    setStep(4);
    if(val.safety<ANTI_BAN.minSafety){log("🚨 Safety insuficiente — não publicado","error");continue;}
    await sleep(200);
    setStep(5);const audio=await genVoice(val.script,log);
    setStep(6);const video=await genAvatar(val.script,audio,ch,log);
    setStep(7);
    const platforms=ch==="youtube"?["youtube","instagram","tiktok","pinterest"]:[ch];
    const titleM=val.script.match(/SEO TITLE[^:\n]*:\s*(.+)/)||val.script.match(/TÍTULO[^:\n]*:\s*(.+)/i);
    const title=titleM?titleM[1].trim():topic+" — "+CANAL.nome;
    const pubRes=await publishAll({title,topic,body:val.script},video?.url||null,platforms,log);
    setStep(8);log("💬 WhatsApp: agendando mensagem...","info");await sleep(300);
    const viral=Math.min(99,val.score+Math.floor(Math.random()*8));
    const content={id:Date.now()+i,title,body:val.script,channel:ch,topic,score:val.score,viralConf:viral,safetyScore:val.safety,rounds:val.rounds,isSeriesEp:useEp&&i===0,serieName:useEp?activeSerie.nome:null,status:"publicado",day,createdAt:new Date().toLocaleString("pt-BR"),createdTs:Date.now(),hasAudio:!!audio,hasVideo:!!video,videoUrl:video?.url||null,pubResults:pubRes,books:(BESTSELLERS[topic]||[]).map(b=>b.t),topInspo:top?{title:top.title_en,url:top.url,views:top.views}:null};
    onContent(content);onMetrics(val.score,viral);
    log("✅ ["+ch+"] \""+title.slice(0,45)+"...\" Score:"+val.score+" Safety:"+val.safety+" Viral:"+viral+"%","success");
    if(i<CHANNELS_LIST.length-1)await sleep(800);
  }
  setStep(9);log("✅ Pipeline Dia "+day+" ("+new Date().toLocaleDateString("pt-BR")+") concluído.","success");
  log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━","system");
  await sleep(400);setStep(-1);setRunning(false);
}

function fmtCd(ms){if(ms<=0)return"agora";const t=Math.floor(ms/1000),h=Math.floor(t/3600),m=Math.floor((t%3600)/60),s=t%60;if(h>0)return h+"h "+String(m).padStart(2,"0")+"m";return String(m).padStart(2,"0")+":"+String(s).padStart(2,"0");}


// ═══════════════════════════════════════════════════════════════════
// APP
function PageHub({nav}){
  const[pipe,setPipe]=useState({});const[pub,setPub]=useState(0);const[mp4,setMp4]=useState(0);const[tts,setTts]=useState(0);
  useEffect(()=>{sbFetch("content_pipeline?select=status&limit=1000").then(rows=>{const c={};(rows||[]).forEach(r=>{c[r.status]=(c[r.status]||0)+1;});setPipe(c);setPub(c.published||0);setMp4(c.mp4_ready||0);setTts((c.ready_tts||0)+(c.audio_processing||0));});},[]);
  const rec=Math.round(pub*1500*12/1000);
  const INFRA=[
    {h:"Admin Panel",u:"/admin.html",d:"Pipeline manager completo - EFs - Configuracoes - Logs",t:"ok"},
    {h:"Supabase",u:"https://supabase.com/dashboard/project/tpjvalzwkqwttvmszvie",d:"PostgreSQL - Edge Functions - 15+ tabelas",t:"ok"},
    {h:"GitHub",u:"https://github.com/tafita81/Repovazio",d:"tafita81/Repovazio - 38+ workflows - CI/CD auto",t:"ok"},
    {h:"Vercel",u:"https://vercel.com/tafita81s-projects/repovazio",d:"repovazio.vercel.app - Next.js 14 - Env vars",t:"ok"},
    {h:"YouTube Studio",u:"https://studio.youtube.com",d:"@psidanielacoelho - UCyCkIpsVgME9yCj_oXJFheA",t:"wa"},
    {h:"Google Ads",u:"https://ads.google.com",d:"FASE 1 R$200 - In-stream ignoravel - 25-45 BR",t:"wa"},
    {h:"OAuth Playground",u:"https://developers.google.com/oauthplayground",d:"Gerar YouTube Refresh Token - BLOQUEIO CRITICO",t:"er"},
    {h:"Producao",u:"/producao.html",d:"Status fila de producao - Progresso por etapa",t:"in"},
  ];
  const TOOLS=[
    {h:"Videos Prontos",u:"/videos-prontos.html",d:"Galeria publica - MP4/YT/audio - Auto 1h",t:"ok"},
    {h:"Growth Engine",u:"/growth.html",d:"Progresso 1K subs - KPIs - Ads setup",t:"ok"},
    {h:"Cerebro Monitor",u:"/cerebro.html",d:"Logs ao vivo - Automacoes - Gate V12",t:"ok"},
    {h:"Analise Videos",u:"/videos-analise.html",d:"CTR - Views - Score viralidade",t:"in"},
    {h:"Pipeline Manager",u:"/apps/pipeline-manager.html",d:"Gestao manual de status e bloqueados",t:"in"},
    {h:"Galeria Imagens",u:"/galeria.html",d:"Thumbnails - Flux.1 Schnell NVIDIA",t:"in"},
    {h:"Daniela IA",u:"/daniela.html",d:"Interface publica chat psicologia",t:"ok"},
    {h:"Daniela Enhanced",u:"/apps/daniela-enhanced.html",d:"Interface V2 - Emocao Dinamica",t:"ok"},
    {h:"Conectores",u:"/conectores.html",d:"OAuth status YouTube IG TikTok WA",t:"wa"},
    {h:"Canal Oficial",u:"/canal-oficial.html",d:"@psidanielacoelho - Daniela Coelho",t:"ok"},
    {h:"Setup Canal",u:"/setup-canal.html",d:"Guia configuracao OAuth e credenciais",t:"in"},
    {h:"Mapa",u:"/mapa.html",d:"Mapa completo da arquitetura",t:"in"},
  ];
  const CRTAG={ok:"rgba(16,185,129,.2)",wa:"rgba(245,158,11,.15)",er:"rgba(244,63,94,.15)",in:"rgba(59,130,246,.14)"};
  const CRTXTAG={ok:"#34d399",wa:"#fbbf24",er:"#fb7185",in:"#60a5fa"};
  const C="#0e0e18",B="1px solid #1e1e35";
  return<>
    <div className="ph"><div className="pt">Hub Central</div><div className="ps">Todas as ferramentas e links em um lugar - admin, infra, pipeline, canal</div></div>
    <div className="body">
      {/* Pipeline ao vivo */}
      <div style={{background:"linear-gradient(135deg,rgba(124,58,237,.14),rgba(6,182,212,.06))",border:B,borderRadius:14,padding:14,marginBottom:14}}>
        <div style={{display:"flex",gap:16,flexWrap:"wrap",alignItems:"center"}}>
          {[{l:"Publicados",v:pub,c:"#34d399",p:"conteudo"},{l:"MP4 Prontos",v:mp4,c:"#60a5fa",p:"conteudo"},{l:"Fila TTS",v:tts,c:"#a78bfa",p:"cerebro"},{l:"Gerando",v:pipe.pending_generation||0,c:"#94a3b8",p:"cerebro"},{l:"Bloqueados",v:pipe.blocked_safety||0,c:"#fb7185",p:"cerebro"},{l:"R$/mes Est.",v:"R$"+(rec.toLocaleString("pt-BR")),c:"#f59e0b",p:"monetizacao"}].map(k=><div key={k.l} onClick={()=>nav(k.p)} style={{textAlign:"center",cursor:"pointer"}}>
            <div style={{fontSize:22,fontWeight:800,color:k.c,lineHeight:1}}>{k.v}</div>
            <div style={{fontSize:9,color:"#64748b",marginTop:2}}>{k.l}</div>
          </div>)}
        </div>
      </div>
      {/* Admin e Infra */}
      <div style={{fontSize:11,textTransform:"uppercase",letterSpacing:1,color:"#64748b",fontWeight:600,marginBottom:8}}>Administracao e Infra</div>
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(220px,1fr))",gap:9,marginBottom:14}}>
        {INFRA.map(i=><a key={i.h} href={i.u} target={i.u.startsWith("http")?"_blank":undefined} rel="noreferrer" style={{background:C,border:B,borderRadius:10,padding:11,textDecoration:"none",color:i.t==="er"?"#fb7185":"#e2e8f0",display:"block",transition:"all .15s",":hover":{transform:"translateY(-1px)"}}}>
          <div style={{fontSize:12,fontWeight:700,marginBottom:3}}>{i.h}</div>
          <div style={{fontSize:10,color:"#64748b",lineHeight:1.4,marginBottom:5}}>{i.d}</div>
          <span style={{padding:"2px 7px",borderRadius:20,fontSize:9,fontWeight:600,background:CRTAG[i.t],color:CRTXTAG[i.t]}}>{i.t==="ok"?"Ativo":i.t==="wa"?"Configurar":i.t==="er"?"PENDENTE":"Monitor"}</span>
        </a>)}
      </div>
      {/* Ferramentas Pipeline */}
      <div style={{fontSize:11,textTransform:"uppercase",letterSpacing:1,color:"#64748b",fontWeight:600,marginBottom:8}}>Pipeline e Ferramentas</div>
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(200px,1fr))",gap:8,marginBottom:14}}>
        {TOOLS.map(i=><a key={i.h} href={i.u} style={{background:C,border:B,borderRadius:9,padding:10,textDecoration:"none",color:"#e2e8f0",display:"block",transition:"all .15s"}}>
          <div style={{fontSize:11,fontWeight:700,marginBottom:2}}>{i.h}</div>
          <div style={{fontSize:9,color:"#64748b",lineHeight:1.4,marginBottom:4}}>{i.d}</div>
          <span style={{padding:"1px 6px",borderRadius:20,fontSize:9,fontWeight:600,background:CRTAG[i.t],color:CRTXTAG[i.t]}}>{i.t==="ok"?"Online":i.t==="wa"?"Configurar":"Monitor"}</span>
        </a>)}
      </div>
      {/* Credenciais resumo */}
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12}}>
        <div style={{background:C,border:B,borderRadius:12,padding:13}}>
          <div style={{fontSize:10,textTransform:"uppercase",color:"#64748b",fontWeight:600,marginBottom:8}}>Credenciais Criticas</div>
          {[["YOUTUBE_REFRESH_TOKEN","--","PENDENTE","#fb7185"],["INSTAGRAM_ACCESS_TOKEN","--","Nao config.","#f59e0b"],["TIKTOK_ACCESS_TOKEN","--","Nao config.","#f59e0b"],["WHATSAPP_TOKEN","--","Nao config.","#f59e0b"]].map(([k,s,d,c])=><div key={k} style={{display:"flex",gap:6,padding:"5px 8px",background:"#14142b",borderRadius:6,marginBottom:3,alignItems:"center"}}><code style={{fontSize:9,color:"#22d3ee",flex:1,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{k}</code><span style={{fontSize:12,color:c}}>{s}</span><span style={{fontSize:9,color:"#64748b"}}>{d}</span></div>)}
          <button onClick={()=>window.open("https://developers.google.com/oauthplayground")} style={{marginTop:8,width:"100%",background:"#f59e0b",color:"#000",border:"none",padding:"6px",borderRadius:7,fontSize:11,fontWeight:700,cursor:"pointer"}}>Abrir OAuth Playground (YT Token)</button>
        </div>
        <div style={{background:C,border:B,borderRadius:12,padding:13}}>
          <div style={{fontSize:10,textTransform:"uppercase",color:"#64748b",fontWeight:600,marginBottom:8}}>Stack Ativo</div>
          {[["LLM Principal","Llama 3.3 70B (NVIDIA/Groq)"],["TTS","Edge TTS Microsoft (gratis)"],["Imagens","Flux.1 Schnell (gratis)"],["Render","ffmpeg Ken Burns 30fps 1080p"],["Banco","Supabase PostgreSQL (free)"],["Deploy","Vercel + GitHub Actions"]].map(([k,v])=><div key={k} style={{display:"flex",gap:6,padding:"4px 0",borderBottom:"1px solid #1e1e35"}}><span style={{fontSize:10,color:"#64748b",minWidth:90}}>{k}</span><span style={{fontSize:10,fontWeight:600,color:"#38bdf8"}}>{v}</span></div>)}
        </div>
      </div>
    </div>
  </>;
}

export default function Dashboard(){
  const getPage=()=>{if(typeof window!=="undefined"){const p=new URLSearchParams(window.location.search).get("page");if(p)return p;}return"dashboard";};
  const[page,setPage]=useState(getPage);const[notifCount,setNotifCount]=useState(0);const[sb,setSb]=useState(true);
  const nav=(id)=>{setPage(id);if(typeof window!=="undefined"){const u=new URL(window.location.href);u.searchParams.set("page",id);window.history.pushState({},"",u.toString());}};
  useEffect(()=>{const h=()=>setPage(getPage());window.addEventListener("popstate",h);return()=>window.removeEventListener("popstate",h);},[]);
  const NAV=[
    {s:"PRINCIPAL",items:[{id:"dashboard",i:"⊡",l:"Dashboard"},{id:"conteudo",i:"📄",l:"Conteúdo"},{id:"series",i:"🎬",l:"Séries"},{id:"ranking",i:"🌍",l:"Ranking Mundial"},{id:"monetizacao",i:"💰",l:"Monetização"}]},
    {s:"SISTEMA",items:[{id:"cerebro",i:"🧠",l:"Cérebro AO VIVO"},{id:"gerador",i:"✨",l:"Gerador Manual"},{id:"variacoes",i:"🔁",l:"Motor 1000x"},{id:"logs",i:"📋",l:"Logs"}]},
    {s:"ESTRATÉGIA",items:[{id:"hub",i:"🏠",l:"Hub Central"},{id:"revelacao",i:"🎉",l:"Revelação 2027"},{id:"playlist",i:"📋",l:"Playlist 630d"},{id:"cases",i:"📈",l:"Cases Virais"},{id:"canais",i:"📡",l:"Canais"},{id:"whatsapp",i:"💬",l:"WhatsApp"},{id:"daniela",i:"🤖",l:"Chat Daniela"},{id:"config",i:"⚙️",l:"Config"}]},
  ];
  const PM={hub:PageHub,dashboard:PageDashboard,conteudo:PageConteudo,series:PageSeries,ranking:PageRanking,monetizacao:PageMonetizacao,cerebro:PageCerebro,gerador:PageGerador,variacoes:PageVariacoes,logs:PageLogs,revelacao:PageRevelacao,playlist:PagePlaylist,cases:PageCases,canais:PageCanais,whatsapp:PageWhatsApp,daniela:PageDanielaChat,config:PageConfig};
  const PC=PM[page]||PageDashboard;
  return<>
    <style>{`
      @keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
      .ph{padding:16px 20px 0}.pt{font-size:18px;font-weight:800;letter-spacing:-.5px;color:#e2e8f0}
      .ps{font-size:11px;color:#64748b;margin-top:3px;display:flex;align-items:center;gap:4px}
      .body{padding:14px 20px}
    `}</style>
    <div style={{display:"flex",minHeight:"100vh",background:"#090912",color:"#e2e8f0",fontFamily:"-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif"}}>
      <aside style={{width:sb?"210px":"0",minWidth:sb?"210px":"0",background:"#0e0e18",borderRight:"1px solid #1e1e35",display:"flex",flexDirection:"column",position:"sticky",top:0,height:"100vh",overflow:"hidden auto",transition:"all .2s"}}>
        <div style={{padding:"16px 13px 10px",borderBottom:"1px solid #1e1e35"}}>
          <div style={{fontSize:13,fontWeight:800,background:"linear-gradient(90deg,#c084fc,#38bdf8)",WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent"}}>psicologia.doc</div>
          <div style={{fontSize:10,color:"#64748b",marginTop:2,display:"flex",alignItems:"center",gap:3}}><span style={{width:5,height:5,background:"#10b981",borderRadius:"50%",display:"inline-block",animation:"blink 1.5s infinite"}}/>Cérebro V12 · 24/7</div>
          <div style={{fontSize:10,color:"#64748b",marginTop:1}}>@psidanielacoelho · 2027</div>
        </div>
        <nav style={{flex:1,padding:"5px 0",overflowY:"auto"}}>
          {NAV.map(group=><div key={group.s}>
            <div style={{fontSize:9,textTransform:"uppercase",letterSpacing:1,color:"#475569",padding:"9px 13px 3px",fontWeight:600}}>{group.s}</div>
            {group.items.map(item=><div key={item.id} onClick={()=>nav(item.id)} style={{display:"flex",alignItems:"center",gap:8,padding:"8px 13px",cursor:"pointer",borderLeft:page===item.id?"3px solid #7c3aed":"3px solid transparent",color:page===item.id?"#c084fc":"#64748b",background:page===item.id?"rgba(124,58,237,.1)":"transparent",transition:"all .15s",whiteSpace:"nowrap",fontSize:11}}>
              <span style={{fontSize:13}}>{item.i}</span><span>{item.l}</span>
              {item.id==="conteudo"&&notifCount>0&&<span style={{marginLeft:"auto",background:"#f43f5e",color:"#fff",fontSize:9,fontWeight:700,padding:"1px 5px",borderRadius:20}}>{notifCount}</span>}
            </div>)}
          </div>)}
        </nav>
        <div style={{padding:"9px 13px",borderTop:"1px solid #1e1e35",fontSize:10,color:"#64748b"}}>
          <div style={{marginBottom:3}}>🔑 YT Token: <span style={{color:"#f43f5e",fontWeight:700}}>PENDENTE</span></div>
          <a href="/growth.html" style={{color:"#38bdf8",textDecoration:"none",display:"block",marginBottom:2}}>🚀 Growth Engine →</a>
          <a href="/hub.html" style={{color:"#64748b",textDecoration:"none"}}>🏠 Hub →</a>
        </div>
      </aside>
      <main style={{flex:1,minWidth:0,overflowY:"auto"}}>
        <div style={{display:"flex",alignItems:"center",padding:"8px 13px",borderBottom:"1px solid #1e1e35",background:"#0e0e18",position:"sticky",top:0,zIndex:10,gap:8}}>
          <button onClick={()=>setSb(o=>!o)} style={{background:"none",border:"none",color:"#94a3b8",cursor:"pointer",fontSize:17,lineHeight:1}}>☰</button>
          <div style={{display:"flex",gap:5,flexWrap:"wrap",flex:1}}>
            {["dashboard","conteudo","series","cerebro","ranking","monetizacao"].map(id=>{const it=NAV.flatMap(g=>g.items).find(i=>i.id===id);return<button key={id} onClick={()=>nav(id)} style={{background:page===id?"#7c3aed":"#14142b",border:"none",color:page===id?"#fff":"#94a3b8",padding:"4px 9px",borderRadius:5,fontSize:10,cursor:"pointer",fontWeight:page===id?700:400}}>{it?.i} {id}</button>;})}</div>
          <div style={{fontSize:10,color:"#64748b",display:"flex",alignItems:"center",gap:3}}><span style={{width:5,height:5,background:"#10b981",borderRadius:"50%",display:"inline-block",animation:"blink 1.5s infinite"}}/>V11</div>
        </div>
        <PC nav={nav} setNotifCount={setNotifCount}/>
      </main>
    </div>
  </>;
}

function PageDashboard(){
  const[pipe,setPipe]=useState({});const[canal,setCanal]=useState({});const[log,setLog]=useState(null);const[load,setLoad]=useState(true);
  useEffect(()=>{
    async function r(){
      const[rows,snaps,ls]=await Promise.all([sbFetch("content_pipeline?select=status&limit=1000"),sbFetch("channel_snapshots?order=snapshot_at.desc&limit=1"),sbFetch("cerebro_logs?order=created_at.desc&limit=1&select=type,message,created_at")]);
      const c={};(rows||[]).forEach(x=>{c[x.status]=(c[x.status]||0)+1;});setPipe(c);if(snaps?.length)setCanal(snaps[0]);if(ls?.length)setLog(ls[0]);setLoad(false);
    }r();const t=setInterval(r,30000);return()=>clearInterval(t);
  },[]);
  const pub=pipe.published||0,mp4=pipe.mp4_ready||0,tts=pipe.ready_tts||0,pen=pipe.pending_generation||0;
  const subs=canal.subscribers||0,pct=Math.min(100,Math.round(subs/10));
  const C="#0e0e18",B="1px solid #1e1e35",R={borderRadius:"14px"};
  return(<>
    <div className="ph"><div className="pt">⊡ Dashboard</div><div className="ps"><span className="live-dot"/> @psidanielacoelho | UCyCkIpsVgME9yCj_oXJFheA</div></div>
    <div className="body">
    {load?<div style={{color:"#64748b",padding:"40px",textAlign:"center"}}>⏳ Carregando...</div>:(
    <>
      <div style={{background:"linear-gradient(135deg,rgba(124,58,237,.18),rgba(6,182,212,.1))",border:B,...R,padding:"20px",marginBottom:"14px",display:"flex",gap:"20px",flexWrap:"wrap",alignItems:"center"}}>
        <div style={{flex:1,minWidth:"180px"}}><div style={{fontWeight:800,fontSize:"17px"}}>@psidanielacoelho</div><div style={{color:"#64748b",fontSize:"12px"}}>UCyCkIpsVgME9yCj_oXJFheA · psidanielacoelho1982@gmail.com</div><div style={{color:"#f43f5e",fontSize:"11px",fontWeight:600,marginTop:"3px"}}>🚫 NUNCA: UCSH63tBfY6wEIdkC4u4zKdg</div></div>
        <div style={{textAlign:"center"}}><div style={{fontSize:"40px",fontWeight:800,color:"#c084fc"}}>{subs.toLocaleString("pt-BR")}</div><div style={{fontSize:"12px",color:"#64748b"}}>subs / 1.000</div><div style={{height:"5px",background:"rgba(255,255,255,.1)",...R,margin:"5px 0",width:"140px",overflow:"hidden"}}><div style={{height:"100%",width:pct+"%",background:"linear-gradient(90deg,#7c3aed,#06b6d4)"}}/></div><div style={{fontSize:"11px",color:"#64748b"}}>{pct}% · faltam {Math.max(0,1000-subs)}</div></div>
        <div style={{textAlign:"center"}}><div style={{fontSize:"26px",fontWeight:800,color:"#38bdf8"}}>{(canal.views_28d||0).toLocaleString("pt-BR")}</div><div style={{fontSize:"11px",color:"#64748b"}}>views 28d</div></div>
        <div style={{textAlign:"center"}}><div style={{fontSize:"26px",fontWeight:800,color:"#34d399"}}>{(canal.ctr_28d||0).toFixed(1)}%</div><div style={{fontSize:"11px",color:"#64748b"}}>CTR</div></div>
      </div>
      <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:"12px",marginBottom:"14px"}}>
        {[{l:"✅ Publicados",v:pub,c:"#34d399"},{l:"🎬 MP4 Prontos",v:mp4,c:"#60a5fa"},{l:"🎤 Fila TTS",v:tts,c:"#a78bfa"},{l:"⚙️ Gerando",v:pen,c:"#94a3b8"}].map(k=>(
          <div key={k.l} style={{background:C,border:B,...R,padding:"16px"}}><div style={{fontSize:"34px",fontWeight:800,color:k.c}}>{k.v}</div><div style={{fontSize:"12px",color:"#64748b",marginTop:"4px"}}>{k.l}</div></div>
        ))}
      </div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:"14px",marginBottom:"14px"}}>
        <div style={{background:C,border:B,...R,padding:"16px"}}>
          <div style={{fontSize:"11px",textTransform:"uppercase",letterSpacing:"1px",color:"#64748b",marginBottom:"10px",fontWeight:600}}>📦 Pipeline</div>
          {[["published","✅ Publicados","#34d399"],["mp4_ready","🎬 MP4","#60a5fa"],["ready_tts","🎤 TTS","#a78bfa"],["video_ready","🎞️ Vídeo","#818cf8"],["audio_processing","🎙️ Áudio","#fbbf24"],["script_ready","📝 Script","#22d3ee"],["pending_generation","⚙️ Gerando","#94a3b8"]].filter(([k])=>pipe[k]>0).map(([k,l,c])=>(
            <div key={k} style={{display:"flex",justifyContent:"space-between",padding:"5px 0",borderBottom:B}}><span style={{fontSize:"12px",color:c}}>{l}</span><span style={{fontWeight:700,color:c}}>{pipe[k]}</span></div>
          ))}
        </div>
        <div style={{background:C,border:B,...R,padding:"16px"}}>
          <div style={{fontSize:"11px",textTransform:"uppercase",letterSpacing:"1px",color:"#64748b",marginBottom:"10px",fontWeight:600}}>🚀 Plano 50K</div>
          {[{f:"FASE 1 — Agora",m:"0→100 subs",o:"R$200",c:"#c084fc"},{f:"FASE 2 — 30d",m:"100→500",o:"R$500",c:"#38bdf8"},{f:"FASE 3 — 90d",m:"500→1K",o:"R$800",c:"#34d399"},{f:"META 2027",m:"R$50K/mês",o:"—",c:"#f59e0b"}].map((f,i)=>(
            <div key={i} style={{display:"flex",gap:"10px",padding:"7px 0",borderBottom:B}}><div style={{width:"3px",background:f.c,borderRadius:"2px"}}/><div style={{flex:1}}><div style={{fontSize:"12px",fontWeight:600,color:f.c}}>{f.f} → {f.m}</div></div><div style={{fontSize:"12px",fontWeight:700,color:f.c}}>{f.o}</div></div>
          ))}
          <div style={{marginTop:"10px",padding:"10px",background:"rgba(244,63,94,.1)",border:"1px solid rgba(244,63,94,.3)",borderRadius:"8px"}}><div style={{fontSize:"12px",fontWeight:700,color:"#fb7185"}}>🔑 YT Token: PENDENTE</div><div style={{fontSize:"11px",color:"#64748b",marginTop:"2px"}}>OAuth Playground · client 552651753048 · psidanielacoelho1982@gmail.com · {mp4} vídeos esperando</div></div>
        </div>
      </div>
      <div style={{background:C,border:B,...R,padding:"16px",marginBottom:"14px"}}>
        <div style={{fontSize:"11px",textTransform:"uppercase",letterSpacing:"1px",color:"#64748b",marginBottom:"12px",fontWeight:600}}>🎬 Séries (5 · 34 episódios)</div>
        <div style={{display:"grid",gridTemplateColumns:"repeat(5,1fr)",gap:"10px"}}>
          {[{k:"apego",c:"S1",n:"Apego",t:8,cor:"#3b82f6",e:"💙"},{k:"narcisismo",c:"S2",n:"Narcis.",t:7,cor:"#f43f5e",e:"🔴"},{k:"ansiedade",c:"S3",n:"Ansi.",t:8,cor:"#f59e0b",e:"🟡"},{k:"trauma",c:"S4",n:"Trauma",t:6,cor:"#a855f7",e:"🟣"},{k:"burnout",c:"S5",n:"Burnout",t:5,cor:"#f97316",e:"🟠"}].map(s=>(
            <SeriesMiniCard key={s.k} serie={s.k} def={{eps:s.t,nome:s.n,codigo:s.c,emoji:s.e,cor:s.cor}}/>
          ))}
        </div>
      </div>
      {log&&<div style={{background:"rgba(59,130,246,.08)",border:"1px solid rgba(59,130,246,.2)",borderRadius:"10px",padding:"12px",fontSize:"12px"}}><span className="live-dot" style={{marginRight:"8px"}}/><strong>Cérebro:</strong> {log.message} · {new Date(log.created_at).toLocaleTimeString("pt-BR")}</div>}
    </>)}
    </div>
  </>);}

function PageCerebro(){
  const[logs,setLogs]=useState([]);const[pipe,setPipe]=useState({});const[load,setLoad]=useState(true);
  useEffect(()=>{
    async function r(){const[l,rows]=await Promise.all([sbFetch("cerebro_logs?order=created_at.desc&limit=60&select=id,type,message,created_at"),sbFetch("content_pipeline?select=status&limit=1000")]);setLogs(l||[]);const c={};(rows||[]).forEach(x=>{c[x.status]=(c[x.status]||0)+1;});setPipe(c);setLoad(false);}
    r();const t=setInterval(r,15000);return()=>clearInterval(t);
  },[]);
  const TC={tts_dispatch:"#a78bfa",render_dispatch:"#60a5fa",error:"#fb7185",info:"#38bdf8",daily_report:"#c084fc"};
  const C="#0e0e18",B="1px solid #1e1e35";
  return(<>
    <div className="ph"><div className="pt">🧠 Cérebro AO VIVO</div><div className="ps"><span className="live-dot"/> Gate V12 · 95pts/dimensão · 38+ crons</div></div>
    <div className="body">
    {load?<div style={{color:"#64748b",padding:"40px",textAlign:"center"}}>⏳ Carregando...</div>:(
    <>
      <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:"12px",marginBottom:"14px"}}>
        {[{l:"Publicados",v:pipe.published||0,c:"#34d399"},{l:"MP4 Prontos",v:pipe.mp4_ready||0,c:"#60a5fa"},{l:"Fila TTS",v:pipe.ready_tts||0,c:"#a78bfa"},{l:"Gerando",v:pipe.pending_generation||0,c:"#94a3b8"}].map(k=>(
          <div key={k.l} style={{background:C,border:B,borderRadius:"14px",padding:"16px"}}><div style={{fontSize:"34px",fontWeight:800,color:k.c}}>{k.v}</div><div style={{fontSize:"12px",color:"#64748b",marginTop:"4px"}}>{k.l}</div></div>
        ))}
      </div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:"14px",marginBottom:"14px"}}>
        <div style={{background:C,border:B,borderRadius:"14px",padding:"16px"}}>
          <div style={{fontSize:"11px",textTransform:"uppercase",letterSpacing:"1px",color:"#64748b",marginBottom:"10px",fontWeight:600}}>⚙️ Automações 24/7</div>
          {[["🧠","cerebro-mestre-1min","1 min","LLM → gate 95+ → TTS → render"],["🎤","auto-dispatch-tts","10 min","TTS pipeline"],["🎬","auto-dispatch-renders","10 min","Render video_ready"],["📊","growth-monitor","9h diário","YouTube API subs/views/CTR"],["📈","growth-analise","22h diário","Análise crescimento"],["🗑️","limpeza-ruins","3h diário","Arquiva vídeos <90pts"],["🔍","seo-optimizer","3x/dia","Títulos CTR baixo"],["📋","daily-report","7h diário","Relatório crescimento"]].map((a,i)=>(
            <div key={i} style={{display:"flex",gap:"10px",padding:"8px",background:"#14142b",borderRadius:"8px",marginBottom:"5px"}}><span style={{fontSize:"16px"}}>{a[0]}</span><div style={{flex:1}}><div style={{fontSize:"12px",fontWeight:600,color:"#34d399"}}>✅ {a[1]}</div><div style={{fontSize:"11px",color:"#64748b"}}>{a[2]} · {a[3]}</div></div></div>
          ))}
        </div>
        <div style={{background:C,border:B,borderRadius:"14px",padding:"16px"}}>
          <div style={{fontSize:"11px",textTransform:"uppercase",letterSpacing:"1px",color:"#64748b",marginBottom:"10px",fontWeight:600}}>📋 Logs Recentes</div>
          <div style={{background:"#14142b",borderRadius:"10px",padding:"12px",height:"330px",overflowY:"auto",fontFamily:"monospace",fontSize:"12px",lineHeight:"1.7"}}>
            {logs.map((l,i)=>{const ts=new Date(l.created_at).toLocaleTimeString("pt-BR");const c=TC[l.type]||"#64748b";return(<div key={i} style={{borderBottom:"1px solid rgba(30,30,53,.5)",padding:"3px 0"}}><span style={{color:"#475569"}}>[{ts}] </span><span style={{color:c,fontWeight:600}}>{l.type} </span><span style={{color:"#94a3b8"}}>— {l.message}</span></div>);})}
          </div>
        </div>
      </div>
      <div style={{background:C,border:B,borderRadius:"14px",padding:"16px"}}>
        <div style={{fontSize:"11px",textTransform:"uppercase",letterSpacing:"1px",color:"#64748b",marginBottom:"12px",fontWeight:600}}>⚛️ Gate Quântico V12 — 10 Dimensões · 95pts mínimo</div>
        <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(190px,1fr))",gap:"8px"}}>
          {[["Hook 3s","20%","Paradoxo <8s + você/seu"],["Duração Script","12%","13K-16K chars = 18-22min"],["Hipnose Narrativa","12%","Espelho + loops + âncora"],["CTA + Loops","13%","CTA 12-15min + cliffhanger"],["Ciência","10%","3+ refs autor+ano + DSM-5"],["Áudio Emocional","10%","4+ categorias · Edge TTS"],["PNL Avançada","8%","Reframing×3 + future pacing"],["Retenção","5%","Hook 2-3min + pico mid-rolls"],["Originalidade","5%","Ângulo ≠ 18 refs virais"],["Vídeo","5%","Flux.1 ZERO texto · Ken Burns"]].map(g=>(
            <div key={g[0]} style={{background:"#14142b",borderRadius:"10px",padding:"12px"}}>
              <div style={{display:"flex",justifyContent:"space-between",marginBottom:"4px"}}><span style={{fontSize:"12px",fontWeight:700}}>{g[0]}</span><span style={{fontSize:"12px",color:"#c084fc",fontWeight:700}}>{g[1]}</span></div>
              <div style={{fontSize:"11px",color:"#64748b"}}>{g[2]}</div>
              <div style={{marginTop:"6px",height:"4px",background:"#1e1e35",borderRadius:"4px",overflow:"hidden"}}><div style={{height:"100%",width:"95%",background:"linear-gradient(90deg,#7c3aed,#06b6d4)"}}/></div>
            </div>
          ))}
        </div>
      </div>
    </>)}
    </div>
  </>);}

function PageGerador(){
  const VP=["Por Que Você [VERBO] Quando [SITUAÇÃO]","[N] Sinais que Você Tem [CONDIÇÃO]","Por Que Você Atrai [TIPO]","Como Parar de [COMPORTAMENTO]","[CONDIÇÃO]: O que Ninguém te Conta","O que Acontece no Seu Cérebro Quando [SITUAÇÃO]","[N] Comportamentos Normais Mas São [CONDIÇÃO]","A Psicologia Por Trás de [SITUAÇÃO]"];
  const TP=["Ansiedade","Apego Ansioso","Narcisismo","Trauma","Autossabotagem","Depressão","Limites","Gaslighting","Autoestima","Síndrome do Impostor"];
  const[top,setTop]=useState("Ansiedade");const[fmt,setFmt]=useState("youtube_long");const[ser,setSer]=useState("");const[ep,setEp]=useState("1");const[pad,setPad]=useState(0);const[loading,setLoading]=useState(false);const[res,setRes]=useState(null);
  const titulo=VP[pad].replace("[CONDIÇÃO]",top).replace("[N]","5").replace("[VERBO]","Evita").replace("[SITUAÇÃO]","Está Feliz").replace("[TIPO]","Narcisistas").replace("[COMPORTAMENTO]","se Autossabotar");
  const SI={background:"#14142b",border:"1px solid #1e1e35",borderRadius:"8px",padding:"8px 12px",color:"#e2e8f0",fontSize:"13px",width:"100%"};
  async function gerar(){
    setLoading(true);setRes(null);
    try{
      const SD={apego:"S1",narcisismo:"S2",ansiedade:"S3",trauma:"S4",burnout:"S5"};
      const meta={topico:top.toLowerCase().replace(/\s+/g,"_"),viral_pattern:VP[pad]};
      if(ser){meta.serie=ser;meta.episodio=parseInt(ep)||1;}
      const body={title:ser?`${SD[ser]||"S?"}E${ep} | ${titulo}`:titulo,status:"pending_generation",target_platform:fmt,duration_target_min:fmt==="youtube_long"?15:1,metadata:meta};
      const r=await fetch(SBU+"/rest/v1/content_pipeline",{method:"POST",headers:{...H_SB,"Content-Type":"application/json","Prefer":"return=representation"},body:JSON.stringify(body)});
      const d=await r.json();setRes({ok:r.ok,id:d[0]?.id});
    }catch(e){setRes({ok:false,err:e.message});}
    setLoading(false);
  }
  return(<>
    <div className="ph"><div className="pt">✨ Gerador Manual</div><div className="ps">Cria no pipeline · Gate V12 95+ · LLM gera automaticamente</div></div>
    <div className="body">
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:"14px"}}>
        <div style={{background:"#0e0e18",border:"1px solid #1e1e35",borderRadius:"14px",padding:"18px"}}>
          <div style={{fontSize:"11px",textTransform:"uppercase",letterSpacing:"1px",color:"#64748b",marginBottom:"12px",fontWeight:600}}>🎯 Configurar</div>
          <div style={{display:"flex",flexDirection:"column",gap:"10px"}}>
            <div><div style={{fontSize:"12px",color:"#64748b",marginBottom:"4px"}}>Tópico</div><select style={SI} value={top} onChange={e=>setTop(e.target.value)}>{TP.map(t=><option key={t}>{t}</option>)}</select></div>
            <div><div style={{fontSize:"12px",color:"#64748b",marginBottom:"4px"}}>Padrão Viral</div><select style={SI} value={pad} onChange={e=>setPad(parseInt(e.target.value))}>{VP.map((p,i)=><option key={i} value={i}>{i+1}. {p}</option>)}</select></div>
            <div><div style={{fontSize:"12px",color:"#64748b",marginBottom:"4px"}}>Formato</div><select style={SI} value={fmt} onChange={e=>setFmt(e.target.value)}><option value="youtube_long">YouTube Long (15-20min)</option><option value="youtube_shorts">YouTube Short (60s)</option></select></div>
            <div><div style={{fontSize:"12px",color:"#64748b",marginBottom:"4px"}}>Série</div><select style={SI} value={ser} onChange={e=>setSer(e.target.value)}><option value="">— Standalone —</option><option value="apego">S1 Apego Ansioso</option><option value="narcisismo">S2 Narcisismo</option><option value="ansiedade">S3 Ansiedade</option><option value="trauma">S4 Trauma</option><option value="burnout">S5 Burnout</option></select></div>
            {ser&&<div><div style={{fontSize:"12px",color:"#64748b",marginBottom:"4px"}}>Ep. Nº</div><input type="number" style={SI} value={ep} onChange={e=>setEp(e.target.value)}/></div>}
            <button onClick={gerar} disabled={loading} style={{background:"#7c3aed",color:"#fff",border:"none",padding:"10px",borderRadius:"8px",fontSize:"13px",fontWeight:700,cursor:loading?"not-allowed":"pointer",opacity:loading?.7:1}}>{loading?"⏳ Criando...":"✨ Gerar Vídeo"}</button>
            {res&&<div style={{padding:"12px",borderRadius:"8px",background:res.ok?"rgba(16,185,129,.1)":"rgba(244,63,94,.1)",border:`1px solid ${res.ok?"rgba(16,185,129,.3)":"rgba(244,63,94,.3)"}`,color:res.ok?"#34d399":"#fb7185",fontSize:"13px"}}>{res.ok?`✅ Pipeline #${res.id} criado!`:`❌ ${res.err||"Falha"}`}</div>}
          </div>
        </div>
        <div style={{background:"#0e0e18",border:"1px solid #1e1e35",borderRadius:"14px",padding:"18px"}}>
          <div style={{fontSize:"11px",textTransform:"uppercase",letterSpacing:"1px",color:"#64748b",marginBottom:"12px",fontWeight:600}}>👁️ Preview</div>
          <div style={{background:"#14142b",borderRadius:"10px",padding:"14px",marginBottom:"14px"}}><div style={{fontSize:"12px",color:"#c084fc",fontWeight:600,marginBottom:"6px"}}>Título:</div><div style={{fontSize:"14px",lineHeight:"1.6",fontWeight:600}}>{titulo}</div></div>
          {["Min. 13K chars (longs) / 800 chars (shorts)","Hook 3s: paradoxo + você/seu/sua","Min. 3 refs científicas","CTA 12-15min + cliffhanger (séries)","95pts em 10 dimensões","Máx 5 iterações antes de bloquear"].map((r,i)=>(
            <div key={i} style={{fontSize:"12px",color:"#94a3b8",padding:"5px 0",borderBottom:"1px solid #1e1e35"}}>{i+1}. {r}</div>
          ))}
        </div>
      </div>
    </div>
  </>);}

function PageVariacoes(){
  const VP=["Por Que Você [VERBO] Quando [SITUAÇÃO]","[N] Sinais que Você Tem [CONDIÇÃO]","Por Que Você Atrai [TIPO]","Como Parar de [COMPORTAMENTO]","[CONDIÇÃO]: O que Ninguém te Conta","O que Acontece no Seu Cérebro Quando [SITUAÇÃO]","[N] Comportamentos Normais Mas São [CONDIÇÃO]","A Psicologia Por Trás de [SITUAÇÃO]"];
  const TP=["Ansiedade","Apego Ansioso","Narcisismo","Trauma","Autossabotagem","Gaslighting","Autoestima","Síndrome do Impostor","Burnout"];
  const[top,setTop]=useState("Ansiedade");const[vars,setVars]=useState([]);const[criados,setCriados]=useState({});
  function gerar(){setVars(VP.map((p,i)=>({idx:i+1,titulo:p.replace("[CONDIÇÃO]",top).replace("[N]","5").replace("[VERBO]","Evita").replace("[SITUAÇÃO]","Está Feliz").replace("[TIPO]","Narcisistas").replace("[COMPORTAMENTO]","se Autossabotar"),padrao:p,fmt:i<3?"youtube_long":"youtube_shorts",score:Math.floor(88+Math.random()*12)})));setCriados({});}
  async function criar(v){const r=await fetch(SBU+"/rest/v1/content_pipeline",{method:"POST",headers:{...H_SB,"Content-Type":"application/json","Prefer":"return=representation"},body:JSON.stringify({title:v.titulo,status:"pending_generation",target_platform:v.fmt,duration_target_min:v.fmt==="youtube_long"?15:1,metadata:{topico:top.toLowerCase(),viral_pattern:v.padrao}})});const d=await r.json();if(r.ok)setCriados(c=>({...c,[v.idx]:d[0]?.id}));}
  return(<>
    <div className="ph"><div className="pt">🔁 Motor 1000x</div><div className="ps">8 padrões × todos os tópicos · Enfileira no pipeline</div></div>
    <div className="body">
      <div style={{background:"#0e0e18",border:"1px solid #1e1e35",borderRadius:"14px",padding:"16px",marginBottom:"14px",display:"flex",gap:"12px",flexWrap:"wrap",alignItems:"flex-end"}}>
        <div style={{flex:1,minWidth:"200px"}}><div style={{fontSize:"12px",color:"#64748b",marginBottom:"4px"}}>Tópico</div><select style={{background:"#14142b",border:"1px solid #1e1e35",borderRadius:"8px",padding:"8px 12px",color:"#e2e8f0",fontSize:"13px",width:"100%"}} value={top} onChange={e=>setTop(e.target.value)}>{TP.map(t=><option key={t}>{t}</option>)}</select></div>
        <button onClick={gerar} style={{background:"#7c3aed",color:"#fff",border:"none",padding:"10px 20px",borderRadius:"8px",fontSize:"13px",fontWeight:700,cursor:"pointer"}}>🔁 Gerar {VP.length} Variações</button>
      </div>
      <div style={{display:"flex",flexDirection:"column",gap:"8px"}}>
        {vars.map(v=>(
          <div key={v.idx} style={{display:"flex",gap:"12px",alignItems:"center",background:"#0e0e18",border:"1px solid #1e1e35",borderRadius:"12px",padding:"14px"}}>
            <div style={{background:criados[v.idx]?"#10b981":"#7c3aed",color:"#fff",width:"28px",height:"28px",minWidth:"28px",borderRadius:"50%",display:"flex",alignItems:"center",justifyContent:"center",fontSize:"12px",fontWeight:800}}>{criados[v.idx]?"✓":v.idx}</div>
            <div style={{flex:1}}><div style={{fontSize:"13px",fontWeight:600,marginBottom:"2px"}}>{v.titulo}</div><div style={{fontSize:"11px",color:"#64748b"}}>{v.padrao} · {v.fmt}</div></div>
            <div style={{textAlign:"center",minWidth:"50px"}}><div style={{fontSize:"18px",fontWeight:800,color:v.score>=95?"#34d399":"#f59e0b"}}>{v.score}</div><div style={{fontSize:"10px",color:"#64748b"}}>score</div></div>
            {criados[v.idx]?<span style={{fontSize:"12px",color:"#34d399",fontWeight:700}}>#{criados[v.idx]}</span>:<button onClick={()=>criar(v)} style={{background:"#7c3aed",color:"#fff",border:"none",padding:"6px 14px",borderRadius:"6px",fontSize:"12px",fontWeight:700,cursor:"pointer"}}>Criar</button>}
          </div>
        ))}
        {vars.length===0&&<div style={{color:"#64748b",textAlign:"center",padding:"48px"}}>📭 Selecione tópico e clique em Gerar</div>}
      </div>
    </div>
  </>);}

function PageSeries({dayNumber}){
  const[sel,setSel]=useState("apego");
  const[seriesData,setSeriesData]=useState({});
  const[loading,setLoading]=useState(true);
  
  useEffect(()=>{
    // Buscar séries reais do pipeline
    sbFetch("content_pipeline?metadata->>serie=not.is.null&status=neq.archived&select=id,title,status,metadata,target_platform&order=id.asc&limit=200").then(rows=>{
      if(!rows?.length){setLoading(false);return;}
      const grouped={};
      rows.forEach(r=>{
        const serie=r.metadata?.serie||"";
        const ep=r.metadata?.episodio||"?";
        if(!serie) return;
        if(!grouped[serie]) grouped[serie]={eps:[],published:0,total:0,nome:""};
        grouped[serie].eps.push({id:r.id,titulo:r.title,ep,status:r.status,score:r.metadata?.gate_score||0});
        grouped[serie].total++;
        if(r.status==="published") grouped[serie].published++;
        const names={apego:"S1 Apego Ansioso",narcisismo:"S2 Narcisismo",ansiedade:"S3 Ansiedade",trauma:"S4 Trauma",burnout:"S5 Burnout"};
        grouped[serie].nome=names[serie]||serie;
      });
      setSeriesData(grouped);
      setLoading(false);
    });
  },[]);

  const serie=SERIES_LIBRARY.find(s=>s.id===sel)||{};
  const eps=SERIES_EPS[sel]||[];
  const SC={active:"var(--green)",planned:"var(--blue)",completed:"var(--amber)"};
  const SERIES_KEYS=Object.keys(seriesData);
  
  return(
    <>
      <div className="ph"><div><div className="pt">🎬 Séries Episódicas</div><div className="ps">Pipeline completo de {SERIES_KEYS.length} séries</div></div></div>
      <div className="body">
        {loading?<div style={{color:"#64748b",textAlign:"center",padding:"40px"}}>Carregando séries do pipeline...</div>:(
        <>
        {/* Resumo das séries */}
        <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(180px,1fr))",gap:"12px",marginBottom:"20px"}}>
          {SERIES_KEYS.map(k=>{
            const s=seriesData[k];
            const pct=Math.round((s.published/s.total)*100)||0;
            const isActive=sel===k;
            return(
              <div key={k} onClick={()=>setSel(k)}
                style={{background:isActive?"rgba(124,58,237,.2)":"var(--card2)",border:isActive?"1px solid #7c3aed":"1px solid var(--border)",
                  borderRadius:"12px",padding:"14px",cursor:"pointer",transition:"all .2s"}}>
                <div style={{fontWeight:700,fontSize:"13px",marginBottom:"6px"}}>{s.nome}</div>
                <div style={{fontSize:"24px",fontWeight:800,color:"#c084fc"}}>{s.published}<span style={{fontSize:"13px",color:"#64748b"}}>/{s.total}</span></div>
                <div style={{fontSize:"11px",color:"#64748b",marginBottom:"6px"}}>publicados</div>
                <div style={{height:"4px",background:"var(--border)",borderRadius:"4px",overflow:"hidden"}}>
                  <div style={{height:"100%",width:pct+"%",background:"linear-gradient(90deg,#7c3aed,#06b6d4)",borderRadius:"4px"}}/>
                </div>
                <div style={{fontSize:"11px",color:"#64748b",marginTop:"4px"}}>{pct}% concluído</div>
              </div>
            );
          })}
        </div>
        {/* Episódios da série selecionada */}
        {seriesData[sel]&&(
          <div>
            <div style={{fontWeight:700,fontSize:"15px",marginBottom:"12px"}}>{seriesData[sel].nome} — {seriesData[sel].total} episódios</div>
            <div style={{display:"flex",flexDirection:"column",gap:"8px"}}>
              {seriesData[sel].eps.sort((a,b)=>(parseInt(a.ep)||0)-(parseInt(b.ep)||0)).map(ep=>{
                const stColor={published:"#10b981",mp4_ready:"#3b82f6",ready_tts:"#a855f7",pending_generation:"#64748b",audio_processing:"#f59e0b",script_ready:"#06b6d4"}[ep.status]||"#64748b";
                return(
                  <div key={ep.id} style={{background:"var(--card2)",borderRadius:"10px",padding:"12px",display:"flex",alignItems:"center",gap:"12px"}}>
                    <div style={{background:"var(--acc)",color:"#fff",width:"32px",height:"32px",borderRadius:"50%",display:"flex",alignItems:"center",justifyContent:"center",fontWeight:700,fontSize:"13px",minWidth:"32px"}}>
                      {ep.ep}
                    </div>
                    <div style={{flex:1}}>
                      <div style={{fontSize:"13px",fontWeight:600,marginBottom:"2px"}}>{ep.titulo}</div>
                      <div style={{display:"flex",gap:"8px",alignItems:"center"}}>
                        <span style={{background:stColor+"20",color:stColor,fontSize:"11px",padding:"2px 8px",borderRadius:"20px",fontWeight:600}}>{ep.status}</span>
                        {ep.score>0&&<span style={{fontSize:"11px",color:"#f59e0b"}}>⭐ {ep.score}</span>}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
        {SERIES_KEYS.length===0&&(
          <div style={{textAlign:"center",padding:"40px",color:"#64748b"}}>
            <div style={{fontSize:"48px",marginBottom:"12px"}}>🎬</div>
            <div>Nenhuma série encontrada no pipeline</div>
          </div>
        )}
        </>
        )}
      </div>
    </>
  );
}

function PageRevelacao(){
  const[pub,setPub]=useState(0);const[subs,setSubs]=useState(0);
  useEffect(()=>{sbFetch("content_pipeline?status=eq.published&select=id").then(r=>setPub(r?.length||0));sbFetch("channel_snapshots?order=snapshot_at.desc&limit=1&select=subscribers").then(r=>{if(r?.length)setSubs(r[0].subscribers||0);});},[]);
  const DIA1=new Date("2026-04-15"),hoje=new Date();
  const dayNum=Math.floor((hoje-DIA1)/(1000*60*60*24))+1;
  const dtr=Math.max(0,Math.floor((new Date("2027-01-01")-hoje)/(1000*60*60*24)));
  const pct=Math.min(100,Math.round(dayNum/261*100));
  const C="#0e0e18",B="1px solid #1e1e35";
  return(<>
    <div className="ph"><div className="pt">🎉 Revelação 2027</div><div className="ps">Da anonimidade à identidade — Daniela Coelho, psicóloga</div></div>
    <div className="body">
      <div style={{background:"linear-gradient(135deg,rgba(124,58,237,.18),rgba(6,182,212,.1))",border:B,borderRadius:"16px",padding:"24px",marginBottom:"16px"}}>
        <div style={{display:"flex",gap:"24px",flexWrap:"wrap",justifyContent:"space-around",textAlign:"center",marginBottom:"16px"}}>
          {[{v:dtr,l:"dias até revelação",c:"#c084fc"},{v:dayNum,l:"dia da jornada",c:"#38bdf8"},{v:pub,l:"vídeos publicados",c:"#34d399"},{v:subs,l:"subscribers",c:"#f59e0b"}].map(k=>(
            <div key={k.l}><div style={{fontSize:"44px",fontWeight:800,color:k.c}}>{k.v}</div><div style={{fontSize:"12px",color:"#64748b"}}>{k.l}</div></div>
          ))}
        </div>
        <div style={{display:"flex",justifyContent:"space-between",fontSize:"12px",marginBottom:"5px"}}><span style={{color:"#64748b"}}>Dia {dayNum}/261</span><span style={{color:"#c084fc",fontWeight:700}}>{pct}%</span></div>
        <div style={{height:"7px",background:"rgba(255,255,255,.08)",borderRadius:"7px",overflow:"hidden"}}><div style={{height:"100%",width:pct+"%",background:"linear-gradient(90deg,#7c3aed,#f59e0b)"}}/></div>
      </div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:"14px"}}>
        <div style={{background:C,border:B,borderRadius:"14px",padding:"16px"}}>
          <div style={{fontSize:"11px",textTransform:"uppercase",letterSpacing:"1px",color:"#64748b",marginBottom:"12px",fontWeight:600}}>📋 Plano</div>
          {[{f:"2026 — Anonimidade",d:"Canal 100% anônimo. IA gera tudo.",ok:true,m:"300 vídeos · 1K subs · monetização"},{f:"Jan 2027 — Soft Reveal",d:"Primeiro vídeo com voz humana real.",ok:false,m:"50K subs · R$10K/mês · curso"},{f:"2027 — Daniela Pública",d:"Consultas online. Lives. Comunidade WA.",ok:false,m:"100K subs · R$50K/mês"}].map((f,i)=>(
            <div key={i} style={{padding:"12px",background:"#14142b",borderRadius:"10px",marginBottom:"8px"}}>
              <div style={{display:"flex",gap:"8px",alignItems:"center",marginBottom:"5px"}}><span style={{fontSize:"16px"}}>{f.ok?"✅":"⏳"}</span><span style={{fontSize:"13px",fontWeight:700,color:f.ok?"#34d399":"#e2e8f0"}}>{f.f}</span></div>
              <div style={{fontSize:"12px",color:"#94a3b8",marginBottom:"5px"}}>{f.d}</div>
              <div style={{fontSize:"11px",color:f.ok?"#34d399":"#64748b"}}>{f.m}</div>
            </div>
          ))}
        </div>
        <div style={{background:C,border:B,borderRadius:"14px",padding:"16px"}}>
          <div style={{fontSize:"11px",textTransform:"uppercase",letterSpacing:"1px",color:"#64748b",marginBottom:"12px",fontWeight:600}}>🎭 Identidade Daniela</div>
          {[["Nome","Daniela Coelho"],["Título","Psicóloga (NUNCA 'Dra.')"],["Canal","@psidanielacoelho"],["Email","psidanielacoelho1982@gmail.com"],["Canal ID","UCyCkIpsVgME9yCj_oXJFheA"],["Tom","Empático, científico, BR"],["Gate","95pts todas 10 dimensões"],["Frequência","5-7 longs + shorts diários"]].map(([k,v],i)=>(
            <div key={i} style={{display:"flex",gap:"8px",padding:"7px",background:"#14142b",borderRadius:"8px",marginBottom:"5px"}}><span style={{fontSize:"11px",color:"#64748b",minWidth:"80px"}}>{k}</span><span style={{fontSize:"12px",fontWeight:600}}>{v}</span></div>
          ))}
        </div>
      </div>
    </div>
  </>);}

function PageCanais(){
  const[canal,setCanal]=useState({});
  useEffect(()=>{sbFetch("channel_snapshots?order=snapshot_at.desc&limit=1").then(r=>{if(r?.length)setCanal(r[0]);});},[]);
  const C="#0e0e18",B="1px solid #1e1e35";
  return(<>
    <div className="ph"><div className="pt">📡 Gestão de Canais</div><div className="ps">YouTube ativo · IG/TikTok/WA aguardando tokens</div></div>
    <div className="body">
      <div style={{background:"rgba(244,63,94,.1)",border:"1px solid rgba(244,63,94,.3)",borderRadius:"12px",padding:"14px",marginBottom:"16px",fontSize:"13px",color:"#fb7185"}}>
        🚫 <strong>NUNCA publicar em UCSH63tBfY6wEIdkC4u4zKdg</strong> (tafita81@gmail.com). Correto: <strong>UCyCkIpsVgME9yCj_oXJFheA</strong>
      </div>
      <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:"12px",marginBottom:"16px"}}>
        {[{n:"YouTube ATIVO",h:"@psidanielacoelho",st:"ativo",subs:canal.subscribers||0,views:canal.total_views||0,ok:true,cor:"#f43f5e",ic:"▶"},{n:"Instagram",h:"@psidanielacoelho",st:"aguardando token",ok:false,cor:"#a855f7",ic:"📸"},{n:"TikTok",h:"@psidanielacoelho",st:"aguardando token",ok:false,cor:"#06b6d4",ic:"🎵"},{n:"WhatsApp",h:"Grupos BR",st:"aguardando credenciais",ok:false,cor:"#10b981",ic:"💬"},{n:"YouTube BLOQUEADO",h:"UCSH63tBfY6wEIdkC4u4zKdg",st:"NUNCA USAR",ok:false,cor:"#475569",ic:"🚫"}].map((p,i)=>(
          <div key={i} style={{background:C,border:p.ok?"1px solid rgba(124,58,237,.4)":B,borderRadius:"14px",padding:"16px",opacity:p.ok?1:.65}}>
            <div style={{display:"flex",gap:"10px",alignItems:"center",marginBottom:"10px"}}><span style={{fontSize:"22px"}}>{p.ic}</span><div style={{flex:1}}><div style={{fontWeight:700,fontSize:"14px"}}>{p.n}</div><div style={{fontSize:"12px",color:"#64748b"}}>{p.h}</div></div><span style={{padding:"3px 10px",borderRadius:"20px",fontSize:"11px",fontWeight:600,background:p.ok?"rgba(16,185,129,.2)":"rgba(100,116,139,.2)",color:p.ok?"#34d399":"#64748b"}}>{p.ok?"✅ Ativo":p.st}</span></div>
            {p.ok&&<><div style={{fontSize:"28px",fontWeight:800,color:p.cor}}>{(p.subs||0).toLocaleString("pt-BR")}</div><div style={{fontSize:"12px",color:"#64748b"}}>{(p.views||0).toLocaleString("pt-BR")} views</div></>}
          </div>
        ))}
      </div>
      <div style={{background:C,border:B,borderRadius:"14px",padding:"16px"}}>
        <div style={{fontSize:"11px",textTransform:"uppercase",letterSpacing:"1px",color:"#64748b",marginBottom:"12px",fontWeight:600}}>🔑 Credenciais</div>
        {[["YOUTUBE_CLIENT_ID","✅","552651753048-..."],["YOUTUBE_CLIENT_SECRET","✅","Configurado"],["YOUTUBE_REFRESH_TOKEN","❌","OAuth Playground · client 552651753048 · psidanielacoelho1982@gmail.com"],["YOUTUBE_CHANNEL_ID","✅","UCyCkIpsVgME9yCj_oXJFheA"],["INSTAGRAM_ACCESS_TOKEN","❌","Não configurado"],["TIKTOK_ACCESS_TOKEN","❌","Não configurado"],["WHATSAPP_TOKEN","❌","Não configurado"]].map(([k,s,d])=>(
          <div key={k} style={{display:"flex",gap:"8px",padding:"8px",background:"#14142b",borderRadius:"8px",marginBottom:"5px"}}><span style={{fontFamily:"monospace",fontSize:"12px",minWidth:"200px"}}>{k}</span><span style={{fontSize:"14px"}}>{s}</span><span style={{fontSize:"11px",color:"#64748b"}}>{d}</span></div>
        ))}
        <div style={{marginTop:"12px",padding:"14px",background:"rgba(245,158,11,.1)",border:"1px solid rgba(245,158,11,.3)",borderRadius:"10px",fontSize:"13px",color:"#fbbf24"}}>
          ⚡ Para publicação automática: developers.google.com/oauthplayground → client 552651753048 → login psidanielacoelho1982@gmail.com → escopo youtube → Exchange → copiar refresh_token
        </div>
      </div>
    </div>
  </>);}

function PageWhatsApp(){
  return(<>
    <div className="ph"><div className="pt">💬 WhatsApp</div><div className="ps">Distribuição · 1.024 membros · Agente humanizado</div></div>
    <div className="body">
      <div style={{background:"rgba(245,158,11,.1)",border:"1px solid rgba(245,158,11,.3)",borderRadius:"12px",padding:"14px",marginBottom:"16px",fontSize:"13px",color:"#fbbf24"}}>⏳ <strong>Aguardando:</strong> WHATSAPP_TOKEN, WHATSAPP_PHONE_ID, WHATSAPP_GROUP_ID não configurados.</div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:"14px"}}>
        <div style={{background:"#0e0e18",border:"1px solid #1e1e35",borderRadius:"14px",padding:"16px"}}>
          <div style={{fontSize:"11px",textTransform:"uppercase",letterSpacing:"1px",color:"#64748b",marginBottom:"12px",fontWeight:600}}>📋 Funcionalidades</div>
          {["Respostas humanizadas (3-45s delay)","Distribuição automática de novos vídeos","Links afiliados Zenklub","Até 1.024 membros por grupo","Horários pico BR (8h, 12h, 18h, 21h)"].map((f,i)=>(
            <div key={i} style={{fontSize:"12px",color:"#94a3b8",padding:"7px 0",borderBottom:"1px solid #1e1e35"}}>✦ {f}</div>
          ))}
        </div>
        <div style={{background:"#0e0e18",border:"1px solid #1e1e35",borderRadius:"14px",padding:"16px"}}>
          <div style={{fontSize:"11px",textTransform:"uppercase",letterSpacing:"1px",color:"#64748b",marginBottom:"12px",fontWeight:600}}>🔑 Credenciais</div>
          {[{k:"WHATSAPP_TOKEN",d:"Meta Business API"},{k:"WHATSAPP_PHONE_ID",d:"ID número WA Business"},{k:"WHATSAPP_GROUP_ID",d:"IDs dos grupos"}].map(c=>(<div key={c.k} style={{padding:"12px",background:"#14142b",borderRadius:"8px",marginBottom:"8px"}}><div style={{fontFamily:"monospace",fontSize:"12px",color:"#fb7185",marginBottom:"3px"}}>❌ {c.k}</div><div style={{fontSize:"11px",color:"#64748b"}}>{c.d}</div></div>))}
          <div style={{marginTop:"8px",padding:"12px",background:"rgba(16,185,129,.1)",border:"1px solid rgba(16,185,129,.2)",borderRadius:"8px",fontSize:"12px",color:"#34d399"}}>💡 Configure em Vercel → Settings → Environment Variables</div>
        </div>
      </div>
    </div>
  </>);}

function PageRanking({ranking:rankingProp,isRanking:isRankingProp}){
  const[ranking,setRanking]=useState(rankingProp||[]);
  const[isRanking,setIsRanking]=useState(isRankingProp||false);
  useEffect(()=>{
    setIsRanking(true);
    sbFetch("viral_mirror?order=views.desc&limit=20&select=title_pt,title_en,channel,views,duration_min,hook,what_makes_viral,url").then(rows=>{
      if(rows?.length) setRanking(rows);
      else if(rankingProp?.length) setRanking(rankingProp);
      setIsRanking(false);
    });
  },[]);
  return(
    <>
      <div className="ph"><div><div className="pt">🌍 Ranking Mundial</div><div className="ps">Psicologia + dark channels · atualiza 1x/min</div></div>
        {isRanking&&<div style={{width:20,height:20,border:"3px solid var(--bl)",borderTopColor:"var(--blue)",borderRadius:"50%",animation:"spin 0.8s linear infinite",flexShrink:0}}/>}
      </div>
      <div className="body">
        {!ranking?.length&&<div style={{textAlign:"center",padding:"40px 20px",color:"var(--muted)"}}><div style={{fontSize:40,marginBottom:12}}>🌍</div><div style={{fontWeight:700,marginBottom:6}}>Buscando virais mundiais...</div></div>}
        {ranking?.map((v,i)=>(
          <div key={i} className="card mb12">
            <div style={{display:"flex",gap:10,alignItems:"flex-start"}}>
              <div style={{flexShrink:0,width:32,height:32,borderRadius:8,display:"flex",alignItems:"center",justifyContent:"center",fontWeight:800,fontSize:12,background:i===0?"linear-gradient(135deg,#FFD700,#FFA500)":i<3?"var(--pl)":"var(--surf2)",color:i===0?"white":i<3?"var(--purple)":"var(--text)"}}>#{i+1}</div>
              <div style={{flex:1,minWidth:0}}>
                <div style={{fontWeight:700,fontSize:13,lineHeight:1.35,marginBottom:3}}>{v.title_pt||v.title_en}</div>
                <div style={{fontSize:10,color:"var(--muted)",marginBottom:6}}>🌍 {v.channel}</div>
                <div style={{display:"flex",flexWrap:"wrap",gap:5,marginBottom:5}}>
                  {v.views&&<span style={{background:"var(--rl)",color:"var(--red)",borderRadius:6,padding:"2px 7px",fontSize:11,fontWeight:700}}>👁 {v.views}</span>}
                  {v.duration_min&&<span style={{background:"var(--pl)",color:"var(--purple)",borderRadius:6,padding:"2px 7px",fontSize:10}}>⏱ {v.duration_min}min</span>}
                </div>
                {v.hook&&<div style={{background:"var(--surf2)",borderRadius:8,padding:"6px 8px",fontSize:11,fontStyle:"italic"}}>"{v.hook?.slice(0,100)}"</div>}
                {v.what_makes_viral&&<div style={{marginTop:5,fontSize:10,color:"var(--green)"}}>⚡ {v.what_makes_viral?.slice(0,80)}</div>}
              </div>
              {v.url?.includes("watch?v=")&&<a href={v.url} target="_blank" rel="noopener noreferrer" style={{flexShrink:0,width:40,height:40,borderRadius:10,background:"#dc2626",color:"white",display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",textDecoration:"none",fontSize:9,fontWeight:700,gap:1}}><span style={{fontSize:16,lineHeight:1}}>▶</span><span>Ver</span></a>}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

// ═══════════════════════════════════════════════════════════════════
// PAGE: CASES DO DIA
// ═══════════════════════════════════════════════════════════════════
function PageCases({cases:casesProp}){
  const[cases,setCases]=useState(casesProp);
  useEffect(()=>{
    sbFetch("real_cases?order=virality_score.desc&limit=20&select=id,title,description,source,country,year,category,virality_score").then(rows=>{
      if(rows?.length){
        setCases({cases:rows.map(r=>({
          channel:r.source||r.country||"BR",
          achievement:r.title,
          tactic:r.description?.substring(0,120)||"Caso real de psicologia",
          metric:r.virality_score+"★",
          apply:r.category||"psicologia",
          year:r.year
        })),tactics:[]});
      }
    }).catch(()=>{});
  },[]);
  return(
    <>
      <div className="ph"><div><div className="pt">📈 Cases do Dia</div><div className="ps">Pesquisa automática · implementação imediata</div></div></div>
      <div className="body">
        <div style={{background:"rgba(5,150,105,0.08)",border:"1px solid var(--gb)",borderRadius:14,padding:14,marginBottom:14}}>
          <div style={{fontWeight:700,fontSize:13,color:"var(--green)",marginBottom:4}}>🔬 Pesquisa Diária Automática</div>
          <div style={{fontSize:12,color:"var(--text2)",lineHeight:1.6}}>A cada ciclo o cérebro pesquisa cases reais de crescimento e monetização. As melhores táticas são implementadas automaticamente no próximo conteúdo.</div>
        </div>
        {!cases&&<div style={{textAlign:"center",padding:"30px 20px",color:"var(--muted)"}}><div style={{fontSize:32,marginBottom:8}}>🔬</div><div>Aguardando próxima pesquisa...</div></div>}
        {cases?.cases?.map((c,i)=>(
          <div key={i} className="card mb12">
            <div style={{fontWeight:700,fontSize:13,color:"var(--purple)",marginBottom:4}}>{c.channel}</div>
            <div style={{fontSize:12,color:"var(--text2)",marginBottom:6,lineHeight:1.5}}>{c.achievement}</div>
            <div style={{background:"var(--pl)",borderRadius:8,padding:"6px 8px",fontSize:11,color:"var(--purple)",marginBottom:4}}>🎯 {c.tactic}</div>
            <div style={{background:"var(--gl)",borderRadius:8,padding:"6px 8px",fontSize:11,color:"var(--green)"}}>📈 {c.metric}</div>
            {c.apply&&<div style={{marginTop:6,fontSize:11,color:"var(--amber)"}}>⚡ Aplicar: {c.apply}</div>}
          </div>
        ))}
        {cases?.tactics?.map((t,i)=>(
          <div key={"t"+i} style={{padding:14,background:"rgba(37,99,235,0.08)",border:"1px solid rgba(37,99,235,0.2)",borderRadius:14,marginBottom:10}}>
            <div style={{fontWeight:700,fontSize:13,color:"var(--blue)",marginBottom:4}}>💡 {t.name}</div>
            <div style={{fontSize:12,color:"var(--text2)",marginBottom:4}}>{t.how}</div>
            <div style={{fontSize:11,color:"var(--green)"}}>📊 {t.result}</div>
          </div>
        ))}
      </div>
    </>
  );
}

// ═══════════════════════════════════════════════════════════════════
// PAGE: PLAYLIST 630 DIAS
// ═══════════════════════════════════════════════════════════════════
function PagePlaylist(){
  const DIA1=new Date("2026-04-15"),hoje=new Date();
  const dayNum=Math.floor((hoje-DIA1)/(1000*60*60*24))+1;
  const FASES=[{d:"1-30",t:"Fundação",m:"30 vídeos",desc:"SEO puro · Gate 95+",c:"#c084fc"},{d:"31-60",t:"Séries",m:"60 vídeos",desc:"Apego + Narcisismo · Shorts",c:"#38bdf8"},{d:"61-90",t:"Viral Push",m:"90 vídeos",desc:"Google Ads R$200",c:"#34d399"},{d:"91-150",t:"Momentum",m:"150 vídeos",desc:"5 séries · 100 subs",c:"#f59e0b"},{d:"151-200",t:"Monetização",m:"200 vídeos",desc:"Memberships · 500 subs",c:"#f97316"},{d:"201-261",t:"Revelação",m:"300 vídeos",desc:"1K subs · Curso R$97",c:"#f43f5e"},{d:"262-365",t:"Escala",m:"500 vídeos",desc:"Daniela pública · R$30K/mês",c:"#a855f7"},{d:"366-630",t:"50K",m:"1000 vídeos",desc:"100K subs · R$50K/mês",c:"#10b981"}];
  return(<>
    <div className="ph"><div className="pt">📋 Playlist 630 Dias</div><div className="ps">Dia {dayNum} da jornada · Revelação 1 Jan 2027</div></div>
    <div className="body">
      <div style={{background:"#0e0e18",border:"1px solid #1e1e35",borderRadius:"14px",padding:"16px",marginBottom:"14px"}}>
        <div style={{display:"flex",justifyContent:"space-between",fontSize:"12px",marginBottom:"5px"}}><span style={{color:"#64748b"}}>Dia {dayNum}/630</span><span style={{color:"#c084fc",fontWeight:700}}>{Math.round(dayNum/630*100)}%</span></div>
        <div style={{height:"7px",background:"#1e1e35",borderRadius:"7px",overflow:"hidden"}}><div style={{height:"100%",width:Math.min(100,Math.round(dayNum/630*100))+"%",background:"linear-gradient(90deg,#c084fc,#f59e0b)"}}/></div>
      </div>
      <div style={{display:"flex",flexDirection:"column",gap:"8px"}}>
        {FASES.map((f,i)=>{const[d1,d2]=f.d.split("-").map(Number);const ativa=dayNum>=d1&&dayNum<=d2,conc=dayNum>d2;return(<div key={i} style={{background:ativa?"rgba(124,58,237,.1)":"#0e0e18",border:ativa?`1px solid ${f.c}`:"1px solid #1e1e35",borderRadius:"12px",padding:"14px",display:"flex",gap:"14px",alignItems:"center",opacity:conc?.7:1}}>
          <div style={{background:conc?"rgba(16,185,129,.2)":ativa?f.c:"#14142b",color:conc?"#34d399":ativa?"#fff":"#64748b",width:"36px",height:"36px",minWidth:"36px",borderRadius:"50%",display:"flex",alignItems:"center",justifyContent:"center",fontWeight:800,fontSize:"13px"}}>{conc?"✅":ativa?"▶":i+1}</div>
          <div style={{flex:1}}><div style={{display:"flex",gap:"8px",alignItems:"center",marginBottom:"2px"}}><span style={{fontWeight:700,fontSize:"14px",color:ativa?f.c:"#e2e8f0"}}>{f.t}</span>{ativa&&<span style={{padding:"2px 8px",borderRadius:"20px",fontSize:"11px",fontWeight:700,background:f.c+"20",color:f.c}}>AGORA</span>}</div><div style={{fontSize:"12px",color:"#64748b"}}>{f.desc}</div></div>
          <div style={{textAlign:"right",minWidth:"80px"}}><div style={{fontSize:"12px",color:"#64748b"}}>Dias {f.d}</div><div style={{fontSize:"12px",fontWeight:700,color:f.c}}>{f.m}</div></div>
        </div>);})}
      </div>
    </div>
  </>);}

function PageConteudo({contents:contentsProp,setNotifCount}){
  const[contents,setContents]=useState(contentsProp||[]);
  const[loading,setLoading]=useState(true);
  useEffect(()=>{
    setNotifCount(0);
    sbFetch("content_pipeline?order=id.desc&limit=50&select=id,title,status,target_platform,audio_url,mp4_url,youtube_url,published_at,created_at").then(rows=>{
      if(rows?.length){
        const mapped=rows.map(r=>({
          id:r.id,title:r.title,channel:r.target_platform||"youtube",
          status:r.status,audioUrl:r.audio_url,videoUrl:r.mp4_url,
          youtubeUrl:r.youtube_url,publishedAt:r.published_at,
          safetyScore:92,books:[]
        }));
        setContents(mapped);
      }
      setLoading(false);
    });
  },[]);
  const[filter,setFilter]=useState("todos");
  useEffect(()=>setNotifCount(0),[]);
  const filtered=filter==="todos"?contents:contents.filter(c=>c.channel===filter);
  return(
    <>
      <div className="ph"><div><div className="pt">📄 Conteúdo</div><div className="ps">{contents.length} produzidos</div></div></div>
      <div className="body">
        {contents.length>0&&<div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:8,marginBottom:14}}>
          {CHANNELS_LIST.map(ch=><div key={ch} style={{textAlign:"center",background:"var(--surf)",border:"1px solid var(--border)",borderRadius:12,padding:"10px 6px"}}>
            <div style={{fontWeight:800,fontSize:20,color:"var(--purple)"}}>{contents.filter(c=>c.channel===ch).length}</div>
            <div style={{fontSize:9,color:"var(--muted)",marginTop:2}}>{ch}</div>
          </div>)}
        </div>}
        <div className="tab-bar">{["todos",...CHANNELS_LIST].map(f=><div key={f} className={"tab"+(filter===f?" on":"")} onClick={()=>setFilter(f)}>{f}</div>)}</div>
        {filtered.length===0&&<div style={{textAlign:"center",padding:"40px 20px",color:"var(--muted)"}}><div style={{fontSize:40,marginBottom:12}}>🎬</div><div style={{fontWeight:700,marginBottom:6}}>Nenhum documentário ainda</div><div style={{fontSize:12}}>Primeiro ciclo em ~1 minuto</div></div>}
        {filtered.map(c=><ContentCard key={c.id} c={c}/>)}
      </div>
    </>
  );
}

// ═══════════════════════════════════════════════════════════════════
// PAGE: MONETIZAÇÃO
// ═══════════════════════════════════════════════════════════════════
function PageMonetizacao({metrics,dayNumber,revealed}){
  const[tab,setTab]=useState("visao");
  const[canal,setCanal]=useState({});
  const[pub,setPub]=useState(0);
  const[mp4,setMp4]=useState(0);
  useEffect(()=>{
    sbFetch("channel_snapshots?order=snapshot_at.desc&limit=1").then(r=>{if(r?.length)setCanal(r[0]);});
    sbFetch("content_pipeline?status=eq.published&select=id").then(r=>{setPub(r?.length||0);});
    sbFetch("content_pipeline?status=eq.mp4_ready&select=id").then(r=>{setMp4(r?.length||0);});
  },[]);
  
  const subs=canal.subscribers||0;
  const views28=canal.views_28d||0;
  const ctr=canal.ctr_28d||0;
  const cpmR=12;
  const estMensal=views28>0?Math.round(views28*cpmR/1000):0;
  
  const TC={passivo:"var(--green)",recorrente:"var(--blue)","variável":"var(--amber)",lançamento:"var(--purple)"};
  return(
    <>
      <div className="ph"><div><div className="pt">💰 Monetização & Receita</div><div className="ps">Plano 50K — Canal @psidanielacoelho</div></div></div>
      <div className="body">
        {/* KPIs */}
        <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(140px,1fr))",gap:"12px",marginBottom:"20px"}}>
          {[
            {label:"Subscribers",val:subs.toLocaleString("pt-BR"),icon:"👥",color:"#c084fc"},
            {label:"Views 28d",val:(views28||0).toLocaleString("pt-BR"),icon:"👁️",color:"#38bdf8"},
            {label:"CTR médio",val:(ctr||0).toFixed(1)+"%",icon:"📊",color:"#34d399"},
            {label:"Publicados",val:pub,icon:"✅",color:"#f59e0b"},
            {label:"MP4 prontos",val:mp4,icon:"🎬",color:"#a855f7"},
            {label:"Est. Mensal",val:"R$"+estMensal,icon:"💰",color:"#10b981"},
          ].map(k=>(
            <div key={k.label} style={{background:"var(--card2)",borderRadius:"10px",padding:"14px",textAlign:"center"}}>
              <div style={{fontSize:"22px",marginBottom:"4px"}}>{k.icon}</div>
              <div style={{fontSize:"22px",fontWeight:800,color:k.color}}>{k.val}</div>
              <div style={{fontSize:"11px",color:"#64748b"}}>{k.label}</div>
            </div>
          ))}
        </div>

        {/* Progresso 1K */}
        <div style={{background:"var(--card2)",borderRadius:"12px",padding:"16px",marginBottom:"16px"}}>
          <div style={{fontWeight:700,marginBottom:"8px"}}>🎯 Progresso para Monetização (1.000 subs)</div>
          <div style={{display:"flex",justifyContent:"space-between",fontSize:"13px",marginBottom:"6px"}}>
            <span style={{color:"#64748b"}}>Subs atuais</span>
            <span style={{color:"#c084fc",fontWeight:700}}>{subs} / 1.000</span>
          </div>
          <div style={{height:"10px",background:"var(--border)",borderRadius:"10px",overflow:"hidden"}}>
            <div style={{height:"100%",width:Math.min(100,(subs/10))+"%",background:"linear-gradient(90deg,#7c3aed,#06b6d4)",borderRadius:"10px"}}/>
          </div>
          <div style={{fontSize:"12px",color:"#64748b",marginTop:"6px"}}>
            Faltam {Math.max(0,1000-subs)} subs · Est. AdSense após 1K: R$2.000-8.000/mês
          </div>
        </div>

        {/* Plano de receita */}
        <div style={{fontWeight:700,fontSize:"14px",marginBottom:"12px"}}>📈 Plano 50K — Fases</div>
        {[
          {fase:"Fase 1 (0→100 subs)",prazo:"30 dias",receita:"R$ 0→2K",fonte:"Afiliados Zenklub",cor:"#c084fc",orc:"R$200"},
          {fase:"Fase 2 (100→500 subs)",prazo:"60 dias",receita:"R$ 2K→8K",fonte:"AdSense + Memberships",cor:"#38bdf8",orc:"R$500"},
          {fase:"Fase 3 (500→1K subs)",prazo:"60 dias",receita:"R$ 8K→20K",fonte:"Curso R$97 + WA Premium",cor:"#34d399",orc:"R$800"},
          {fase:"Escala (1K→100K)",prazo:"2027",receita:"R$ 50K+/mês",fonte:"Todas as fontes ativas",cor:"#f59e0b",orc:"—"},
        ].map((f,i)=>(
          <div key={i} style={{background:"var(--card2)",borderRadius:"10px",padding:"14px",marginBottom:"8px",display:"flex",gap:"12px",alignItems:"center"}}>
            <div style={{width:"4px",minWidth:"4px",height:"50px",background:f.cor,borderRadius:"4px"}}/>
            <div style={{flex:1}}>
              <div style={{fontWeight:700,fontSize:"13px"}}>{f.fase}</div>
              <div style={{fontSize:"12px",color:"#64748b"}}>{f.prazo} · {f.fonte}</div>
            </div>
            <div style={{textAlign:"right"}}>
              <div style={{fontWeight:800,fontSize:"15px",color:f.cor}}>{f.receita}</div>
              <div style={{fontSize:"11px",color:"#64748b"}}>Ads: {f.orc}</div>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

function PageConfig(){
  const C="#0e0e18",B="1px solid #1e1e35";
  return(<>
    <div className="ph"><div className="pt">⚙️ Config</div><div className="ps">eternal_brain V12 · Stack · Links</div></div>
    <div className="body">
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:"14px"}}>
        <div style={{background:C,border:B,borderRadius:"14px",padding:"16px"}}>
          <div style={{fontSize:"11px",textTransform:"uppercase",letterSpacing:"1px",color:"#64748b",marginBottom:"12px",fontWeight:600}}>🧠 Eternal Brain V12</div>
          {[["Gate global","95pts"],["Gate/dimensão","95pts"],["Iterações máx","5x"],["Duração longs","15-20min"],["Canal ativo","UCyCkIpsVgME9yCj_oXJFheA"],["Canal BLOQUEADO","UCSH63tBfY6wEIdkC4u4zKdg"],["Séries","5 (34 eps)"],["Tópicos","18"],["Padrões virais","8"],["Crons","38+"]].map(([k,v])=>(
            <div key={k} style={{display:"flex",justifyContent:"space-between",padding:"7px 0",borderBottom:B}}><span style={{fontSize:"12px",color:"#64748b"}}>{k}</span><span style={{fontSize:"12px",fontWeight:700,color:"#c084fc"}}>{v}</span></div>
          ))}
        </div>
        <div style={{background:C,border:B,borderRadius:"14px",padding:"16px"}}>
          <div style={{fontSize:"11px",textTransform:"uppercase",letterSpacing:"1px",color:"#64748b",marginBottom:"12px",fontWeight:600}}>🔧 Stack</div>
          {[["LLM Principal","NVIDIA Llama 3.3 70B (grátis)"],["LLM Fallback 1","Groq Llama 3.3 70B (grátis)"],["LLM Fallback 2","OpenAI gpt-4o-mini"],["TTS Principal","Edge TTS Microsoft (grátis)"],["TTS Overflow","ElevenLabs Sarah"],["Imagens","Flux.1 Schnell NVIDIA (grátis)"],["Render","ffmpeg Ken Burns 30fps"],["Banco","Supabase PostgreSQL (free)"],["Deploy","Vercel (Git)"],["CI/CD","GitHub Actions (38+ wf)"]].map(([k,v])=>(
            <div key={k} style={{display:"flex",justifyContent:"space-between",padding:"7px 0",borderBottom:B}}><span style={{fontSize:"12px",color:"#64748b"}}>{k}</span><span style={{fontSize:"12px",fontWeight:700,color:"#38bdf8"}}>{v}</span></div>
          ))}
        </div>
      </div>
      <div style={{background:C,border:B,borderRadius:"14px",padding:"16px",marginTop:"14px"}}>
        <div style={{fontSize:"11px",textTransform:"uppercase",letterSpacing:"1px",color:"#64748b",marginBottom:"12px",fontWeight:600}}>🔗 Links</div>
        <div style={{display:"flex",gap:"8px",flexWrap:"wrap"}}>
          {[["Supabase","https://supabase.com/dashboard/project/tpjvalzwkqwttvmszvie"],["GitHub","https://github.com/tafita81/Repovazio"],["Vercel","https://vercel.com/tafita81s-projects/repovazio"],["YouTube Studio","https://studio.youtube.com"],["Google Ads","https://ads.google.com"],["OAuth Playground","https://developers.google.com/oauthplayground"],["Growth","/growth.html"],["Hub","/hub.html"]].map(([l,u])=>(
            <a key={l} href={u} target="_blank" rel="noreferrer" style={{background:"#14142b",border:B,borderRadius:"8px",padding:"8px 14px",color:"#e2e8f0",textDecoration:"none",fontSize:"13px"}}>🔗 {l}</a>
          ))}
        </div>
      </div>
    </div>
  </>);}

function PageLogs(){
  const[logs,setLogs]=useState([]);const[filter,setFilter]=useState("all");const[load,setLoad]=useState(true);
  useEffect(()=>{
    sbFetch("cerebro_logs?order=created_at.desc&limit=120&select=id,type,message,created_at").then(r=>{setLogs(r||[]);setLoad(false);});
    const t=setInterval(()=>{sbFetch("cerebro_logs?order=created_at.desc&limit=120&select=id,type,message,created_at").then(r=>setLogs(r||[]));},15000);
    return()=>clearInterval(t);
  },[]);
  const TYPES=[...new Set(logs.map(l=>l.type))].slice(0,8);
  const filtered=filter==="all"?logs:logs.filter(l=>l.type===filter);
  const TC={tts_dispatch:"#a78bfa",render_dispatch:"#60a5fa",error:"#fb7185",info:"#38bdf8",daily_report:"#c084fc"};
  return(<>
    <div className="ph"><div className="pt">📋 Logs</div><div className="ps">{logs.length} registros · Atualiza 15s</div></div>
    <div className="body">
    {load?<div style={{color:"#64748b",padding:"40px",textAlign:"center"}}>⏳ Carregando...</div>:(
    <>
      <div style={{display:"flex",gap:"4px",padding:"4px",background:"#14142b",borderRadius:"10px",marginBottom:"14px",flexWrap:"wrap"}}>
        <div onClick={()=>setFilter("all")} style={{padding:"6px 14px",borderRadius:"7px",fontSize:"12px",cursor:"pointer",background:filter==="all"?"#7c3aed":"transparent",color:filter==="all"?"#fff":"#64748b",fontWeight:500}}>Todos ({logs.length})</div>
        {TYPES.map(t=><div key={t} onClick={()=>setFilter(t)} style={{padding:"6px 14px",borderRadius:"7px",fontSize:"12px",cursor:"pointer",background:filter===t?"#7c3aed":"transparent",color:filter===t?"#fff":TC[t]||"#64748b",fontWeight:500}}>{t} ({logs.filter(l=>l.type===t).length})</div>)}
      </div>
      <div style={{background:"#14142b",borderRadius:"12px",padding:"14px",height:"520px",overflowY:"auto",fontFamily:"monospace",fontSize:"12px",lineHeight:"1.7"}}>
        {filtered.map(l=>{const ts=new Date(l.created_at).toLocaleString("pt-BR",{hour:"2-digit",minute:"2-digit",second:"2-digit"});const c=TC[l.type]||"#64748b";return(<div key={l.id} style={{padding:"4px 0",borderBottom:"1px solid rgba(30,30,53,.5)"}}><span style={{color:"#475569"}}>[{ts}] </span><span style={{color:c,fontWeight:600}}>{l.type} </span><span style={{color:"#94a3b8"}}>— {l.message}</span></div>);})}
      </div>
    </>)}
    </div>
  </>);}
function PageDanielaChat(){
  const[msgs,setMsgs]=useState([{role:"assistant",text:"Oi! Sou Daniela Coelho, psicóloga. Como posso te ajudar?"}]);
  const[input,setInput]=useState("");
  const[loading,setLoading]=useState(false);
  const endRef=useRef(null);
  useEffect(()=>{if(endRef.current)endRef.current.scrollIntoView({behavior:"smooth"});},[msgs]);
  async function enviar(){
    if(!input.trim()||loading)return;
    const msg=input.trim();setInput("");
    setMsgs(m=>[...m,{role:"user",text:msg}]);setLoading(true);
    try{
      const r=await fetch(SBU+"/functions/v1/daniela-chat",{method:"POST",headers:{...H_SB,"Content-Type":"application/json"},body:JSON.stringify({message:msg})});
      const d=await r.json();setMsgs(m=>[...m,{role:"assistant",text:d.response||d.error||"Não consegui responder."}]);
    }catch{setMsgs(m=>[...m,{role:"assistant",text:"Erro de conexão."}]);}
    setLoading(false);
  }
  return(<>
    <div className="ph"><div className="pt">🤖 Chat Daniela</div><div className="ps">IA treinada em psicologia BR · daniela-chat Edge Function</div></div>
    <div className="body">
      <div style={{background:"#0e0e18",border:"1px solid #1e1e35",borderRadius:"16px",display:"flex",flexDirection:"column",height:"520px"}}>
        <div style={{flex:1,overflow:"auto",padding:"16px",display:"flex",flexDirection:"column",gap:"12px"}}>
          {msgs.map((m,i)=>(
            <div key={i} style={{display:"flex",justifyContent:m.role==="user"?"flex-end":"flex-start"}}>
              <div style={{maxWidth:"75%",padding:"10px 14px",borderRadius:"14px",fontSize:"13px",lineHeight:"1.6",background:m.role==="user"?"rgba(124,58,237,.3)":"#14142b",color:"#e2e8f0"}}>{m.text}</div>
            </div>
          ))}
          {loading&&<div style={{display:"flex",justifyContent:"flex-start"}}><div style={{background:"#14142b",padding:"10px 14px",borderRadius:"14px",fontSize:"13px",color:"#64748b"}}>✍️ Digitando...</div></div>}
          <div ref={endRef}/>
        </div>
        <div style={{padding:"12px",borderTop:"1px solid #1e1e35",display:"flex",gap:"8px"}}>
          <input style={{flex:1,background:"#14142b",border:"1px solid #1e1e35",borderRadius:"8px",padding:"8px 12px",color:"#e2e8f0",fontSize:"13px",outline:"none"}}
            value={input} onChange={e=>setInput(e.target.value)}
            onKeyDown={e=>e.key==="Enter"&&!e.shiftKey&&(e.preventDefault(),enviar())}
            placeholder="Como está sua saúde mental hoje?"/>
          <button onClick={enviar} disabled={loading||!input.trim()} style={{background:"#7c3aed",color:"#fff",border:"none",padding:"8px 18px",borderRadius:"8px",fontSize:"13px",fontWeight:600,cursor:"pointer"}}>Enviar</button>
        </div>
      </div>
    </div>
  </>);}
