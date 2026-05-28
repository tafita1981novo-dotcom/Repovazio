import { NextResponse } from 'next/server';
export const runtime = 'nodejs';

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const t = searchParams.get('t') || '';
  const html = `<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>Dice Auto-Apply</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,sans-serif;background:#09090f;color:#fff;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:24px 16px}
h1{font-size:1.5rem;color:#7C3AED;margin:20px 0 4px;text-align:center;font-weight:700}
.sub{font-size:.9rem;color:#6b7280;margin-bottom:24px;text-align:center}
.card{background:#111827;border:1px solid #1f2937;border-radius:16px;padding:22px;width:100%;max-width:440px}
.step{display:flex;gap:12px;align-items:flex-start;padding:12px 0;border-bottom:1px solid #1f2937}
.step:last-child{border-bottom:none}
.num{background:#7C3AED;color:#fff;border-radius:50%;width:30px;height:30px;min-width:30px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.9rem}
.txt{font-size:.88rem;line-height:1.55;color:#d1d5db;padding-top:4px}
.txt strong{color:#fff;display:block;margin-bottom:4px}
.code{background:#0a0a14;border:1px solid #2d2d4e;border-radius:8px;padding:10px;font-family:monospace;font-size:.7rem;color:#a78bfa;word-break:break-all;margin-top:8px;cursor:pointer;line-height:1.5}
.hint{color:#4b5563;font-size:.72rem;margin-top:4px}
input{width:100%;background:#0f172a;border:2px solid #1f2937;border-radius:10px;padding:14px;color:#fff;font-size:.95rem;margin-top:10px;outline:none}
input:focus{border-color:#7C3AED}
input::placeholder{color:#4b5563}
.btn{width:100%;background:#7C3AED;color:#fff;border:none;border-radius:12px;padding:15px;font-size:1rem;font-weight:600;cursor:pointer;margin-top:12px}
.btn:active{background:#5B21B6}
.status{border-radius:10px;padding:14px;margin-top:14px;font-size:.85rem;line-height:1.65;display:none}
.ok{background:#052e16;border:1px solid #14532d;color:#4ade80}
.err{background:#2d0808;border:1px solid #7f1d1d;color:#fca5a5}
.warn{background:#1a1200;border:1px solid #92400e;color:#fbbf24}
</style></head>
<body>
<h1>🎲 Dice Auto-Apply</h1>
<p class="sub">Configure uma vez — sistema aplica todo dia sozinho</p>
<div class="card">
  <div class="step"><div class="num">1</div><div class="txt"><strong>Abra dice.com no Safari (já logado)</strong>Não feche esta aba</div></div>
  <div class="step"><div class="num">2</div><div class="txt">
    <strong>Cole este código na barra de endereço do Dice:</strong>
    <div class="code" id="bm" onclick="copyBM()">javascript:(function(){var ks=['access_token','id_token','token','dice_token','authToken'];var t='';for(var i=0;i<ks.length;i++){try{t=localStorage.getItem(ks[i]);if(t&&t.length>20)break;}catch(e){}}if(!t){var cs=document.cookie.split(';');for(var j=0;j<cs.length;j++){var p=cs[j].trim().split('=');if(/access|token|auth/i.test(p[0])&&p[1]&&p[1].length>20){t=p.slice(1).join('=');break;}}}if(t){location.href='https://repovazio.vercel.app/api/dice-setup?t='+encodeURIComponent(t);}else{alert('Chaves localStorage: '+Object.keys(localStorage).filter(function(x){return x.length<30}).slice(0,8).join(', '));}})();</div>
    <p class="hint">👆 Toque para copiar · Cole na barra URL do Dice · Enter</p>
  </div></div>
  <div class="step"><div class="num">3</div><div class="txt"><strong>Ou cole o token manualmente:</strong></div></div>
  <input id="ti" placeholder="Cole o token aqui..." oninput="onInput(this.value)">
  <button class="btn" onclick="save()">✅ Salvar Token — Ativar Dice Auto-Apply</button>
  <div class="status" id="st"></div>
</div>
<script>
const S='https://tpjvalzwkqwttvmszvie.supabase.co';
const K='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRwanZhbHp3a3F3dHR2bXN6dmllIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYwMzUyOTMsImV4cCI6MjA5MTYxMTI5M30.UEgUo0Mw15ihQZykLAY5QApRzgTXkfIewZFzIgwao3Q';
const initToken='${t.replace("'", "\'")}';
window.onload=function(){if(initToken&&initToken.length>10){document.getElementById('ti').value=initToken;show('warn','🔑 Token detectado! Toque Salvar.');}};
function copyBM(){navigator.clipboard&&navigator.clipboard.writeText(document.getElementById('bm').innerText).then(()=>{document.getElementById('bm').textContent='✅ Copiado! Cole na barra URL do Dice';setTimeout(()=>location.reload(),2200);});}
function onInput(v){if(v.length>30)show('warn','Token '+v.length+' chars. Toque Salvar.');}
function show(cls,msg){const el=document.getElementById('st');el.style.display='block';el.className='status '+cls;el.innerHTML=msg;}
async function save(){
  const t=document.getElementById('ti').value.trim();
  if(!t||t.length<15){show('err','❌ Token muito curto.');return;}
  show('warn','⏳ Salvando...');
  try{
    const r=await fetch(S+'/rest/v1/ia_cache',{method:'POST',
      headers:{'apikey':K,'Authorization':'Bearer '+K,'Content-Type':'application/json','Prefer':'resolution=merge-duplicates'},
      body:JSON.stringify({cache_key:'secret:DICE_SESSION_TOKEN',value:t,expires_at:new Date(Date.now()+30*24*60*60*1000).toISOString()})});
    if(r.status<300||r.status===409){
      show('ok','<strong>✅ Token salvo! Dice Auto-Apply ativo.</strong><br>O sistema aplica automaticamente todo dia às 9h UTC.<br><small>Token: '+t.substring(0,14)+'…'+t.slice(-5)+'</small>');
    }else{throw new Error('HTTP '+r.status);}
  }catch(e){show('err','❌ Erro: '+e.message);}
}
</script></body></html>`;
  return new NextResponse(html, { headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' } });
}
