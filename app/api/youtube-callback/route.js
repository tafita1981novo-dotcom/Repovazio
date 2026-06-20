
import { NextResponse } from 'next/server';

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const code = searchParams.get('code');
  const error = searchParams.get('error');
  
  if (error) {
    return new Response(`<h1>Erro: ${error}</h1>`, {headers: {'Content-Type': 'text/html'}});
  }
  
  if (!code) {
    return new Response('<h1>Sem codigo OAuth</h1>', {headers: {'Content-Type': 'text/html'}});
  }
  
  const CLIENT_ID = process.env.YT_CLIENT_ID || '552651753048-p26lb7afjs5f75nvfrmmf4eb1ps4sc98.apps.googleusercontent.com';
  const CLIENT_SECRET = process.env.YT_CLIENT_SECRET || '';
  const REDIRECT = 'https://repovazio.vercel.app/api/youtube-callback';
  
  const tokenResp = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_id: CLIENT_ID,
      client_secret: CLIENT_SECRET,
      code,
      grant_type: 'authorization_code',
      redirect_uri: REDIRECT
    })
  });
  
  const tokens = await tokenResp.json();
  
  const refreshToken = tokens.refresh_token || '';
  const accessToken = (tokens.access_token || '').substring(0, 50);
  
  const html = `<!DOCTYPE html>
<html>
<head><title>YouTube OAuth OK</title>
<style>body{font-family:monospace;max-width:800px;margin:50px auto;padding:20px;}
.token{background:#f0f0f0;padding:15px;word-break:break-all;margin:10px 0;border:1px solid #ccc;}
h1{color:green;} .err{color:red;}
button{background:#333;color:white;padding:10px 20px;border:none;cursor:pointer;font-size:14px;margin:5px;}
</style></head>
<body>
<h1>AUTORIZADO!</h1>
<h3>Refresh Token (permanente):</h3>
<div class="token" id="rt">${refreshToken}</div>
<button onclick="navigator.clipboard.writeText(document.getElementById('rt').textContent).then(()=>alert('Copiado!'))">Copiar Refresh Token</button>
<br><br>
<h3>Proximos passos:</h3>
<ol>
<li>Copie o Refresh Token acima</li>
<li>Va em: github.com/tafita1981novo-dotcom/Repovazio/settings/secrets/actions</li>
<li>Crie o secret: <strong>YOUTUBE_REFRESH_TOKEN_NEW</strong></li>
<li>Cole o refresh token como valor</li>
<li>Execute o workflow: <strong>upload_noise_to_youtube.yml</strong></li>
</ol>
</body></html>`;
  
  return new Response(html, {headers: {'Content-Type': 'text/html'}});
}
