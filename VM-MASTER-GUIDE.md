# PSIDOC VM MASTER — Guia de Conexão

## Após VM criar, seu IP estará em:
- Supabase ia_cache → cache_key = `oracle_vm_ip`
- Supabase ia_cache → cache_key = `vm_master_config` (JSON completo)

---

## ENDPOINTS DISPONÍVEIS

### Health Check
GET http://{IP}/health
→ {"status":"ok","vm":"psidoc-oracle-arm"}

---

### LLM LOCAL — Ollama (100% gratuito, sem API key)

**Chat com Llama 3.1 8B:**
POST http://{IP}:11434/api/generate
Body: {"model":"llama3.1:8b","prompt":"Sua pergunta","stream":false}

**OpenAI-compatible (para apps que usam OpenAI SDK):**
POST http://{IP}:11434/v1/chat/completions
Headers: Authorization: Bearer ollama
Body: {"model":"llama3.1:8b","messages":[{"role":"user","content":"Sua pergunta"}]}

**Listar modelos:**
GET http://{IP}:11434/api/tags

---

### API GATEWAY (porta 8080)

**Chat local via gateway:**
POST http://{IP}:8080/chat/local
Body: {"model":"llama3.1:8b","prompt":"Sua pergunta"}

**Chat Groq (Llama 70B gratuito):**
POST http://{IP}:8080/chat/groq
Body: {"messages":[{"role":"user","content":"Sua pergunta"}]}

**Listar modelos:**
GET http://{IP}:8080/models

---

## COMO APONTAR SEUS APPS PARA ESTA VM

### iPhone App (Swift)
```swift
let baseURL = "http://SEU_IP:8080"
// Chat local
URLSession.shared.dataTask(with: URL(string: "\(baseURL)/chat/local")!)
```

### Python / IA Agent
```python
import requests
IP = "SEU_IP"
# LLM local
r = requests.post(f"http://{IP}:11434/api/generate",
    json={"model":"llama3.1:8b","prompt":"Olá","stream":False})
print(r.json()["response"])
```

### OpenAI SDK (drop-in replacement)
```python
from openai import OpenAI
client = OpenAI(base_url="http://SEU_IP:11434/v1", api_key="ollama")
response = client.chat.completions.create(
    model="llama3.1:8b",
    messages=[{"role":"user","content":"Olá"}]
)
```

### JavaScript / Node.js
```javascript
const res = await fetch('http://SEU_IP:8080/chat/local', {
  method: 'POST',
  headers: {'Content-Type':'application/json'},
  body: JSON.stringify({model:'llama3.1:8b', prompt:'Olá'})
})
const data = await res.json()
```

### Supabase Edge Function
```typescript
const resp = await fetch('http://SEU_IP:8080/chat/local', {
  method: 'POST',
  body: JSON.stringify({prompt: userMessage})
})
```

---

## MODELOS DISPONÍVEIS

| Modelo | Uso | Velocidade | Qualidade |
|--------|-----|-----------|-----------|
| llama3.1:8b | Geral, código | Rápido | ★★★★ |
| mistral:7b | Texto, análise | Rápido | ★★★★ |
| Llama 3.1 70B via Groq | Alta qualidade | Via API | ★★★★★ |
| Gemini via API | Multimodal | Via API | ★★★★★ |

---

## SERVIÇOS RODANDO

| Serviço | Porta | Status |
|---------|-------|--------|
| Ollama LLM | 11434 | Auto-start |
| API Gateway | 8080 | Auto-start |
| Nginx proxy | 80 | Auto-start |
| Stream YouTube 24/7 | - | Auto-start |
| Fail2ban | - | Auto-start |

---

## SSH ACESSO
```bash
ssh ubuntu@SEU_IP
# Logs da API:
sudo journalctl -u psidoc-api -f
# Logs do Ollama:
sudo journalctl -u ollama -f
# Modelos instalados:
ollama list
```

---

## SEGURANÇA
- Firewall UFW ativo (só portas necessárias abertas)
- Fail2ban ativo (bloqueia brute force SSH)
- .env em /opt/psidoc/.env (chmod 600)
- Spending limit $0 na Oracle (nunca cobra)
