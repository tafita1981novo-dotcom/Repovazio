#!/usr/bin/env python3
"""
GRAVIA LOCAL — roda no seu PC/Mac com IP residencial
Polymarket só aceita ordens de IPs residenciais (nao datacenter)
"""
import subprocess, sys
subprocess.check_call([sys.executable,"-m","pip","install","py-clob-client","web3","requests","--quiet"])

import os, json, math, time, requests
from datetime import datetime, timezone
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs
from py_clob_client.constants import POLYGON
from eth_account import Account

# === CONFIGURACAO ===
PRIVATE_KEY = "0xed39d2609e95b2f5b0df96d14a06ba56b83f6783d8a800c6ea8944ff23eac023"
TRADE_USDC  = 5.0      # Tamanho por trade (dolares)
THRESHOLD   = 0.03     # Edge minimo 3%
LOOP_MINS   = 5        # Roda a cada 5 minutos
LIVE        = True     # True = ordens reais, False = paper

SB  = "https://tpjvalzwkqwttvmszvie.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRwanZhbHp3a3F3dHR2bXN6dmllIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYwMzUyOTMsImV4cCI6MjA5MTYxMTI5M30.UEgUo0Mw15ihQZykLAY5QApRzgTXkfIewZFzIgwao3Q"

def _h(): return{"apikey":KEY,"Authorization":f"Bearer {KEY}","Content-Type":"application/json","Prefer":"return=representation"}
def sg(t,f=""): return requests.get(f"{SB}/rest/v1/{t}?{f}",headers=_h(),timeout=8).json() or [{}]
def su(t,d): requests.post(f"{SB}/rest/v1/{t}",headers={**_h(),"Prefer":"resolution=merge-duplicates,return=minimal"},json=d,timeout=8)
def si(t,d): return requests.post(f"{SB}/rest/v1/{t}",headers=_h(),json=d,timeout=8).json()

KMAP={"OKC":["thunder","oklahoma"],"KNICKS":["knicks"],"SPURS":["spurs","san antonio"],
      "CAR":["hurricanes"],"VGK":["golden knights"],"MTL":["canadiens"]}

def poly_markets():
    r=requests.get("https://gamma-api.polymarket.com/markets?active=true&closed=false&_limit=50",timeout=10)
    ms=r.json() if isinstance(r.json(),list) else[]
    out={}
    for m in ms:
        q=(m.get("question") or"").lower()
        team=next((t for t,kws in KMAP.items() if any(k in q for k in kws)),None)
        if not team: continue
        cids_raw=m.get("clobTokenIds","[]") or"[]"
        try: cids=json.loads(cids_raw) if isinstance(cids_raw,str) else(cids_raw or[])
        except: cids=[]
        b=float(m.get("bestBid") or 0);a=float(m.get("bestAsk") or 0)
        out[team]={"yes":cids[0] if cids else None,"no":cids[1] if len(cids)>1 else None,
            "bid":b,"ask":a,"mid":(b+a)/2,"1h":float(m.get("oneHourPriceChange") or 0),
            "vol24":float(m.get("volume24hr") or 0)}
    return out

def ml2p(ml):
    ml=float(ml)
    return 100/(ml+100) if ml>0 else abs(ml)/(abs(ml)+100)

def espn_odds():
    games=[]
    for sport,league in[("basketball","nba"),("hockey","nhl")]:
        try:
            evs=requests.get(f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard",timeout=8).json().get("events",[])
            for ev in evs:
                c=ev.get("competitions",[{}])[0];eid=ev.get("id","");cid=c.get("id","")
                stype=ev.get("status",{}).get("type",{});ser=c.get("series",{}).get("summary","")
                tr={t.get("team",{}).get("abbreviation","?"):(t.get("homeAway",""),int(t.get("score","0") or 0)) for t in c.get("competitors",[])}
                r2=requests.get(f"https://sports.core.api.espn.com/v2/sports/{sport}/leagues/{league}/events/{eid}/competitions/{cid}/odds",timeout=6)
                if r2.status_code!=200: continue
                items=r2.json().get("items",[])
                if not items: continue
                r3=requests.get(items[0].get("$ref",""),timeout=5)
                if r3.status_code!=200: continue
                bd=r3.json();aw=bd.get("awayTeamOdds",{});hw=bd.get("homeTeamOdds",{})
                aml=aw.get("moneyLine");hml=hw.get("moneyLine")
                if not(aml and hml): continue
                ap=ml2p(aml);hp=ml2p(hml);tot=ap+hp
                away=next((k for k,(ha,s) in tr.items() if ha=="away"),list(tr.keys())[0])
                home=next((k for k,(ha,s) in tr.items() if ha=="home"),list(tr.keys())[-1])
                games.append({"sport":league,"name":ev.get("name","?"),"away":away,"home":home,
                    "scores":{k:s for k,(ha,s) in tr.items()},"series":ser,
                    "status":stype.get("description","?"),"is_final":stype.get("completed",False),
                    "prov":bd.get("provider",{}).get("name","?"),"details":bd.get("details",""),
                    "away_p":ap/tot,"home_p":hp/tot})
        except Exception as e: print(f"  ESPN {league}: {e}")
    return games

def champ_prob(wp,opp,g7=0.58): return wp*(1-opp)+(1-wp)*g7*(1-opp)

def place_order_live(token_id, side, price, usdc):
    try:
        c=ClobClient(host="https://clob.polymarket.com",key=PRIVATE_KEY,chain_id=POLYGON)
        creds=c.derive_api_key()
        c2=ClobClient(host="https://clob.polymarket.com",key=PRIVATE_KEY,chain_id=POLYGON,creds=creds)
        signed=c2.create_order(OrderArgs(token_id=token_id,price=price,size=round(usdc/price,2),side=side))
        resp=c2.post_order(signed)
        return{"ok":True,"order_id":resp.get("orderID","?"),"status":resp.get("status","?")}
    except Exception as e:
        return{"ok":False,"err":str(e)[:150]}

def run_once():
    T0=time.time()
    ts=datetime.fromtimestamp(T0,tz=timezone.utc).strftime("%H:%M:%S")
    mode="🔴 LIVE" if LIVE else "📄 PAPER"
    print(f"\n[{ts} UTC] GRAVIA LOCAL | {mode}")

    poly=poly_markets()
    if not poly: print("  Poly API erro"); return

    for t,p in sorted(poly.items(),key=lambda x:-x[1]["vol24"]):
        fl="⚡" if abs(p["1h"])>=0.003 else" "
        print(f"  {fl}{t:6}: {p['mid']:.3f} 1h={p['1h']:+.4f} vol24=${p['vol24']:,.0f}")

    games=espn_odds();signals=[]
    for g in games:
        away,home=g["away"],g["home"];ap,hp=g["away_p"],g["home_p"];ser=g["series"]
        print(f"\n  [{g['prov']}] {g['name']} {g['details']} | {g['status']}")
        print(f"    {g['scores']} | {ser} | {away}={ap:.3f} {home}={hp:.3f}")

        if g["sport"]=="nba" and"OKC" in(away,home):
            okc_p=ap if away=="OKC" else hp
            fair=champ_prob(okc_p,poly.get("KNICKS",{}).get("mid",0.284))
            mid=poly.get("OKC",{}).get("mid",0);edge=mid-fair
            print(f"    OKC fair={fair:.3f} poly={mid:.3f} EDGE={edge*100:+.1f}%")
            if abs(edge)>THRESHOLD and mid>0.01:
                buy_no=edge>0;tok=poly.get("OKC",{}).get("no" if buy_no else"yes")
                signals.append({"asset":"OKC_NBA","token_id":tok,
                    "direction":"BUY_NO" if buy_no else"BUY_YES",
                    "entry":round((1-mid) if buy_no else mid,4),
                    "fair":round((1-fair) if buy_no else fair,4),"edge":abs(edge)})

        if g["sport"]=="nba" and"SA" in(away,home) and not g["is_final"]:
            sa_p=ap if away=="SA" else hp
            spu=poly.get("SPURS",{}).get("mid",0)
            if any(x in ser for x in["3-0","3-1","2-0","3-2"]):
                fair_s=sa_p**4*0.4;edge=spu-fair_s
                print(f"    SPURS fair={fair_s:.3f} poly={spu:.3f} EDGE={edge*100:+.1f}%")
                if edge>THRESHOLD and spu>0.01:
                    tok=poly.get("SPURS",{}).get("no")
                    signals.append({"asset":"SPURS_NBA","token_id":tok,"direction":"BUY_NO",
                        "entry":round(1-spu,4),"fair":round(1-fair_s,4),"edge":abs(edge)})

        if g["sport"]=="nhl" and"CAR" in(away,home):
            car_p=ap if away=="CAR" else hp
            fair=champ_prob(car_p,poly.get("VGK",{}).get("mid",0.441))
            mid=poly.get("CAR",{}).get("mid",0);edge=mid-fair
            print(f"    CAR fair={fair:.3f} poly={mid:.3f} EDGE={edge*100:+.1f}%")
            if abs(edge)>THRESHOLD and mid>0.01:
                buy_no=edge>0;tok=poly.get("CAR",{}).get("no" if buy_no else"yes")
                signals.append({"asset":"CAR_NHL","token_id":tok,
                    "direction":"BUY_NO" if buy_no else"BUY_YES",
                    "entry":round((1-mid) if buy_no else mid,4),
                    "fair":round((1-fair) if buy_no else fair,4),"edge":abs(edge)})

    if not signals:
        print("\n  Sem sinal"); return

    signals.sort(key=lambda x:-x["edge"])
    sig=signals[0]
    if not sig.get("token_id"): print(f"\n  Token ausente: {sig['asset']}"); return

    print(f"\n  🎯 SINAL: {sig['asset']} {sig['direction']} edge={sig['edge']*100:.1f}%")
    print(f"  Entry={sig['entry']:.4f} Fair={sig['fair']:.4f}")

    if LIVE:
        order=place_order_live(sig["token_id"],"BUY" if"YES" in sig["direction"] else"SELL",sig["entry"],TRADE_USDC)
        print(f"  {'✅ ORDEM REAL' if order.get('ok') else '❌ ERRO'}: {order}")
        if order.get("ok"):
            si("gravia_trades",{"direction":sig["direction"],"entry_price":sig["entry"],
                "size_usdc":TRADE_USDC,"edge":sig["edge"],"btc_pct":sig["edge"],
                "market_id":sig["asset"],"status":"open"})
            su("gravia_state",{"id":1,"has_open_position":True,"open_direction":sig["direction"],
                "open_entry_price":sig["entry"],"open_entry_ts":int(T0),"open_size_usdc":TRADE_USDC,
                "open_fair_prob":sig["fair"],"open_edge":sig["edge"],"market_id":sig["asset"],
                "last_run_ts":int(T0)})
            roi=(sig["fair"]-sig["entry"])/max(sig["entry"],0.001)*TRADE_USDC
            print(f"  P&L esperado: +${roi:.2f}")
    else:
        print(f"  PAPER: {sig['asset']} {sig['direction']} @ {sig['entry']}")

if __name__=="__main__":
    print("GRAVIA LOCAL — bot de arbitragem Polymarket")
    print(f"Wallet: {Account.from_key(PRIVATE_KEY).address}")
    print(f"Modo: {'LIVE' if LIVE else 'PAPER'} | Loop: {LOOP_MINS}min | Trade: ${TRADE_USDC}")
    print("Ctrl+C para parar\n")
    while True:
        try:
            run_once()
        except KeyboardInterrupt:
            print("\nParado pelo usuario")
            break
        except Exception as e:
            print(f"Erro: {e}")
        print(f"  Proxima rodada em {LOOP_MINS} min...")
        time.sleep(LOOP_MINS*60)
