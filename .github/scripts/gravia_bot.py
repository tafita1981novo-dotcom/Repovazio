import os,json,math,time,requests
from datetime import datetime,timezone

# ── Config ────────────────────────────────────────────────────────
SB_URL  = "https://tpjvalzwkqwttvmszvie.supabase.co"
SB_KEY  = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRwanZhbHp3a3F3dHR2bXN6dmllIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYwMzUyOTMsImV4cCI6MjA5MTYxMTI5M30.UEgUo0Mw15ihQZykLAY5QApRzgTXkfIewZFzIgwao3Q"
NVIDIA  = os.environ.get("NVIDIA_API_KEY","")
GROQ    = os.environ.get("GROQ_API_KEY","")
OPENAI  = os.environ.get("OPENAI_API_KEY","")

def hdr(): return {"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json","Prefer":"return=representation"}
def sb_get(t,f=""):
    r=requests.get(f"{SB_URL}/rest/v1/{t}?{f}",headers=hdr(),timeout=8); return r.json()
def sb_up(t,data,filt):
    requests.patch(f"{SB_URL}/rest/v1/{t}?{filt}",headers=hdr(),json=data,timeout=8)
def sb_ins(t,data):
    r=requests.post(f"{SB_URL}/rest/v1/{t}",headers=hdr(),json=data,timeout=8); return r.json()
def sb_upsert(t,data):
    requests.post(f"{SB_URL}/rest/v1/{t}",headers={**hdr(),"Prefer":"resolution=merge-duplicates,return=minimal"},json=data,timeout=8)

# ── AI Router: Groq → NVIDIA → skip ──────────────────────────────
def ai_decide(prompt):
    # 1. Groq Llama 3.3 70B (< 200ms, most reliable free)
    if GROQ:
        try:
            r=requests.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization":f"Bearer {GROQ}","Content-Type":"application/json"},
                json={"model":"llama-3.3-70b-versatile","messages":[{"role":"user","content":prompt}],"max_tokens":60,"temperature":0.1},
                timeout=5)
            ans=r.json()["choices"][0]["message"]["content"].strip().upper()
            return ans, "groq/llama-3.3-70b"
        except: pass
    # 2. NVIDIA DeepSeek V4 Pro
    if NVIDIA:
        try:
            r=requests.post("https://integrate.api.nvidia.com/v1/chat/completions",
                headers={"Authorization":f"Bearer {NVIDIA}","Content-Type":"application/json"},
                json={"model":"deepseek-ai/deepseek-v3","messages":[{"role":"user","content":prompt}],"max_tokens":60,"temperature":0.1},
                timeout=8)
            ans=r.json()["choices"][0]["message"]["content"].strip().upper()
            return ans, "nvidia/deepseek-v3"
        except: pass
    # 3. OpenAI fallback
    if OPENAI:
        try:
            r=requests.post("https://api.openai.com/v1/chat/completions",
                headers={"Authorization":f"Bearer {OPENAI}","Content-Type":"application/json"},
                json={"model":"gpt-4o-mini","messages":[{"role":"user","content":prompt}],"max_tokens":60,"temperature":0.1},
                timeout=8)
            ans=r.json()["choices"][0]["message"]["content"].strip().upper()
            return ans, "openai/gpt-4o-mini"
        except: pass
    return "EXECUTE", "no-ai-fallback"

# ── BTC Price ─────────────────────────────────────────────────────
def get_btc():
    try:
        r=requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",timeout=5)
        return float(r.json()["price"])
    except: return None

# ── Polymarket ────────────────────────────────────────────────────
def find_market():
    try:
        r=requests.get("https://gamma-api.polymarket.com/markets?active=true&closed=false&tag_slug=crypto&_limit=100",timeout=8)
        ms=r.json(); ms=ms if isinstance(ms,list) else ms.get("markets",[])
        for m in ms:
            q=(m.get("question") or m.get("title","")).lower()
            tk=m.get("tokens",[])
            if len(tk)<2 or ("btc" not in q and "bitcoin" not in q): continue
            up=next((t for t in tk if (t.get("outcome") or "").lower() in ["up","yes","higher","above"]),None)
            dn=next((t for t in tk if (t.get("outcome") or "").lower() in ["down","no","lower","below"]),None)
            upid=(up or tk[0]).get("token_id") or (up or tk[0]).get("tokenId")
            dnid=(dn or tk[1]).get("token_id") or (dn or tk[1]).get("tokenId") if dn else upid
            if not upid: continue
            end_ts=int(time.time())+300
            try: end_ts=int(datetime.fromisoformat((m.get("endDate") or "").replace("Z","+00:00")).timestamp())
            except: pass
            return {"id":m.get("id","?"),"upid":upid,"dnid":dnid,"end_ts":end_ts}
    except: pass
    return None

def get_poly(upid,dnid):
    def mid(tid):
        try:
            b=requests.get(f"https://clob.polymarket.com/book?token_id={tid}",timeout=5).json()
            a=float(b["asks"][0]["price"]) if b.get("asks") else None
            bi=float(b["bids"][0]["price"]) if b.get("bids") else None
            return (a+bi)/2 if a and bi else (a or bi)
        except: return None
    return mid(upid),mid(dnid)

# ── Signal ────────────────────────────────────────────────────────
def detect(hist,btc,up,dn,end_ts,start_ts):
    now=int(time.time())
    if not btc or not up: return None
    if up<0.35 or up>0.65: return None
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
    return {"dir":direction,"entry":min(pp*1.003,0.97),"fv":fv,"pp":pp,"edge":edge,"pct":pct}

# ── Main ──────────────────────────────────────────────────────────
def main():
    now=int(time.time())
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Gravia Bot — AI-Enhanced Latency Arb")

    # State
    st_arr=sb_get("gravia_state","id=eq.1"); st=st_arr[0] if st_arr else {}
    if st.get("is_halted"): print("HALTED"); return

    # BTC
    btc=get_btc()
    if not btc: print("Binance unavailable"); return
    print(f"BTC=${btc:,.2f}")

    # Price history
    hist=st.get("price_history") or []
    if isinstance(hist,str): hist=json.loads(hist)
    hist.append({"ts":now,"btc":btc}); hist=hist[-20:]

    # Market
    mid_=st.get("market_id"); up=st.get("market_up_token"); dn=st.get("market_down_token")
    end_ts=st.get("market_end_ts",0); start_ts=st.get("market_start_ts",now-150)
    if not end_ts or now>=end_ts-5 or not up:
        m=find_market()
        if not m:
            sb_upsert("gravia_state",{"id":1,"btc_price":btc,"price_history":hist,"last_run_ts":now}); return
        mid_=m["id"]; up=m["upid"]; dn=m["dnid"]; end_ts=m["end_ts"]; start_ts=now
        print(f"Market expires {end_ts-now}s")

    # Polymarket prices
    up_p,dn_p=get_poly(up,dn)
    print(f"PM UP={up_p:.3f if up_p else 'N/A'}")

    # Close open position
    if st.get("has_open_position") and st.get("open_entry_ts"):
        hold=now-st["open_entry_ts"]; ep=(up_p if st["open_direction"]=="UP" else dn_p) or st["open_entry_price"]
        if hold>=240 or end_ts-now<60:
            pnl=(ep-st["open_entry_price"])*(1 if st["open_direction"]=="UP" else -1)*(10/st["open_entry_price"])
            won=pnl>0
            ot=sb_get("gravia_trades","status=eq.open&order=ts.desc&limit=1")
            if ot: sb_up("gravia_trades",{"exit_price":round(ep,4),"hold_seconds":hold,"pnl_usdc":round(pnl,4),"roi_pct":round(pnl/10*100,2),"won":won,"status":"closed"},f"id=eq.{ot[0]['id']}")
            tpnl=(st.get("total_pnl") or 0)+pnl; cl=(0 if won else (st.get("consec_losses") or 0)+1)
            print(f"{'WIN' if won else 'LOSS'} P&L={pnl:.4f} total=${tpnl:.4f}")
            sb_upsert("gravia_state",{"id":1,"has_open_position":False,"open_direction":None,"open_entry_price":None,"open_entry_ts":None,"total_pnl":tpnl,"total_wins":(st.get("total_wins") or 0)+(1 if won else 0),"total_trades":(st.get("total_trades") or 0)+1,"consec_losses":cl,"daily_pnl":(st.get("daily_pnl") or 0)+pnl,"is_halted":(st.get("daily_pnl") or 0)+pnl<=-100 or cl>=3,"btc_price":btc,"poly_up_price":up_p,"price_history":hist,"last_run_ts":now,"market_id":mid_,"market_up_token":up,"market_down_token":dn,"market_end_ts":end_ts})
            return

    # Detect signal
    h5m=[p for p in hist if p["ts"]>=now-300]
    pct5m=(btc-h5m[0]["btc"])/h5m[0]["btc"]*100 if len(h5m)>1 else 0
    sig=detect(hist,btc,up_p or 0,dn_p,end_ts,start_ts)

    if not sig:
        print(f"No signal | BTC5m={pct5m:+.3f}% | PM={up_p:.3f if up_p else 'N/A'}")
        sb_upsert("gravia_state",{"id":1,"btc_price":btc,"poly_up_price":up_p,"last_btc_pct":pct5m,"price_history":hist,"last_run_ts":now,"market_id":mid_,"market_up_token":up,"market_down_token":dn,"market_end_ts":end_ts})
        return

    # ── AI DECISION ──────────────────────────────────────────────
    prompt=f"""Polymarket BTC Latency Arbitrage — Decisão de Trade

Contexto de mercado:
- BTC agora: ${btc:,.2f}
- BTC 5min atrás: variação {sig['pct']:+.2f}%
- Polymarket UP token: {sig['pp']:.3f} (fair value calculado: {sig['fv']:.3f})
- Edge: {sig['edge']*100:.1f}% (lucro esperado por token)
- Mercado expira em: {end_ts-now}s
- Posição no ciclo: {now-start_ts}s desde início

A estratégia explora o lag de repricing do Polymarket vs Binance.
Edge positivo = mercado ainda não processou o movimento {sig['pct']:+.2f}% do BTC.

Responda APENAS: EXECUTE ou SKIP (sem mais nada)"""

    decision, model = ai_decide(prompt)
    print(f"AI ({model}): {decision[:20]}")

    if "SKIP" in decision:
        print(f"AI rejeitou trade | edge={sig['edge']*100:.1f}%")
        sb_ins("gravia_signals",{"direction":sig["dir"],"btc_pct":round(sig["pct"],4),"poly_price":round(sig["pp"],4),"fair_prob":round(sig["fv"],4),"edge":round(sig["edge"],4),"executed":False})
        sb_upsert("gravia_state",{"id":1,"btc_price":btc,"poly_up_price":up_p,"last_btc_pct":pct5m,"price_history":hist,"last_run_ts":now,"market_id":mid_,"market_up_token":up,"market_down_token":dn,"market_end_ts":end_ts})
        return

    # EXECUTE
    print(f"SIGNAL {sig['dir']} BTC{sig['pct']:+.2f}% edge={sig['edge']*100:.1f}% AI={model}")
    sb_ins("gravia_signals",{"direction":sig["dir"],"btc_pct":round(sig["pct"],4),"poly_price":round(sig["pp"],4),"fair_prob":round(sig["fv"],4),"edge":round(sig["edge"],4),"executed":True})
    sb_ins("gravia_trades",{"direction":sig["dir"],"entry_price":round(sig["entry"],4),"size_usdc":10,"edge":round(sig["edge"],4),"btc_pct":round(sig["pct"],4),"market_id":mid_,"status":"open"})
    sb_upsert("gravia_state",{"id":1,"has_open_position":True,"open_direction":sig["dir"],"open_entry_price":round(sig["entry"],4),"open_entry_ts":now,"open_size_usdc":10,"open_fair_prob":round(sig["fv"],4),"open_edge":round(sig["edge"],4),"btc_price":btc,"poly_up_price":up_p,"last_btc_pct":pct5m,"price_history":hist,"last_run_ts":now,"market_id":mid_,"market_up_token":up,"market_down_token":dn,"market_end_ts":end_ts,"market_start_ts":start_ts})
    print(f"Trade ABERTO @ {sig['entry']:.4f}")

main()
