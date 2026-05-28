#!/usr/bin/env python3
# GRAVIA v3 — Sportsbook vs Polymarket Arb | threshold=3% | tokens dinamicos
import os,json,math,time,requests
from datetime import datetime,timezone

SB="https://tpjvalzwkqwttvmszvie.supabase.co"
KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRwanZhbHp3a3F3dHR2bXN6dmllIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYwMzUyOTMsImV4cCI6MjA5MTYxMTI5M30.UEgUo0Mw15ihQZykLAY5QApRzgTXkfIewZFzIgwao3Q"
def _h():
    return{"apikey":KEY,"Authorization":"Bearer "+KEY,"Content-Type":"application/json","Prefer":"return=representation"}
def sg(t,f=""):
    try:return requests.get(SB+"/rest/v1/"+t+"?"+f,headers=_h(),timeout=8).json() or [{}]
    except:return[{}]
def su(t,d):
    requests.post(SB+"/rest/v1/"+t,headers={**_h(),"Prefer":"resolution=merge-duplicates,return=minimal"},json=d,timeout=8)
def si(t,d):
    return requests.post(SB+"/rest/v1/"+t,headers=_h(),json=d,timeout=8).json()
def sp(t,d,f):
    requests.patch(SB+"/rest/v1/"+t+"?"+f,headers=_h(),json=d,timeout=8)

def ntp():
    for u in["http://worldtimeapi.org/api/timezone/UTC","https://timeapi.io/api/Time/current/zone?timeZone=UTC"]:
        try:
            r=requests.get(u,timeout=3)
            if r.status_code==200:
                d=r.json()
                t=d.get("unixtime") or time.time()
                return float(t),u.split("/")[2]
        except:pass
    return time.time(),"sys"

def get_btc():
    for u,p in[
        ("https://api.kraken.com/0/public/Ticker?pair=XBTUSD",lambda d:float(list(d["result"].values())[0]["c"][0])),
        ("https://www.bitstamp.net/api/v2/ticker/btcusd/",lambda d:float(d["last"])),
        ("https://api.coinbase.com/v2/prices/BTC-USD/spot",lambda d:float(d["data"]["amount"]))
    ]:
        try:
            r=requests.get(u,timeout=4)
            if r.status_code==200:return p(r.json())
        except:pass
    return None

KMAP={"OKC":["thunder","oklahoma"],"KNICKS":["knicks"],"SPURS":["spurs","san antonio"],
      "CAR":["hurricanes"],"VGK":["golden knights"],"MTL":["canadiens"]}

def poly_markets():
    r=requests.get("https://gamma-api.polymarket.com/markets?active=true&closed=false&_limit=50",timeout=10)
    ms=r.json() if isinstance(r.json(),list) else[]
    out={}
    for m in ms:
        q=(m.get("question") or"").lower()
        team=next((t for t,kws in KMAP.items() if any(k in q for k in kws)),None)
        if not team:continue
        cids_raw=m.get("clobTokenIds","[]") or"[]"
        try:cids=json.loads(cids_raw) if isinstance(cids_raw,str) else(cids_raw or[])
        except:cids=[]
        b=float(m.get("bestBid") or 0);a=float(m.get("bestAsk") or 0)
        out[team]={"yes":cids[0] if cids else None,"no":cids[1] if len(cids)>1 else None,
            "bid":b,"ask":a,"mid":(b+a)/2,"last":float(m.get("lastTradePrice") or 0),
            "1h":float(m.get("oneHourPriceChange") or 0),"24h":float(m.get("oneDayPriceChange") or 0),
            "vol24":float(m.get("volume24hr") or 0)}
    return out

def ml2p(ml):
    ml=float(ml)
    return 100/(ml+100) if ml>0 else abs(ml)/(abs(ml)+100)

def espn_odds():
    games=[]
    for sport,league in[("basketball","nba"),("hockey","nhl")]:
        try:
            url="https://site.api.espn.com/apis/site/v2/sports/"+sport+"/"+league+"/scoreboard"
            evs=requests.get(url,timeout=8).json().get("events",[])
            for ev in evs:
                c=ev.get("competitions",[{}])[0]
                eid=ev.get("id","");cid=c.get("id","")
                stype=ev.get("status",{}).get("type",{})
                ser=c.get("series",{}).get("summary","")
                tr={t.get("team",{}).get("abbreviation","?"):(t.get("homeAway",""),int(t.get("score","0") or 0)) for t in c.get("competitors",[])}
                ou="https://sports.core.api.espn.com/v2/sports/"+sport+"/leagues/"+league+"/events/"+eid+"/competitions/"+cid+"/odds"
                r2=requests.get(ou,timeout=6)
                if r2.status_code!=200:continue
                items=r2.json().get("items",[])
                if not items:continue
                r3=requests.get(items[0].get("$ref",""),timeout=5)
                if r3.status_code!=200:continue
                bd=r3.json()
                aw=bd.get("awayTeamOdds",{});hw=bd.get("homeTeamOdds",{})
                aml=aw.get("moneyLine");hml=hw.get("moneyLine")
                if not(aml and hml):continue
                ap=ml2p(aml);hp=ml2p(hml);tot=ap+hp
                away=next((k for k,(ha,s) in tr.items() if ha=="away"),list(tr.keys())[0])
                home=next((k for k,(ha,s) in tr.items() if ha=="home"),list(tr.keys())[-1])
                games.append({"sport":league,"name":ev.get("name","?"),"away":away,"home":home,
                    "scores":{k:s for k,(ha,s) in tr.items()},"series":ser,
                    "status":stype.get("description","?"),"is_final":stype.get("completed",False),
                    "prov":bd.get("provider",{}).get("name","?"),"details":bd.get("details",""),
                    "away_ml":float(aml),"home_ml":float(hml),"away_p":ap/tot,"home_p":hp/tot})
        except Exception as e:
            print("  ESPN "+league+": "+str(e))
    return games

def champ_prob(win_tonight,opp_mid,p_g7=0.58):
    pw=1.0-opp_mid
    pl=p_g7*(1.0-opp_mid)
    return win_tonight*pw+(1-win_tonight)*pl

def ai_decide(prompt):
    for k,url,model in[
        (os.environ.get("GROQ_API_KEY",""),"https://api.groq.com/openai/v1/chat/completions","llama-3.3-70b-versatile"),
        (os.environ.get("NVIDIA_API_KEY",""),"https://integrate.api.nvidia.com/v1/chat/completions","deepseek-ai/deepseek-v3")
    ]:
        if not k:continue
        try:
            r=requests.post(url,headers={"Authorization":"Bearer "+k,"Content-Type":"application/json"},
                json={"model":model,"messages":[{"role":"user","content":prompt}],"max_tokens":10,"temperature":0.0},timeout=6)
            ans=r.json()["choices"][0]["message"]["content"].strip().upper()
            return"EXECUTE" in ans,model
        except:pass
    return True,"no-ai"

LIVE=os.environ.get("POLY_TRADING_LIVE","").lower()=="true"

def place_order(token_id,side,price,usdc):
    if not LIVE:
        return{"PAPER":True,"token":str(token_id)[:12],"side":side,"price":round(price,4)}
    try:
        from py_clob_client.client import ClobClient
        from py_clob_client.clob_types import OrderArgs,OrderType
        from py_clob_client.constants import POLYGON
        c=ClobClient(host="https://clob.polymarket.com",key=os.environ.get("POLY_PRIVATE_KEY",""),
            chain_id=POLYGON,creds={"key":os.environ.get("POLY_API_KEY",""),
                "secret":os.environ.get("POLY_SECRET",""),"passphrase":os.environ.get("POLY_PASSPHRASE","")})
        s=c.create_order(OrderArgs(token_id=token_id,price=price,size=round(usdc/price,2),side=side,order_type=OrderType.GTC))
        resp=c.post_order(s)
        return{"LIVE":True,"order_id":resp.get("orderID","?"),"status":resp.get("status","?")}
    except Exception as e:
        return{"LIVE":True,"err":str(e)[:80]}

def main():
    T0,tsrc=ntp()
    ts=datetime.fromtimestamp(T0,tz=timezone.utc).strftime("%H:%M:%S")
    mode="LIVE" if LIVE else "PAPER"
    print("["+ts+"UTC/"+tsrc+"] GRAVIA v3 | "+mode+" | threshold=3%")
    st=(sg("gravia_state","id=eq.1") or[{}])[0]
    if st.get("is_halted"):print("HALTED");return
    price_btc=get_btc();now=int(T0)
    hist=st.get("price_history") or[]
    if isinstance(hist,str):
        try:hist=json.loads(hist)
        except:hist=[]
    if price_btc:hist.append({"ts":now,"btc":price_btc});hist=hist[-30:]
    print("  BTC $"+str(round(price_btc,2)) if price_btc else"  BTC n/a")
    poly=poly_markets()
    if not poly:print("  ERRO Gamma API");return
    print("  Polymarket ("+str(len(poly))+" mercados):")
    for t,p in sorted(poly.items(),key=lambda x:-x[1]["vol24"]):
        fl="!" if abs(p["1h"])>=0.003 else" "
        print("    "+fl+t+" mid="+str(round(p["mid"],3))+" 1h="+str(round(p["1h"],4))+" vol24=$"+str(int(p["vol24"])))
    games=espn_odds()
    signals=[]
    for g in games:
        away=g["away"];home=g["home"];ap=g["away_p"];hp=g["home_p"];ser=g["series"]
        print("\n  ["+g["prov"]+"] "+g["name"]+" "+g["details"]+" | "+g["status"])
        print("    "+str(g["scores"])+" | "+ser+" | "+away+"="+str(round(ap,3))+" "+home+"="+str(round(hp,3)))
        if g["sport"]=="nba" and "OKC" in(away,home):
            okc_p=ap if away=="OKC" else hp
            k_mid=poly.get("KNICKS",{}).get("mid") or 0.284
            fair=champ_prob(okc_p,k_mid)
            mid=poly.get("OKC",{}).get("mid") or 0
            edge=mid-fair
            print("    OKC game_p="+str(round(okc_p,3))+" fair_champ="+str(round(fair,3))+" poly="+str(round(mid,3))+" EDGE="+str(round(edge*100,1))+"%")
            if abs(edge)>0.03 and mid>0.01:
                buy_no=edge>0
                tok=poly.get("OKC",{}).get("no" if buy_no else"yes")
                entry=round((1-mid) if buy_no else mid,4)
                signals.append({"asset":"OKC_NBA","token_id":tok,
                    "direction":"BUY_NO" if buy_no else"BUY_YES",
                    "entry":entry,"fair":round((1-fair) if buy_no else fair,4),
                    "edge":abs(edge),"reason":"DK="+str(round(okc_p,3))+" fair="+str(round(fair,3))+" poly="+str(round(mid,3))})
        if g["sport"]=="nba" and "SA" in(away,home) and not g["is_final"]:
            sa_p=ap if away=="SA" else hp
            spurs_mid=poly.get("SPURS",{}).get("mid") or 0
            if any(x in ser for x in["3-0","3-1","2-0","3-2"]):
                fair_s=sa_p**4*0.4
                edge=spurs_mid-fair_s
                print("    SPURS losing_series fair="+str(round(fair_s,3))+" poly="+str(round(spurs_mid,3))+" EDGE="+str(round(edge*100,1))+"%")
                if edge>0.03 and spurs_mid>0.01:
                    tok=poly.get("SPURS",{}).get("no")
                    signals.append({"asset":"SPURS_NBA","token_id":tok,"direction":"BUY_NO",
                        "entry":round(1-spurs_mid,4),"fair":round(1-fair_s,4),
                        "edge":abs(edge),"reason":"SA losing series fair="+str(round(fair_s,3))+" poly="+str(round(spurs_mid,3))})
        if g["sport"]=="nhl" and "CAR" in(away,home):
            car_p=ap if away=="CAR" else hp
            vgk_mid=poly.get("VGK",{}).get("mid") or 0.441
            fair=champ_prob(car_p,vgk_mid)
            mid=poly.get("CAR",{}).get("mid") or 0
            edge=mid-fair
            print("    CAR game_p="+str(round(car_p,3))+" fair_champ="+str(round(fair,3))+" poly="+str(round(mid,3))+" EDGE="+str(round(edge*100,1))+"%")
            if abs(edge)>0.03 and mid>0.01:
                buy_no=edge>0
                tok=poly.get("CAR",{}).get("no" if buy_no else"yes")
                entry=round((1-mid) if buy_no else mid,4)
                signals.append({"asset":"CAR_NHL","token_id":tok,
                    "direction":"BUY_NO" if buy_no else"BUY_YES",
                    "entry":entry,"fair":round((1-fair) if buy_no else fair,4),
                    "edge":abs(edge),"reason":"DK="+str(round(car_p,3))+" fair="+str(round(fair,3))+" poly="+str(round(mid,3))})
    if not signals:
        for t,p in sorted(poly.items(),key=lambda x:-x[1]["vol24"]):
            if abs(p["1h"])>=0.005 and 0.05<p["mid"]<0.95 and p["vol24"]>30000:
                buy=p["1h"]>0
                tok=p.get("yes" if buy else"no")
                if tok:
                    entry=round(p["ask"] if buy else 1-p["bid"],4)
                    signals.append({"asset":t+"_MOM","token_id":tok,
                        "direction":"BUY_YES" if buy else"BUY_NO",
                        "entry":entry,"fair":round(p["mid"]+p["1h"]*3,4),
                        "edge":abs(p["1h"])*3,"reason":t+" 1h="+str(round(p["1h"],4))+" vol24="+str(int(p["vol24"]))})
                    break
    signals.sort(key=lambda x:-x["edge"])
    base={"id":1,"btc_price":price_btc,"price_history":hist,"last_run_ts":now,
          "poly_up_price":poly.get("OKC",{}).get("mid") or 0}
    if not signals:
        print("\n  Sem sinal (edges abaixo de 3%)")
        su("gravia_state",base);return
    sig=signals[0]
    if not sig.get("token_id"):
        print("\n  Token ausente: "+sig["asset"])
        su("gravia_state",base);return
    ex,model=ai_decide("Arb "+sig["asset"]+" "+sig["direction"]+" edge="+str(round(sig["edge"]*100,1))+"%\n"+sig["reason"]+"\nEXECUTE or SKIP?")
    print("\n  AI("+model+"): "+("EXECUTE" if ex else"SKIP")+" | "+sig["asset"]+" "+sig["direction"]+" edge="+str(round(sig["edge"]*100,1))+"%")
    si("gravia_signals",{"direction":sig["direction"],"btc_pct":sig["edge"],
        "poly_price":sig["entry"],"fair_prob":sig["fair"],"edge":sig["edge"],"executed":ex})
    if not ex:su("gravia_state",base);return
    if st.get("has_open_position") and st.get("open_entry_ts"):
        ot=sg("gravia_trades","status=eq.open&order=ts.desc&limit=1")
        if ot and ot[0].get("id"):
            hold=now-(st.get("open_entry_ts") or now)
            dir_yes="YES" in(st.get("open_direction") or"")
            old_t=(st.get("market_id") or"").split("_")[0]
            cur=poly.get(old_t,{}).get("mid") or st.get("open_entry_price") or 0.5
            ep=float(cur if dir_yes else 1-cur)
            op=st.get("open_entry_price") or 0.5
            sz=st.get("open_size_usdc") or 10
            pnl=(ep-op)*(1 if dir_yes else-1)*(sz/max(op,0.001))
            won=pnl>0
            sp("gravia_trades",{"exit_price":round(ep,4),"hold_seconds":hold,
                "pnl_usdc":round(pnl,4),"roi_pct":round(pnl/sz*100,2),"won":won,"status":"closed"},
                "id=eq."+str(ot[0]["id"]))
            tp=(st.get("total_pnl") or 0)+pnl
            cl=0 if won else(st.get("consec_losses") or 0)+1
            print("  "+("WIN" if won else"LOSS")+" P&L="+str(round(pnl,4))+" total=$"+str(round(tp,4)))
            base.update({"has_open_position":False,"total_pnl":tp,
                "total_wins":(st.get("total_wins") or 0)+(1 if won else 0),
                "total_trades":(st.get("total_trades") or 0)+1,"consec_losses":cl,
                "daily_pnl":(st.get("daily_pnl") or 0)+pnl,
                "is_halted":(st.get("daily_pnl") or 0)+pnl<=-50 or cl>=5})
    order=place_order(sig["token_id"],"BUY" if"YES" in sig["direction"] else"SELL",sig["entry"],5.0)
    si("gravia_trades",{"direction":sig["direction"],"entry_price":sig["entry"],
        "size_usdc":5,"edge":sig["edge"],"btc_pct":sig["edge"],"market_id":sig["asset"],"status":"open"})
    base.update({"has_open_position":True,"open_direction":sig["direction"],
        "open_entry_price":sig["entry"],"open_entry_ts":now,"open_size_usdc":10,
        "open_fair_prob":sig["fair"],"open_edge":sig["edge"],"market_id":sig["asset"]})
    su("gravia_state",base)
    roi=(sig["fair"]-sig["entry"])/max(sig["entry"],0.001)*10
    print("\n  "+mode+": "+str(order))
    print("  OK "+str(int((time.time()-T0)*1000))+"ms | "+sig["asset"]+" "+sig["direction"]+" @ "+str(sig["entry"])+" fair="+str(sig["fair"])+" P&L_esp=$"+str(round(roi,2)))

main()
