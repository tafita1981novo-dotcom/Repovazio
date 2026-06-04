#!/usr/bin/env python3
"""Diagnóstico do erro 400 no upload do YouTube"""
import os, sys, json, urllib.request, urllib.parse, pathlib, tempfile

YT_CLIENT_ID     = os.environ.get("YT_CLIENT_ID","")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET","")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN","")
SBU = os.environ.get("SUPABASE_URL","")
SBK = os.environ.get("SUPABASE_SERVICE_KEY","")

def get_token():
    data = urllib.parse.urlencode({
        "client_id": YT_CLIENT_ID, "client_secret": YT_CLIENT_SECRET,
        "refresh_token": YT_REFRESH_TOKEN, "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    req.add_header("Content-Type","application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.loads(r.read())
    tok = d.get("access_token","")
    print(f"Token: {tok[:30]}... scope={d.get('scope','?')[:80]}")
    return tok

def check_scopes(token):
    """Verifica os escopos do token"""
    req = urllib.request.Request(f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read())
        print(f"Escopos: {d.get('scope','?')}")
        print(f"Email: {d.get('email','?')}")
        return "youtube" in d.get("scope","").lower()
    except Exception as e:
        print(f"Erro ao verificar token: {e}")
        return False

def test_minimal_upload(token):
    """Testa upload mínimo com arquivo de teste"""
    # Criar MP4 mínimo válido (1 segundo, preto)
    import subprocess
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tf:
        tmp_path = tf.name

    # Gerar MP4 mínimo com ffmpeg/imageio
    try:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except:
        import shutil
        ffmpeg = shutil.which("ffmpeg") or "ffmpeg"

    result = subprocess.run([
        ffmpeg, "-y",
        "-f", "lavfi", "-i", "color=black:s=1080x1920:r=1:d=5",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-t", "5",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "35",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "64k",
        "-movflags", "+faststart",
        tmp_path
    ], capture_output=True, timeout=30)

    file_size = pathlib.Path(tmp_path).stat().st_size
    print(f"MP4 teste: {file_size//1024}KB")

    # Iniciar upload resumável
    snippet = {
        "title": "Teste de Diagnóstico — pode ser deletado",
        "description": "Teste de diagnóstico",
        "tags": ["teste"],
        "categoryId": "22"
    }
    status = {"privacyStatus": "private", "selfDeclaredMadeForKids": False}
    body = json.dumps({"snippet": snippet, "status": status}).encode()

    init_url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
    req = urllib.request.Request(init_url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Upload-Content-Type", "video/mp4")
    req.add_header("X-Upload-Content-Length", str(file_size))

    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            upload_url = r.headers.get("Location", "")
            print(f"Upload URL: {upload_url[:60]}... OK")
    except urllib.error.HTTPError as e:
        body_err = e.read().decode()
        print(f"ERRO init upload: {e.code}")
        print(f"Body: {body_err[:500]}")
        return

    if not upload_url:
        print("Sem upload URL!")
        return

    # Enviar arquivo
    with open(tmp_path, "rb") as f:
        video_data = f.read()

    req2 = urllib.request.Request(upload_url, data=video_data, method="PUT")
    req2.add_header("Content-Type", "video/mp4")
    req2.add_header("Content-Length", str(file_size))

    try:
        with urllib.request.urlopen(req2, timeout=120) as r:
            result = json.loads(r.read())
            vid_id = result.get("id","")
            print(f"SUCESSO! Video ID: {vid_id}")
            if vid_id:
                # Deletar o video de teste
                del_req = urllib.request.Request(
                    f"https://www.googleapis.com/youtube/v3/videos?id={vid_id}",
                    method="DELETE")
                del_req.add_header("Authorization", f"Bearer {token}")
                try:
                    urllib.request.urlopen(del_req, timeout=10)
                    print(f"Video teste deletado: {vid_id}")
                except: pass
    except urllib.error.HTTPError as e:
        body_err = e.read().decode()
        print(f"ERRO upload: {e.code}")
        print(f"Body: {body_err[:800]}")
    finally:
        pathlib.Path(tmp_path).unlink(missing_ok=True)

def main():
    print("=== DIAGNÓSTICO YOUTUBE UPLOAD ===")
    token = get_token()
    if not token: print("Sem token!"); return
    has_yt = check_scopes(token)
    print(f"Tem escopo YouTube: {has_yt}")
    print("\n=== TESTE DE UPLOAD MÍNIMO ===")
    test_minimal_upload(token)

if __name__ == "__main__":
    main()
