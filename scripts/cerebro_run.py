#!/usr/bin/env python3
"""Cerebro Autonomo — processa fila autonomous_queue do Supabase"""
import os, json, time, requests
from datetime import datetime, timezone

SUPA_URL = os.environ.get('SUPABASE_URL', '')
SUPA_KEY = os.environ.get('SUPABASE_KEY', '') or os.environ.get('SUPABASE_SERVICE_KEY', '')

if not SUPA_URL or not SUPA_KEY:
    print("ERRO: SUPABASE_URL e SUPABASE_SERVICE_KEY obrigatorios")
    exit(1)

HEADERS = {
    'apikey': SUPA_KEY,
    'Authorization': f'Bearer {SUPA_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
}

def get(table, params=''):
    r = requests.get(f'{SUPA_URL}/rest/v1/{table}?{params}', headers=HEADERS)
    return r.json() if r.ok else []

def patch(table, match, data):
    p = '&'.join([f'{k}=eq.{v}' for k,v in match.items()])
    return requests.patch(f'{SUPA_URL}/rest/v1/{table}?{p}', headers=HEADERS, json=data).ok

def post(table, data):
    return requests.post(f'{SUPA_URL}/rest/v1/{table}', headers=HEADERS, json=data).ok

def log(tarefa, canal, acao, resultado, detalhe=None):
    post('autonomous_log', {
        'tarefa': tarefa, 'canal_slug': canal,
        'acao_executada': acao, 'resultado': resultado,
        'detalhe': detalhe or {},
        'data_hora': datetime.now(timezone.utc).isoformat()
    })

print(f"CEREBRO AUTONOMO v100 — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
print(f"Supabase: {SUPA_URL[:40]}...")

tarefas = get('autonomous_queue', 'status=eq.pendente&order=prioridade.asc,criado_em.asc&limit=5')
print(f"Tarefas pendentes: {len(tarefas)}")

if not tarefas:
    print("Fila vazia — sistema saudavel")
    exit(0)

GH_TOKEN = os.environ.get('GH_TOKEN', '')
REPO = 'tafita1981novo-dotcom/Repovazio'

for t in tarefas:
    tid, tipo, canal = t['id'], t['tarefa'], t.get('canal_slug','')
    payload = t.get('payload') or {}
    if isinstance(payload, str):
        try: payload = json.loads(payload)
        except: payload = {}

    print(f"\n[{tid}] {tipo} | {canal}")
    patch('autonomous_queue', {'id': tid}, {
        'status': 'executando',
        'iniciado_em': datetime.now(timezone.utc).isoformat(),
        'tentativas': (t.get('tentativas') or 0) + 1
    })

    try:
        resultado = 'ok'

        if tipo == 'render_short' and t.get('script_id'):
            sid = t['script_id']
            r = requests.post(
                f'https://api.github.com/repos/{REPO}/actions/workflows/render-short-58s.yml/dispatches',
                headers={'Authorization': f'token {GH_TOKEN}', 'Accept': 'application/vnd.github.v3+json'},
                json={'ref': 'main', 'inputs': {'script_id': str(sid)}}
            )
            resultado = f'dispatched_script_{sid}' if r.ok else f'err_{r.status_code}'
            log(tipo, canal, resultado, 'sucesso' if r.ok else 'falha')

        elif tipo == 'render_long' and t.get('script_id'):
            sid = t['script_id']
            r = requests.post(
                f'https://api.github.com/repos/{REPO}/actions/workflows/render-long-bank.yml/dispatches',
                headers={'Authorization': f'token {GH_TOKEN}', 'Accept': 'application/vnd.github.v3+json'},
                json={'ref': 'main', 'inputs': {'script_id': str(sid)}}
            )
            resultado = f'dispatched_long_{sid}' if r.ok else f'err_{r.status_code}'
            log(tipo, canal, resultado, 'sucesso' if r.ok else 'falha')

        elif tipo in ('setup_affiliate_clickbank','setup_hotmart_affiliate',
                      'create_youtube_channel_en','ativar_mid_rolls_noise','post_reddit'):
            instrucoes = {
                'setup_affiliate_clickbank': {'url':'https://www.clickbank.com','acao':'Criar conta -> Marketplace -> hoplinks: bbrainwave adhdfocus tinnitus911 sleepwell brainsong -> descriptions 5 canais noise'},
                'setup_hotmart_affiliate': {'url':'https://app.hotmart.com/affiliates','acao':'Solicitar afiliacao: Protocolo Anti-Ansiedade + Saindo da Codependencia'},
                'create_youtube_channel_en': {'url':'https://youtube.com/create_channel','acao':'Criar @MindBehindTheGame com Gmail novo -> YOUTUBE_RT_EN no Supabase'},
                'ativar_mid_rolls_noise': {'url':'https://studio.youtube.com','acao':'Editar cada video noise -> Monetizacao -> Ad breaks 900s (15min)','video_ids':payload.get('video_ids',[])},
                'post_reddit': {'url':'https://reddit.com','acao':'Post educacional sem link direto. Bio = canal YT'}
            }.get(tipo, {})
            log(tipo, canal, f'instrucoes_{tipo}', 'pendente_manual', instrucoes)
            resultado = 'instrucoes_salvas'

        else:
            resultado = f'tipo_nao_mapeado_{tipo}'

        patch('autonomous_queue', {'id': tid}, {
            'status': 'concluido',
            'resultado': json.dumps({'r': resultado}),
            'concluido_em': datetime.now(timezone.utc).isoformat()
        })
        print(f"  OK: {resultado}")

    except Exception as e:
        err = str(e)[:200]
        tent = (t.get('tentativas') or 0) + 1
        patch('autonomous_queue', {'id': tid}, {
            'status': 'erro' if tent >= 3 else 'pendente',
            'erro': err,
            'concluido_em': datetime.now(timezone.utc).isoformat()
        })
        log(tipo, canal, 'excecao', 'falha', {'error': err})
        print(f"  ERRO: {err[:80]}")

print(f"\nCiclo completo. Proximo em 30min.")
