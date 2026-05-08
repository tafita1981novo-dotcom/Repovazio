"""
llm_router.py - Fallback chain for free LLMs (psicologia.doc pipeline)

Tries in order (configurable via prefer_engine kwarg):
1. Groq (Llama 3.3 70B)         - primary, 14.4k req/dia FREE, ~250ms
2. DeepSeek direct (V3.2)       - secondary, creditos iniciais gratis
3. Nvidia Build (DeepSeek V4Pro)- tertiary, FREE ILIMITADO 2026
4. OpenAI gpt-4o-mini           - last resort, paid

All engines speak OpenAI-compatible chat completions API.
"""
import os, json, time, urllib.request, urllib.error


class LLMRouter:
    ENGINES = [
        # 1. DeepSeek V4 Pro via Nvidia Build - DEFAULT 2026, FREE ILIMITADO (1.6T params)
        ("nvidia_deepseek_v4",   "NVIDIA_API_KEY",   "https://integrate.api.nvidia.com/v1",    "deepseek-ai/deepseek-v4-pro"),
        # 2. Groq Llama 3.3 70B - fallback gratis (14.4k req/dia FREE, ~250ms)
        ("groq",                 "GROQ_API_KEY",     "https://api.groq.com/openai/v1",         "llama-3.3-70b-versatile"),
        # 3. OpenAI gpt-4o-mini - ULTIMO RECURSO (paid, raramente alcancado)
        ("openai_mini",          "OPENAI_API_KEY",   "https://api.openai.com/v1",              "gpt-4o-mini"),
    ]

    def __init__(self, prefer_engine=None):
        self.prefer_engine = prefer_engine
        self.last_engine_used = None

    def chat(self, messages, max_tokens=2000, temperature=0.7, response_format=None, timeout=45):
        engines = list(self.ENGINES)
        if self.prefer_engine:
            engines.sort(key=lambda e: 0 if e[0] == self.prefer_engine else 1)
        last_err = None
        for name, env_key, base_url, model in engines:
            api_key = os.environ.get(env_key)
            if not api_key:
                continue
            try:
                t0 = time.time()
                payload = {"model": model, "messages": messages,
                           "max_tokens": max_tokens, "temperature": temperature}
                if response_format:
                    payload["response_format"] = response_format
                req = urllib.request.Request(
                    f"{base_url}/chat/completions",
                    data=json.dumps(payload).encode(),
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "User-Agent": "psicologia-doc-llm-router/1.0",
                    }, method="POST",
                )
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    data = json.loads(r.read().decode())
                content = data["choices"][0]["message"]["content"]
                latency = int((time.time() - t0) * 1000)
                self.last_engine_used = name
                print(f"[llm_router] OK {name} ({model}) {latency}ms")
                return {"content": content, "engine_used": name, "model_used": model,
                        "latency_ms": latency, "tokens": data.get("usage", {})}
            except urllib.error.HTTPError as e:
                err_body = e.read().decode() if hasattr(e, "read") else str(e)
                last_err = f"{name}: HTTP {e.code} {err_body[:200]}"
                print(f"[llm_router] FAIL {name}: HTTP {e.code}, trying next...")
                continue
            except Exception as e:
                last_err = f"{name}: {type(e).__name__}: {str(e)[:200]}"
                print(f"[llm_router] FAIL {name}: {type(e).__name__}, trying next...")
                continue
        raise RuntimeError(f"All LLM engines failed. Last: {last_err}")

    def classify_emotion(self, paragraph):
        prompt = (
            "Classifique este paragrafo em UMA das 6 categorias emocionais "
            "(retorne APENAS a categoria):\n"
            "INTRO_CALMO, ALERTA_TENSO, EMPATIA_ACOLHEDOR, "
            "ANALITICO_FRIO, ESPERANCA_CRESCENTE, CTA_URGENTE\n\n"
            f"Paragrafo: {paragraph}\n\nCategoria:"
        )
        result = self.chat([{"role": "user", "content": prompt}],
                           max_tokens=20, temperature=0.3)
        cat = result["content"].strip().upper()
        valid = {"INTRO_CALMO", "ALERTA_TENSO", "EMPATIA_ACOLHEDOR",
                 "ANALITICO_FRIO", "ESPERANCA_CRESCENTE", "CTA_URGENTE"}
        for v in valid:
            if v in cat:
                return v
        return "EMPATIA_ACOLHEDOR"

    def classify_emotions_batch(self, paragraphs):
        numbered = "\n\n".join(f"P{i}: {p}" for i, p in enumerate(paragraphs))
        prompt = (
            "Para CADA paragrafo abaixo, classifique a emocao dominante em UMA "
            "destas 6 categorias:\n"
            "INTRO_CALMO, ALERTA_TENSO, EMPATIA_ACOLHEDOR, "
            "ANALITICO_FRIO, ESPERANCA_CRESCENTE, CTA_URGENTE\n\n"
            f"Paragrafos:\n{numbered}\n\n"
            'Responda em JSON valido neste formato exato:\n'
            '{"emotions": ["INTRO_CALMO", "EMPATIA_ACOLHEDOR", ...]}\n'
            "O array deve ter exatamente o mesmo numero de itens que paragrafos."
        )
        result = self.chat([{"role": "user", "content": prompt}],
                           max_tokens=500, temperature=0.3,
                           response_format={"type": "json_object"})
        try:
            parsed = json.loads(result["content"])
            emotions = parsed.get("emotions", [])
            if len(emotions) == len(paragraphs):
                return emotions, result["engine_used"]
        except Exception:
            pass
        return ([self.classify_emotion(p) for p in paragraphs],
                result.get("engine_used", "unknown"))


# Compatibility alias for legacy scripts (tts_edge.py, produce_video.py)
def classify_emotions_groq(paragraphs):
    """Legacy alias - now uses fallback chain instead of Groq-only."""
    return LLMRouter().classify_emotions_batch(paragraphs)


if __name__ == "__main__":
    router = LLMRouter()
    test = router.chat(
        [{"role": "user", "content": "Diga apenas OK em portugues"}],
        max_tokens=10)
    print(f"Engine: {test['engine_used']}, Latency: {test['latency_ms']}ms")
    print(f"Content: {test['content']}")
