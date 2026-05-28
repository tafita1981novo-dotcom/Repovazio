import os,json,math,time,requests
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────
SB_URL = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRwanZhbHp3a3F3dHR2bXN6dmllIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYwMzUyOTMsImV4cCI6MjA5MTYxMTI5M30.UEgUo0Mw15ihQZykLAY5QApRzgTXkfIewZFzIgwao3Q"
NVIDIA = os.environ.get("NVIDIA_API_KEY","")
GROQ   = os.environ.get("GROQ_API_KEY","")
OPENAI = os.environ.get("OPENAI_API_KEY","")

def hdr():return{"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json","Prefer":"return=representation"}
def sb_get(t,f=""):
    r=requests.get(f"{SB_URL}/rest/v1/{t}?{f}",headers=hdr(),timeout=8)
    return r.json() if r.status_code==200 else []
def sb_up(t,d,filt):
    requests.patch(f"{SB_URL}/rest/v1/{t}?{filt}",headers=hdr(),json=d,timeout=8)
def sb_ins(t,d):
    r=requests.post(f"{SB_URL}/rest/v1/{t}",headers=hdr(),json=d,timeout=8)
    return r.json()
def sb_us(t,d):
    requests.post(f"{SB_URL}/rest/v1/{t}",
        headers={**hdr(),"Prefer":"resolution=merge-duplicates,return=minimal"},
        json=d,timeout=8)

# ── BTC Price — multi-source fallback (Binance bloqueado no GH Actions) ──
def get_btc():
    sources = [
        # (url, parser)
        ("https://api.kraken.com/0/public/Ticker?pair=XBTUSD",
         lambda d: float(list(d["result"].values())[0]["c"][0])),
        ("https://www.bitstamp.net/api/v2/ticker/btcusd/",
         lambda d: float(d["last"])),
        ("https://api.coinbase.com/v2/prices/BTC-USD/spot",
         lambda d: float(d["data"]["amount"])),
        ("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
         lambda d: float(d["bitcoin"]["usd"])),
    ]
    for url, parse in sources:
        try:
            r=requests.get(url,timeout=5)
            if r.status_code==200:
                price=parse(r.json())
                if price and price > 1000:
                    print(f"  BTC via {url.split('/')[2]}: ${price:,.2f}")
                    return price
        except Exception as e:
            print(f"  {url.split('/')[2]}: {e}")
    return None

# ── AI Router: Groq (< 200ms) → NVIDIA DeepSeek V3 → OpenAI ──────
def ai_decide(prompt):
    # Groq llama-3.3-70b: mais rápido, free tier generoso
    if GROQ:
        try:
            r=requests.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization":f"Bearer {GROQ}","Content-Type":"application/json"},
                json={"model":"llama-3.3-70b-versatile",
                      "messages":[{"role":"system","content":"Você é um analisador de arbitragem de latência no Polymarket. Responda APENAS com EXECUTE ou SKIP."},
                                  {"role":"user","content":prompt}],
                      "max_tokens":10,"temperature":0.0},
                timeout=5)
            ans=r.json()["choices"][0]["message"]["content"].strip().upper()
            return ans,"groq/llama-3.3-70b"
        except Exception as e:
            print(f"  Groq error: {e}")
    # NVIDIA DeepSeek V3: melhor raciocínio
    if NVIDIA:
        try:
            r=requests.post("https://integrate.api.nvidia.com/v1/chat/completions",
                headers={"Authorization":f"Bearer {NVIDIA}","Content-Type":"application/json"},
                json={"model":"deepseek-ai/deepseek-v3",
                      "messages":[{"role":"user","content":prompt+" Responda apenas EXECUTE ou SKIP."}],
                      "max_tokens":10,"temperature":0.0},
                timeout=8)
            ans=r.json()["choices"][0]["message"]["content"].strip().upper()
            return ans,"nvidia/deepseek-v3"
        except Exception as e:
            print(f"  NVIDIA error: {e}")
    # OpenAI gpt-4o-mini: último recurso
    if OPENAI:
        try:
            r=requests.post("https://api.openai.com/v1/chat/completions",
                headers={"Authorization":f"Bearer {OPENAI}","Content-Type":"application/json"},
                json={"model":"gpt-4o-mini",
                      "messages":[{"role":"user","content":prompt}],
                      "max_tokens":10,"temperature":0.0},
                timeout=8)
            ans=r.json()["choices"][0]["message"]["content"].strip().upper()
            return ans,"openai/gpt-4o-mini"
        except: pass
    return "EXECUTE","no-ai-execute"

# ── Polymarket ────────────────────────────────────────────────────
def find_market():
    try:
        r=requests.get("https://gamma-api.polymarket.com/markets?active=true&closed=false&tag_slug=crypto&_limit=100",timeout=8)
        ms=r.json() if r.status_code==200 else []
        ms=ms if isinstance(ms,list) else ms.get("markets",[])
        for m in ms:
            q=(m.get("question") or m.get("title","")).lower()
            tk=m.get("tokens",[])
            if len(tk)<2 or ("btc" not in q and "bitcoin" not in q): continue
            up=next((t for t in tk if (t.get("outcome")or"").lower() in ["up","yes","higher","above"]),None)
            dn=next((t for t in tk if (t.get("outcome")or"").lower() in ["down","no","lower","below"]),None)
            uid=(up or tk[0]).get("token_id") or (up or tk[0]).get("tokenId")
            did=(dn or tk[1]).get("token_id") or (dn or tk[1]).get("tokenId") if dn else uid
            if not uid: continue
            et=int(time.time())+300
            try: et=int(datetime.fromisoformat((m.get("endDate")or"").replace("Z","+00:00")).timestamp())
            except: pass
            return {"id":m.get("id","?"),"upid":uid,"dnid":did,"end_ts":et}
    except Exception as e:
        print(f"  Polymarket error: {e}")
    return None

def get_poly(ui,di):
    def mid(tid):
        try:
            b=requests.get(f"https://clob.polymarket.com/book?token_id={tid}",timeout=5).json()
            a=float(b["asks"][0]["price"]) if b.get("asks") else None
            bi=float(b["bids"][0]["price"]) if b.get("bids") else None
            return (a+bi)/2 if a and bi else (a or bi)
        except: return None
    return mid(ui),mid(di)

# ── Signal ────────────────────────────────────────────────────────
def detect(hist,btc,up,dn,end_ts,start_ts):
    now=int(time.time())
    if not btc or not up or up<0.35 or up>0.65: return None
    if end_ts-now<90 or now-start_ts<120: return None
    h=[p for p in hist if p["ts"]>=now-300]
    if len(h)<2: return None
    old=min(h,key=lambda p:p["ts"])
    pct=(btc-old["btc"])/old["btc"]*100
    if abs(pct)<0.8: return None
    fv=1/(1+math.exp(-abs(pct)*3))
    direction="UP" if pct>0 else "DOWN"
    pp=up if direction=="UP" else (dn or 1-up)
    edge=fv-pp
    if edge<0.08: return None
    return{"dir":direction,"entry":min(pp*1.003,0.97),"fv":fv,"pp":pp,"edge":edge,"pct":pct}

# ── Main ──────────────────────────────────────────────────────────
def main():
    now=int(time.time())
    ts=datetime.utcnow().strftime("%H:%M:%S")
    print(f"[{ts}] GRAVIA AI BOT — Groq+NVIDIA DeepSeek | Latency Arb")

    # Estado
    st_a=sb_get("gravia_state","id=eq.1"); st=st_a[0] if st_a else {}
    if st.get("is_halted"): print("HALTED — daily loss limit"); return

    # BTC (multi-source)
    btc=get_btc()
    if not btc: print("ERROR: todos BTC APIs falharam"); return
    print(f"  BTC=${btc:,.2f}")

    # Histórico
    hist=st.get("price_history") or []
    if isinstance(hist,str): hist=json.loads(hist)
    hist.append({"ts":now,"btc":btc}); hist=hist[-20:]

    # Mercado
    mid_=st.get("market_id"); up=st.get("market_up_token"); dn=st.get("market_down_token")
    end_ts=st.get("market_end_ts",0); start_ts=st.get("market_start_ts",now-150)
    if not end_ts or now>=end_ts-5 or not up:
        m=find_market()
        if not m:
            print("  Nenhum mercado BTC ativo"); 
            sb_us("gravia_state",{"id":1,"btc_price":btc,"price_history":hist,"last_run_ts":now}); return
        mid_=m["id"]; up=m["upid"]; dn=m["dnid"]; end_ts=m["end_ts"]; start_ts=now
        print(f"  Mercado: {mid_[:30]} | expira {end_ts-now}s")

    # PM prices
    up_p,dn_p=get_poly(up,dn)
    print(f"  PM UP={f'{up_p:.3f}' if up_p else 'N/A'}")

    # Fecha posição aberta?
    if st.get("has_open_position") and st.get("open_entry_ts"):
        hold=now-st["open_entry_ts"]
        ep=(up_p if st["open_direction"]=="UP" else dn_p) or st["open_entry_price"]
        if hold>=240 or end_ts-now<60:
            pnl=(ep-st["open_entry_price"])*(1 if st["open_direction"]=="UP" else -1)*(10/st["open_entry_price"])
            won=pnl>0
            ot=sb_get("gravia_trades","status=eq.open&order=ts.desc&limit=1")
            if ot:
                sb_up("gravia_trades",{"exit_price":round(ep,4),"hold_seconds":hold,
                    "pnl_usdc":round(pnl,4),"roi_pct":round(pnl/10*100,2),"won":won,"status":"closed"},
                    f"id=eq.{ot[0]['id']}")
            tp=(st.get("total_pnl") or 0)+pnl; cl=0 if won else (st.get("consec_losses") or 0)+1
            print(f"  {'✅ WIN' if won else '❌ LOSS'} P&L={pnl:+.4f} | Total=${tp:.4f}")
            sb_us("gravia_state",{"id":1,"has_open_position":False,"open_direction":None,
                "open_entry_price":None,"open_entry_ts":None,"total_pnl":tp,
                "total_wins":(st.get("total_wins") or 0)+(1 if won else 0),
                "total_trades":(st.get("total_trades") or 0)+1,"consec_losses":cl,
                "daily_pnl":(st.get("daily_pnl") or 0)+pnl,
                "is_halted":(st.get("daily_pnl") or 0)+pnl<=-100 or cl>=3,
                "btc_price":btc,"poly_up_price":up_p,"price_history":hist,"last_run_ts":now,
                "market_id":mid_,"market_up_token":up,"market_down_token":dn,"market_end_ts":end_ts})
            return

    # Detecta sinal
    h5m=[p for p in hist if p["ts"]>=now-300]
    pct5m=(btc-h5m[0]["btc"])/h5m[0]["btc"]*100 if len(h5m)>1 else 0
    sig=detect(hist,btc,up_p or 0,dn_p,end_ts,start_ts)

    if not sig:
        print(f"  No signal | BTC5m={pct5m:+.3f}% | PM={f'{up_p:.3f}' if up_p else 'N/A'}")
        sb_us("gravia_state",{"id":1,"btc_price":btc,"poly_up_price":up_p,"last_btc_pct":pct5m,
            "price_history":hist,"last_run_ts":now,
            "market_id":mid_,"market_up_token":up,"market_down_token":dn,"market_end_ts":end_ts})
        return

    # ── AI DECISION (Groq → NVIDIA DeepSeek) ─────────────────────
    prompt = (
        f"Polymarket BTC Latency Arb.\n"
        f"BTC: ${btc:,.0f} | Variação 5min: {sig['pct']:+.2f}%\n"
        f"Polymarket UP: {sig['pp']:.3f} | Fair value: {sig['fv']:.3f} | Edge: {sig['edge']*100:.1f}%\n"
        f"Mercado expira: {end_ts-now}s\n"
        f"O mercado não reprece o movimento BTC ainda. EXECUTE ou SKIP?"
    )
    dec,model=ai_decide(prompt)
    print(f"  🤖 AI ({model}): {dec[:10]}")

    if "SKIP" in dec:
        print(f"  AI rejeitou | edge={sig['edge']*100:.1f}%")
        sb_ins("gravia_signals",{"direction":sig["dir"],"btc_pct":round(sig["pct"],4),
            "poly_price":round(sig["pp"],4),"fair_prob":round(sig["fv"],4),
            "edge":round(sig["edge"],4),"executed":False})
        sb_us("gravia_state",{"id":1,"btc_price":btc,"poly_up_price":up_p,"last_btc_pct":pct5m,
            "price_history":hist,"last_run_ts":now,
            "market_id":mid_,"market_up_token":up,"market_down_token":dn,"market_end_ts":end_ts})
        return

    # EXECUTE
    print(f"  🎯 EXECUTE {sig['dir']} BTC{sig['pct']:+.2f}% edge={sig['edge']*100:.1f}% via {model}")
    sb_ins("gravia_signals",{"direction":sig["dir"],"btc_pct":round(sig["pct"],4),
        "poly_price":round(sig["pp"],4),"fair_prob":round(sig["fv"],4),
        "edge":round(sig["edge"],4),"executed":True})
    sb_ins("gravia_trades",{"direction":sig["dir"],"entry_price":round(sig["entry"],4),
        "size_usdc":10,"edge":round(sig["edge"],4),"btc_pct":round(sig["pct"],4),
        "market_id":mid_,"status":"open"})
    sb_us("gravia_state",{"id":1,"has_open_position":True,"open_direction":sig["dir"],
        "open_entry_price":round(sig["entry"],4),"open_entry_ts":now,"open_size_usdc":10,
        "open_fair_prob":round(sig["fv"],4),"open_edge":round(sig["edge"],4),
        "btc_price":btc,"poly_up_price":up_p,"last_btc_pct":pct5m,
        "price_history":hist,"last_run_ts":now,"market_id":mid_,
        "market_up_token":up,"market_down_token":dn,"market_end_ts":end_ts,
        "market_start_ts":start_ts})
    print(f"  Trade ABERTO @ {sig['entry']:.4f}")

main()
