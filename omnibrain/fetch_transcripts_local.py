#!/usr/bin/env python3
"""
OMNIBRAIN — YouTube Transcript Fetcher LOCAL
Roda na máquina local (IP residencial, sem bloqueio do YouTube)

Uso:
    pip install requests supabase
    python omnibrain_fetch_local.py

Configurar:
    SUPABASE_URL e SUPABASE_KEY como variáveis de ambiente, ou editar as constantes abaixo.
"""

import os, json, re, time, sys, logging
import xml.etree.ElementTree as ET
import requests
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Configuração ──────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://tpjvalzwkqwttvmszvie.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')  # service_role key aqui

BATCH_SIZE  = int(os.environ.get('BATCH_SIZE', '200'))   # vídeos por rodada
MAX_WORKERS = int(os.environ.get('MAX_WORKERS', '15'))    # threads paralelas
MAX_CHARS   = 60_000                                       # limite de chars por transcrição

ANDROID_UA  = 'com.google.android.youtube/20.10.38 (Linux; U; Android 11) gzip'
WEB_UA      = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
LANG_PRIO   = ['pt', 'en', 'es', 'fr', 'de']

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger('omnibrain')

# ── Supabase REST helpers ─────────────────────────────────────────────────────
def sb_get_pending(n: int) -> list[str]:
    """Retorna até n video_ids com status=pending."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/yt_transcripts",
        params={'select': 'video_id', 'status': 'eq.pending', 'limit': str(n)},
        headers={'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'},
        timeout=15
    )
    resp.raise_for_status()
    return [row['video_id'] for row in resp.json()]

def sb_update(results: list[dict]) -> None:
    """Atualiza cada resultado no Supabase via PATCH REST."""
    now = datetime.now(timezone.utc).isoformat()
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal',
    }
    for r in results:
        vid = r['video_id']
        body = {'status': r['status'], 'fetched_at': now}
        if r['status'] == 'done':
            body['transcript'] = r.get('transcript', '')
            body['lang']       = r.get('lang', '')
            body['word_count'] = r.get('word_count', 0)
        else:
            body['error_msg'] = r.get('error_msg', '')[:255]
        
        try:
            resp = requests.patch(
                f"{SUPABASE_URL}/rest/v1/yt_transcripts",
                params={'video_id': f'eq.{vid}'},
                headers=headers,
                json=body,
                timeout=10
            )
            resp.raise_for_status()
        except Exception as e:
            log.warning(f"DB update failed for {vid}: {e}")

# ── YouTube transcript logic ──────────────────────────────────────────────────
def parse_timedtext(xml_text: str) -> str:
    """Extrai texto limpo do XML timedtext do YouTube."""
    clean_xml = re.sub(r' xmlns[^"]*"[^"]*"', '', xml_text)
    try:
        root = ET.fromstring(clean_xml)
        texts = []
        for p in root.iter('p'):
            parts = []
            for s in p.iter('s'):
                if s.text:
                    parts.append(s.text.strip())
            if parts:
                texts.append(' '.join(parts))
            elif p.text and p.text.strip():
                texts.append(p.text.strip())
        if texts:
            return ' '.join(texts)
    except ET.ParseError:
        pass
    # Fallback: strip tags
    txt = re.sub(r'<[^>]+>', ' ', xml_text)
    for esc, rep in [('&amp;','&'),('&#39;',"'"),('&quot;','"'),('&lt;','<'),('&gt;','>')]:
        txt = txt.replace(esc, rep)
    return re.sub(r'\s+', ' ', txt).strip()

def fetch_one(vid: str, api_key: str, session: requests.Session) -> dict:
    """Busca transcrição de um vídeo via InnerTube API."""
    try:
        resp = session.post(
            f"https://www.youtube.com/youtubei/v1/player?key={api_key}",
            json={
                "videoId": vid,
                "context": {"client": {"clientName": "ANDROID", "clientVersion": "20.10.38"}}
            },
            headers={'User-Agent': ANDROID_UA, 'Content-Type': 'application/json'},
            timeout=14
        )
        data = resp.json()
        
        pb = data.get('playabilityStatus', {})
        if pb.get('status') == 'ERROR':
            return {'video_id': vid, 'status': 'no_captions', 'error_msg': pb.get('reason','error')[:100]}
        if 'Sign in' in pb.get('reason','') or pb.get('status') == 'LOGIN_REQUIRED':
            return {'video_id': vid, 'status': 'error', 'error_msg': 'login_required'}
        
        tracks = (data.get('captions', {})
                      .get('playerCaptionsTracklistRenderer', {})
                      .get('captionTracks', []))
        
        if not tracks:
            return {'video_id': vid, 'status': 'no_captions', 'error_msg': 'no_tracks'}
        
        # Seleciona melhor idioma
        selected = tracks[0]
        for lang in LANG_PRIO:
            for t in tracks:
                if t.get('languageCode', '').startswith(lang):
                    selected = t
                    break
            else:
                continue
            break
        
        lang_code   = selected.get('languageCode', '')
        caption_url = selected.get('baseUrl', '')
        
        cr = session.get(caption_url, timeout=12,
                         headers={'User-Agent': ANDROID_UA})
        
        if not cr.text:
            return {'video_id': vid, 'status': 'no_captions', 'error_msg': 'empty_caption'}
        
        text = parse_timedtext(cr.text)
        if not text or len(text) < 20:
            return {'video_id': vid, 'status': 'no_captions', 'error_msg': 'empty_after_parse'}
        
        return {
            'video_id'  : vid,
            'status'    : 'done',
            'transcript': text[:MAX_CHARS],
            'lang'      : lang_code,
            'word_count': len(text.split()),
        }
    
    except requests.exceptions.Timeout:
        return {'video_id': vid, 'status': 'error', 'error_msg': 'timeout'}
    except Exception as e:
        return {'video_id': vid, 'status': 'error', 'error_msg': str(e)[:200]}

# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    if not SUPABASE_KEY:
        print("❌ SUPABASE_KEY não configurada. Abra o script e coloque sua service_role key.")
        sys.exit(1)
    
    log.info(f"🚀 OMNIBRAIN local | batch={BATCH_SIZE} workers={MAX_WORKERS}")
    
    # Pega o API key do YouTube uma vez
    session = requests.Session()
    r0 = session.get("https://www.youtube.com", timeout=10,
                     headers={'User-Agent': WEB_UA, 'Accept-Language': 'pt-BR,pt;q=0.9'})
    api_key_match = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', r0.text)
    if not api_key_match:
        log.error("Não conseguiu extrair INNERTUBE_API_KEY. Verifique conexão.")
        sys.exit(1)
    api_key = api_key_match.group(1)
    log.info(f"✅ API key: {api_key[:20]}...")
    
    total_done = total_no_cap = total_err = 0
    round_num = 0
    
    while True:
        round_num += 1
        
        # Pega pending
        try:
            vids = sb_get_pending(BATCH_SIZE)
        except Exception as e:
            log.error(f"Erro ao buscar pending: {e}")
            time.sleep(10)
            continue
        
        if not vids:
            log.info(f"✅ Tudo processado! done={total_done} no_captions={total_no_cap} errors={total_err}")
            break
        
        log.info(f"📋 Round {round_num}: {len(vids)} vídeos a processar...")
        
        # Processa em paralelo
        results = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {pool.submit(fetch_one, vid, api_key, session): vid for vid in vids}
            for i, fut in enumerate(as_completed(futures), 1):
                r = fut.result()
                results.append(r)
                if i % 25 == 0:
                    log.info(f"  ↳ {i}/{len(vids)} ({r['status']})")
        
        # Salva
        log.info(f"💾 Salvando {len(results)} resultados...")
        sb_update(results)
        
        # Stats
        rd = sum(1 for r in results if r['status'] == 'done')
        rn = sum(1 for r in results if r['status'] == 'no_captions')
        re_ = sum(1 for r in results if r['status'] == 'error')
        total_done += rd; total_no_cap += rn; total_err += re_
        log.info(f"  Round {round_num}: ✅{rd} 🔇{rn} ❌{re_} | Total: ✅{total_done} 🔇{total_no_cap} ❌{total_err}")
        
        # Pausa pequena entre rounds para não sobrecarregar
        if vids:
            time.sleep(2)

if __name__ == '__main__':
    main()
