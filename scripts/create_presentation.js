const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "Carlos Candeira";
pres.title = "Ford Intelligence OS — Desafio Ford x Universidade 2026";

// ─── Ford Brand Palette ──────────────────────────────────
const C = {
  blue:      "003478",
  blueDark:  "00234D",
  blueLight: "1B4F9E",
  accent:    "00A3E0",
  white:     "FFFFFF",
  offWhite:  "F0F4F8",
  gray:      "6B7280",
  grayLight: "E5E7EB",
  dark:      "1E293B",
  success:   "00B74A",
  warning:   "FFA900",
  danger:    "F93154",
};

const makeShadow = () => ({
  type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.12,
});

// ══════════════════════════════════════════════════════════
// SLIDE 1 — Title
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.blueDark };

  // Top accent bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.accent },
  });

  // FORD text
  s.addText("FORD", {
    x: 0.8, y: 1.0, w: 8.4, h: 1.2,
    fontSize: 72, fontFace: "Arial Black", color: C.white,
    bold: true, charSpacing: 8, align: "left", margin: 0,
  });

  // Subtitle
  s.addText("Intelligence OS", {
    x: 0.8, y: 2.0, w: 8.4, h: 0.8,
    fontSize: 36, fontFace: "Calibri", color: C.accent,
    bold: false, align: "left", margin: 0,
  });

  // Divider line
  s.addShape(pres.shapes.LINE, {
    x: 0.8, y: 3.0, w: 3, h: 0,
    line: { color: C.accent, width: 2 },
  });

  // Description
  s.addText("Inteligencia competitiva + Retencao de clientes\npara o mercado automotivo brasileiro", {
    x: 0.8, y: 3.3, w: 8, h: 0.9,
    fontSize: 16, fontFace: "Calibri", color: C.grayLight,
    align: "left", margin: 0,
  });

  // Footer
  s.addText("Desafio Ford x Universidade 2026  |  Carlos Candeira", {
    x: 0.8, y: 4.8, w: 8, h: 0.5,
    fontSize: 12, fontFace: "Calibri", color: C.gray,
    align: "left", margin: 0,
  });
}

// ══════════════════════════════════════════════════════════
// SLIDE 2 — O Problema
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offWhite };

  // Header bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.8, fill: { color: C.blue },
  });
  s.addText("O PROBLEMA", {
    x: 0.8, y: 0.1, w: 8, h: 0.6,
    fontSize: 24, fontFace: "Arial Black", color: C.white,
    bold: true, align: "left", margin: 0,
  });

  // Problem cards — 3 cards side by side
  const cards = [
    { title: "Dados fragmentados", desc: "Especificacoes de concorrentes espalhadas em dezenas de sites, sem padronizacao ou atualizacao automatica" },
    { title: "Churn invisivel", desc: "Clientes Ford com alto risco de abandono nao sao identificados ate que ja tenham migrado para concorrentes" },
    { title: "Retencao generica", desc: "Mensagens de retencao nao usam diferenciais competitivos reais — perdem poder de convencimento" },
  ];

  cards.forEach((card, i) => {
    const cx = 0.5 + i * 3.1;
    // Card bg
    s.addShape(pres.shapes.RECTANGLE, {
      x: cx, y: 1.2, w: 2.85, h: 3.5,
      fill: { color: C.white }, shadow: makeShadow(),
    });
    // Left accent
    s.addShape(pres.shapes.RECTANGLE, {
      x: cx, y: 1.2, w: 0.06, h: 3.5,
      fill: { color: C.danger },
    });
    // Number circle
    s.addShape(pres.shapes.OVAL, {
      x: cx + 0.3, y: 1.5, w: 0.5, h: 0.5,
      fill: { color: C.danger },
    });
    s.addText(String(i + 1), {
      x: cx + 0.3, y: 1.5, w: 0.5, h: 0.5,
      fontSize: 18, fontFace: "Arial", color: C.white,
      bold: true, align: "center", valign: "middle", margin: 0,
    });
    // Title
    s.addText(card.title, {
      x: cx + 0.2, y: 2.2, w: 2.4, h: 0.6,
      fontSize: 15, fontFace: "Calibri", color: C.dark,
      bold: true, align: "left", margin: 0,
    });
    // Description
    s.addText(card.desc, {
      x: cx + 0.2, y: 2.8, w: 2.4, h: 1.7,
      fontSize: 12, fontFace: "Calibri", color: C.gray,
      align: "left", valign: "top", margin: 0,
    });
  });

  // Bottom question
  s.addText("Como transformar dados publicos em vantagem competitiva E retencao ativa?", {
    x: 0.5, y: 5.0, w: 9, h: 0.4,
    fontSize: 13, fontFace: "Calibri", color: C.blue,
    bold: true, italic: true, align: "center", margin: 0,
  });
}

// ══════════════════════════════════════════════════════════
// SLIDE 3 — A Solucao (Architecture Overview)
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.8, fill: { color: C.blue },
  });
  s.addText("A SOLUCAO — ARQUITETURA", {
    x: 0.8, y: 0.1, w: 8, h: 0.6,
    fontSize: 24, fontFace: "Arial Black", color: C.white,
    bold: true, align: "left", margin: 0,
  });

  // Module 1 box
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.2, w: 4.0, h: 3.6,
    fill: { color: C.white }, shadow: makeShadow(),
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.2, w: 4.0, h: 0.06,
    fill: { color: C.accent },
  });
  s.addText("MODULO 1", {
    x: 0.7, y: 1.4, w: 3.5, h: 0.4,
    fontSize: 11, fontFace: "Calibri", color: C.accent,
    bold: true, margin: 0,
  });
  s.addText("Radar Competitivo", {
    x: 0.7, y: 1.75, w: 3.5, h: 0.45,
    fontSize: 18, fontFace: "Calibri", color: C.dark,
    bold: true, margin: 0,
  });
  s.addText([
    { text: "Scraper dinamico 2 etapas", options: { bullet: true, breakLine: true } },
    { text: "Descobre modelos atuais automaticamente", options: { bullet: true, breakLine: true } },
    { text: "Banco EAV (PostgreSQL)", options: { bullet: true, breakLine: true } },
    { text: "Consulta em linguagem natural (NL-to-SQL)", options: { bullet: true, breakLine: true } },
    { text: "Ficha tecnica comparativa", options: { bullet: true } },
  ], {
    x: 0.7, y: 2.3, w: 3.5, h: 2.3,
    fontSize: 12, fontFace: "Calibri", color: C.gray,
    paraSpaceAfter: 6, margin: 0,
  });

  // Module 2 box
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.5, y: 1.2, w: 4.0, h: 3.6,
    fill: { color: C.white }, shadow: makeShadow(),
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.5, y: 1.2, w: 4.0, h: 0.06,
    fill: { color: C.success },
  });
  s.addText("MODULO 2", {
    x: 5.7, y: 1.4, w: 3.5, h: 0.4,
    fontSize: 11, fontFace: "Calibri", color: C.success,
    bold: true, margin: 0,
  });
  s.addText("Motor de Retencao", {
    x: 5.7, y: 1.75, w: 3.5, h: 0.45,
    fontSize: 18, fontFace: "Calibri", color: C.dark,
    bold: true, margin: 0,
  });
  s.addText([
    { text: "Churn scoring 0-100 (5 regras)", options: { bullet: true, breakLine: true } },
    { text: "97 testes automatizados", options: { bullet: true, breakLine: true } },
    { text: "Conformidade LGPD", options: { bullet: true, breakLine: true } },
    { text: "Templates WhatsApp personalizados", options: { bullet: true, breakLine: true } },
    { text: "Reviewer pass (guardrail anti-alucinacao)", options: { bullet: true } },
  ], {
    x: 5.7, y: 2.3, w: 3.5, h: 2.3,
    fontSize: 12, fontFace: "Calibri", color: C.gray,
    paraSpaceAfter: 6, margin: 0,
  });

  // Bridge arrow
  s.addShape(pres.shapes.RECTANGLE, {
    x: 3.0, y: 5.0, w: 4.0, h: 0.5,
    fill: { color: C.blue },
  });
  s.addText("A PONTE  —  JOIN vehicle_spec + retention_vehicles", {
    x: 3.0, y: 5.0, w: 4.0, h: 0.5,
    fontSize: 10, fontFace: "Calibri", color: C.white,
    bold: true, align: "center", valign: "middle", margin: 0,
  });
}

// ══════════════════════════════════════════════════════════
// SLIDE 4 — Module 1: Scraper Dinamico
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.8, fill: { color: C.accent },
  });
  s.addText("MODULO 1 — SCRAPER DINAMICO", {
    x: 0.8, y: 0.1, w: 8, h: 0.6,
    fontSize: 24, fontFace: "Arial Black", color: C.white,
    bold: true, align: "left", margin: 0,
  });

  // 3 steps flow
  const steps = [
    { num: "ETAPA 1", title: "Discovery", desc: "Acessa catalogo oficial de cada marca e descobre TODOS os modelos atuais via regex" },
    { num: "ETAPA 2", title: "Extraction", desc: "Para cada modelo, extrai specs (potencia, torque, motor, preco...) da pagina do veiculo" },
    { num: "ETAPA 3", title: "Prices", desc: "Coleta precos reais de concessionarias via webmotors.com.br, icarros.com.br e mobiauto.com.br" },
  ];

  steps.forEach((step, i) => {
    const sy = 1.1 + i * 1.35;
    // Step card
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y: sy, w: 9.0, h: 1.15,
      fill: { color: C.white }, shadow: makeShadow(),
    });
    // Number badge
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y: sy, w: 1.4, h: 1.15,
      fill: { color: C.accent },
    });
    s.addText(step.num, {
      x: 0.5, y: sy, w: 1.4, h: 0.5,
      fontSize: 10, fontFace: "Calibri", color: C.white,
      bold: true, align: "center", valign: "bottom", margin: 0,
    });
    s.addText(step.title, {
      x: 0.5, y: sy + 0.45, w: 1.4, h: 0.55,
      fontSize: 16, fontFace: "Calibri", color: C.white,
      bold: true, align: "center", valign: "top", margin: 0,
    });
    // Description
    s.addText(step.desc, {
      x: 2.2, y: sy + 0.1, w: 7.0, h: 0.95,
      fontSize: 14, fontFace: "Calibri", color: C.dark,
      align: "left", valign: "middle", margin: 0,
    });
  });

  // Stats row
  const stats = [
    { val: "8", label: "Marcas cobertas" },
    { val: "27+", label: "Modelos descobertos" },
    { val: "94+", label: "Specs coletadas" },
    { val: "24", label: "Precos concessionaria" },
  ];

  stats.forEach((st, i) => {
    const sx = 0.5 + i * 2.4;
    s.addShape(pres.shapes.RECTANGLE, {
      x: sx, y: 4.6, w: 2.1, h: 0.85,
      fill: { color: C.blue },
    });
    s.addText(st.val, {
      x: sx, y: 4.6, w: 2.1, h: 0.5,
      fontSize: 24, fontFace: "Arial Black", color: C.white,
      bold: true, align: "center", valign: "bottom", margin: 0,
    });
    s.addText(st.label, {
      x: sx, y: 5.1, w: 2.1, h: 0.35,
      fontSize: 10, fontFace: "Calibri", color: C.grayLight,
      align: "center", valign: "top", margin: 0,
    });
  });
}

// ══════════════════════════════════════════════════════════
// SLIDE 5 — Module 1: NL Query + EAV
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.8, fill: { color: C.accent },
  });
  s.addText("MODULO 1 — CONSULTA INTELIGENTE", {
    x: 0.8, y: 0.1, w: 8, h: 0.6,
    fontSize: 24, fontFace: "Arial Black", color: C.white,
    bold: true, align: "left", margin: 0,
  });

  // Left: flow
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.1, w: 4.5, h: 4.0,
    fill: { color: C.white }, shadow: makeShadow(),
  });
  s.addText("Fluxo NL-to-SQL", {
    x: 0.7, y: 1.2, w: 4.0, h: 0.5,
    fontSize: 16, fontFace: "Calibri", color: C.dark,
    bold: true, margin: 0,
  });

  const flowSteps = [
    "Usuario pergunta em portugues",
    "LLM (gpt-5.4-nano) gera SQL",
    "Sanitizador valida (apenas SELECT)",
    "Executa no PostgreSQL (EAV)",
    "Resultado com fonte + data",
  ];
  flowSteps.forEach((txt, i) => {
    const fy = 1.8 + i * 0.6;
    s.addShape(pres.shapes.OVAL, {
      x: 0.8, y: fy + 0.05, w: 0.3, h: 0.3,
      fill: { color: C.accent },
    });
    s.addText(String(i + 1), {
      x: 0.8, y: fy + 0.05, w: 0.3, h: 0.3,
      fontSize: 10, fontFace: "Arial", color: C.white,
      bold: true, align: "center", valign: "middle", margin: 0,
    });
    s.addText(txt, {
      x: 1.25, y: fy, w: 3.5, h: 0.4,
      fontSize: 12, fontFace: "Calibri", color: C.dark,
      align: "left", valign: "middle", margin: 0,
    });
  });

  // Right: EAV explanation
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.3, y: 1.1, w: 4.2, h: 4.0,
    fill: { color: C.white }, shadow: makeShadow(),
  });
  s.addText("Modelo EAV (Entity-Attribute-Value)", {
    x: 5.5, y: 1.2, w: 3.8, h: 0.5,
    fontSize: 14, fontFace: "Calibri", color: C.dark,
    bold: true, margin: 0,
  });
  s.addText("Nao existem colunas potencia, torque, etc.\nCada spec e uma LINHA:", {
    x: 5.5, y: 1.7, w: 3.8, h: 0.7,
    fontSize: 11, fontFace: "Calibri", color: C.gray,
    margin: 0,
  });

  // Mini table
  const tableData = [
    [
      { text: "campo", options: { fill: { color: C.blue }, color: C.white, bold: true, fontSize: 10 } },
      { text: "valor", options: { fill: { color: C.blue }, color: C.white, bold: true, fontSize: 10 } },
      { text: "unidade", options: { fill: { color: C.blue }, color: C.white, bold: true, fontSize: 10 } },
    ],
    [
      { text: "potencia", options: { fontSize: 10 } },
      { text: "397", options: { fontSize: 10 } },
      { text: "cv", options: { fontSize: 10 } },
    ],
    [
      { text: "torque", options: { fontSize: 10 } },
      { text: "59,4", options: { fontSize: 10 } },
      { text: "kgfm", options: { fontSize: 10 } },
    ],
    [
      { text: "preco_sugerido", options: { fontSize: 10 } },
      { text: "449.990", options: { fontSize: 10 } },
      { text: "BRL", options: { fontSize: 10 } },
    ],
  ];
  s.addTable(tableData, {
    x: 5.5, y: 2.5, w: 3.8,
    border: { pt: 0.5, color: C.grayLight },
    colW: [1.5, 1.2, 1.1],
  });

  // Guardrails
  s.addText("Guardrails de seguranca:", {
    x: 5.5, y: 3.7, w: 3.8, h: 0.35,
    fontSize: 12, fontFace: "Calibri", color: C.dark,
    bold: true, margin: 0,
  });
  s.addText([
    { text: "SQL sanitizer (bloqueia DDL/DML)", options: { bullet: true, breakLine: true } },
    { text: "Filtro mercado = 'BR' obrigatorio", options: { bullet: true, breakLine: true } },
    { text: "Rastreabilidade: fonte_url + extraido_em", options: { bullet: true } },
  ], {
    x: 5.5, y: 4.0, w: 3.8, h: 1.0,
    fontSize: 11, fontFace: "Calibri", color: C.gray,
    paraSpaceAfter: 4, margin: 0,
  });
}

// ══════════════════════════════════════════════════════════
// SLIDE 6 — Module 2: Churn Scoring
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.8, fill: { color: C.success },
  });
  s.addText("MODULO 2 — MOTOR DE RETENCAO", {
    x: 0.8, y: 0.1, w: 8, h: 0.6,
    fontSize: 24, fontFace: "Arial Black", color: C.white,
    bold: true, align: "left", margin: 0,
  });

  // Scoring rules — 5 cards
  const rules = [
    { pts: "40", name: "Ultima visita paga", desc: "NULL = max risco. >365 dias = 40pts" },
    { pts: "20", name: "Tipo ultimo servico", desc: "Recall/garantia = 20pts (nunca pagou)" },
    { pts: "15", name: "Idade do veiculo", desc: ">5 anos = 15pts (fora da garantia)" },
    { pts: "15", name: "Frequencia", desc: "0 visitas pagas em 2 anos = 15pts" },
    { pts: "10", name: "Revisao proxima", desc: "Proximo de 10k/20k/40k km = 10pts" },
  ];

  rules.forEach((rule, i) => {
    const ry = 1.1 + i * 0.8;
    // Row bg
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y: ry, w: 9.0, h: 0.65,
      fill: { color: i % 2 === 0 ? C.white : C.offWhite },
    });
    // Points badge
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y: ry, w: 0.8, h: 0.65,
      fill: { color: i === 0 ? C.danger : C.warning },
    });
    s.addText(rule.pts + "pt", {
      x: 0.5, y: ry, w: 0.8, h: 0.65,
      fontSize: 14, fontFace: "Arial", color: C.white,
      bold: true, align: "center", valign: "middle", margin: 0,
    });
    // Name
    s.addText(rule.name, {
      x: 1.5, y: ry, w: 2.5, h: 0.65,
      fontSize: 13, fontFace: "Calibri", color: C.dark,
      bold: true, align: "left", valign: "middle", margin: 0,
    });
    // Description
    s.addText(rule.desc, {
      x: 4.2, y: ry, w: 5.0, h: 0.65,
      fontSize: 12, fontFace: "Calibri", color: C.gray,
      align: "left", valign: "middle", margin: 0,
    });
  });

  // Bottom stats
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 5.2, w: 9.0, h: 0.06,
    fill: { color: C.success },
  });

  const bottomStats = [
    { val: "100", label: "Veiculos na base" },
    { val: "97", label: "Testes automatizados" },
    { val: "LGPD", label: "Conformidade total" },
    { val: ">70", label: "Alto risco threshold" },
  ];
  bottomStats.forEach((bs, i) => {
    const bx = 0.5 + i * 2.35;
    s.addText(bs.val, {
      x: bx, y: 5.35, w: 2.0, h: 0.55,
      fontSize: 22, fontFace: "Arial Black", color: C.success,
      bold: true, align: "center", valign: "bottom", margin: 0,
    });
    // There's not enough vertical space so skip label under value on the slide
  });
}

// ══════════════════════════════════════════════════════════
// SLIDE 7 — A Ponte
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.blueDark };

  s.addText("A PONTE", {
    x: 0.8, y: 0.3, w: 8, h: 0.7,
    fontSize: 32, fontFace: "Arial Black", color: C.white,
    bold: true, margin: 0,
  });
  s.addText("O diferencial — conectando inteligencia a acao", {
    x: 0.8, y: 0.9, w: 8, h: 0.4,
    fontSize: 14, fontFace: "Calibri", color: C.accent,
    margin: 0,
  });

  // Flow: 5 steps horizontal
  const bridgeSteps = [
    { title: "Churn\nScoring", color: C.success },
    { title: "Veiculo\nAlto Risco", color: C.warning },
    { title: "Diferenciais\nCompetitivos", color: C.accent },
    { title: "Template\nLLM", color: C.blueLight },
    { title: "WhatsApp\n(Aprovado)", color: C.blue },
  ];

  bridgeSteps.forEach((bs, i) => {
    const bx = 0.3 + i * 1.95;
    // Card
    s.addShape(pres.shapes.RECTANGLE, {
      x: bx, y: 1.6, w: 1.7, h: 1.3,
      fill: { color: bs.color }, shadow: makeShadow(),
    });
    s.addText(bs.title, {
      x: bx, y: 1.6, w: 1.7, h: 1.3,
      fontSize: 12, fontFace: "Calibri", color: C.white,
      bold: true, align: "center", valign: "middle", margin: 0,
    });
    // Arrow (except last)
    if (i < 4) {
      s.addText(">", {
        x: bx + 1.7, y: 1.9, w: 0.25, h: 0.6,
        fontSize: 20, fontFace: "Arial", color: C.accent,
        bold: true, align: "center", valign: "middle", margin: 0,
      });
    }
  });

  // Guardrail explanation
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 3.3, w: 9.0, h: 1.8,
    fill: { color: "0A1F3D" },
  });
  s.addText("GUARDRAILS (Anti-alucinacao)", {
    x: 0.7, y: 3.4, w: 8.5, h: 0.5,
    fontSize: 15, fontFace: "Calibri", color: C.accent,
    bold: true, margin: 0,
  });
  s.addText([
    { text: "System prompt restritivo — LLM recebe apenas campos reais do veiculo", options: { bullet: true, breakLine: true } },
    { text: "Reviewer pass — compara TODOS os numeros do template vs dados de entrada", options: { bullet: true, breakLine: true } },
    { text: "Aprovacao humana obrigatoria antes de envio", options: { bullet: true, breakLine: true } },
    { text: "Se numero nao bate com input, template e flaggado automaticamente", options: { bullet: true } },
  ], {
    x: 0.7, y: 3.9, w: 8.5, h: 1.1,
    fontSize: 12, fontFace: "Calibri", color: C.grayLight,
    paraSpaceAfter: 4, margin: 0,
  });
}

// ══════════════════════════════════════════════════════════
// SLIDE 8 — Stack Tecnico
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.8, fill: { color: C.blue },
  });
  s.addText("STACK TECNICO", {
    x: 0.8, y: 0.1, w: 8, h: 0.6,
    fontSize: 24, fontFace: "Arial Black", color: C.white,
    bold: true, align: "left", margin: 0,
  });

  // 2x3 grid of tech cards
  const techs = [
    { cat: "Frontend", items: "Streamlit + Plotly\nDashboard interativo" },
    { cat: "Backend", items: "Python 3.9\nPostgreSQL (EAV)" },
    { cat: "IA/LLM", items: "GPT-5.4-nano\nNL-to-SQL + Templates" },
    { cat: "Scraping", items: "Requests + Regex\nPlaywright-stealth (WAF)" },
    { cat: "Testes", items: "pytest (97 testes)\n100% coverage regras" },
    { cat: "Deploy", items: "GitHub + Streamlit Cloud\nCI/CD automatizado" },
  ];

  techs.forEach((tech, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const tx = 0.5 + col * 3.1;
    const ty = 1.1 + row * 2.05;

    s.addShape(pres.shapes.RECTANGLE, {
      x: tx, y: ty, w: 2.85, h: 1.8,
      fill: { color: C.white }, shadow: makeShadow(),
    });
    // Top accent
    s.addShape(pres.shapes.RECTANGLE, {
      x: tx, y: ty, w: 2.85, h: 0.06,
      fill: { color: C.accent },
    });
    s.addText(tech.cat, {
      x: tx + 0.15, y: ty + 0.15, w: 2.55, h: 0.4,
      fontSize: 14, fontFace: "Calibri", color: C.blue,
      bold: true, margin: 0,
    });
    s.addText(tech.items, {
      x: tx + 0.15, y: ty + 0.6, w: 2.55, h: 1.0,
      fontSize: 12, fontFace: "Calibri", color: C.gray,
      margin: 0,
    });
  });
}

// ══════════════════════════════════════════════════════════
// SLIDE 9 — Resultados / Demo
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.8, fill: { color: C.blue },
  });
  s.addText("RESULTADOS & DEMO AO VIVO", {
    x: 0.8, y: 0.1, w: 8, h: 0.6,
    fontSize: 24, fontFace: "Arial Black", color: C.white,
    bold: true, align: "left", margin: 0,
  });

  // Key results in big numbers
  const results = [
    { val: "237", label: "Specs no banco\n(atualizadas ao vivo)", color: C.blue },
    { val: "8", label: "Marcas cobertas\n(VW, Toyota, Ford...)", color: C.accent },
    { val: "97", label: "Testes passando\n(100% green)", color: C.success },
    { val: "<2s", label: "Tempo de resposta\n(NL query end-to-end)", color: C.blueLight },
  ];

  results.forEach((r, i) => {
    const rx = 0.5 + i * 2.4;
    s.addShape(pres.shapes.RECTANGLE, {
      x: rx, y: 1.1, w: 2.1, h: 1.6,
      fill: { color: C.white }, shadow: makeShadow(),
    });
    s.addText(r.val, {
      x: rx, y: 1.2, w: 2.1, h: 0.8,
      fontSize: 36, fontFace: "Arial Black", color: r.color,
      bold: true, align: "center", valign: "bottom", margin: 0,
    });
    s.addText(r.label, {
      x: rx, y: 2.1, w: 2.1, h: 0.55,
      fontSize: 10, fontFace: "Calibri", color: C.gray,
      align: "center", valign: "top", margin: 0,
    });
  });

  // Demo tabs preview
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 3.0, w: 9.0, h: 2.2,
    fill: { color: C.white }, shadow: makeShadow(),
  });
  s.addText("DEMO AO VIVO — 4 ABAS", {
    x: 0.7, y: 3.1, w: 8.5, h: 0.4,
    fontSize: 14, fontFace: "Calibri", color: C.dark,
    bold: true, margin: 0,
  });

  const tabs = [
    { name: "Consulta Inteligente", desc: "Pergunte em portugues, receba specs com fonte verificavel" },
    { name: "Ficha Tecnica", desc: "Compare Ranger vs Hilux vs Amarok lado a lado com graficos" },
    { name: "Retencao & Churn", desc: "Veja scores de risco, filtre por modelo, analise breakdown" },
    { name: "A Ponte", desc: "Gere template WhatsApp com guardrails anti-alucinacao" },
  ];

  tabs.forEach((tab, i) => {
    const ty = 3.55 + i * 0.4;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.7, y: ty, w: 0.15, h: 0.3,
      fill: { color: C.accent },
    });
    s.addText(tab.name, {
      x: 1.0, y: ty, w: 2.5, h: 0.3,
      fontSize: 11, fontFace: "Calibri", color: C.dark,
      bold: true, align: "left", valign: "middle", margin: 0,
    });
    s.addText(tab.desc, {
      x: 3.5, y: ty, w: 5.7, h: 0.3,
      fontSize: 11, fontFace: "Calibri", color: C.gray,
      align: "left", valign: "middle", margin: 0,
    });
  });
}

// ══════════════════════════════════════════════════════════
// SLIDE 10 — Proximos Passos
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.8, fill: { color: C.blue },
  });
  s.addText("PROXIMOS PASSOS", {
    x: 0.8, y: 0.1, w: 8, h: 0.6,
    fontSize: 24, fontFace: "Arial Black", color: C.white,
    bold: true, align: "left", margin: 0,
  });

  // Timeline
  const phases = [
    { phase: "CURTO PRAZO", items: ["Agente monitor de precos (alerta automatico)", "Cobertura de todas as marcas do mercado BR", "Integrar API Ford Developer Portal"], color: C.accent },
    { phase: "MEDIO PRAZO", items: ["ML para churn scoring (substituir regras)", "Integrar WhatsApp Business API real", "Dashboard regional (concessionarias)"], color: C.blueLight },
    { phase: "LONGO PRAZO", items: ["Modelo preditivo de demanda por modelo", "Personalizacao por perfil do cliente (CLV)", "Expansao para mercados LATAM"], color: C.blue },
  ];

  phases.forEach((ph, i) => {
    const px = 0.5 + i * 3.1;
    // Card
    s.addShape(pres.shapes.RECTANGLE, {
      x: px, y: 1.1, w: 2.85, h: 3.8,
      fill: { color: C.white }, shadow: makeShadow(),
    });
    // Phase header
    s.addShape(pres.shapes.RECTANGLE, {
      x: px, y: 1.1, w: 2.85, h: 0.55,
      fill: { color: ph.color },
    });
    s.addText(ph.phase, {
      x: px, y: 1.1, w: 2.85, h: 0.55,
      fontSize: 13, fontFace: "Calibri", color: C.white,
      bold: true, align: "center", valign: "middle", margin: 0,
    });
    // Items
    const itemTexts = ph.items.map((item, j) => ({
      text: item,
      options: { bullet: true, breakLine: j < ph.items.length - 1 },
    }));
    s.addText(itemTexts, {
      x: px + 0.15, y: 1.8, w: 2.55, h: 2.9,
      fontSize: 11, fontFace: "Calibri", color: C.gray,
      paraSpaceAfter: 8, margin: 0,
    });
  });
}

// ══════════════════════════════════════════════════════════
// SLIDE 11 — Thank You / Q&A
// ══════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.blueDark };

  // Top accent
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.accent },
  });

  s.addText("FORD", {
    x: 0.8, y: 1.2, w: 8.4, h: 0.9,
    fontSize: 52, fontFace: "Arial Black", color: C.white,
    bold: true, charSpacing: 6, align: "center", margin: 0,
  });
  s.addText("Intelligence OS", {
    x: 0.8, y: 2.0, w: 8.4, h: 0.6,
    fontSize: 28, fontFace: "Calibri", color: C.accent,
    align: "center", margin: 0,
  });

  s.addShape(pres.shapes.LINE, {
    x: 3.5, y: 2.9, w: 3, h: 0,
    line: { color: C.accent, width: 2 },
  });

  s.addText("Obrigado!", {
    x: 0.8, y: 3.2, w: 8.4, h: 0.6,
    fontSize: 24, fontFace: "Calibri", color: C.grayLight,
    align: "center", margin: 0,
  });

  s.addText("Perguntas?", {
    x: 0.8, y: 3.7, w: 8.4, h: 0.5,
    fontSize: 18, fontFace: "Calibri", color: C.gray,
    align: "center", margin: 0,
  });

  // Contact info
  s.addText("Carlos Candeira  |  github.com/carloscandeira/ford-intelligence-os", {
    x: 0.8, y: 4.8, w: 8.4, h: 0.4,
    fontSize: 12, fontFace: "Calibri", color: C.gray,
    align: "center", margin: 0,
  });
}

// ─── Generate ─────────────────────────────────────────────
const outputPath = process.cwd() + "/Ford_Intelligence_OS_Apresentacao.pptx";
pres.writeFile({ fileName: outputPath }).then(() => {
  console.log("Presentation created: " + outputPath);
}).catch(err => {
  console.error("Error:", err);
});
