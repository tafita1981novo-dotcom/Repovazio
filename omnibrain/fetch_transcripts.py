#!/usr/bin/env python3
"""
OMNIBRAIN — YouTube Transcript Fetcher FAST
Usa ThreadPoolExecutor para buscar 500 transcrições em paralelo por run.
"""

import os
import json
import time
import logging
import concurrent.futures
from datetime import datetime, timezone
from supabase import create_client, Client
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    CouldNotRetrieveTranscript,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_KEY']
BATCH_SIZE   = int(os.environ.get('BATCH_SIZE', '500'))
MAX_WORKERS  = int(os.environ.get('MAX_WORKERS', '30'))
MAX_CHARS    = 60_000   # chars máximos por transcrição

LANG_PRIORITY = ['pt', 'pt-BR', 'pt-PT', 'en', 'en-US', 'en-GB',
                 'es', 'fr', 'de', 'it', 'ja', 'ko', 'zh-Hans', 'zh']


def fetch_one(video_id: str) -> dict:
    """Busca a transcrição de um vídeo. Retorna dict seguro para UPDATE."""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        transcript = None
        lang_used  = None

        # 1) tenta idiomas na ordem de prioridade
        for lang in LANG_PRIORITY:
            try:
                t = transcript_list.find_transcript([lang])
                transcript = t
                lang_used  = t.language_code
                break
            except Exception:
                continue

        # 2) pega o primeiro disponível (manual ou gerado)
        if transcript is None:
            for t in transcript_list:
                transcript = t
                lang_used  = t.language_code
                break

        if transcript is None:
            return {
                'video_id': video_id,
                'status':   'no_captions',
                'error_msg': 'no transcript in any language',
            }

        snippets  = transcript.fetch()
        full_text = ' '.join(s.get('text', '') for s in snippets).strip()

        if not full_text:
            return {
                'video_id':  video_id,
                'status':    'no_captions',
                'error_msg': 'empty transcript',
            }

        return {
            'video_id':   video_id,
            'status':     'done',
            'transcript': full_text[:MAX_CHARS],
            'lang':       lang_used or '',
            'word_count': len(full_text.split()),
        }

    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable):
        return {'video_id': video_id, 'status': 'no_captions',
                'error_msg': 'disabled or unavailable'}
    except CouldNotRetrieveTranscript as e:
        return {'video_id': video_id, 'status': 'no_captions',
                'error_msg': str(e)[:200]}
    except Exception as e:
        return {'video_id': video_id, 'status': 'error',
                'error_msg': str(e)[:200]}


def update_batch(sb: Client, results: list[dict]) -> None:
    """Grava todos os resultados de volta no Supabase em upserts individuais."""
    now = datetime.now(timezone.utc).isoformat()
    for r in results:
        data = {
            'status':     r['status'],
            'fetched_at': now,
        }
        if r['status'] == 'done':
            data['transcript'] = r.get('transcript', '')
            data['lang']       = r.get('lang', '')
            data['word_count'] = r.get('word_count', 0)
        else:
            data['error_msg'] = r.get('error_msg', '')

        try:
            sb.table('yt_transcripts') \
              .update(data) \
              .eq('video_id', r['video_id']) \
              .execute()
        except Exception as e:
            logger.warning(f"Supabase update failed for {r['video_id']}: {e}")


def main():
    logger.info(f"⚡ OMNIBRAIN fast-fetch | batch={BATCH_SIZE} workers={MAX_WORKERS}")
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Pega os vídeos pending
    res = (
        sb.table('yt_transcripts')
          .select('video_id')
          .eq('status', 'pending')
          .limit(BATCH_SIZE)
          .execute()
    )
    videos = res.data or []
    logger.info(f"📋 {len(videos)} vídeos a processar")

    if not videos:
        logger.info("✅ Nada pendente.")
        return

    video_ids = [v['video_id'] for v in videos]

    # Processa em paralelo
    results = []
    done_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(fetch_one, vid): vid for vid in video_ids}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            done_count += 1
            if done_count % 50 == 0:
                logger.info(f"  ↳ {done_count}/{len(video_ids)} processados...")

    # Salva no Supabase
    logger.info(f"💾 Gravando {len(results)} resultados no Supabase...")
    update_batch(sb, results)

    # Estatísticas
    stats = {}
    for r in results:
        s = r['status']
        stats[s] = stats.get(s, 0) + 1

    logger.info("=== Resultado do batch ===")
    logger.info(f"  ✅ done:        {stats.get('done', 0)}")
    logger.info(f"  🔇 no_captions: {stats.get('no_captions', 0)}")
    logger.info(f"  ❌ error:       {stats.get('error', 0)}")

    # Contagem geral
    try:
        total_res  = sb.table('yt_transcripts').select('video_id', count='exact').execute()
        pend_res   = sb.table('yt_transcripts').select('video_id', count='exact').eq('status', 'pending').execute()
        done_res   = sb.table('yt_transcripts').select('video_id', count='exact').eq('status', 'done').execute()
        logger.info(f"📊 Total: {total_res.count} | Pending: {pend_res.count} | Done: {done_res.count}")
    except Exception:
        pass


if __name__ == '__main__':
    main()
