export const runtime = 'edge';

// @ts-nocheck
// app/api/criar-daniela/route.js — create daniela-ia Vercel project
import{NextResponse}from'next/server';
const VTK=process.env.VERCEL_TOKEN;
const TEAM='team_zr9vAef0Zz3njNAiGm3v5Y3h';
const GK=process.env.GROQ_API_KEY,GEK=process.env.GEMINI_API_KEY;
const PAT=process.env.GH_PAT,SBU=process.env.NEXT_PUBLIC_SUPABASE_URL,SBK=process.env.SUPABASE_SERVICE_KEY;

export async function GET(){
  if(!VTK)return NextResponse.json({error:'VERCEL_TOKEN not set'},{ status:400});
  const results={};
  
  // 1. Create project
  const pr=await fetch(`https://api.vercel.com/v10/projects?teamId=${TEAM}`,{
    method:'POST',
    headers:{Authorization:`Bearer ${VTK}`,'Content-Type':'application/json'},
    body:JSON.stringify({name:'daniela-ia',gitRepository:{type:'github',repo:'tafita81/daniela-ia'},framework:'nextjs'})
  });
  const pd=await pr.json();
  results.project={status:pr.status,id:pd.id,name:pd.name,error:pd.error?.message};
  
  const projectId=pd.id;
  if(!projectId){return NextResponse.json({error:'Project ID not returned',detail:pd});}
  
  // 2. Add env vars
  const vars=[
    {key:'GROQ_API_KEY',value:GK},
    {key:'GEMINI_API_KEY',value:GEK},
    {key:'GH_PAT',value:PAT},
    {key:'NEXT_PUBLIC_SUPABASE_URL',value:SBU},
    {key:'SUPABASE_SERVICE_KEY',value:SBK},
    {key:'VERCEL_TOKEN',value:VTK},
    {key:'VERCEL_TEAM_ID',value:TEAM}
  ].filter(e=>e.value);
  
  const envR=[];
  for(const e of vars){
    const r=await fetch(`https://api.vercel.com/v10/projects/${projectId}/env?teamId=${TEAM}`,{
      method:'POST',
      headers:{Authorization:`Bearer ${VTK}`,'Content-Type':'application/json'},
      body:JSON.stringify({key:e.key,value:e.value,type:'encrypted',target:['production','preview']})
    });
    envR.push({key:e.key,status:r.status});
  }
  results.envVars=envR;
  
  // 3. Trigger deploy
  const dr=await fetch(`https://api.vercel.com/v13/deployments?teamId=${TEAM}`,{
    method:'POST',
    headers:{Authorization:`Bearer ${VTK}`,'Content-Type':'application/json'},
    body:JSON.stringify({name:'daniela-ia',gitSource:{type:'github',repo:'tafita81/daniela-ia',ref:'main'},projectId})
  });
  const dd=await dr.json();
  results.deploy={status:dr.status,id:dd.id,url:dd.url,error:dd.error?.message};
  
  return NextResponse.json({ok:true,...results,chat_url:'https://daniela-ia.vercel.app/chat'});
}
