"""
Ford Intelligence OS — Professional PDF Report Generator

Generates branded PDF reports for:
1. Ficha Tecnica Comparativa (vehicle spec comparison)
2. Retencao & Churn (at-risk vehicles report)
"""

import io
from datetime import datetime
from typing import Optional

from fpdf import FPDF


# ─── Ford Brand Constants ─────────────────────────────────────
FORD_BLUE = (0, 52, 120)
FORD_BLUE_DARK = (0, 26, 58)
FORD_ACCENT = (0, 163, 224)
FORD_TEXT = (26, 26, 46)
FORD_TEXT_SEC = (90, 98, 117)
FORD_BORDER = (200, 210, 220)
FORD_SUCCESS = (14, 164, 122)
FORD_WARNING = (229, 150, 10)
FORD_DANGER = (220, 53, 69)
WHITE = (255, 255, 255)
LIGHT_BG = (245, 247, 250)
ROW_ALT = (248, 250, 252)


class FordPDF(FPDF):
    """Custom FPDF with Ford branding."""

    def __init__(self, title="Ford Intelligence OS", subtitle=""):
        super().__init__(orientation="L", unit="mm", format="A4")
        self.report_title = title
        self.report_subtitle = subtitle
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        # Blue header bar
        self.set_fill_color(*FORD_BLUE)
        self.rect(0, 0, self.w, 18, "F")

        # Accent line
        self.set_fill_color(*FORD_ACCENT)
        self.rect(0, 18, self.w, 1, "F")

        # FORD text
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*WHITE)
        self.set_xy(8, 3)
        self.cell(30, 12, "FORD", align="L")

        # Title
        self.set_font("Helvetica", "", 11)
        self.set_xy(30, 3)
        self.cell(100, 12, self.report_title, align="L")

        # Subtitle right-aligned
        if self.report_subtitle:
            self.set_font("Helvetica", "", 8)
            self.set_text_color(180, 200, 220)
            self.set_xy(self.w - 110, 3)
            self.cell(100, 12, self.report_subtitle, align="R")

        # Date
        self.set_font("Helvetica", "", 7)
        self.set_text_color(180, 200, 220)
        self.set_xy(self.w - 50, 10)
        self.cell(40, 5, datetime.now().strftime("Gerado em %d/%m/%Y %H:%M"), align="R")

        self.ln(22)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*FORD_TEXT_SEC)
        self.cell(0, 5, f"Ford Intelligence OS | Desafio Ford x Universidade 2026 | Pagina {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title, color=FORD_BLUE):
        """Add a section title with underline."""
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*color)
        self.cell(0, 8, title, ln=True)
        # Underline
        self.set_fill_color(*color)
        self.rect(self.get_x(), self.get_y(), 40, 0.8, "F")
        self.ln(4)

    def info_badge(self, text, bg_color=FORD_ACCENT, text_color=WHITE):
        """Small badge label."""
        self.set_font("Helvetica", "B", 7)
        self.set_fill_color(*bg_color)
        self.set_text_color(*text_color)
        w = self.get_string_width(text) + 8
        self.cell(w, 5, text, fill=True, align="C")
        self.set_text_color(*FORD_TEXT)
        self.cell(3, 5, "")

    def stat_box(self, label, value, x, y, w=40, h=18, color=FORD_BLUE):
        """Metric box with label and value."""
        # Background
        self.set_fill_color(*WHITE)
        self.set_draw_color(*FORD_BORDER)
        self.rect(x, y, w, h, "DF")
        # Top accent
        self.set_fill_color(*color)
        self.rect(x, y, w, 1.2, "F")
        # Value
        self.set_xy(x, y + 2)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*color)
        self.cell(w, 8, str(value), align="C")
        # Label
        self.set_xy(x, y + 10)
        self.set_font("Helvetica", "", 6.5)
        self.set_text_color(*FORD_TEXT_SEC)
        self.cell(w, 5, label, align="C")
        self.set_text_color(*FORD_TEXT)


# ══════════════════════════════════════════════════════════════
# FICHA TECNICA COMPARATIVA PDF
# ══════════════════════════════════════════════════════════════

FIELD_LABELS = {
    "potencia": "Potencia (cv)", "torque": "Torque (kgfm)", "motor": "Motor",
    "transmissao": "Transmissao", "tracao": "Tracao", "capacidade_carga": "Cap. Carga (kg)",
    "entre_eixos": "Entre-eixos (mm)", "comprimento": "Comprimento (mm)",
    "tanque": "Tanque (L)", "preco_sugerido": "Preco (R$)",
    "preco_concessionaria": "Preco Concessionaria", "autonomia_eletrica": "Autonomia (km)",
}

FIELD_ORDER = [
    "preco_sugerido", "potencia", "torque", "motor", "transmissao",
    "tracao", "capacidade_carga", "tanque", "entre_eixos", "comprimento",
    "autonomia_eletrica",
]

NUMERIC_FIELDS = {
    "potencia": "higher", "torque": "higher", "capacidade_carga": "higher",
    "entre_eixos": "higher", "comprimento": "higher", "tanque": "higher",
    "preco_sugerido": "lower",
}


def _format_value_pdf(valor, unidade):
    if not valor or valor == "N/D":
        return "—"
    if unidade == "BRL":
        try:
            return f"R$ {int(valor):,}".replace(",", ".")
        except ValueError:
            return valor
    if unidade:
        return f"{valor} {unidade}"
    return valor


def _to_float_pdf(valor):
    try:
        s = str(valor).replace(",", ".")
        return float(s.replace(".", "", s.count(".") - 1))
    except Exception:
        return None


def generate_specs_pdf(selected_specs, selected_vehicles):
    """
    Generate a Ficha Tecnica Comparativa PDF.

    Args:
        selected_specs: dict of {(marca, modelo, versao): {campo: (valor, unidade)}}
        selected_vehicles: list of (marca, modelo, versao) tuples
    Returns:
        bytes: PDF file content
    """
    vehicle_names = [f"{m} {mod} {v}" for m, mod, v in selected_vehicles]
    n_vehicles = len(vehicle_names)

    pdf = FordPDF(
        title="Ficha Tecnica Comparativa",
        subtitle=f"{n_vehicles} veiculos comparados",
    )
    pdf.alias_nb_pages()
    pdf.add_page()

    # ─── Vehicle badges ───────────────────────────────────────
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*FORD_TEXT)
    pdf.cell(0, 6, "Veiculos selecionados:", ln=True)
    pdf.ln(1)

    for name in vehicle_names:
        is_ford = "Ford" in name
        pdf.info_badge(name, bg_color=FORD_BLUE if is_ford else (150, 160, 175))
    pdf.ln(8)

    # ─── Stats row ────────────────────────────────────────────
    # Count wins per vehicle
    all_campos = set()
    for vspecs in selected_specs.values():
        all_campos.update(vspecs.keys())
    ordered = [c for c in FIELD_ORDER if c in all_campos] + [c for c in all_campos if c not in FIELD_ORDER]

    wins = {}
    for campo in ordered:
        if campo not in NUMERIC_FIELDS:
            continue
        numeric_vals = {}
        for (marca, modelo, versao), vspecs in selected_specs.items():
            col = f"{marca} {modelo} {versao}"
            if campo in vspecs:
                fval = _to_float_pdf(vspecs[campo][0])
                if fval is not None:
                    numeric_vals[col] = fval
        if numeric_vals:
            direction = NUMERIC_FIELDS[campo]
            best = max(numeric_vals, key=numeric_vals.get) if direction == "higher" else min(numeric_vals, key=numeric_vals.get)
            wins[best] = wins.get(best, 0) + 1

    start_x = pdf.get_x()
    start_y = pdf.get_y()
    box_w = min(50, (pdf.w - 20) / max(n_vehicles, 1))

    for i, name in enumerate(vehicle_names):
        w = wins.get(name, 0)
        color = FORD_BLUE if "Ford" in name else FORD_TEXT_SEC
        pdf.stat_box(name[:25], f"{w} vitoria{'s' if w != 1 else ''}", start_x + i * (box_w + 4), start_y, box_w, 18, color)

    pdf.ln(24)

    # ─── Comparison Table ─────────────────────────────────────
    pdf.section_title("Especificacoes Tecnicas")

    # Column widths
    label_w = 38
    remaining = pdf.w - 20 - label_w
    col_w = remaining / n_vehicles

    # Table header
    pdf.set_fill_color(*FORD_BLUE)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.cell(label_w, 7, "Especificacao", border=1, fill=True, align="C")
    for name in vehicle_names:
        short = name.replace("Volkswagen", "VW")
        pdf.cell(col_w, 7, short[:28], border=1, fill=True, align="C")
    pdf.ln()

    # Table rows
    pdf.set_text_color(*FORD_TEXT)
    row_idx = 0
    for campo in ordered:
        label = FIELD_LABELS.get(campo, campo)

        # Determine best value
        numeric_vals = {}
        for (marca, modelo, versao), vspecs in selected_specs.items():
            col = f"{marca} {modelo} {versao}"
            if campo in vspecs and campo in NUMERIC_FIELDS:
                fval = _to_float_pdf(vspecs[campo][0])
                if fval is not None:
                    numeric_vals[col] = fval

        best_col = ""
        if numeric_vals and campo in NUMERIC_FIELDS:
            direction = NUMERIC_FIELDS[campo]
            best_col = max(numeric_vals, key=numeric_vals.get) if direction == "higher" else min(numeric_vals, key=numeric_vals.get)

        # Row background
        if row_idx % 2 == 0:
            pdf.set_fill_color(*WHITE)
        else:
            pdf.set_fill_color(*ROW_ALT)

        # Label cell
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*FORD_TEXT)
        pdf.cell(label_w, 6.5, label, border="LTB", fill=True)

        # Value cells
        for name, key in zip(vehicle_names, selected_vehicles):
            vspecs = selected_specs.get(key, {})
            if campo in vspecs:
                valor, unidade = vspecs[campo]
                display = _format_value_pdf(valor, unidade)
            else:
                display = "—"

            is_best = (name == best_col and display != "—")
            is_ford_col = "Ford" in name

            if is_best:
                pdf.set_font("Helvetica", "B", 7)
                pdf.set_text_color(*FORD_SUCCESS)
                display = display + " *"
            elif is_ford_col:
                pdf.set_font("Helvetica", "", 7)
                pdf.set_text_color(*FORD_BLUE)
            else:
                pdf.set_font("Helvetica", "", 7)
                pdf.set_text_color(*FORD_TEXT)

            border = "RTB" if name == vehicle_names[-1] else "TB"
            pdf.cell(col_w, 6.5, display[:35], border=border, fill=True, align="C")

        pdf.ln()
        row_idx += 1

    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(*FORD_TEXT_SEC)
    pdf.cell(0, 4, "* Melhor valor na categoria. Dados extraidos de sites oficiais (.com.br) e carrosnaweb.com.br.", ln=True)

    # ─── Sources ──────────────────────────────────────────────
    pdf.ln(4)
    pdf.section_title("Fontes", FORD_TEXT_SEC)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(*FORD_TEXT_SEC)
    pdf.cell(0, 4, "VW: vw.com.br | Toyota: toyota.com.br | Mitsubishi: mitsubishimotors.com.br | Ford: carrosnaweb.com.br", ln=True)
    pdf.cell(0, 4, "ford.com.br bloqueia scraping automatizado (Cloudflare WAF). Em producao: Ford Developer Portal API.", ln=True)

    # Output
    return pdf.output()


# ══════════════════════════════════════════════════════════════
# RETENCAO & CHURN PDF
# ══════════════════════════════════════════════════════════════

def generate_retention_pdf(results, vehicles, vehicle_map):
    """
    Generate a Retencao & Churn report PDF.

    Args:
        results: list of ScoreResult objects (sorted by score desc)
        vehicles: list of VehicleData objects
        vehicle_map: dict {vehicle_id: VehicleData}
    Returns:
        bytes: PDF file content
    """
    high_risk = [r for r in results if r.is_high_risk]
    contact_now = [r for r in results if r.contact_this_week]
    avg_score = sum(r.score for r in results) / len(results) if results else 0

    pdf = FordPDF(
        title="Relatorio de Retencao & Churn",
        subtitle=f"{len(results)} veiculos analisados",
    )
    pdf.alias_nb_pages()
    pdf.add_page()

    # ─── Summary Stats ────────────────────────────────────────
    pdf.section_title("Resumo Executivo")

    start_x = pdf.get_x()
    start_y = pdf.get_y()

    pdf.stat_box("Total Frota", len(results), start_x, start_y, 55, 20, FORD_BLUE)
    pdf.stat_box("Alto Risco (>70)", len(high_risk), start_x + 59, start_y, 55, 20, FORD_WARNING)
    pdf.stat_box("Contatar Urgente (>85)", len(contact_now), start_x + 118, start_y, 55, 20, FORD_DANGER)
    pdf.stat_box("Score Medio", f"{avg_score:.0f}/100", start_x + 177, start_y, 55, 20, FORD_ACCENT)

    pdf.ln(28)

    # ─── Risk distribution ────────────────────────────────────
    ranges = {"Baixo (0-40)": 0, "Moderado (41-70)": 0, "Alto (71-85)": 0, "Critico (86-100)": 0}
    for r in results:
        if r.score <= 40:
            ranges["Baixo (0-40)"] += 1
        elif r.score <= 70:
            ranges["Moderado (41-70)"] += 1
        elif r.score <= 85:
            ranges["Alto (71-85)"] += 1
        else:
            ranges["Critico (86-100)"] += 1

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*FORD_TEXT)
    pdf.cell(0, 5, "Distribuicao de risco:", ln=True)
    pdf.ln(2)

    range_colors = [FORD_SUCCESS, FORD_ACCENT, FORD_WARNING, FORD_DANGER]
    bar_max_w = 120
    max_val = max(ranges.values()) if ranges.values() else 1

    for (label, count), color in zip(ranges.items(), range_colors):
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*FORD_TEXT)
        pdf.cell(35, 5, label, align="R")
        pdf.cell(2, 5, "")

        bar_w = max(2, (count / max_val) * bar_max_w)
        pdf.set_fill_color(*color)
        pdf.cell(bar_w, 5, "", fill=True)
        pdf.cell(3, 5, "")

        pdf.set_font("Helvetica", "B", 7)
        pdf.cell(15, 5, str(count))
        pdf.ln()

    pdf.ln(6)

    # ─── Vehicles Table ───────────────────────────────────────
    # Only show high risk (>70) in the report
    high_risk_results = sorted(
        [r for r in results if r.score >= 70],
        key=lambda r: r.score, reverse=True,
    )

    pdf.section_title(f"Veiculos em Risco ({len(high_risk_results)} com score > 70)", FORD_DANGER)

    # Table header
    col_widths = [12, 22, 28, 14, 18, 12, 28, 16, 25, 82]
    headers = ["Risco", "ID", "Modelo", "Ano", "KM", "Score", "Ult. Visita", "Visitas 2a", "Connected", "Acao Sugerida"]

    pdf.set_x(10)  # reset to left margin before drawing table
    pdf.set_fill_color(*FORD_BLUE)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 6.5)
    for w, h in zip(col_widths, headers):
        pdf.cell(w, 6, h, border=1, fill=True, align="C")
    pdf.ln()

    # Table rows
    for idx, r in enumerate(high_risk_results[:30]):  # Limit to 30
        v = vehicle_map.get(r.vehicle_id)
        if not v:
            continue

        # Row background
        pdf.set_fill_color(*(WHITE if idx % 2 == 0 else ROW_ALT))

        # Risk indicator
        if r.score > 85:
            risk = "CRITICO"
            risk_color = FORD_DANGER
        elif r.score > 70:
            risk = "ALTO"
            risk_color = FORD_WARNING
        else:
            risk = "MOD"
            risk_color = FORD_ACCENT

        # Risk badge
        pdf.set_font("Helvetica", "B", 5.5)
        pdf.set_text_color(*risk_color)
        pdf.cell(col_widths[0], 5.5, risk, border="LTB", fill=True, align="C")

        # Regular cells
        pdf.set_font("Helvetica", "", 6.5)
        pdf.set_text_color(*FORD_TEXT)

        cells = [
            r.vehicle_id,
            v.modelo,
            str(v.ano_fabricacao or "N/D"),
            f"{v.km_estimado:,}" if v.km_estimado else "N/D",
        ]
        for i, val in enumerate(cells):
            pdf.cell(col_widths[i + 1], 5.5, val, border="TB", fill=True, align="C")

        # Score (colored)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*risk_color)
        pdf.cell(col_widths[5], 5.5, str(r.score), border="TB", fill=True, align="C")

        # More cells
        pdf.set_font("Helvetica", "", 6.5)
        pdf.set_text_color(*FORD_TEXT)

        visita = str(v.ultima_visita_paga) if v.ultima_visita_paga else "NUNCA"
        pdf.cell(col_widths[6], 5.5, visita, border="TB", fill=True, align="C")

        pdf.cell(col_widths[7], 5.5, str(v.qtd_visitas_pagas_2_anos), border="TB", fill=True, align="C")

        connected = "Sim" if v.connected_vehicle_available else "—"
        if v.connected_vehicle_available and v.sinal_falha_ativo:
            connected = "FALHA ATIVA"
            pdf.set_text_color(*FORD_DANGER)
            pdf.set_font("Helvetica", "B", 5.5)
        pdf.cell(col_widths[8], 5.5, connected, border="TB", fill=True, align="C")

        # Action suggestion
        pdf.set_font("Helvetica", "I", 6)
        pdf.set_text_color(*FORD_BLUE)
        if r.contact_this_week:
            action = "CONTATAR ESTA SEMANA — agendar revisao preventiva"
        elif r.is_high_risk:
            action = "Campanha de retencao — template WhatsApp personalizado"
        else:
            action = "Monitorar"
        pdf.cell(col_widths[9], 5.5, action, border="RTB", fill=True)

        pdf.ln()

    # ─── Methodology ──────────────────────────────────────────
    pdf.ln(6)
    pdf.section_title("Metodologia de Scoring", FORD_TEXT_SEC)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(*FORD_TEXT_SEC)

    rules = [
        ("Ultima visita paga", "40pts", "NULL ou >365 dias = risco maximo"),
        ("Tipo ultimo servico", "20pts", "Recall ou garantia = nunca pagou = risco"),
        ("Idade do veiculo", "15pts", ">5 anos = fora da garantia"),
        ("Frequencia", "15pts", "0 visitas pagas em 2 anos = sem vinculo"),
        ("Revisao proxima", "10pts", "Proximo de milestone 10k/20k/40k km"),
    ]

    for name, pts, desc in rules:
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*FORD_TEXT)
        pdf.cell(35, 4.5, name)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*FORD_ACCENT)
        pdf.cell(12, 4.5, pts)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*FORD_TEXT_SEC)
        pdf.cell(0, 4.5, desc, ln=True)

    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 6.5)
    pdf.cell(0, 4, "Filtro LGPD aplicado — apenas veiculos com consentimento ativo. Scoring v1: regras ponderadas (sem ML).", ln=True)

    return pdf.output()
