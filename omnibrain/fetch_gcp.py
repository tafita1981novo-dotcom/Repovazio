#!/usr/bin/env python3
"""
OMNIBRAIN — Transcript Fetcher para VM GCP
Roda em 34.148.152.96 (IP de datacenter Google, precisa de cookies YT)
Usa yt-dlp que funciona mesmo em IP de datacenter quando tem cookies
"""
import os, json, re, time, tempfile, subprocess, sys, glob, logging
import requests
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_KEY']
COOKIES_FILE = os.environ.get('COOKIES_FILE', '/home/rafael/yt_cookies.txt')
BATCH_SIZE   = int(os.environ.get('BATCH_SIZE', '50'))
MAX_WORKERS  = int(os.environ.get('MAX_WORKERS', '5'))
MAX_CHARS    = 60_000
LANG_PRIO    = ['pt', 'pt-BR', 'en', 'es']

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('omnibrain')

def sb(method, path, **kw):
    hdrs = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal',
    }
    r = requests.request(method, f"{SUPABASE_URL}/rest/v1{path}",
                         headers=hdrs, timeout=15, **kw)
    r.raise_for_status()
    return r

def get_pending(n):
    r = sb('GET', '/yt_transcripts',
           params={'select': 'video_id', 'status': 'eq.pending', 'limit': str(n)})
    return [row['video_id'] for row in r.json()]

def count_status(status):
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/yt_transcripts",
        params={'select': 'video_id', 'status': f'eq.{status}'},
        headers={'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}',
                 'Prefer': 'count=exact'},
        timeout=10
    )
    return int(r.headers.get('content-range','0/0').split('/')[-1])

def update_results(results):
    now = datetime.now(timezone.utc).isoformat()
    for r in results:
        body = {'status': r['status'], 'fetched_at': now}
        if r['status'] == 'done':
            body.update({
                'transcript': r.get('transcript', ''),
                'lang': r.get('lang', ''),
                'word_count': r.get('word_count', 0),
            })
        else:
            body['error_msg'] = r.get('error_msg', '')[:255]
        try:
            sb('PATCH', '/yt_transcripts',
               params={'video_id': f'eq.{r["video_id"]}'}, json=body)
        except Exception as e:
            log.warning(f"  DB error {r['video_id']}: {e}")

def parse_vtt(vtt_text):
    """Extrai texto limpo de um arquivo VTT."""
    lines = vtt_text.split('\n')
    texts, prev = [], ''
    for line in lines:
        line = line.strip()
        if not line or line.startswith('WEBVTT') or '-->' in line or re.match(r'^\d+$', line) or line.startswith('NOTE'):
            continue
        clean = re.sub(r'<[^>]+>', '', line)
        clean = clean.replace('&amp;','&').replace('&#39;',"'").replace('&quot;','"')
        clean = clean.strip()
        if clean and clean != prev:
            texts.append(clean)
            prev = clean
    return ' '.join(texts)

def fetch_one(vid):
    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            'yt-dlp',
            '--write-auto-sub', '--write-sub',
            '--sub-langs', ','.join(LANG_PRIO),
            '--sub-format', 'vtt',
            '--skip-download', '--no-playlist',
            '-o', f'{tmpdir}/%(id)s.%(ext)s',
        ]
        if os.path.exists(COOKIES_FILE):
            cmd += ['--cookies', COOKIES_FILE]
        cmd.append(f'https://www.youtube.com/watch?v={vid}')

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        except subprocess.TimeoutExpired:
            return {'video_id': vid, 'status': 'error', 'error_msg': 'timeout'}

        out = result.stdout + result.stderr

        if 'Sign in' in out or 'cookies' in out.lower() and 'unavailable' not in out:
            return {'video_id': vid, 'status': 'error', 'error_msg': 'login_required'}
        if any(x in out for x in ['unavailable', 'removed', 'private', 'Private video']):
            return {'video_id': vid, 'status': 'no_captions', 'error_msg': 'video_unavailable'}
        if any(x in out for x in ["doesn't have", 'No subtitles', 'no subtitle']):
            return {'video_id': vid, 'status': 'no_captions', 'error_msg': 'no_subtitles'}

        vtt_files = sorted(glob.glob(f'{tmpdir}/*.vtt'))
        if not vtt_files:
            return {'video_id': vid, 'status': 'no_captions', 'error_msg': 'no_vtt'}

        # Seleciona melhor idioma
        selected = vtt_files[0]
        for lang in LANG_PRIO:
            for f in vtt_files:
                if f'.{lang}.' in f or f'-{lang}.' in f:
                    selected = f; break
            else: continue
            break

        lang_code = 'und'
        m = re.search(r'\.([\w-]+)\.vtt$', os.path.basename(selected))
        if m:
            lang_code = m.group(1)

        with open(selected, encoding='utf-8') as f:
            text = parse_vtt(f.read())

        if not text or len(text) < 20:
            return {'video_id': vid, 'status': 'no_captions', 'error_msg': 'empty_vtt'}

        return {
            'video_id': vid, 'status': 'done',
            'transcript': text[:MAX_CHARS],
            'lang': lang_code,
            'word_count': len(text.split()),
        }

def main():
    log.info(f"🚀 OMNIBRAIN GCP | batch={BATCH_SIZE} workers={MAX_WORKERS}")
    log.info(f"   Cookies: {'✅ ' + COOKIES_FILE if os.path.exists(COOKIES_FILE) else '❌ não encontrado'}")

    try:
        p = count_status('pending')
        d = count_status('done')
        log.info(f"📊 Supabase: {p} pending | {d} done")
    except Exception as e:
        log.error(f"Erro Supabase: {e}")
        sys.exit(1)

    total_done = total_nc = total_err = 0
    round_n = 0

    while True:
        round_n += 1
        vids = get_pending(BATCH_SIZE)
        if not vids:
            log.info(f"\n✅ Concluído! ✅{total_done} 🔇{total_nc} ❌{total_err}")
            break

        log.info(f"\n📋 Round {round_n}: {len(vids)} vídeos...")
        t0 = time.time()

        results = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {pool.submit(fetch_one, vid): vid for vid in vids}
            for i, fut in enumerate(as_completed(futures), 1):
                r = fut.result()
                results.append(r)
                if i % 10 == 0:
                    d_ = sum(1 for x in results if x['status']=='done')
                    log.info(f"  ↳ {i}/{len(vids)} | ✅{d_}")

        update_results(results)
        d = sum(1 for r in results if r['status']=='done')
        nc = sum(1 for r in results if r['status']=='no_captions')
        er = sum(1 for r in results if r['status']=='error')
        total_done += d; total_nc += nc; total_err += er

        elapsed = time.time() - t0
        vps = len(vids)/elapsed if elapsed > 0 else 0
        pending_left = count_status('pending')
        eta = int(pending_left/vps/60) if vps > 0 else 999
        log.info(f"  ✅{d} 🔇{nc} ❌{er} | {vps:.1f}v/s | {pending_left} restantes | ETA ~{eta}min")
        time.sleep(2)

if __name__ == '__main__':
    main()
