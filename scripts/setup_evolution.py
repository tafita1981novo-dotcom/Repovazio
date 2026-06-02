"""
setup_evolution.py — cria instância WhatsApp + configura webhook
Execute UMA VEZ após deploy no Railway:
  python scripts/setup_evolution.py
"""
import os, requests, json, time, base64

EVOLUTION_URL    = os.environ["EVOLUTION_URL"]
EVOLUTION_APIKEY = os.environ["EVOLUTION_APIKEY"]
INSTANCE_NAME    = os.getenv("EVOLUTION_INSTANCE", "rafael")
WEBHOOK_URL      = os.getenv("WEBHOOK_URL", "https://repovazio.vercel.app/api/wa-webhook")
WEBHOOK_SECRET   = os.environ["WEBHOOK_SECRET"]

H = {"Content-Type":"application/json","apikey":EVOLUTION_APIKEY}

def create_instance():
    print(f"🔧 Criando instância {INSTANCE_NAME!r}...")
    payload = {
        "instanceName": INSTANCE_NAME,
        "qrcode": True,
        "integration": "WHATSAPP-BAILEYS",
        "webhook": {
            "url": WEBHOOK_URL,
            "byEvents": True,
            "base64": False,
            "headers": {"apikey": WEBHOOK_SECRET},
            "events": ["MESSAGES_UPSERT"]
        }
    }
    r = requests.post(f"{EVOLUTION_URL}/instance/create", json=payload, headers=H, timeout=30)
    print(f"  Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))

def get_qrcode():
    print(f"\n📱 Buscando QR Code...")
    r = requests.get(f"{EVOLUTION_URL}/instance/connect/{INSTANCE_NAME}", headers=H, timeout=30)
    data = r.json()
    b64 = data.get("base64") or data.get("qrcode", {}).get("base64", "")
    if b64:
        html = f"""<!DOCTYPE html>
<html><body style="background:#0a0a0f;display:flex;align-items:center;justify-content:center;
min-height:100vh;flex-direction:column;font-family:sans-serif;color:#fff">
<h2 style="margin-bottom:8px">📱 Escaneie no WhatsApp</h2>
<p style="color:#888;margin-bottom:20px">WhatsApp → Aparelhos conectados → Conectar aparelho</p>
<img src="{b64}" style="border:4px solid #7c3aed;border-radius:12px" width="300">
<p style="color:#555;font-size:12px;margin-top:12px">Instância: {INSTANCE_NAME} | {EVOLUTION_URL}</p>
</body></html>"""
        with open("qrcode.html", "w") as f:
            f.write(html)
        print("  ✅ QR Code salvo em qrcode.html — abra no navegador!")
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    create_instance()
    print("\n⏳ Aguardando 3s...")
    time.sleep(3)
    get_qrcode()
