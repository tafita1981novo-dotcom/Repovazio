#!/usr/bin/env python3
"""
daily_report.py — Relatório diário de crescimento @psidanielacoelho
Gera relatório e salva no Supabase + notifica via webhook
"""
import os, json, requests
from datetime import datetime, timezone, timedelta

SBU = os.getenv("SBU","https://tpjvalzwkqwttvmszvie.supabase.co")
SBK = os.getenv("SBK","")
H_SB = {"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json"}

def sb(path): return requests.get(SBU+"/rest/v1/"+path,headers=H_SB,timeout=10).json()

def main():
    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Pipeline
    pipe   = sb("content_pipeline?select=status")
    status = {}
    for r in (pipe if isinstance(pipe,list) else []):
        status[r['status']] = status.get(r['status'],0)+1

    # Snapshot do canal
    snap = sb("channel_snapshots?order=snapshot_at.desc&limit=1")
    canal = snap[0] if isinstance(snap,list) and snap else {}
    
    subs     = canal.get("subscribers",0)
    views_28 = canal.get("views_28d",0)
    ctr_28   = canal.get("ctr_28d",0)
    delta    = canal.get("delta_subs",0)
    
    # Plano ativo
    plano = sb("growth_plan?status=eq.ativo&limit=1")
    fase_atual = plano[0].get("fase","—") if isinstance(plano,list) and plano else "—"
    
    pct_1k = round(subs/1000*100,1) if subs else 0

    report = f"""# 📊 Relatório Diário — @psidanielacoelho
**Data:** {hoje}

## 🎯 Canal
- **Subscribers:** {subs} / 1.000 ({pct_1k}% da meta)
- **Delta hoje:** {'+' if delta>=0 else ''}{delta} subs
- **Views 28d:** {(views_28 or 0):,}
- **CTR médio:** {ctr_28:.1f}%

## 📦 Pipeline
- ✅ Publicados: {status.get('published',0)}
- 🎙️ Prontos para TTS: {status.get('ready_tts',0)}
- 🎬 MP4 prontos: {status.get('mp4_ready',0)}
- ⚙️ Gerando: {status.get('pending_generation',0)}

## 🚀 Fase Atual
{fase_atual}

## ⚡ Ações do Dia
1. Publicar os {status.get('mp4_ready',0)} vídeos prontos (aguardando YouTube token)
2. Responder todos os comentários nas primeiras 2h
3. Postar 1 Short dos melhores momentos do long mais recente
4. Verificar CTR — dobrar orçamento ads no melhor vídeo
5. Meta do dia: +{max(1, round(1000-subs)/30):.0f} novos subscribers

---
*Gerado automaticamente por Growth Engine V1 | psicologia.doc*
"""
    
    # Salvar no Supabase
    requests.post(SBU+"/rest/v1/cerebro_logs",
        headers={**H_SB,"Prefer":"return=minimal"},
        json={"type":"daily_report","message":f"Relatório {hoje}",
              "details":{"report":report,"subs":subs,"delta":delta,"pct_1k":pct_1k}}
    )
    print(report)

if __name__ == "__main__":
    main()
