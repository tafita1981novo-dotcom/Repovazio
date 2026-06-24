#!/usr/bin/env python3
"""
OMNIBRAIN — YouTube Transcript Fetcher SEM KEY SUPABASE
Salva resultados em /tmp/transcripts_batch_NNN.json
Enviar para o Supabase depois via MCP ou pelo dashboard.

Uso:
    python omnibrain_fetch_no_key.py

Requisitos:
    pip install requests
"""

import json, re, time, sys, logging, os
import xml.etree.ElementTree as ET
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

BATCH_FILE_PREFIX = '/tmp/transcripts_batch'
MAX_CHARS   = 60_000
MAX_WORKERS = 15
ANDROID_UA  = 'com.google.android.youtube/20.10.38 (Linux; U; Android 11) gzip'
WEB_UA      = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('omnibrain')

# Lista de video IDs — lê do arquivo all_video_ids.json se existir
VIDEO_IDS_FILE = 'data/video_metadata.json'  # ou all_video_ids.json

def load_video_ids() -> list:
    """Carrega lista de video IDs."""
    # Tenta vários caminhos
    for path in [VIDEO_IDS_FILE, '/tmp/all_video_ids.json', 'all_video_ids.json']:
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            if isinstance(data, list):
                # all_video_ids.json: lista direta
                if data and isinstance(data[0], str):
                    return data
                # video_metadata.json: lista de objetos com videoId
                if data and isinstance(data[0], dict):
                    return [v.get('videoId') or v.get('video_id','') for v in data]
    log.error("Nenhum arquivo de video IDs encontrado!")
    sys.exit(1)

def parse_timedtext(xml_text: str) -> str:
    clean_xml = re.sub(r' xmlns[^"]*"[^"]*"', '', xml_text)
    try:
        root = ET.fromstring(clean_xml)
        texts = []
        for p in root.iter('p'):
            parts = [s.text.strip() for s in p.iter('s') if s.text]
            if parts:
                texts.append(' '.join(parts))
            elif p.text and p.text.strip():
                texts.append(p.text.strip())
        if texts:
            return ' '.join(texts)
    except ET.ParseError:
        pass
    txt = re.sub(r'<[^>]+>', ' ', xml_text)
    for esc, rep in [('&amp;','&'),('&#39;',"'"),('&quot;','"'),('&lt;','<'),('&gt;','>')]:
        txt = txt.replace(esc, rep)
    return re.sub(r'\s+', ' ', txt).strip()

def fetch_one(vid: str, api_key: str, session: requests.Session) -> dict:
    try:
        resp = session.post(
            f"https://www.youtube.com/youtubei/v1/player?key={api_key}",
            json={"videoId": vid,
                  "context": {"client": {"clientName": "ANDROID", "clientVersion": "20.10.38"}}},
            headers={'User-Agent': ANDROID_UA, 'Content-Type': 'application/json'},
            timeout=14
        )
        data = resp.json()
        pb = data.get('playabilityStatus', {})
        if pb.get('status') == 'ERROR':
            return {'video_id': vid, 'status': 'no_captions', 'error_msg': pb.get('reason','')[:100]}
        if 'Sign in' in pb.get('reason', ''):
            return {'video_id': vid, 'status': 'error', 'error_msg': 'login_required'}
        
        tracks = (data.get('captions',{})
                      .get('playerCaptionsTracklistRenderer',{})
                      .get('captionTracks',[]))
        if not tracks:
            return {'video_id': vid, 'status': 'no_captions', 'error_msg': 'no_tracks'}
        
        selected = tracks[0]
        for lang in ['pt','en','es','fr']:
            for t in tracks:
                if t.get('languageCode','').startswith(lang):
                    selected = t; break
            else: continue
            break
        
        caption_url = selected.get('baseUrl', '')
        lang_code   = selected.get('languageCode', '')
        
        cr = session.get(caption_url, timeout=12, headers={'User-Agent': ANDROID_UA})
        if not cr.text:
            return {'video_id': vid, 'status': 'no_captions', 'error_msg': 'empty_caption'}
        
        text = parse_timedtext(cr.text)
        if not text or len(text) < 20:
            return {'video_id': vid, 'status': 'no_captions', 'error_msg': 'empty_after_parse'}
        
        return {'video_id': vid, 'status': 'done',
                'transcript': text[:MAX_CHARS], 'lang': lang_code,
                'word_count': len(text.split())}
    except requests.exceptions.Timeout:
        return {'video_id': vid, 'status': 'error', 'error_msg': 'timeout'}
    except Exception as e:
        return {'video_id': vid, 'status': 'error', 'error_msg': str(e)[:200]}

def main():
    vids = [v for v in load_video_ids() if v]
    log.info(f"🚀 {len(vids)} vídeos carregados | workers={MAX_WORKERS}")
    
    session = requests.Session()
    r0 = session.get("https://www.youtube.com", timeout=10,
                     headers={'User-Agent': WEB_UA, 'Accept-Language': 'pt-BR,pt;q=0.9'})
    api_key = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', r0.text).group(1)
    log.info(f"✅ YouTube API key obtida")
    
    CHUNK = 200
    all_results = []
    
    for batch_num, start in enumerate(range(0, len(vids), CHUNK), 1):
        chunk = vids[start:start+CHUNK]
        log.info(f"📋 Batch {batch_num}/{(len(vids)+CHUNK-1)//CHUNK}: {len(chunk)} vídeos...")
        
        results = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {pool.submit(fetch_one, vid, api_key, session): vid for vid in chunk}
            for i, fut in enumerate(as_completed(futures), 1):
                r = fut.result()
                results.append(r)
                if i % 50 == 0:
                    log.info(f"  ↳ {i}/{len(chunk)}")
        
        all_results.extend(results)
        
        # Salva batch em arquivo JSON
        outfile = f"{BATCH_FILE_PREFIX}_{batch_num:03d}.json"
        with open(outfile, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False)
        
        done = sum(1 for r in results if r['status']=='done')
        no_cap = sum(1 for r in results if r['status']=='no_captions')
        err = sum(1 for r in results if r['status']=='error')
        log.info(f"  💾 Salvo em {outfile} | ✅{done} 🔇{no_cap} ❌{err}")
        
        time.sleep(1)
    
    # Resumo final
    total_done = sum(1 for r in all_results if r['status']=='done')
    total_nc   = sum(1 for r in all_results if r['status']=='no_captions')
    total_err  = sum(1 for r in all_results if r['status']=='error')
    log.info(f"\n=== COMPLETO === ✅{total_done} 🔇{total_nc} ❌{total_err}")
    log.info(f"Arquivos salvos: {BATCH_FILE_PREFIX}_001.json ... _{batch_num:03d}.json")
    log.info("Próximo passo: enviar os JSONs para o Supabase via script de upload")

if __name__ == '__main__':
    main()
