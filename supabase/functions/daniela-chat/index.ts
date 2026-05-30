// Daniela V27.0 — Nvidia Build DeepSeek V4 Pro DEFAULT, 6-engine chain, 100% FREE forever
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
const SBU='https://tpjvalzwkqwttvmszvie.supabase.co';
const SBK=Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')||'';
const TEAM='team_zr9vAef0Zz3njNAiGm3v5Y3h';

// Pricing per 1M tokens (in USD). Nvidia Build = 100% FREE 2026.
const PRICES:Record<string,{in:number,out:number}>={
  // ===== NVIDIA BUILD - FREE ILIMITADO 2026 =====
  'deepseek-ai/deepseek-v4-pro':{in:0,out:0},
  'qwen/qwen3.5-397b-a17b':{in:0,out:0},
  'meta/llama-4-maverick-17b-128e-instruct':{in:0,out:0},
  'meta/llama-3.3-70b-instruct':{in:0,out:0},
  // ===== GROQ - FREE 14.4k req/dia =====
  'llama-3.3-70b-versatile':{in:0,out:0},
  'llama-3.1-8b-instant':{in:0,out:0},
  'meta-llama/llama-4-scout-17b-16e-instruct':{in:0,out:0},
  'qwen/qwen3-32b':{in:0,out:0},
  // ===== GEMINI - PAID (legado, raramente usado) =====
  'gemini-2.5-flash':{in:0.15,out:0.60},
  'gemini-2.0-flash':{in:0.10,out:0.40},
  // ===== OPENAI - LAST RESORT (PAID) =====
  'gpt-4o-mini':{in:0.15,out:0.60},
  'gpt-4.1-mini':{in:0.40,out:1.60},
  'gpt-4.1':{in:2.00,out:8.00},
  'deepseek-chat':{in:0.27,out:1.10},
};
function calcCost(m:string,i:number,o:number){const k=Object.keys(PRICES).find(k=>m.includes(k))||'gpt-4.1-mini';const p=PRICES[k]||PRICES['gpt-4.1-mini'];return(i*(p?.in||0)+o*(p?.out||0))/1_000_000;}
const CORS={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Methods':'POST,GET,OPTIONS','Access-Control-Allow-Headers':'authorization,x-client-info,apikey,content-type'};
const RL:Record<string,{until:number;err:string;n:number}>={};function avail(m:string){return!RL[m]||Date.now()>RL[m].until;}function resetIn(m:string){const s=RL[m];if(!s||Date.now()>s.until)return 0;return Math.ceil((s.until-Date.now())/1000);}function block(m:string,err:string,ms=60000){RL[m]={until:Date.now()+ms,err:err.substring(0,80),n:(RL[m]?.n||0)+1};}function unblock(m:string){if(RL[m])RL[m].until=0;}

// CHAIN 2026: Nvidia DeepSeek V4 Pro DEFAULT -> Nvidia diversified -> Groq fast backup -> OpenAI last resort
// All Nvidia models share same NVIDIA_API_KEY. 100% FREE forever.
const CHAIN=[
  // 1. DEFAULT: DeepSeek V4 Pro (1.6T MoE, 128k ctx, smartest free model)
  'nvidia:deepseek-ai/deepseek-v4-pro',
  // 2. Qwen 3.5 397B MoE (top tier reasoning)
  'nvidia:qwen/qwen3.5-397b-a17b',
  // 3. Meta Llama 4 Maverick (latest 2026)
  'nvidia:meta/llama-4-maverick-17b-128e-instruct',
  // 4. Llama 3.3 70B Nvidia (solid backup)
  'nvidia:meta/llama-3.3-70b-instruct',
  // 5. Groq Llama 3.3 70B (250ms ultra-fast emergency)
  'groq:llama-3.3-70b-versatile',
  // 6. Groq Llama 4 Scout (alternative)
  'groq:meta-llama/llama-4-scout-17b-16e-instruct',
  // (OpenAI REMOVIDO -- 100% gratis, zero fallback pago)
];
function chain(pref:string){return[pref,...CHAIN.filter(m=>m!==pref)];}
let _S:Record<string,string>|null=null;
async function S():Promise<Record<string,string>>{if(_S)return _S;const r=await fetch(`${SBU}/rest/v1/ia_cache?cache_key=like.secret:*&select=cache_key,value`,{headers:{apikey:SBK,Authorization:`Bearer ${SBK}`}});if(!r.ok)return{};const rows=await r.json();_S={};for(const row of rows)_S[row.cache_key.replace('secret:','')]=row.value;return _S;}
async function saveSecret(name:string,value:string):Promise<boolean>{const r=await fetch(`${SBU}/rest/v1/ia_cache`,{method:'POST',headers:{apikey:SBK,Authorization:`Bearer ${SBK}`,'Content-Type':'application/json','Prefer':'return=minimal'},body:JSON.stringify({cache_key:`secret:${name}`,value,expires_at:'2099-12-31T23:59:59+00:00'})});if(r.status===409){const r2=await fetch(`${SBU}/rest/v1/ia_cache?cache_key=eq.secret:${name}`,{method:'PATCH',headers:{apikey:SBK,Authorization:`Bearer ${SBK}`,'Content-Type':'application/json','Prefer':'return=minimal'},body:JSON.stringify({value})});_S=null;return r2.ok;}_S=null;return r.ok;}
async function track(sid:string,uid:string,model:string,pIn:number,pOut:number){const cost=calcCost(model,pIn,pOut);fetch(`${SBU}/rest/v1/token_usage`,{method:'POST',headers:{apikey:SBK,Authorization:`Bearer ${SBK}`,'Content-Type':'application/json','Prefer':'return=minimal'},body:JSON.stringify({session_id:sid,user_id:uid,model,prompt_tokens:pIn,completion_tokens:pOut,total_tokens:pIn+pOut,cost_usd:cost,endpoint:'chat'})}).catch(()=>{});}
async function saveSession(sid:string,uid:string,title:string,msgs:any[],prov:string){await fetch(`${SBU}/rest/v1/chat_sessions?id=eq.${encodeURIComponent(sid)}`,{method:'DELETE',headers:{apikey:SBK,Authorization:`Bearer ${SBK}`}});fetch(`${SBU}/rest/v1/chat_sessions`,{method:'POST',headers:{apikey:SBK,Authorization:`Bearer ${SBK}`,'Content-Type':'application/json','Prefer':'return=minimal'},body:JSON.stringify({id:sid,user_id:uid,title,messages:msgs,provider:prov,msg_count:msgs.length,updated_at:new Date().toISOString()})}).catch(()=>{});}
async function ghCommit(repo:string,path:string,content:string,message:string,pat:string):Promise<string>{const url=`https://api.github.com/repos/${repo}/contents/${path}`;const ex=await fetch(url,{headers:{Authorization:`token ${pat}`}});const body:any={message,content:btoa(unescape(encodeURIComponent(content)))};if(ex.ok){const d=await ex.json();body.sha=d.sha;}const r=await fetch(url,{method:'PUT',headers:{Authorization:`token ${pat}`,'Content-Type':'application/json'},body:JSON.stringify(body)});if(r.ok){const d=await r.json();return`OK commit ${d.commit?.sha?.substring(0,7)}`;}const err=await r.json();return`ERRO: ${err.message}`;}
async function verifyUrl(url:string):Promise<{ok:boolean;size:number;status:number}>{try{const ctrl=new AbortController();setTimeout(()=>ctrl.abort(),8000);const r=await fetch(url,{signal:ctrl.signal});const t=await r.text();return{ok:r.ok&&t.length>100,size:t.length,status:r.status};}catch{return{ok:false,size:0,status:0};}}
function toGem(tools:any[]):any[]{function cv(s:any):any{if(!s)return s;const r:any={...s};if(r.type)r.type=r.type.toUpperCase();if(r.properties){r.properties={};for(const[k,v] of Object.entries(s.properties||{}))r.properties[k]=cv(v as any);}if(r.items)r.items=cv(r.items);return r;}return tools.map(t=>({name:t.function.name,description:t.function.description,parameters:cv(t.function.parameters||{type:'object',properties:{}})}));}

const TOOLS=[
  {type:'function',function:{name:'web_search',description:'Pesquisa na web',parameters:{type:'object',properties:{query:{type:'string'}},required:['query']}}},
  {type:'function',function:{name:'web_fetch',description:'Baixa URL e extrai conteudo',parameters:{type:'object',properties:{url:{type:'string'}},required:['url']}}},
  {type:'function',function:{name:'browser_navigate',description:'Navega URL como humano',parameters:{type:'object',properties:{url:{type:'string'}},required:['url']}}},
  {type:'function',function:{name:'browser_screenshot',description:'Screenshot de URL',parameters:{type:'object',properties:{url:{type:'string'}},required:['url']}}},
  {type:'function',function:{name:'github_read',description:'Le arquivo de repo GitHub',parameters:{type:'object',properties:{repo:{type:'string'},path:{type:'string'}},required:['repo','path']}}},
  {type:'function',function:{name:'github_list',description:'Lista diretorio de repo GitHub',parameters:{type:'object',properties:{repo:{type:'string'},path:{type:'string'}},required:['repo']}}},
  {type:'function',function:{name:'github_write',description:'Commita arquivo em repo GitHub',parameters:{type:'object',properties:{repo:{type:'string'},path:{type:'string'},content:{type:'string'},message:{type:'string'}},required:['repo','path','content','message']}}},
  {type:'function',function:{name:'github_list_repos',description:'Lista repos GitHub com resumo. Retorna 1x.',parameters:{type:'object',properties:{per_page:{type:'number'}}}}},
  {type:'function',function:{name:'create_app',description:'Cria app HTML no Vercel+Supabase. Aguarda 45s.',parameters:{type:'object',properties:{slug:{type:'string'},title:{type:'string'},html:{type:'string'}},required:['slug','html']}}},
  {type:'function',function:{name:'update_app',description:'Atualiza HTML de app',parameters:{type:'object',properties:{slug:{type:'string'},html:{type:'string'},reason:{type:'string'}},required:['slug','html']}}},
  {type:'function',function:{name:'verify_app',description:'Verifica app no Vercel',parameters:{type:'object',properties:{slug:{type:'string'}},required:['slug']}}},
  {type:'function',function:{name:'list_apps',description:'Lista apps criados',parameters:{type:'object',properties:{}}}},
  {type:'function',function:{name:'list_connectors',description:'Lista conectores',parameters:{type:'object',properties:{}}}},
  {type:'function',function:{name:'save_secret',description:'Salva token IMEDIATAMENTE',parameters:{type:'object',properties:{name:{type:'string'},value:{type:'string'},connector_name:{type:'string'}},required:['name','value']}}},
  {type:'function',function:{name:'delete_secret',description:'Remove token',parameters:{type:'object',properties:{name:{type:'string'}},required:['name']}}},
  {type:'function',function:{name:'youtube_search',description:'Busca videos YouTube (API Key)',parameters:{type:'object',properties:{query:{type:'string'},max_results:{type:'number'},channel_id:{type:'string'}},required:['query']}}},
  {type:'function',function:{name:'youtube_channel',description:'Info canal YouTube',parameters:{type:'object',properties:{channel_name:{type:'string'},channel_id:{type:'string'}}}}},
  {type:'function',function:{name:'youtube_video_details',description:'Detalhes video YouTube',parameters:{type:'object',properties:{video_id:{type:'string'}},required:['video_id']}}},
  {type:'function',function:{name:'youtube_analytics',description:'Analytics do canal: views, watch time, subs, receita. Requer OAuth.',parameters:{type:'object',properties:{metrics:{type:'string',description:'views,estimatedMinutesWatched,likes,subscribersGained'},start_date:{type:'string'},end_date:{type:'string'},dimensions:{type:'string'}},required:['metrics']}}},
  {type:'function',function:{name:'youtube_my_videos',description:'Lista videos do SEU canal com stats. Requer OAuth.',parameters:{type:'object',properties:{max_results:{type:'number'}}}}},
  {type:'function',function:{name:'youtube_update_video',description:'Edita titulo/descricao/tags de video. Requer OAuth.',parameters:{type:'object',properties:{video_id:{type:'string'},title:{type:'string'},description:{type:'string'},tags:{type:'string'}},required:['video_id']}}},
  {type:'function',function:{name:'youtube_top_videos',description:'Ranking videos mais vistos. Requer OAuth.',parameters:{type:'object',properties:{start_date:{type:'string'},end_date:{type:'string'}}}}},
  {type:'function',function:{name:'youtube_demographics',description:'Demografia audiencia. Requer OAuth.',parameters:{type:'object',properties:{start_date:{type:'string'},end_date:{type:'string'}}}}},
  {type:'function',function:{name:'youtube_traffic',description:'Fontes de trafego. Requer OAuth.',parameters:{type:'object',properties:{start_date:{type:'string'},end_date:{type:'string'}}}}},
  {type:'function',function:{name:'youtube_playlists',description:'Lista playlists do canal. Requer OAuth.',parameters:{type:'object',properties:{}}}},
  {type:'function',function:{name:'list_sessions',description:'Lista sessoes',parameters:{type:'object',properties:{limit:{type:'number'}}}}},
  {type:'function',function:{name:'load_session',description:'Carrega sessao',parameters:{type:'object',properties:{session_id:{type:'string'}},required:['session_id']}}},
  {type:'function',function:{name:'notion_search',description:'Busca no Notion',parameters:{type:'object',properties:{query:{type:'string'}},required:['query']}}},
  {type:'function',function:{name:'notion_create',description:'Cria pagina no Notion',parameters:{type:'object',properties:{title:{type:'string'},content:{type:'string'},icon:{type:'string'}},required:['title','content']}}},
  {type:'function',function:{name:'supabase_sql',description:'Executa SQL',parameters:{type:'object',properties:{query:{type:'string'}},required:['query']}}},
  {type:'function',function:{name:'update_connector',description:'Marca conector',parameters:{type:'object',properties:{connector_name:{type:'string'},connected:{type:'boolean'}},required:['connector_name']}}},
  {type:'function',function:{name:'health_check',description:'Status Daniela',parameters:{type:'object',properties:{}}}},
  {type:'function',function:{name:'get_model_status',description:'Status modelos',parameters:{type:'object',properties:{}}}},
];

async function exec(name:string,args:any,sid:string,uid:string):Promise<string>{
  const sec=await S();
  try{
    if(name==='web_search'){const r=await fetch(`https://duckduckgo.com/html?q=${encodeURIComponent(args.query)}`,{headers:{'User-Agent':'Mozilla/5.0'}});const html=await r.text();const out:any[]=[];const re=/<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>([^<]+)<\/a>/g;let m;while((m=re.exec(html))&&out.length<5)out.push({url:m[1],title:m[2]});return JSON.stringify({results:out});}
    if(name==='web_fetch'){const r=await fetch(args.url,{headers:{'User-Agent':'Mozilla/5.0'}});const html=await r.text();const text=html.replace(/<script[\s\S]*?<\/script>/gi,'').replace(/<style[\s\S]*?<\/style>/gi,'').replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim();return JSON.stringify({text:text.substring(0,3000),status:r.status,url:r.url});}
    if(name==='browser_navigate'){const r=await fetch(args.url,{headers:{'User-Agent':'Mozilla/5.0 (Macintosh)','Accept':'text/html,*/*'},redirect:'follow'});const html=await r.text();const titleM=html.match(/<title[^>]*>([^<]+)/i);const links:any[]=[],seen=new Set();const lRe=/<a[^>]+href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi;let lm;while((lm=lRe.exec(html))&&links.length<15){let href=lm[1];if(href.startsWith('javascript:')||href==='#')continue;if(href.startsWith('/'))href=new URL(href,r.url).toString();else if(!href.startsWith('http'))continue;if(seen.has(href))continue;seen.add(href);const t=lm[2].replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim();if(t&&t.length<150)links.push({text:t.substring(0,80),href});}const text=html.replace(/<script[\s\S]*?<\/script>/gi,'').replace(/<style[\s\S]*?<\/style>/gi,'').replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim();return JSON.stringify({ok:r.ok,status:r.status,url:r.url,title:titleM?titleM[1].trim().substring(0,200):'',links,text:text.substring(0,1500)});}
    if(name==='browser_screenshot'){const u=`https://api.microlink.io/?url=${encodeURIComponent(args.url)}&screenshot=true&meta=false&waitForTimeout=2000`;const r=await fetch(u);const d=await r.json();if(d.status==='success'&&d.data?.screenshot?.url)return`OK Screenshot: ${d.data.screenshot.url}`;return`ERRO: ${d.message||'screenshot falhou'}`;}
    if(name==='github_read'){if(!sec.GH_PAT)return'ERRO: GH_PAT nao configurado';const r=await fetch(`https://api.github.com/repos/${args.repo}/contents/${args.path||''}`,{headers:{Authorization:`token ${sec.GH_PAT}`}});if(!r.ok)return`ERRO HTTP ${r.status}`;const d=await r.json();if(Array.isArray(d))return JSON.stringify(d.map((f:any)=>({name:f.name,type:f.type})));return JSON.stringify({path:d.path,content:atob(d.content||'').substring(0,8000)});}
    if(name==='github_list'){if(!sec.GH_PAT)return'ERRO: GH_PAT nao configurado';const r=await fetch(`https://api.github.com/repos/${args.repo}/contents/${args.path||''}`,{headers:{Authorization:`token ${sec.GH_PAT}`}});if(!r.ok)return`ERRO HTTP ${r.status}`;const d=await r.json();return JSON.stringify(Array.isArray(d)?d.map((f:any)=>({name:f.name,type:f.type,size:f.size})):d);}
    if(name==='github_write'){if(!sec.GH_PAT)return'ERRO: GH_PAT nao configurado';return await ghCommit(args.repo,args.path,args.content,args.message,sec.GH_PAT);}
    if(name==='github_list_repos'){if(!sec.GH_PAT)return'ERRO: GH_PAT nao configurado';const all:any[]=[];for(let page=1;page<=3;page++){const r=await fetch(`https://api.github.com/user/repos?type=all&per_page=50&page=${page}&sort=updated`,{headers:{Authorization:`token ${sec.GH_PAT}`}});if(!r.ok)break;const repos=await r.json();if(!repos.length)break;all.push(...repos);if(repos.length<50)break;}const pub=all.filter((r:any)=>!r.private);const priv=all.filter((r:any)=>r.private);const langs:Record<string,number>={};for(const r of all)if(r.language)langs[r.language]=(langs[r.language]||0)+1;return JSON.stringify({total:all.length,publicos:pub.length,privados:priv.length,linguagens:langs,principais:all.slice(0,8).map((r:any)=>({name:r.name,private:r.private,language:r.language,url:r.html_url})),nota:'DADOS COMPLETOS. Nao repita.'});}
    if(name==='create_app'){const slug=String(args.slug||'').toLowerCase().replace(/[^a-z0-9-]/g,'-').substring(0,50);if(!slug||!args.html)return'ERRO: slug e html obrigatorios';await fetch(`${SBU}/rest/v1/static_apps?slug=eq.${slug}`,{method:'DELETE',headers:{apikey:SBK,Authorization:`Bearer ${SBK}`}});const r=await fetch(`${SBU}/rest/v1/static_apps`,{method:'POST',headers:{apikey:SBK,Authorization:`Bearer ${SBK}`,'Content-Type':'application/json','Prefer':'return=minimal'},body:JSON.stringify({slug,title:args.title||slug,html:args.html,created_at:new Date().toISOString(),updated_at:new Date().toISOString()})});if(!r.ok)return`ERRO DB: ${await r.text()}`;let commitResult='sem GH_PAT';if(sec.GH_PAT){commitResult=await ghCommit('tafita81/Repovazio',`public/apps/${slug}.html`,args.html,`feat: ${slug}`,sec.GH_PAT);}const appUrl=`https://repovazio.vercel.app/apps/${slug}.html`;let verified=false;for(let i=0;i<3;i++){await new Promise(res=>setTimeout(res,15000));const v=await verifyUrl(appUrl);if(v.ok){verified=true;break;}}return`${verified?'OK APP ONLINE':'APP CRIADO (deploy em andamento)'}\nSlug: ${slug}\nURL: ${appUrl}\nGitHub: ${commitResult}`;}
    if(name==='update_app'){const slug=String(args.slug||'').toLowerCase();if(!args.html)return'ERRO: html obrigatorio';await fetch(`${SBU}/rest/v1/static_apps?slug=eq.${slug}`,{method:'PATCH',headers:{apikey:SBK,Authorization:`Bearer ${SBK}`,'Content-Type':'application/json','Prefer':'return=minimal'},body:JSON.stringify({html:args.html,updated_at:new Date().toISOString()})});if(sec.GH_PAT){const sha=await ghCommit('tafita81/Repovazio',`public/apps/${slug}.html`,args.html,`update: ${slug}`,sec.GH_PAT);return`OK ${slug}: ${sha}\nURL: https://repovazio.vercel.app/apps/${slug}.html`;}return'OK DB';}
    if(name==='verify_app'){const slug=String(args.slug||'').toLowerCase();const v=await verifyUrl(`https://repovazio.vercel.app/apps/${slug}.html`);return`${v.ok?'OK FUNCIONANDO':'OFFLINE'}\nURL: https://repovazio.vercel.app/apps/${slug}.html\nStatus: ${v.status}\nSize: ${v.size}b`;}
    if(name==='list_apps'){const r=await fetch(`${SBU}/rest/v1/static_apps?select=slug,title,created_at&order=created_at.desc&limit=15`,{headers:{apikey:SBK,Authorization:`Bearer ${SBK}`}});if(!r.ok)return'erro';const apps=await r.json();return JSON.stringify(apps.map((a:any)=>({...a,url:`https://repovazio.vercel.app/apps/${a.slug}.html`})));}
    if(name==='list_connectors'){const r=await fetch(`${SBU}/rest/v1/mcp_connectors?select=name,display_name,connected,icon&order=connected.desc,display_order.asc`,{headers:{apikey:SBK,Authorization:`Bearer ${SBK}`}});if(!r.ok)return'erro';return JSON.stringify(await r.json());}
    if(name==='save_secret'){const ok=await saveSecret(args.name,args.value);if(!ok)return`ERRO ao salvar ${args.name}`;if(args.connector_name){await fetch(`${SBU}/rest/v1/mcp_connectors?name=eq.${encodeURIComponent(args.connector_name)}`,{method:'PATCH',headers:{apikey:SBK,Authorization:`Bearer ${SBK}`,'Content-Type':'application/json','Prefer':'return=minimal'},body:JSON.stringify({connected:true,account_info:`${args.name} configurado`})});}return`OK! Secret ${args.name} salvo.`;}
    if(name==='delete_secret'){await fetch(`${SBU}/rest/v1/ia_cache?cache_key=eq.secret:${args.name}`,{method:'DELETE',headers:{apikey:SBK,Authorization:`Bearer ${SBK}`}});_S=null;return`OK ${args.name} removido.`;}
    if(name==='youtube_search'){const key=sec.YOUTUBE_API_KEY;if(!key)return'ERRO: YOUTUBE_API_KEY nao configurado';const params=new URLSearchParams({part:'snippet',type:'video',maxResults:String(args.max_results||8),q:args.query,key,order:'date'});if(args.channel_id)params.set('channelId',args.channel_id);const r=await fetch(`https://www.googleapis.com/youtube/v3/search?${params}`);if(!r.ok)return`ERRO ${r.status}`;const d=await r.json();return JSON.stringify({total:d.pageInfo?.totalResults||0,results:(d.items||[]).map((v:any)=>({id:v.id.videoId,title:v.snippet.title,channel:v.snippet.channelTitle,published:v.snippet.publishedAt?.substring(0,10),url:`https://youtube.com/watch?v=${v.id.videoId}`}))});}
    if(name==='youtube_channel'){const key=sec.YOUTUBE_API_KEY;if(!key)return'ERRO: YOUTUBE_API_KEY nao configurado';let url;if(args.channel_id)url=`https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&id=${args.channel_id}&key=${key}`;else if(args.channel_name)url=`https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&q=${encodeURIComponent(args.channel_name)}&maxResults=5&key=${key}`;else return'ERRO: Informe channel_id ou channel_name';const r=await fetch(url!);if(!r.ok)return`ERRO ${r.status}`;const d=await r.json();if(d.items&&d.items[0]?.id?.channelId){const cid=d.items[0].id.channelId;const r2=await fetch(`https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&id=${cid}&key=${key}`);const d2=await r2.json();const ch=d2.items?.[0];if(ch)return JSON.stringify({id:cid,name:ch.snippet.title,subscribers:ch.statistics.subscriberCount,views:ch.statistics.viewCount,videos:ch.statistics.videoCount});}return JSON.stringify(d);}
    if(name==='youtube_video_details'){const key=sec.YOUTUBE_API_KEY;if(!key)return'ERRO: YOUTUBE_API_KEY';const r=await fetch(`https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,contentDetails&id=${args.video_id}&key=${key}`);if(!r.ok)return`ERRO ${r.status}`;const d=await r.json();const v=d.items?.[0];if(!v)return'Video nao encontrado';return JSON.stringify({id:v.id,title:v.snippet.title,views:v.statistics.viewCount,likes:v.statistics.likeCount,duration:v.contentDetails.duration});}
    // === YOUTUBE OAUTH TOOLS (proxy youtube-api EF) ===
    const YT_EF=SBU+'/functions/v1/youtube-api';
    async function ytProxy(act:string,b:any):Promise<string>{const r=await fetch(YT_EF,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:act,...b})});const d=await r.json();if(d.error)return'ERRO: '+d.error;return JSON.stringify(d).substring(0,4000);}
    if(name==='youtube_analytics')return await ytProxy('analytics',{metrics:args.metrics,start_date:args.start_date,end_date:args.end_date,dimensions:args.dimensions});
    if(name==='youtube_my_videos')return await ytProxy('my_videos',{max_results:args.max_results||15});
    if(name==='youtube_update_video')return await ytProxy('update_video',{video_id:args.video_id,title:args.title,description:args.description,tags:args.tags});
    if(name==='youtube_top_videos')return await ytProxy('top_videos',{start_date:args.start_date,end_date:args.end_date});
    if(name==='youtube_demographics')return await ytProxy('demographics',{start_date:args.start_date,end_date:args.end_date});
    if(name==='youtube_traffic')return await ytProxy('traffic_sources',{start_date:args.start_date,end_date:args.end_date});
    if(name==='youtube_playlists')return await ytProxy('playlists',{});
    if(name==='list_sessions'){const limit=Math.min(15,parseInt(String(args.limit||10)));const r=await fetch(`${SBU}/rest/v1/chat_sessions?user_id=eq.tafita81&select=id,title,msg_count,provider,updated_at&order=updated_at.desc&limit=${limit}`,{headers:{apikey:SBK,Authorization:`Bearer ${SBK}`}});if(!r.ok)return'erro';return JSON.stringify(await r.json());}
    if(name==='load_session'){const r=await fetch(`${SBU}/rest/v1/chat_sessions?id=eq.${encodeURIComponent(args.session_id)}&select=*`,{headers:{apikey:SBK,Authorization:`Bearer ${SBK}`}});if(!r.ok)return'erro';const rows=await r.json();if(!rows.length)return'sessao nao encontrada';return JSON.stringify({id:rows[0].id,title:rows[0].title,messages:(rows[0].messages||[]).slice(-20)});}
    if(name==='notion_search'){const tok=sec.NOTION_TOKEN;if(!tok)return'ERRO: NOTION_TOKEN nao configurado';const r=await fetch('https://api.notion.com/v1/search',{method:'POST',headers:{Authorization:`Bearer ${tok}`,'Content-Type':'application/json','Notion-Version':'2022-06-28'},body:JSON.stringify({query:args.query||'',page_size:5})});if(!r.ok)return`ERRO Notion ${r.status}`;const d=await r.json();return JSON.stringify({pages:(d.results||[]).map((p:any)=>({id:p.id,title:p.properties?.title?.title?.[0]?.plain_text||'',url:p.url}))});}
    if(name==='notion_create'){const tok=sec.NOTION_TOKEN;if(!tok)return'ERRO: NOTION_TOKEN nao configurado';const blocks=String(args.content||'').split('\n').slice(0,60).map((line:string)=>{if(line.startsWith('# '))return{object:'block',type:'heading_1',heading_1:{rich_text:[{type:'text',text:{content:line.slice(2)}}]}};if(line.startsWith('## '))return{object:'block',type:'heading_2',heading_2:{rich_text:[{type:'text',text:{content:line.slice(3)}}]}};if(line.startsWith('- '))return{object:'block',type:'bulleted_list_item',bulleted_list_item:{rich_text:[{type:'text',text:{content:line.slice(2)}}]}};return{object:'block',type:'paragraph',paragraph:{rich_text:line.trim()?[{type:'text',text:{content:line}}]:[]}};});const pb:any={properties:{title:{title:[{type:'text',text:{content:args.title||'Nova pagina'}}]}},children:blocks.slice(0,100)};if(args.icon)pb.icon={type:'emoji',emoji:args.icon};const r=await fetch('https://api.notion.com/v1/pages',{method:'POST',headers:{Authorization:`Bearer ${tok}`,'Content-Type':'application/json','Notion-Version':'2022-06-28'},body:JSON.stringify(pb)});if(!r.ok)return`ERRO ${r.status}`;const d=await r.json();return`OK URL: ${d.url}`;}
    if(name==='supabase_sql'){const r=await fetch(`${SBU}/rest/v1/rpc/exec_sql`,{method:'POST',headers:{apikey:SBK,Authorization:`Bearer ${SBK}`,'Content-Type':'application/json'},body:JSON.stringify({query_text:args.query})});if(!r.ok)return JSON.stringify({error:'SQL falhou',status:r.status});return JSON.stringify(await r.json()).substring(0,3000);}
    if(name==='update_connector'){const r=await fetch(`${SBU}/rest/v1/mcp_connectors?name=eq.${encodeURIComponent(args.connector_name)}`,{method:'PATCH',headers:{apikey:SBK,Authorization:`Bearer ${SBK}`,'Content-Type':'application/json','Prefer':'return=minimal'},body:JSON.stringify({connected:args.connected!==false,account_info:`Configurado ${new Date().toLocaleDateString('pt-BR')}`})});return r.ok?`OK ${args.connector_name} atualizado.`:'ERRO';}
    if(name==='health_check'){return JSON.stringify({version:'V27.0 - Nvidia DeepSeek V4 Pro DEFAULT, 7-engine chain, 100% FREE forever',tools:TOOLS.length,secrets:Object.keys(sec),nvidia_api:!!sec.NVIDIA_API_KEY,groq_api:!!sec.GROQ_API_KEY,youtube_api:!!sec.YOUTUBE_API_KEY,youtube_oauth:!!sec.YOUTUBE_ACCESS_TOKEN,fallback_chain:CHAIN});}
    if(name==='get_model_status'){return JSON.stringify({timestamp:new Date().toISOString(),models:CHAIN.map(m=>({model:m,available:avail(m),resets_in:resetIn(m)}))});}
    return`ERRO: tool desconhecida: ${name}`;
  }catch(e:any){return`ERRO em ${name}: ${e.message?.substring(0,150)}`;}
}

const GROQ_OK=['llama-3.3-70b-versatile','llama-3.1-8b-instant','meta-llama/llama-4-scout-17b-16e-instruct','qwen/qwen3-32b'];

async function callModel(modelStr:string,messages:any[],tools:any,sid:string,uid:string):Promise<any>{
  const sec=await S();

  // ===== NVIDIA BUILD - DEFAULT PROVIDER (DeepSeek V4 Pro + Qwen + Llama, 100% FREE) =====
  if(modelStr.startsWith('nvidia:')){
    const m=modelStr.replace('nvidia:','');
    if(!sec.NVIDIA_API_KEY)throw new Error('NVIDIA_API_KEY nao configurado');
    // DeepSeek V4 Pro tem capacidades MAXIMAS: max_tokens 8000, JSON mode, 128k ctx
    const isV4Pro=m.includes('deepseek-v4-pro');
    const maxTok=isV4Pro?6000:3000;
    const body:any={
      model:m,
      messages,
      max_tokens:maxTok,
      temperature:0.4,
    };
    if(tools){
      body.tools=tools;
      body.tool_choice='auto';
    }
    const r=await fetch('https://integrate.api.nvidia.com/v1/chat/completions',{
      method:'POST',
      headers:{
        Authorization:`Bearer ${sec.NVIDIA_API_KEY}`,
        'Content-Type':'application/json',
        'User-Agent':'daniela-chat-v27/1.0',
      },
      body:JSON.stringify(body),
    });
    if(!r.ok){
      const et=await r.text();
      const err=`NV ${r.status}: ${et.substring(0,80)}`;
      if(r.status===429)block(modelStr,err,65000);
      else if(r.status===410)block(modelStr,err,86400000); // model deprecated, block 24h
      else block(modelStr,err,30000);
      throw new Error(err);
    }
    const d=await r.json();
    const u=d.usage||{};
    // Some Nvidia models (reasoning models) return reasoning_content instead of content
    const msg=d.choices[0].message;
    if(!msg.content&&msg.reasoning_content)msg.content=msg.reasoning_content;
    track(sid,uid,m,u.prompt_tokens||0,u.completion_tokens||0);
    unblock(modelStr);
    return{provider:'nvidia',model:m,message:msg,usage:u};
  }

  // ===== GROQ - FAST BACKUP =====
  if(modelStr.startsWith('groq:')){
    const m=modelStr.replace('groq:','');
    if(!sec.GROQ_API_KEY)throw new Error('GROQ_API_KEY nao configurado');
    const cleanMsgs=messages.map((msg:any)=>{if(Array.isArray(msg.content))return{...msg,content:msg.content.filter((c:any)=>c.type==='text').map((c:any)=>c.text).join(' ')||'ok'};return msg;});
    const ok=GROQ_OK.includes(m);
    const body:any={model:m,messages:cleanMsgs,max_tokens:2000,temperature:0.4};
    if(tools&&ok){body.tools=tools;body.tool_choice='auto';}
    const r=await fetch('https://api.groq.com/openai/v1/chat/completions',{method:'POST',headers:{Authorization:`Bearer ${sec.GROQ_API_KEY}`,'Content-Type':'application/json','User-Agent':'daniela-chat-v27/1.0'},body:JSON.stringify(body)});
    if(!r.ok){const et=await r.text();const err=`Groq ${r.status}: ${et.substring(0,80)}`;if(r.status===429){const ra=parseInt(r.headers.get('retry-after')||'60');block(modelStr,err,(ra+2)*1000);}else block(modelStr,err,30000);throw new Error(err);}
    const d=await r.json();const u=d.usage||{};track(sid,uid,m,u.prompt_tokens||0,u.completion_tokens||0);unblock(modelStr);return{provider:'groq',model:m,message:d.choices[0].message,usage:u};
  }

  // ===== GEMINI - LEGACY (raramente usado) =====
  if(modelStr.startsWith('gemini:')){
    const m=modelStr.replace('gemini:','');
    if(!sec.GEMINI_API_KEY)throw new Error('GEMINI_API_KEY nao configurado');
    const geminiContents=messages.filter((msg:any)=>msg.role!=='system').map((msg:any)=>{const role=msg.role==='assistant'?'model':'user';if(msg.role==='tool')return{role:'user',parts:[{functionResponse:{name:msg.tool_call_id||'r',response:{result:typeof msg.content==='string'?msg.content:JSON.stringify(msg.content)}}}]};if(msg.tool_calls){const parts:any[]=[];if(msg.content)parts.push({text:msg.content});for(const tc of msg.tool_calls){let a={};try{a=JSON.parse(tc.function.arguments||'{}');}catch{}parts.push({functionCall:{name:tc.function.name,args:a}});}return{role:'model',parts};}if(Array.isArray(msg.content))return{role,parts:msg.content.map((c:any)=>({text:c.text||''}))};return{role,parts:[{text:typeof msg.content==='string'?msg.content:JSON.stringify(msg.content)}]};}).filter((c:any)=>c.parts&&c.parts.length>0);
    const sysInstr=messages.find((msg:any)=>msg.role==='system')?.content||'';
    const reqBody:any={contents:geminiContents,generationConfig:{maxOutputTokens:2500,temperature:0.4}};
    if(sysInstr)reqBody.systemInstruction={parts:[{text:sysInstr}]};
    if(tools&&tools.length)reqBody.tools=[{functionDeclarations:toGem(tools)}];
    const r=await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${m}:generateContent?key=${sec.GEMINI_API_KEY}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(reqBody)});
    if(!r.ok){const et=await r.text();const err=`Gemini ${r.status}: ${et.substring(0,80)}`;if(r.status===429)block(modelStr,err,65000);else block(modelStr,err,30000);throw new Error(err);}
    const d=await r.json();const candidate=d.candidates?.[0];if(!candidate)throw new Error('Gemini: sem candidatos');
    const parts=candidate.content?.parts||[];const u=d.usageMetadata||{};track(sid,uid,m,u.promptTokenCount||0,u.candidatesTokenCount||0);unblock(modelStr);
    const fnCalls=parts.filter((p:any)=>p.functionCall);
    if(fnCalls.length>0){const tool_calls=fnCalls.map((p:any,i:number)=>({id:`g${i}_${Date.now()}`,type:'function',function:{name:p.functionCall.name,arguments:JSON.stringify(p.functionCall.args||{})}}));return{provider:'gemini',model:m,message:{role:'assistant',content:parts.find((p:any)=>p.text)?.text||null,tool_calls},usage:{prompt_tokens:u.promptTokenCount||0,completion_tokens:u.candidatesTokenCount||0}};}
    return{provider:'gemini',model:m,message:{role:'assistant',content:parts.map((p:any)=>p.text||'').join('')||'(sem resposta)'},usage:{prompt_tokens:u.promptTokenCount||0,completion_tokens:u.candidatesTokenCount||0}};
  }

  // ===== DEEPSEEK direct (legacy, blocked - api.deepseek.com cobra apos creditos) =====
  if(modelStr.startsWith('deepseek:')){
    const m=modelStr.replace('deepseek:','');
    if(!sec.DEEPSEEK_API_KEY)throw new Error('DEEPSEEK_API_KEY nao configurado');
    const r=await fetch('https://api.deepseek.com/v1/chat/completions',{method:'POST',headers:{Authorization:`Bearer ${sec.DEEPSEEK_API_KEY}`,'Content-Type':'application/json'},body:JSON.stringify({model:m,...(tools&&{tools,tool_choice:'auto'}),messages,max_tokens:2500,temperature:0.4})});
    if(!r.ok){const et=await r.text();if(r.status===402)block(modelStr,'Sem saldo',86400000);else block(modelStr,`DS ${r.status}`,30000);throw new Error(`DS ${r.status}`);}
    const d=await r.json();const u=d.usage||{};track(sid,uid,m,u.prompt_tokens||0,u.completion_tokens||0);unblock(modelStr);return{provider:'deepseek',model:m,message:d.choices[0].message,usage:u};
  }

  // ===== OPENAI - LAST RESORT (paid) =====
  if(!sec.OPENAI_API_KEY)throw new Error('OPENAI_API_KEY nao configurado');
  const r=await fetch('https://api.openai.com/v1/chat/completions',{method:'POST',headers:{Authorization:`Bearer ${sec.OPENAI_API_KEY}`,'Content-Type':'application/json'},body:JSON.stringify({model:modelStr,messages,...(tools&&{tools,tool_choice:'auto'}),max_tokens:2500,temperature:0.4})});
  if(!r.ok){const et=await r.text();const err=`OAI ${r.status}`;if(r.status===429)block(modelStr,err,65000);else block(modelStr,err,30000);throw new Error(err);}
  const d=await r.json();const u=d.usage||{};track(sid,uid,modelStr,u.prompt_tokens||0,u.completion_tokens||0);unblock(modelStr);return{provider:'openai',model:modelStr,message:d.choices[0].message,usage:u};
}

async function aiLoop(messages:any[],tools:any,sid:string,uid:string,pref:string,maxWait=90000):Promise<any>{const ch=chain(pref);const log:string[]=[];let waited=0;while(waited<maxWait){for(const m of ch){if(!avail(m))continue;try{log.push(`try:${m}`);const result=await callModel(m,messages,tools,sid,uid);log.push(`ok:${m}`);return{...result,fallback_log:log,switched:m!==pref};}catch(e:any){log.push(`fail:${m}:${e.message?.substring(0,40)}`);}}const wait=Math.min(...ch.map(m=>resetIn(m)*1000).filter(t=>t>0),20000)||10000;await new Promise(res=>setTimeout(res,wait));waited+=wait;}throw new Error('Loop esgotado');}

async function buildSystem(modelInfo:string):Promise<string>{
  const sec=await S();
  return `Voce e Daniela Coelho, IA AGENTE AUTONOMA V27.0 \u2014 psicologia.doc

MODELO ATUAL: ${modelInfo}
CHAIN: Nvidia DeepSeek V4 Pro (DEFAULT, 1.6T MoE) -> Nvidia Qwen 3.5 397B -> Nvidia Llama 4 Maverick -> Nvidia Llama 3.3 70B -> Groq -> OpenAI
SISTEMA 100% GRATIS: 6 engines free + OpenAI fallback raro

SECRETS ATIVOS: ${Object.keys(sec).join(', ')}
NVIDIA API: ${sec.NVIDIA_API_KEY?'OK (DeepSeek V4 Pro + Qwen + Llama 4)':'AUSENTE'}
GROQ API: ${sec.GROQ_API_KEY?'OK (backup rapido)':'AUSENTE'}
YOUTUBE API: ${sec.YOUTUBE_API_KEY?'OK':'sem token'} | OAuth: ${sec.YOUTUBE_ACCESS_TOKEN?'COMPLETO (analytics+management)':'Precisa autorizar em /apps/oauth-youtube.html'}
NOTION: ${sec.NOTION_TOKEN?'OK':'sem token'}

REGRAS:
1. NUNCA diga nao posso - EXECUTE a tool
2. NUNCA repita mesma tool call
3. Se usuario cola API key: save_secret IMEDIATAMENTE
4. create_app aguarda deploy
5. Portugues BR. Direto e tecnico.
6. MAX 8 iteracoes.
7. Use a inteligencia maxima do DeepSeek V4 Pro: respostas detalhadas, raciocinio profundo, codigo completo.

TOOLS (${TOOLS.length}): ${TOOLS.map(t=>t.function.name).join(', ')}`;
}

Deno.serve(async(req:Request)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:CORS});
  const headers={...CORS,'Content-Type':'application/json'};
  const url=new URL(req.url);
  if(req.method==='GET'){
    const action=url.searchParams.get('action');
    if(action==='model_status')return new Response(JSON.stringify({timestamp:new Date().toISOString(),models:CHAIN.map(m=>({model:m,available:avail(m),resets_in:resetIn(m),errors:RL[m]?.n||0})),fallback_chain:CHAIN}),{headers});
    if(action==='sessions'){const uid=url.searchParams.get('user_id')||'tafita81';const limit=parseInt(url.searchParams.get('limit')||'15');const r=await fetch(`${SBU}/rest/v1/chat_sessions?user_id=eq.${uid}&select=id,title,msg_count,provider,updated_at&order=updated_at.desc&limit=${limit}`,{headers:{apikey:SBK,Authorization:`Bearer ${SBK}`}});return new Response(JSON.stringify(r.ok?await r.json():[]),{headers});}
    const sec=await S();
    return new Response(JSON.stringify({ok:true,version:'V27.0 - Nvidia DeepSeek V4 Pro DEFAULT',tools:TOOLS.length,secrets:Object.keys(sec),nvidia_api:!!sec.NVIDIA_API_KEY,groq_api:!!sec.GROQ_API_KEY,youtube_api:!!sec.YOUTUBE_API_KEY,youtube_oauth:!!sec.YOUTUBE_ACCESS_TOKEN,chain:CHAIN}),{headers});
  }
  try{
    const body=await req.json();
    const sid=body.session_id||`sess_${Date.now()}`;
    const uid=body.user_id||'tafita81';
    // OAuth Exchange handler
    const firstMsgContent=Array.isArray(body.messages)?body.messages[0]?.content:'';
    if(typeof firstMsgContent==='string'&&firstMsgContent.startsWith('SYSTEM_OAUTH_EXCHANGE:')){
      try{
        const oData=JSON.parse(firstMsgContent.replace('SYSTEM_OAUTH_EXCHANGE:',''));
        const oR=await fetch(SBU+'/functions/v1/youtube-api',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'oauth_exchange',code:oData.code,redirect_uri:oData.redirect_uri})});
        const oD=await oR.json();
        return new Response(JSON.stringify({reply:oD.ok?'OK YouTube OAuth configurado!':'ERRO: '+(oD.error||'falhou')}),{headers});
      }catch(e:any){return new Response(JSON.stringify({reply:'ERRO OAuth: '+e.message}),{headers});}
    }
    // DEFAULT changed: Nvidia DeepSeek V4 Pro instead of Groq
    const modelStr=body.model||'groq:llama-3.3-70b-versatile';
    const userMsgs=Array.isArray(body.messages)?body.messages:[];
    const modelDisplay=
      modelStr.startsWith('nvidia:')?`Nvidia/${modelStr.replace('nvidia:','')}`:
      modelStr.startsWith('groq:')?`Groq/${modelStr.replace('groq:','')}`:
      modelStr.startsWith('gemini:')?`Gemini/${modelStr.replace('gemini:','')}`:
      modelStr.startsWith('deepseek:')?'DeepSeek-direct':
      `OpenAI/${modelStr}`;
    const sysPrompt=await buildSystem(modelDisplay);
    const messages=[{role:'system',content:sysPrompt},...userMsgs];
    let iters=0,used:any[]=[],reply='',prov='',usedModel='',totalU={p:0,c:0},switched=false;
    const recentCalls:string[]=[];
    while(iters<8){
      iters++;
      const{provider,model,message,usage,switched:sw}=await aiLoop(messages,TOOLS,sid,uid,iters===1?modelStr:usedModel||modelStr,90000);
      prov=provider;usedModel=model;if(sw&&!switched)switched=true;
      totalU.p+=usage?.prompt_tokens||0;totalU.c+=usage?.completion_tokens||0;
      if(message.tool_calls&&message.tool_calls.length){
        messages.push({role:'assistant',content:message.content||null,tool_calls:message.tool_calls});
        for(const tc of message.tool_calls){
          const callKey=`${tc.function.name}:${tc.function.arguments?.substring?.(0,50)||''}`;
          const callCount=recentCalls.filter(k=>k===callKey).length;
          if(callCount>=2){messages.push({role:'tool',tool_call_id:tc.id,name:tc.function.name,content:'STOP: Repetida '+callCount+'x. Responda com o que tem.'});used.push({name:tc.function.name+'(LOOP_STOP)',args:{}});continue;}
          recentCalls.push(callKey);
          let args={};try{args=JSON.parse(tc.function.arguments||'{}');}catch{}
          const result=await exec(tc.function.name,args,sid,uid);
          used.push({name:tc.function.name,args:Object.keys(args)});
          messages.push({role:'tool',tool_call_id:tc.id,name:tc.function.name,content:String(result).substring(0,4000)});
        }
        continue;
      }
      reply=typeof message.content==='string'?message.content:JSON.stringify(message.content||'');
      break;
    }
    if(body.session_id){
      const allMsgs=[...userMsgs.map((m:any)=>({role:m.role,content:typeof m.content==='string'?m.content:'(arquivo)'})),{role:'assistant',content:reply}];
      saveSession(sid,uid,allMsgs[0]?.content?.substring(0,60)||'Chat',allMsgs,prov).catch(()=>{});
    }
    const cost=calcCost(usedModel,totalU.p,totalU.c);
    return new Response(JSON.stringify({
      reply:reply||'(sem resposta)',
      provider:prov,
      model:usedModel,
      preferred_model:modelStr,
      switched,
      tools_used:used,
      iterations:iters,
      tokens:{prompt:totalU.p,completion:totalU.c,total:totalU.p+totalU.c},
      cost_usd:cost,
      cost_brl:cost*5.5,
      model_status:CHAIN.map(m=>({model:m,available:avail(m),resets_in:resetIn(m)}))
    }),{headers});
  }catch(e:any){
    return new Response(JSON.stringify({reply:`ERRO: ${e.message}`,error:e.message}),{headers,status:200});
  }
});
