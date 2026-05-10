"""
YouTube Channel Deep Research:
- Refresh OAuth token from refresh_token
- Fetch channel metadata, full upload list, video stats, transcripts
- Save to Supabase tables: viral_channel_research + viral_video_research
- Targets: Psych2Go + top psychology channels worldwide
"""
import os, sys, json, time, requests, re

YT_CLIENT_ID = os.environ['YT_CLIENT_ID']
YT_CLIENT_SECRET = os.environ['YT_CLIENT_SECRET']
YT_REFRESH_TOKEN = os.environ['YT_REFRESH_TOKEN']
SUPA_URL = os.environ['SUPABASE_URL']
SUPA_KEY = os.environ['SUPABASE_SERVICE_KEY']

S = requests.Session()
S.headers.update({
    'apikey': SUPA_KEY,
    'Authorization': f'Bearer {SUPA_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
})

def refresh_token():
    r = requests.post('https://oauth2.googleapis.com/token', data={
        'client_id': YT_CLIENT_ID,
        'client_secret': YT_CLIENT_SECRET,
        'refresh_token': YT_REFRESH_TOKEN,
        'grant_type': 'refresh_token'
    }, timeout=20)
    r.raise_for_status()
    return r.json()['access_token']

def yt_get(token, path, **params):
    r = requests.get(f'https://www.googleapis.com/youtube/v3/{path}',
        params={**params, 'access_token': token}, timeout=30)
    if not r.ok:
        print(f'  YT API error {r.status_code}: {r.text[:300]}')
    r.raise_for_status()
    return r.json()

def find_channel_id(token, handle_or_username):
    """Try multiple methods to resolve a channel ID from a handle/name."""
    h = handle_or_username.lstrip('@')
    # Method 1: search
    try:
        r = yt_get(token, 'search', part='snippet', type='channel', q=h, maxResults=5)
        if r.get('items'):
            for it in r['items']:
                if h.lower() in it['snippet']['channelTitle'].lower():
                    return it['snippet']['channelId']
            return r['items'][0]['snippet']['channelId']
    except Exception as e:
        print(f'  search failed: {e}')
    return None

def get_channel_data(token, channel_id):
    r = yt_get(token, 'channels', part='snippet,statistics,contentDetails,brandingSettings',
        id=channel_id, maxResults=1)
    if not r.get('items'):
        return None
    it = r['items'][0]
    return {
        'channel_id': channel_id,
        'title': it['snippet']['title'],
        'description': it['snippet'].get('description',''),
        'country': it['snippet'].get('country',''),
        'published_at': it['snippet']['publishedAt'],
        'subscriber_count': int(it['statistics'].get('subscriberCount',0)),
        'view_count': int(it['statistics'].get('viewCount',0)),
        'video_count': int(it['statistics'].get('videoCount',0)),
        'uploads_playlist': it['contentDetails']['relatedPlaylists']['uploads'],
        'keywords': it.get('brandingSettings',{}).get('channel',{}).get('keywords','')
    }

def list_uploads(token, uploads_playlist, max_videos=200):
    """Get all video IDs from uploads playlist (up to max)."""
    video_ids = []
    next_token = None
    while len(video_ids) < max_videos:
        params = {
            'part': 'contentDetails,snippet',
            'playlistId': uploads_playlist,
            'maxResults': 50
        }
        if next_token: params['pageToken'] = next_token
        r = yt_get(token, 'playlistItems', **params)
        for it in r.get('items',[]):
            video_ids.append({
                'video_id': it['contentDetails']['videoId'],
                'title': it['snippet']['title'],
                'published_at': it['contentDetails'].get('videoPublishedAt') or it['snippet']['publishedAt'],
                'description': it['snippet'].get('description','')[:500]
            })
        next_token = r.get('nextPageToken')
        if not next_token: break
        time.sleep(0.2)  # respect rate limits
    return video_ids[:max_videos]

def get_video_stats_batch(token, video_ids):
    """Get stats for up to 50 videos at once."""
    out = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        r = yt_get(token, 'videos', part='statistics,contentDetails,snippet',
            id=','.join(batch), maxResults=50)
        for it in r.get('items',[]):
            stats = it.get('statistics',{})
            duration = it['contentDetails']['duration']  # ISO 8601 PT15M30S
            # Parse ISO duration
            m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
            h, mn, sec = (int(m.group(i)) if m and m.group(i) else 0 for i in (1,2,3))
            duration_s = h*3600 + mn*60 + sec
            out[it['id']] = {
                'view_count': int(stats.get('viewCount',0)),
                'like_count': int(stats.get('likeCount',0)),
                'comment_count': int(stats.get('commentCount',0)),
                'duration_s': duration_s,
                'tags': it['snippet'].get('tags',[])[:20],
                'category_id': it['snippet'].get('categoryId',''),
                'default_language': it['snippet'].get('defaultLanguage','')
            }
        time.sleep(0.2)
    return out

def get_transcript(video_id):
    """Try to get English transcript via youtube-transcript-api (no auth needed)."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        try:
            t = YouTubeTranscriptApi.get_transcript(video_id, languages=['en','en-US','en-GB'])
        except:
            try:
                t = YouTubeTranscriptApi.get_transcript(video_id)
            except:
                return None
        if not t: return None
        text = ' '.join(s['text'] for s in t).replace('\n',' ').strip()
        return text[:8000]  # cap at 8K chars
    except Exception as e:
        return None

def supa_upsert(table, row, conflict_col='video_id'):
    r = S.post(f'{SUPA_URL}/rest/v1/{table}?on_conflict={conflict_col}',
        headers={'Prefer': 'resolution=merge-duplicates,return=representation'},
        json=[row], timeout=20)
    if not r.ok:
        print(f'  upsert {table} error {r.status_code}: {r.text[:200]}')
    return r.ok

def supa_upsert_channel(row):
    r = S.post(f'{SUPA_URL}/rest/v1/viral_channel_research?on_conflict=channel_id',
        headers={'Prefer': 'resolution=merge-duplicates,return=representation'},
        json=[row], timeout=20)
    if not r.ok:
        print(f'  upsert channel error {r.status_code}: {r.text[:200]}')

def research_channel(token, handle, max_videos=80, transcribe_top=15):
    print(f'\n========== {handle} ==========')
    cid = find_channel_id(token, handle)
    if not cid:
        print(f'  Could not resolve channel for {handle}')
        return
    print(f'  Channel ID: {cid}')
    
    ch = get_channel_data(token, cid)
    if not ch:
        print(f'  Could not fetch channel data')
        return
    print(f"  {ch['title']} | {ch['subscriber_count']:,} subs | {ch['video_count']:,} vids | {ch['view_count']:,} total views")
    
    supa_upsert_channel({
        'channel_id': ch['channel_id'],
        'handle': handle,
        'title': ch['title'],
        'description': ch['description'][:2000],
        'subscriber_count': ch['subscriber_count'],
        'video_count': ch['video_count'],
        'total_view_count': ch['view_count'],
        'country': ch['country'],
        'published_at': ch['published_at'],
        'keywords': ch['keywords'][:1000],
        'fetched_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    })
    
    print(f'  Listing uploads (max {max_videos})...')
    videos = list_uploads(token, ch['uploads_playlist'], max_videos=max_videos)
    print(f'  Got {len(videos)} videos')
    
    print(f'  Fetching stats...')
    stats = get_video_stats_batch(token, [v['video_id'] for v in videos])
    
    # Merge
    for v in videos:
        s = stats.get(v['video_id'], {})
        v.update(s)
    
    # Sort by views desc
    videos.sort(key=lambda x: x.get('view_count',0), reverse=True)
    
    # Save all
    print(f'  Saving {len(videos)} videos to Supabase...')
    for rank, v in enumerate(videos, 1):
        row = {
            'video_id': v['video_id'],
            'channel_id': cid,
            'channel_handle': handle,
            'title': v['title'],
            'published_at': v['published_at'],
            'description': v.get('description','')[:1000],
            'duration_s': v.get('duration_s', 0),
            'view_count': v.get('view_count', 0),
            'like_count': v.get('like_count', 0),
            'comment_count': v.get('comment_count', 0),
            'tags': v.get('tags', []),
            'rank_in_channel': rank,
            'is_short': v.get('duration_s', 0) <= 60,
            'fetched_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        }
        supa_upsert('viral_video_research', row)
    
    # Transcribe top N most viewed (only if NOT shorts - shorts rarely have transcripts)
    print(f'  Transcribing top {transcribe_top} (long-form)...')
    long_videos = [v for v in videos if v.get('duration_s',0) > 120][:transcribe_top]
    transcribed = 0
    for v in long_videos:
        t = get_transcript(v['video_id'])
        if t:
            S.patch(f"{SUPA_URL}/rest/v1/viral_video_research?video_id=eq.{v['video_id']}",
                json={'transcript_en': t}, timeout=20)
            transcribed += 1
            print(f"    ✓ {v['title'][:60]} ({len(t)}c)")
        time.sleep(0.5)
    print(f'  Transcribed {transcribed}/{len(long_videos)}')

def run():
    print('[1/4] Refreshing OAuth token...')
    token = refresh_token()
    print('  ✓ Token refreshed')
    
    # Top viral psychology channels worldwide
    targets = [
        ('Psych2Go',          120, 25),  # primary target — deep dive
        ('TherapyinaNutshell', 60, 10),
        ('Charisma',          60, 10),  # Charisma on Command
        ('TheSchoolofLifeTV', 60, 10),  # The School of Life
        ('PracticalPsychology1', 60, 10),
    ]
    
    for handle, mvids, ttop in targets:
        try:
            research_channel(token, handle, max_videos=mvids, transcribe_top=ttop)
        except Exception as e:
            print(f'  FAILED {handle}: {e}')
            continue
    
    print('\n========== SUMMARY ==========')
    r = S.get(f'{SUPA_URL}/rest/v1/viral_channel_research?select=handle,title,subscriber_count,video_count&order=subscriber_count.desc',
        timeout=20)
    if r.ok:
        for ch in r.json():
            print(f"  {ch['handle']:30s} {ch['title']:35s} {ch['subscriber_count']:>15,} subs / {ch['video_count']:>5} vids")

if __name__ == '__main__':
    run()
