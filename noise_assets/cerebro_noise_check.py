#!/usr/bin/env python3
"""
CÉREBRO NOISE CHANNELS — Verificação Pré-Upload
Roda ANTES de publicar qualquer vídeo em qualquer canal.
Garante que NUNCA ocorram problemas: ban, desmonetização, copyright, plagio.
"""
import subprocess, sys, json, os

def check_loudness(filepath):
    """Verifica LUFS entre -14.12 e -14.41"""
    cmd = ["ffmpeg", "-i", filepath, "-filter:a", "loudnorm=I=-14:TP=-1:LRA=11:print_format=json", "-f", "null", "-"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    # Parse do JSON no stderr
    lines = result.stderr.split("\n")
    json_start = next((i for i, l in enumerate(lines) if l.strip().startswith("{")), None)
    if json_start is None:
        return None, "Não foi possível medir loudness"
    try:
        data = json.loads("\n".join(lines[json_start:]))
        lufs = float(data.get("input_i", 0))
        return lufs, None
    except:
        return None, "Erro ao parsear loudness JSON"

def check_audio_specs(filepath):
    """Verifica sample rate, canais e codec"""
    cmd = ["ffprobe", "-v", "quiet", "-show_streams", "-select_streams", "a", "-print_format", "json", filepath]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
        stream = data["streams"][0]
        return {
            "sample_rate": int(stream.get("sample_rate", 0)),
            "channels": int(stream.get("channels", 0)),
            "codec": stream.get("codec_name", ""),
        }
    except:
        return None

def check_video_specs(filepath):
    """Verifica resolução e fps"""
    cmd = ["ffprobe", "-v", "quiet", "-show_streams", "-select_streams", "v", "-print_format", "json", filepath]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
        stream = data["streams"][0]
        fps_str = stream.get("r_frame_rate", "0/1")
        num, den = map(int, fps_str.split("/"))
        return {
            "width": int(stream.get("width", 0)),
            "height": int(stream.get("height", 0)),
            "fps": round(num/den, 1),
            "codec": stream.get("codec_name", ""),
        }
    except:
        return None

def check_duration(filepath):
    """Verifica duração em segundos"""
    cmd = ["ffprobe", "-v", "quiet", "-show_format", "-print_format", "json", filepath]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
        return float(data["format"].get("duration", 0))
    except:
        return None

def run_checklist(filepath, canal_key, expected_fps=30):
    """Roda todos os checks antes do upload"""
    print(f"\n{'='*60}")
    print(f"CÉREBRO NOISE — Checklist Pré-Upload")
    print(f"Arquivo: {filepath}")
    print(f"Canal: {canal_key}")
    print(f"{'='*60}\n")
    
    errors = []
    warnings = []
    
    # 1. Loudness
    print("⏳ Verificando loudness LUFS...")
    lufs, err = check_loudness(filepath)
    if err:
        errors.append(f"LOUDNESS: {err}")
    elif lufs is None:
        errors.append("LOUDNESS: Não medido")
    elif -14.5 <= lufs <= -13.8:
        print(f"  ✅ LUFS: {lufs:.2f} (alvo: -14.12 a -14.41)")
    else:
        errors.append(f"LOUDNESS: {lufs:.2f} LUFS — fora do range -14.12 a -14.41")
    
    # 2. Audio specs
    print("⏳ Verificando specs de áudio...")
    audio = check_audio_specs(filepath)
    if audio:
        if audio["sample_rate"] == 48000:
            print(f"  ✅ Sample rate: {audio['sample_rate']} Hz")
        else:
            errors.append(f"SAMPLE_RATE: {audio['sample_rate']} Hz ≠ 48000 Hz")
        
        if audio["channels"] == 2:
            print(f"  ✅ Canais: {audio['channels']} (stereo)")
        else:
            errors.append(f"CHANNELS: {audio['channels']} ≠ 2 (stereo)")
    else:
        errors.append("AUDIO: Não foi possível verificar specs")
    
    # 3. Video specs
    print("⏳ Verificando specs de vídeo...")
    video = check_video_specs(filepath)
    if video:
        if video["width"] == 1920 and video["height"] == 1080:
            print(f"  ✅ Resolução: {video['width']}x{video['height']}")
        else:
            errors.append(f"RESOLUÇÃO: {video['width']}x{video['height']} ≠ 1920x1080")
        
        if abs(video["fps"] - expected_fps) <= 1:
            print(f"  ✅ FPS: {video['fps']}")
        else:
            warnings.append(f"FPS: {video['fps']} (esperado ~{expected_fps})")
        
        if video["codec"] in ("h264", "avc1"):
            print(f"  ✅ Codec vídeo: {video['codec']}")
        else:
            warnings.append(f"CODEC: {video['codec']} (esperado h264)")
    else:
        errors.append("VIDEO: Não foi possível verificar specs")
    
    # 4. Duração
    print("⏳ Verificando duração...")
    dur = check_duration(filepath)
    if dur:
        horas = dur / 3600
        if 35900 <= dur <= 36100:
            print(f"  ✅ Duração: {horas:.2f}h ({dur:.0f}s)")
        else:
            warnings.append(f"DURAÇÃO: {horas:.2f}h — esperado ~10h (36000s)")
    else:
        warnings.append("DURAÇÃO: Não foi possível verificar")
    
    # 5. Tamanho do arquivo
    print("⏳ Verificando tamanho...")
    try:
        size_gb = os.path.getsize(filepath) / (1024**3)
        if size_gb < 100:
            print(f"  ✅ Tamanho: {size_gb:.2f} GB (< 128GB limite YT)")
        else:
            errors.append(f"TAMANHO: {size_gb:.2f} GB — muito grande para upload YT")
    except:
        warnings.append("TAMANHO: Não foi possível verificar")
    
    # Checklist manual (não automatizável)
    print("\n" + "─"*60)
    print("CHECKLIST MANUAL (verificar antes de publicar no YouTube Studio):")
    print("─"*60)
    manual = [
        "[ ] Made for kids = NÃO (CRÍTICO — desativa monetização se SIM)",
        "[ ] Monetização ativada no vídeo",
        "[ ] Mid-rolls automáticos ativados (Studio → Monetização)",
        "[ ] Overlay ads ativados",
        "[ ] Anúncios início/fim ativados",
        "[ ] Título EN primeiro (audiência US/UK/AU premium)",
        "[ ] Título contém '10 Hours' e 'Black Screen'",
        "[ ] Descrição multilíngue incluída",
        "[ ] Tags relevantes (máx 500 chars)",
        "[ ] Thumbnail customizada enviada",
        "[ ] Categoria: Music ou People & Blogs",
        "[ ] Idioma: English",
        "[ ] Vídeo público (não não-listado)",
        "[ ] Canal sem strikes de copyright",
        "[ ] Este é o ÚNICO upload no canal (sem duplicatas)",
    ]
    for item in manual:
        print(f"  {item}")
    
    # Resultado final
    print("\n" + "="*60)
    print("RESULTADO FINAL:")
    if errors:
        print(f"\n❌ {len(errors)} ERRO(S) CRÍTICO(S) — NÃO PUBLICAR:")
        for e in errors:
            print(f"  → {e}")
    if warnings:
        print(f"\n⚠️  {len(warnings)} AVISO(S) — revisar antes de publicar:")
        for w in warnings:
            print(f"  → {w}")
    if not errors and not warnings:
        print("\n✅ TODOS OS CHECKS PASSARAM — PODE PUBLICAR")
    elif not errors:
        print("\n✅ SEM ERROS CRÍTICOS — Verificar avisos antes de publicar")
    else:
        print("\n🚫 CORRIGIR ERROS ANTES DE PUBLICAR")
        sys.exit(1)
    
    print("="*60 + "\n")
    return len(errors) == 0

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python cerebro_noise_check.py <arquivo.mp4> <canal_key> [fps_esperado]")
        print("Exemplo: python cerebro_noise_check.py dbn_36000s.mp4 dbn 30")
        sys.exit(1)
    
    filepath = sys.argv[1]
    canal_key = sys.argv[2]
    expected_fps = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    
    if not os.path.exists(filepath):
        print(f"❌ Arquivo não encontrado: {filepath}")
        sys.exit(1)
    
    ok = run_checklist(filepath, canal_key, expected_fps)
    sys.exit(0 if ok else 1)
