import "jsr:@supabase/functions-js/edge-runtime.d.ts";
const SBU=Deno.env.get('SUPABASE_URL')||'https://tpjvalzwkqwttvmszvie.supabase.co';
const SBK=Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')||'';
const H={'apikey':SBK,'Authorization':'Bearer '+SBK,'Content-Type':'application/json','Prefer':'resolution=merge-duplicates'};
const CORS={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Methods':'POST,OPTIONS','Access-Control-Allow-Headers':'*'};
const SECRETS={
  'YOUTUBE_STREAM_KEY_ACTIVE':'ewme-91sq-yae7-yj1q-5skw',
  'YOUTUBE_STREAM_KEY':'ewme-91sq-yae7-yj1q-5skw',
  'YOUTUBE_STREAM_KEY_DEFAULT':'uaqu-vx24-86d8-r0wy-0jwc',
};
Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:CORS});
  const results=[];
  for(const[k,v]of Object.entries(SECRETS)){
    const r=await fetch(SBU+'/rest/v1/ia_cache',{method:'POST',headers:H,body:JSON.stringify({cache_key:'secret:'+k,value:v})});
    results.push({key:k,ok:r.ok,status:r.status});
  }
  return new Response(JSON.stringify({ok:true,saved:results}),{headers:{...CORS,'Content-Type':'application/json'}});
});
