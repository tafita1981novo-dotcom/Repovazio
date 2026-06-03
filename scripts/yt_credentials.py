"""
🔑 yt_credentials.py — Busca credenciais YT do Supabase ia_cache
Evita necessidade de secrets adicionais no GitHub Actions
"""
import os, json, urllib.request, urllib.parse

SBU = os.getenv("SUPABASE_URL","")
SBK = os.getenv("SUPABASE_SERVICE_KEY","")

def _sb_get_secret(key):
    """Busca um secret do Supabase ia_cache"""
    if not SBU or not SBK: return ""
    req = urllib.request.Request(
        f"{SBU}/rest/v1/ia_cache?cache_key=eq.{key}&select=value",
        headers={"apikey": SBK, "Authorization": f"Bearer {SBK}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            rows = json.loads(r.read())
            return rows[0]["value"] if rows else ""
    except:
        return ""

def get_yt_credentials(project=1):
    """
    Retorna (refresh_token, client_id, client_secret) para o projeto 1 ou 2
    Prioriza variáveis de ambiente, depois busca no Supabase
    """
    if project == 2:
        rt = os.getenv("YT_REFRESH_TOKEN_2","") or _sb_get_secret("secret:YT_REFRESH_TOKEN_2")
        ci = os.getenv("YT_CLIENT_ID_2","") or _sb_get_secret("secret:YT_CLIENT_ID_2")
        cs = os.getenv("YT_CLIENT_SECRET_2","") or _sb_get_secret("secret:YT_CLIENT_SECRET_2")
    else:
        rt = os.getenv("YT_REFRESH_TOKEN","") or _sb_get_secret("secret:YT_REFRESH_TOKEN")
        ci = os.getenv("YT_CLIENT_ID","") or _sb_get_secret("secret:YT_CLIENT_ID")
        cs = os.getenv("YT_CLIENT_SECRET","") or _sb_get_secret("secret:YT_CLIENT_SECRET")
    return rt, ci, cs

def get_access_token(project=1):
    """Obtém access token via refresh token"""
    rt, ci, cs = get_yt_credentials(project)
    if not all([rt, ci, cs]):
        raise ValueError(f"Credenciais YT projeto {project} não encontradas")
    body = urllib.parse.urlencode({
        "client_id": ci, "client_secret": cs,
        "refresh_token": rt, "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=body)
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
        if "error" in data:
            raise ValueError(f"Token error: {data}")
        return data["access_token"]

if __name__ == "__main__":
    # Teste
    try:
        tok = get_access_token(1)
        print(f"✅ Projeto 1: token obtido ...{tok[-10:]}")
    except Exception as e:
        print(f"❌ Projeto 1: {e}")
    try:
        tok2 = get_access_token(2)
        print(f"✅ Projeto 2: token obtido ...{tok2[-10:]}")
    except Exception as e:
        print(f"❌ Projeto 2: {e}")
