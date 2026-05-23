#!/usr/bin/env python3
"""
master_producao.py — Orquestra todos os sistemas de produção
Roda: podcast + canal EN + newsletter + bluesky + quantum brain
Custo: $0 (tudo grátis)
"""
import os, subprocess, sys, time

def run_step(nome, cmd, env_extra=None):
    env = {**os.environ, **(env_extra or {})}
    print(f"\n[{nome}]")
    result = subprocess.run(
        [sys.executable] + cmd if isinstance(cmd, list) else cmd,
        env=env, capture_output=False, text=True, timeout=300
    )
    ok = result.returncode == 0
    print(f"  {'✅' if ok else '❌'} {nome}")
    return ok

def main():
    import datetime
    hora_br = (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).strftime("%H:%M")
    print(f"=== MASTER PRODUCAO — {hora_br} BRT ===")
    
    steps = [
        ("Quantum Brain Expand",   ["scripts/brain_mass_expander.py"]),
        ("Podcast Ep1",            ["scripts/podcast_pipeline.py"],   {"EPISODE_NUM": "1"}),
        ("Canal EN Ep1",           ["scripts/en_channel_engine.py"],  {"TEMA_IDX": "0"}),
        ("Newsletter",             ["scripts/newsletter_engine.py"]),
        ("Bluesky Bot",            ["scripts/bluesky_psicologia_bot.py"], {"N_POSTS": "3"}),
        ("Trilhas Guide",          ["scripts/trilhas_spotify_uploader.py"]),
        ("KDP Converter",          ["scripts/kdp_converter.py"]),
    ]
    
    ok_count = 0
    for step in steps:
        nome = step[0]
        cmd  = step[1]
        env  = step[2] if len(step) > 2 else {}
        if run_step(nome, cmd, env):
            ok_count += 1
        time.sleep(2)
    
    print(f"\n=== RESULTADO: {ok_count}/{len(steps)} sistemas OK ===")

if __name__ == "__main__":
    main()
