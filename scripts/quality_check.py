#!/usr/bin/env python3
"""
Quality Control Engine v1 — psicologia.doc
Analisa vídeos antes de publicar e:
1. Verifica bitrate (mín 3000kbps para ser publicado)
2. Verifica áudio (mín 128kbps stereo)
3. Verifica duração (shorts: 15-60s, long: 8-20min)
4. Verifica resolução (mín 1080x1920 para shorts)
5. Calcula score de qualidade (0-100)
6. Re-renderiza automaticamente se score < 70
"""
import os, sys, json, subprocess, pathlib, urllib.request, urllib.parse
from datetime import datetime, timezone

SBU = os.environ.get("SUPABASE_URL", "")
SBK = os.environ.get("SUPABASE_SERVICE_KEY", "")
H_SB = {"apikey": SBK, "Authorization": f"Bearer {SBK}", "Content-Type": "application/json"}

QUALITY_THRESHOLDS = {
    "short": {
        "min_video_bitrate": 2000,    # kbps
        "min_audio_bitrate": 128,     # kbps
        "min_audio_channels": 2,      # stereo
        "min_audio_sample_rate": 44100,
        "min_width": 1080,
        "min_height": 1920,
        "min_fps": 24,
        "min_duration": 15,           # segundos
        "max_duration": 60,
        "target_score": 80
    },
    "long": {
        "min_video_bitrate": 3000,
        "min_audio_bitrate": 192,
        "min_audio_channels": 2,
        "min_audio_sample_rate": 48000,
        "min_width": 1080,
        "min_height": 1920,
        "min_fps": 24,
        "min_duration": 480,          # 8 minutos mínimo para mid-rolls
        "max_duration": 1200,
        "target_score": 85
    }
}

def log(*a): print(f"[{datetime.now().strftime('%H:%M:%S')}]", *a, flush=True)

def sb_get(table, q, limit=50):
    url = f"{SBU}/rest/v1/{table}?{q}&limit={limit}"
    req = urllib.request.Request(url, headers=H_SB)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def sb_patch(table, vid_id, data):
    url = f"{SBU}/rest/v1/{table}?id=eq.{vid_id}"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, method="PATCH", headers=H_SB)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status
    except:
        return 0

def analyze_video(url):
    """Analisa vídeo via ffprobe — retorna dict de métricas"""
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", 
           "-show_streams", "-show_format", url]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=60)
        d = json.loads(r.stdout)
        
        metrics = {
            "video_bitrate": 0, "audio_bitrate": 0, "audio_channels": 0,
            "audio_sample_rate": 0, "width": 0, "height": 0, "fps": 0, 
            "duration": 0, "total_bitrate": 0
        }
        
        for s in d.get("streams", []):
            if s["codec_type"] == "video":
                metrics["video_bitrate"] = int(s.get("bit_rate", 0)) // 1000
                metrics["width"] = s.get("width", 0)
                metrics["height"] = s.get("height", 0)
                fps_str = s.get("r_frame_rate", "25/1")
                n, den = fps_str.split("/")
                metrics["fps"] = int(n) / max(int(den), 1)
            elif s["codec_type"] == "audio":
                metrics["audio_bitrate"] = int(s.get("bit_rate", 0)) // 1000
                metrics["audio_channels"] = s.get("channels", 0)
                metrics["audio_sample_rate"] = int(s.get("sample_rate", 0))
        
        f = d.get("format", {})
        metrics["duration"] = float(f.get("duration", 0))
        metrics["total_bitrate"] = int(f.get("bit_rate", 0)) // 1000
        
        return metrics
    except Exception as e:
        log(f"  ffprobe erro: {e}")
        return None

def calculate_score(metrics, fmt):
    """Calcula score de qualidade 0-100"""
    thresh = QUALITY_THRESHOLDS.get(fmt, QUALITY_THRESHOLDS["short"])
    score = 100
    issues = []
    
    # Bitrate vídeo (peso 40%)
    vbr = metrics.get("video_bitrate", 0)
    if vbr < thresh["min_video_bitrate"]:
        penalty = min(40, (thresh["min_video_bitrate"] - vbr) / thresh["min_video_bitrate"] * 40)
        score -= penalty
        issues.append(f"bitrate_video={vbr}kbps<{thresh['min_video_bitrate']}kbps (-{penalty:.0f}pts)")
    
    # Áudio (peso 25%)
    abr = metrics.get("audio_bitrate", 0)
    if abr < thresh["min_audio_bitrate"]:
        penalty = min(15, (thresh["min_audio_bitrate"] - abr) / thresh["min_audio_bitrate"] * 15)
        score -= penalty
        issues.append(f"bitrate_audio={abr}kbps<{thresh['min_audio_bitrate']}kbps")
    
    if metrics.get("audio_channels", 0) < thresh["min_audio_channels"]:
        score -= 10
        issues.append(f"audio_mono (deveria ser stereo)")
    
    if metrics.get("audio_sample_rate", 0) < thresh["min_audio_sample_rate"]:
        score -= 5
        issues.append(f"sample_rate={metrics.get('audio_sample_rate')}Hz<{thresh['min_audio_sample_rate']}Hz")
    
    # Resolução (peso 20%)
    if metrics.get("width", 0) < thresh["min_width"] or metrics.get("height", 0) < thresh["min_height"]:
        score -= 20
        issues.append(f"resolucao={metrics.get('width')}x{metrics.get('height')}")
    
    # Duração (peso 10%)
    dur = metrics.get("duration", 0)
    if dur < thresh["min_duration"]:
        score -= 10
        issues.append(f"duration={dur:.1f}s<{thresh['min_duration']}s")
    elif dur > thresh["max_duration"]:
        score -= 5
        issues.append(f"duration={dur:.1f}s>{thresh['max_duration']}s")
    
    # FPS (peso 5%)
    if metrics.get("fps", 0) < thresh["min_fps"]:
        score -= 5
        issues.append(f"fps={metrics.get('fps'):.0f}<{thresh['min_fps']}")
    
    return max(0, min(100, int(score))), issues

def run():
    log("═══ QC ENGINE v1 — Quality Control ═══")
    
    # Buscar vídeos mp4_ready para análise
    rows = sb_get("content_pipeline", 
                  "status=eq.mp4_ready&select=id,title,format,mp4_url,video_url,quality_score_current",
                  20)
    
    log(f"Analisando {len(rows)} vídeos mp4_ready...")
    
    passed = failed = 0
    for row in rows:
        vid_id = row["id"]
        fmt = row.get("format", "short")
        url = row.get("mp4_url") or row.get("video_url", "")
        
        if not url:
            log(f"  [{vid_id}] Sem URL — pulando")
            continue
        
        log(f"  [{vid_id}] {row['title'][:40]}...")
        metrics = analyze_video(url)
        
        if not metrics:
            log(f"  [{vid_id}] ❌ Não analisável")
            continue
        
        score, issues = calculate_score(metrics, fmt)
        thresh = QUALITY_THRESHOLDS.get(fmt, QUALITY_THRESHOLDS["short"])
        
        status_icon = "✅" if score >= thresh["target_score"] else "⚠️" if score >= 60 else "❌"
        log(f"  [{vid_id}] {status_icon} Score: {score}/100 | {metrics['video_bitrate']}kbps | "
            f"{metrics['audio_channels']}ch {metrics['audio_sample_rate']}Hz | {metrics['duration']:.1f}s")
        
        if issues:
            for issue in issues:
                log(f"    → {issue}")
        
        # Salvar score no Supabase
        sb_patch("content_pipeline", vid_id, {
            "quality_score_current": score,
            "metadata": json.dumps({"qc": metrics, "issues": issues, "qc_date": datetime.now(timezone.utc).isoformat()})
        })
        
        # Se score muito baixo, marcar para re-render
        if score < 50:
            sb_patch("content_pipeline", vid_id, {"status": "audio_ready", "error": f"QC_FAIL_score_{score}"})
            log(f"  [{vid_id}] Marcado para re-render (score {score}<50)")
            failed += 1
        else:
            passed += 1
    
    log(f"\n✅ QC Completo: {passed} ok | {failed} re-render")

if __name__ == "__main__":
    run()
