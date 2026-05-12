import { createClient } from "@supabase/supabase-js";
export const dynamic = "force-dynamic";
export const revalidate = 0;

// ============================================================
// SOCIAL MANAGER V1 — Controle total das redes sociais
// Memória eterna + Auto-melhoria evolutiva
// IDENTIDADE: Psicologia (NUNCA psicóloga até jan/2027)
// ============================================================

const IDENTIDADE = {
  nome: "Daniela Coelho | Psicologia",
  area: "Psicologia",
  tagline: "A ciência que explica quem você é",
  canal: "@psidanielacoelho",
  canal_id: "UCyCkIpsVgME9yCj_oXJFheA",
  nunca_usar: ["psicóloga","psicologa","CRP","clínica","diagnóstico"],
  data_titulo_psicologa: "2027-01-01",
  nota_legal: "Usar apenas PSICOLOGIA como área até 01/01/2027"
};

const PERFIS = {
  youtube: {
    nome: "Daniela Coelho | Psicologia",
    descricao: `Psicologia para entender quem você é. 🧠

Toda semana: documentários sobre apego, narcisismo, trauma, ansiedade e relacionamentos — com base científica, em formato que você vai querer assistir até o final.

📌 Séries exclusivas:
• Apego Ansioso — Por que você tem medo de perder?
• Mentes Narcisistas — O que está por trás da manipulação
• Trauma Invisível — O que ninguém te contou sobre o passado
• Ansiedade e Pânico — A ciência por trás do medo
• Burnout — Por que você está esgotado e não sabe por quê

🔔 Ative o sininho para não perder nenhum episódio.

psicologia.doc | @psidanielacoelho`,
    palavras_chave: ["psicologia","saude mental","apego ansioso","narcisismo","trauma","ansiedade","burnout","relacionamentos","dependencia emocional","autoconhecimento","neurociencia","bem estar","inteligencia emocional","psicologia comportamental","saude mental brasil"],
    categoria: "Education",
    pais: "BR",
    idioma: "pt-BR",
    links: [
      { title: "📱 Instagram", url: "https://instagram.com/psidanielacoelho" },
      { title: "🎵 TikTok", url: "https://tiktok.com/@psidanielacoelho" }
    ]
  },
  instagram: {
    nome: "Daniela Coelho | Psicologia",
    bio_principal: "🧠 psicologia.doc\nA ciência que explica quem você é\n📌 Apego · Trauma · Narcisismo · Ansiedade\n🎬 Novos vídeos toda semana\n👇 YouTube no link",
    bio_v2:        "🧠 Psicologia para entender quem você é\nApego · Trauma · Narcisismo · Burnout\n🎬 @psidanielacoelho · psicologia.doc\n📌 Novos vídeos toda semana",
    link:          "https://youtube.com/@psidanielacoelho",
    categoria:     "Educação",
    tipo_conta:    "Criadora de conteúdo",
    destaques_stories: ["Apego 🧠","Narcisismo 😈","Trauma 💔","Ansiedade 😰","Séries 🎬","Sobre ✨"],
    hashtags_fixas: ["#psicologia","#saudemental","#apego","#narcisismo","#trauma","#ansiedade","#burnout","#autoconhecimento","#psicologiaonline","#saudementalimporta"]
  },
  tiktok: {
    nome:  "Daniela Coelho | Psicologia",
    bio:   "🧠 psicologia.doc | A ciência que explica quem você é 🇧🇷 | Apego · Narcisismo · Trauma | @psidanielacoelho",
    bio_v2:"Psicologia para entender quem você é 🧠 | Apego Narcisismo Trauma Ansiedade | YouTube no link",
    link:  "https://youtube.com/@psidanielacoelho",
    hashtags: ["#psicologia","#saudemental","#psicologiatiktok","#apego","#narcisismo","#trauma","#ansiedade","#autoconhecimento","#relacionamentos","#burnout"]
  },
  pinterest: {
    nome:   "psicologia.doc | Daniela Coelho",
    bio:    "Psicologia para entender quem você é. 🧠 Conteúdo baseado em ciência sobre apego, narcisismo, trauma, ansiedade e relacionamentos. Novos vídeos toda semana no YouTube.",
    site:   "https://youtube.com/@psidanielacoelho",
    boards: ["Psicologia 🧠","Saúde Mental","Apego e Relacionamentos 💔","Narcisismo 😈","Trauma","Ansiedade 😰","Burnout","Neurociência 🔬","Autoconhecimento ✨"]
  },
  whatsapp: {
    nome_grupo:   "psicologia.doc | Comunidade 🧠",
    descricao:    "🧠 psicologia.doc\nComunidade de psicologia com Daniela Coelho\n\nRegras:\n✅ Respeito mútuo\n✅ Compartilhe aprendizados\n✅ Perguntas sobre os vídeos\n❌ Sem spam ou divulgação\n\n🎬 youtube.com/@psidanielacoelho",
    imagem_grupo: "ψ psicologia.doc — fundo roxo profundo #06060F com símbolo ψ em #7C3AED",
    tipo:         "comunidade_educacional",
    limite:       1024,
    status:       "aguardando_WHATSAPP_TOKEN"
  }
};

const AUTO_MELHORIA_SCHEDULE = [
  { freq: "daily",   acao: "backup_memoria", desc: "Salvar estado atual do sistema" },
  { freq: "weekly",  acao: "analisar_ctr",   desc: "Identificar thumbnails com maior CTR" },
  { freq: "weekly",  acao: "otimizar_bios",  desc: "Verificar palavras-chave e atualizar bios" },
  { freq: "monthly", acao: "evoluir_prompts",desc: "Melhorar prompts baseado em performance" },
  { freq: "monthly", acao: "revisar_series", desc: "Adaptar séries baseado em engajamento" },
];

export async function GET(request) {
  const sbUrl = process.env.SUPABASE_URL || "https://tpjvalzwkqwttvmszvie.supabase.co";
  const sbKey = process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";
  const sb = createClient(sbUrl, sbKey);
  const url = new URL(request.url);
  const action = url.searchParams.get("action") || "status";

  try {
    if (action === "identidade") {
      return Response.json({ identidade: IDENTIDADE, nota: "NUNCA usar psicóloga até 01/01/2027" });
    }

    if (action === "perfis") {
      return Response.json({ perfis: PERFIS, identidade: IDENTIDADE });
    }

    if (action === "youtube") {
      return Response.json({
        textos: PERFIS.youtube,
        identidade: IDENTIDADE,
        instrucoes_manuais: [
          "1. Acessar studio.youtube.com com psidanielacoelho1982@gmail.com",
          "2. Personalização do canal → Informações básicas",
          "3. Colar o nome: " + PERFIS.youtube.nome,
          "4. Colar a descrição completa acima",
          "5. Adicionar palavras-chave: " + PERFIS.youtube.palavras_chave.join(", "),
          "6. Em Branding: fazer upload do banner (repovazio.vercel.app/brand/youtube-banner.html)",
          "7. Salvar todas as alterações"
        ],
        banner_url: "https://repovazio.vercel.app/brand/youtube-banner.html",
        thumb_generator: "https://repovazio.vercel.app/brand/thumb-generator.html"
      });
    }

    if (action === "instagram") {
      return Response.json({
        textos: PERFIS.instagram,
        instrucoes_manuais: [
          "1. Instagram > Perfil > Editar perfil",
          "2. Nome: " + PERFIS.instagram.nome,
          "3. Bio: copiar bio_principal acima",
          "4. Link: " + PERFIS.instagram.link,
          "5. Categoria: Educação",
          "6. Criar destaques: " + PERFIS.instagram.destaques_stories.join(", ")
        ]
      });
    }

    if (action === "tiktok") {
      return Response.json({
        textos: PERFIS.tiktok,
        instrucoes_manuais: [
          "1. TikTok > Perfil > Editar perfil",
          "2. Nome: " + PERFIS.tiktok.nome,
          "3. Bio: copiar bio acima",
          "4. Link: " + PERFIS.tiktok.link
        ]
      });
    }

    if (action === "auto_melhorar") {
      // Executar ciclo de auto-melhoria
      const { data: tarefas } = await sb.from("cerebro_tarefas")
        .select("*").eq("status", "pendente").order("prioridade", { ascending: false }).limit(5);
      
      const executadas = [];
      for (const tarefa of (tarefas || [])) {
        let resultado = null;
        
        if (tarefa.tipo === "auto_evolucao_prompts") {
          const { data: pub } = await sb.from("content_pipeline")
            .select("title,score,metadata").eq("status", "published").order("id", { ascending: false }).limit(10);
          const topTitulos = (pub || []).filter(v => (v.score || 0) >= 90).map(v => v.title);
          resultado = { analise: "prompts_analisados", top_titulos: topTitulos.slice(0, 5) };
        }
        
        if (tarefa.tipo === "backup_memoria_eterna") {
          const { data: stats } = await sb.from("content_pipeline").select("status").limit(2000);
          const cnt = {};
          (stats || []).forEach(r => { cnt[r.status] = (cnt[r.status] || 0) + 1; });
          resultado = { backup: "ok", pipeline_stats: cnt, timestamp: new Date().toISOString() };
        }
        
        if (resultado) {
          await sb.from("cerebro_tarefas").update({ status: "executado", resultado, executado_em: new Date().toISOString() }).eq("id", tarefa.id);
          executadas.push({ tarefa: tarefa.tipo, resultado });
        }
      }
      
      // Registrar evolução
      await sb.from("cerebro_evolucao").insert({ versao: "v14", tipo: "auto_melhoria", descricao: `Auto-melhoria: ${executadas.length} tarefas executadas`, mudancas: { executadas } });
      
      return Response.json({ ok: true, executadas: executadas.length, detalhes: executadas });
    }

    // Status completo
    const { data: profiles } = await sb.from("social_profiles").select("platform,status,last_updated");
    const { data: tarefas_count } = await sb.from("cerebro_tarefas").select("tipo").eq("status", "pendente");
    const { data: evolucoes } = await sb.from("cerebro_evolucao").select("versao,tipo,descricao,criado_em").order("criado_em", { ascending: false }).limit(3);
    
    const pmap = {};
    (profiles || []).forEach(p => { pmap[p.platform] = p.status; });

    return Response.json({
      identidade: IDENTIDADE,
      nota_legal: "NUNCA usar psicóloga, CRP ou títulos não autorizados até 01/01/2027",
      perfis_configurados: PERFIS,
      status_redes: {
        youtube:   { status: pmap.youtube || "nao_configurado",   acao: "Atualizar no YouTube Studio manualmente + configurar YOUTUBE_REFRESH_TOKEN" },
        instagram: { status: pmap.instagram || "nao_configurado", acao: "Atualizar perfil + configurar META_ACCESS_TOKEN" },
        tiktok:    { status: pmap.tiktok || "nao_configurado",    acao: "Atualizar perfil + configurar TIKTOK_ACCESS_TOKEN" },
        pinterest: { status: pmap.pinterest || "nao_configurado", acao: "Atualizar perfil + configurar PINTEREST_ACCESS_TOKEN" },
        whatsapp:  { status: pmap.whatsapp || "nao_configurado",  acao: "Configurar WHATSAPP_TOKEN + WHATSAPP_PHONE_ID" },
      },
      auto_melhoria: {
        tarefas_pendentes: (tarefas_count || []).length,
        schedule: AUTO_MELHORIA_SCHEDULE,
        evolucoes_recentes: (evolucoes || []).slice(0, 3)
      },
      brand_assets: {
        thumb_generator:     "https://repovazio.vercel.app/brand/thumb-generator.html",
        youtube_banner:      "https://repovazio.vercel.app/brand/youtube-banner.html",
        instagram_templates: "https://repovazio.vercel.app/brand/instagram-templates.html"
      },
      instrucoes_rapidas: {
        youtube:   "studio.youtube.com > Personalização > Informações básicas",
        instagram: "App IG > Perfil > Editar perfil",
        tiktok:    "App TT > Perfil > Editar perfil",
        pinterest: "pinterest.com > Perfil > Editar",
        whatsapp:  "Aguardando WHATSAPP_TOKEN"
      }
    });

  } catch (e) {
    return Response.json({ error: e.message }, { status: 500 });
  }
}
