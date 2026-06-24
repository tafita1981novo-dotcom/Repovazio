#!/usr/bin/env python3
"""
OMNIBRAIN — YouTube Transcript Fetcher
Busca transcrições dos vídeos pending no Supabase.
Roda via GitHub Actions a cada 4h, processando 50 vídeos por run.
"""

import os
import json
import time
import logging
from datetime import datetime
from supabase import create_client, Client
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from youtube_transcript_api.formatters import TextFormatter

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_KEY']
BATCH_SIZE = int(os.environ.get('BATCH_SIZE', '50'))

# Idiomas preferidos para busca de transcrição
LANG_PRIORITY = ['pt', 'pt-BR', 'pt-PT', 'en', 'en-US', 'en-GB', 'es', 'fr', 'de', 'it', 'ja', 'ko', 'zh']

def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_transcript(video_id: str) -> dict:
    """Busca transcrição de um vídeo. Retorna dict com transcript, lang, word_count."""
    try:
        # Lista todas as transcrições disponíveis
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        transcript = None
        lang_used = None
        
        # Tenta idiomas na ordem de prioridade
        for lang in LANG_PRIORITY:
            try:
                t = transcript_list.find_transcript([lang])
                transcript = t
                lang_used = t.language_code
                break
            except (NoTranscriptFound, Exception):
                continue
        
        # Se não achou nenhum da lista, pega o primeiro disponível
        if not transcript:
            try:
                # Tenta pegar qualquer transcrição manualmente gerada
                for t in transcript_list:
                    transcript = t
                    lang_used = t.language_code
                    break
            except Exception:
                pass
        
        if not transcript:
            return {'status': 'no_captions', 'error': 'No transcript found in any language'}
        
        # Busca o conteúdo da transcrição
        formatter = TextFormatter()
        snippets = transcript.fetch()
        
        # Concatena texto
        text_parts = [s['text'] for s in snippets]
        full_text = ' '.join(text_parts).strip()
        
        if not full_text:
            return {'status': 'no_captions', 'error': 'Empty transcript'}
        
        word_count = len(full_text.split())
        
        return {
            'status': 'done',
            'transcript': full_text[:50000],  # limita a 50k chars
            'lang': lang_used,
            'word_count': word_count
        }
        
    except TranscriptsDisabled:
        return {'status': 'no_captions', 'error': 'Transcripts disabled'}
    except VideoUnavailable:
        return {'status': 'no_captions', 'error': 'Video unavailable'}
    except NoTranscriptFound:
        return {'status': 'no_captions', 'error': 'No transcript found'}
    except Exception as e:
        err = str(e)[:200]
        logger.error(f"Error fetching {video_id}: {err}")
        return {'status': 'error', 'error': err}

def main():
    logger.info(f"Starting transcript fetch — batch size: {BATCH_SIZE}")
    sb = get_supabase()
    
    # Busca batch de vídeos pendentes
    res = sb.table('yt_transcripts')\
        .select('video_id, title')\
        .eq('status', 'pending')\
        .limit(BATCH_SIZE)\
        .execute()
    
    videos = res.data
    logger.info(f"Found {len(videos)} pending videos to process")
    
    if not videos:
        logger.info("No pending videos. Done!")
        return
    
    stats = {'done': 0, 'no_captions': 0, 'error': 0}
    
    for i, video in enumerate(videos):
        vid_id = video['video_id']
        title = video.get('title', '')[:60]
        logger.info(f"[{i+1}/{len(videos)}] {vid_id} — {title}")
        
        result = fetch_transcript(vid_id)
        status = result['status']
        stats[status] = stats.get(status, 0) + 1
        
        # Atualiza no Supabase
        update_data = {
            'status': status,
            'fetched_at': datetime.utcnow().isoformat()
        }
        if status == 'done':
            update_data['transcript'] = result.get('transcript', '')
            update_data['lang'] = result.get('lang', '')
            update_data['word_count'] = result.get('word_count', 0)
        else:
            update_data['error_msg'] = result.get('error', '')
        
        try:
            sb.table('yt_transcripts')\
                .update(update_data)\
                .eq('video_id', vid_id)\
                .execute()
        except Exception as e:
            logger.error(f"Supabase update error for {vid_id}: {e}")
        
        # Rate limiting gentil
        time.sleep(0.3)
    
    logger.info(f"Batch complete — done:{stats.get('done',0)} no_captions:{stats.get('no_captions',0)} error:{stats.get('error',0)}")
    
    # Relatório final
    count_res = sb.table('yt_transcripts').select('status', count='exact').execute()
    total = sum(1 for r in sb.table('yt_transcripts').select('video_id').execute().data)
    logger.info(f"Total in table: {total}")

if __name__ == '__main__':
    main()
