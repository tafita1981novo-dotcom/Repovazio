#!/usr/bin/env node
/**
 * OBSIDIAN VAULT MCP SERVER
 * Filesystem-first: lê/escreve vault local sincronizado com GitHub
 * Protocolo: MCP SSE (StreamableHTTP)
 * Uso de tokens Claude: ~50-200 tokens por query (vs 2000-10000 do Notion)
 */

const { Server } = require("@modelcontextprotocol/sdk/server/index.js");
const { SSEServerTransport } = require("@modelcontextprotocol/sdk/server/sse.js");
const { CallToolRequestSchema, ListToolsRequestSchema } = require("@modelcontextprotocol/sdk/types.js");
const http = require("http");
const fs = require("fs");
const path = require("path");
const matter = require("gray-matter");
const { glob } = require("glob");

const VAULT_PATH = process.env.VAULT_PATH || "/vault";
const PORT = parseInt(process.env.MCP_PORT || "8766");

// ── UTILITÁRIOS ──────────────────────────────────────────────────────────────

function resolvePath(notePath) {
  const clean = notePath.replace(/^\/+/, "").replace(/\.\./g, "");
  if (!clean.endsWith(".md")) return path.join(VAULT_PATH, clean + ".md");
  return path.join(VAULT_PATH, clean);
}

function readNote(notePath) {
  const full = resolvePath(notePath);
  if (!fs.existsSync(full)) return null;
  const raw = fs.readFileSync(full, "utf8");
  const { data: frontmatter, content } = matter(raw);
  return { path: notePath, frontmatter, content, raw, size: raw.length };
}

function writeNote(notePath, content, frontmatter = {}) {
  const full = resolvePath(notePath);
  fs.mkdirSync(path.dirname(full), { recursive: true });
  const hasFrontmatter = Object.keys(frontmatter).length > 0;
  const raw = hasFrontmatter
    ? matter.stringify(content, { ...frontmatter, updated: new Date().toISOString() })
    : content;
  fs.writeFileSync(full, raw, "utf8");
  return { path: notePath, size: raw.length };
}

function searchNotes(query, maxResults = 10) {
  const files = fs.readdirSync(VAULT_PATH, { recursive: true })
    .filter(f => f.endsWith(".md"))
    .map(f => path.join(VAULT_PATH, f));
  
  const results = [];
  const q = query.toLowerCase();
  
  for (const file of files) {
    try {
      const raw = fs.readFileSync(file, "utf8");
      if (raw.toLowerCase().includes(q)) {
        const relPath = path.relative(VAULT_PATH, file);
        // Extrair só o trecho relevante (~200 chars) — economiza tokens
        const idx = raw.toLowerCase().indexOf(q);
        const snippet = raw.substring(Math.max(0, idx - 80), Math.min(raw.length, idx + 120));
        results.push({ path: relPath, snippet: snippet.trim() });
        if (results.length >= maxResults) break;
      }
    } catch {}
  }
  return results;
}

function listNotes(dirPath = "") {
  const base = path.join(VAULT_PATH, dirPath);
  if (!fs.existsSync(base)) return [];
  const files = fs.readdirSync(base, { recursive: false });
  return files.map(f => ({
    name: f,
    type: fs.statSync(path.join(base, f)).isDirectory() ? "dir" : "file",
    path: dirPath ? `${dirPath}/${f}` : f,
  }));
}

function patchSection(notePath, sectionHeading, newContent) {
  const note = readNote(notePath);
  if (!note) return null;
  // Substitui apenas a seção especificada — NÃO reescreve arquivo inteiro
  const heading = `## ${sectionHeading}`;
  const lines = note.content.split("\n");
  let startIdx = -1, endIdx = lines.length;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim() === heading) startIdx = i;
    else if (startIdx >= 0 && i > startIdx && lines[i].startsWith("## ")) {
      endIdx = i; break;
    }
  }
  if (startIdx < 0) {
    // Seção não existe, adicionar ao final
    note.content += `\n\n${heading}\n${newContent}`;
  } else {
    lines.splice(startIdx + 1, endIdx - startIdx - 1, newContent);
    note.content = lines.join("\n");
  }
  return writeNote(notePath, note.content, note.frontmatter);
}

function appendToNote(notePath, content) {
  const note = readNote(notePath);
  const existing = note ? note.content : "";
  const ts = new Date().toISOString().substring(0, 19).replace("T", " ");
  return writeNote(notePath, existing + `\n\n<!-- ${ts} -->\n${content}`);
}

function getSection(notePath, sectionHeading) {
  const note = readNote(notePath);
  if (!note) return null;
  const heading = `## ${sectionHeading}`;
  const lines = note.content.split("\n");
  let startIdx = -1, endIdx = lines.length;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim() === heading) startIdx = i;
    else if (startIdx >= 0 && i > startIdx && lines[i].startsWith("## ")) {
      endIdx = i; break;
    }
  }
  if (startIdx < 0) return null;
  return lines.slice(startIdx, endIdx).join("\n");
}

// ── MCP SERVER SETUP ─────────────────────────────────────────────────────────

const server = new Server(
  { name: "obsidian-vault-mcp", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "vault_read",
      description: "Lê uma nota do vault. Retorna apenas ~200 chars de contexto por default para economizar tokens.",
      inputSchema: {
        type: "object",
        properties: {
          path: { type: "string", description: "Caminho da nota (ex: channels/CH01, rules/anti-inauthentic)" },
          section: { type: "string", description: "Opcional: ler só uma seção ## específica (economiza 90% de tokens)" },
          full: { type: "boolean", description: "Se true, retorna nota inteira. Default: false (só frontmatter + preview)" }
        },
        required: ["path"]
      }
    },
    {
      name: "vault_write",
      description: "Cria ou substitui uma nota no vault.",
      inputSchema: {
        type: "object",
        properties: {
          path: { type: "string" },
          content: { type: "string" },
          frontmatter: { type: "object", description: "Metadados YAML opcionais" }
        },
        required: ["path", "content"]
      }
    },
    {
      name: "vault_patch_section",
      description: "Atualiza APENAS uma seção ## de uma nota — NÃO reescreve o arquivo inteiro. Economiza tokens.",
      inputSchema: {
        type: "object",
        properties: {
          path: { type: "string" },
          section: { type: "string", description: "Nome da seção SEM ##" },
          content: { type: "string", description: "Novo conteúdo da seção" }
        },
        required: ["path", "section", "content"]
      }
    },
    {
      name: "vault_append",
      description: "Adiciona conteúdo ao final de uma nota sem sobrescrever.",
      inputSchema: {
        type: "object",
        properties: {
          path: { type: "string" },
          content: { type: "string" }
        },
        required: ["path", "content"]
      }
    },
    {
      name: "vault_search",
      description: "Busca full-text no vault. Retorna trechos relevantes (não arquivos inteiros).",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string" },
          max_results: { type: "number", default: 10 }
        },
        required: ["query"]
      }
    },
    {
      name: "vault_list",
      description: "Lista arquivos/pastas do vault.",
      inputSchema: {
        type: "object",
        properties: {
          dir: { type: "string", description: "Diretório a listar (vazio = root)" }
        }
      }
    }
  ]
}));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { name, arguments: args } = req.params;
  
  try {
    if (name === "vault_read") {
      const note = readNote(args.path);
      if (!note) return { content: [{ type: "text", text: `Nota não encontrada: ${args.path}` }] };
      
      if (args.section) {
        const section = getSection(args.path, args.section);
        if (!section) return { content: [{ type: "text", text: `Seção '${args.section}' não encontrada em ${args.path}` }] };
        return { content: [{ type: "text", text: section }] };
      }
      
      if (args.full) {
        return { content: [{ type: "text", text: note.raw }] };
      }
      
      // Default: frontmatter + preview (economiza tokens)
      const preview = note.content.substring(0, 400);
      const result = { frontmatter: note.frontmatter, preview, size: note.size };
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }
    
    if (name === "vault_write") {
      const result = writeNote(args.path, args.content, args.frontmatter || {});
      return { content: [{ type: "text", text: `✅ Escrito: ${result.path} (${result.size} bytes)` }] };
    }
    
    if (name === "vault_patch_section") {
      const result = patchSection(args.path, args.section, args.content);
      if (!result) return { content: [{ type: "text", text: `Nota base não encontrada: ${args.path}` }] };
      return { content: [{ type: "text", text: `✅ Seção '${args.section}' atualizada em ${args.path}` }] };
    }
    
    if (name === "vault_append") {
      const result = appendToNote(args.path, args.content);
      return { content: [{ type: "text", text: `✅ Conteúdo adicionado a ${result.path}` }] };
    }
    
    if (name === "vault_search") {
      const results = searchNotes(args.query, args.max_results || 10);
      if (!results.length) return { content: [{ type: "text", text: "Nenhum resultado encontrado." }] };
      return { content: [{ type: "text", text: JSON.stringify(results, null, 2) }] };
    }
    
    if (name === "vault_list") {
      const files = listNotes(args.dir || "");
      return { content: [{ type: "text", text: JSON.stringify(files, null, 2) }] };
    }
    
    return { content: [{ type: "text", text: `Tool desconhecida: ${name}` }] };
  } catch (err) {
    return { content: [{ type: "text", text: `Erro: ${err.message}` }], isError: true };
  }
});

// ── HTTP SERVER (SSE transport) ───────────────────────────────────────────────

const httpServer = http.createServer(async (req, res) => {
  if (req.url === "/health") {
    res.writeHead(200); res.end("ok");
    return;
  }
  
  if (req.url === "/sse") {
    const transport = new SSEServerTransport("/message", res);
    await server.connect(transport);
    return;
  }
  
  if (req.url === "/message" && req.method === "POST") {
    // handled by SSEServerTransport
    return;
  }
  
  res.writeHead(404); res.end("Not found");
});

httpServer.listen(PORT, "0.0.0.0", () => {
  console.log(`🗒️  Obsidian Vault MCP rodando na porta ${PORT}`);
  console.log(`   Vault: ${VAULT_PATH}`);
  console.log(`   Health: http://localhost:${PORT}/health`);
  console.log(`   SSE: http://localhost:${PORT}/sse`);
});

process.on("SIGTERM", () => { httpServer.close(); process.exit(0); });
