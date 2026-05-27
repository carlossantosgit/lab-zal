import io
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import matplotlib
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

matplotlib.use("Agg")
logger = logging.getLogger(__name__)

# ── Palette ──────────────────────────────────────────────────────────────────
DARK   = colors.HexColor("#060b14")
NAVY   = colors.HexColor("#0d1526")
CARD   = colors.HexColor("#111c30")
BORDER = colors.HexColor("#1e2d47")
BLUE   = colors.HexColor("#1e40af")
BLUE_L = colors.HexColor("#3b82f6")
BLUE_X = colors.HexColor("#60a5fa")
RED    = colors.HexColor("#ef4444")
ORANGE = colors.HexColor("#f97316")
YELLOW = colors.HexColor("#eab308")
GREEN  = colors.HexColor("#22c55e")
WHITE  = colors.white
GRAY_1 = colors.HexColor("#f8fafc")
GRAY_2 = colors.HexColor("#f1f5f9")
GRAY_D = colors.HexColor("#334155")
GRAY_M = colors.HexColor("#64748b")
GRAY_T = colors.HexColor("#1e293b")

SEV_COLORS = {
    "critical": RED, "high": ORANGE, "medium": YELLOW, "low": GREEN,
    "4": RED, "5": RED, "3": ORANGE, "2": YELLOW, "1": GREEN, "0": GREEN,
}

SEV_LABELS = {
    "4": "Critical", "5": "Critical", "3": "High",
    "2": "Medium", "1": "Low", "0": "Low",
    "critical": "Critical", "high": "High", "medium": "Medium", "low": "Low",
}

PAGE_W, PAGE_H = letter
MARGIN = 0.7 * inch
CONTENT_W = PAGE_W - 2 * MARGIN


def _sev_color(sev: str) -> colors.Color:
    return SEV_COLORS.get(str(sev).lower(), GRAY_M)


def _sev_label(sev: str) -> str:
    return SEV_LABELS.get(str(sev).lower(), sev.capitalize())


# ── Page decorations ──────────────────────────────────────────────────────────
def _header_footer(canvas, doc):
    canvas.saveState()

    # Top gradient bar (simulated with two rects)
    canvas.setFillColor(DARK)
    canvas.rect(0, PAGE_H - 0.52 * inch, PAGE_W, 0.52 * inch, fill=1, stroke=0)
    # accent line
    canvas.setFillColor(BLUE_L)
    canvas.rect(0, PAGE_H - 0.52 * inch, PAGE_W, 2, fill=1, stroke=0)

    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(MARGIN, PAGE_H - 0.33 * inch,
                      "Carlos-IA  ·  Intelligent Infrastructure Observability")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GRAY_M)
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 0.33 * inch,
                           datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))

    # Bottom bar
    canvas.setFillColor(GRAY_2)
    canvas.rect(0, 0, PAGE_W, 0.42 * inch, fill=1, stroke=0)
    canvas.setFillColor(GRAY_D)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(MARGIN, 0.15 * inch,
                      "CONFIDENTIAL — For authorised internal use only")
    canvas.drawRightString(PAGE_W - MARGIN, 0.15 * inch,
                           f"Page {doc.page}")

    canvas.restoreState()


# ── Helper: section title ─────────────────────────────────────────────────────
def _section(title: str, styles) -> list:
    return [
        Paragraph(title, styles["SectionH"]),
        HRFlowable(width=CONTENT_W, thickness=1, color=BORDER, spaceAfter=8),
    ]


# ── Main class ────────────────────────────────────────────────────────────────
class PDFGenerator:
    def __init__(self, title: str = "IA Analyzer Report"):
        self.title = title
        self.styles = getSampleStyleSheet()
        self._add_styles()

    def _add_styles(self):
        s = self.styles
        common = dict(fontName="Helvetica", textColor=GRAY_D)

        s.add(ParagraphStyle("ReportTitle", fontSize=28, textColor=DARK,
                             fontName="Helvetica-Bold", spaceAfter=4,
                             alignment=TA_CENTER, leading=34))
        s.add(ParagraphStyle("Subtitle", fontSize=10, textColor=GRAY_M,
                             fontName="Helvetica", spaceAfter=18,
                             alignment=TA_CENTER))
        s.add(ParagraphStyle("SectionH", fontSize=12, textColor=BLUE,
                             fontName="Helvetica-Bold", spaceBefore=14,
                             spaceAfter=4))
        s.add(ParagraphStyle("Body", fontSize=9.5, leading=15,
                             spaceAfter=5, **common))
        s.add(ParagraphStyle("Small", fontSize=8.5, leading=13,
                             textColor=GRAY_M, fontName="Helvetica"))
        s.add(ParagraphStyle("TH", fontSize=8, fontName="Helvetica-Bold",
                             textColor=WHITE, alignment=TA_LEFT))
        s.add(ParagraphStyle("TD", fontSize=8.5, leading=12,
                             textColor=GRAY_D, fontName="Helvetica"))
        s.add(ParagraphStyle("TDmono", fontSize=7.5, leading=11,
                             textColor=GRAY_D, fontName="Courier"))

    # ── Public entry ──────────────────────────────────────────────────────────
    def create_report(
        self,
        alerts_data: Dict[str, Any],
        analysis_data: Dict[str, Any],
        output_path: str,
        problems: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                leftMargin=MARGIN, rightMargin=MARGIN,
                topMargin=0.82 * inch, bottomMargin=0.62 * inch,
            )
            story: list = []
            story += self._cover(alerts_data, analysis_data)
            story += self._kpi_section(alerts_data, analysis_data)
            story += self._charts_section(alerts_data)
            story += self._analysis_section(analysis_data)
            story += self._recommendations_section(analysis_data)
            story.append(PageBreak())
            story += self._hosts_table(alerts_data)
            if problems:
                story += self._alerts_table(problems)
            story += self._methodology()

            doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
            logger.info(f"✅ PDF created: {output_path}")
            return True
        except Exception as e:
            logger.error(f"❌ PDF error: {e}", exc_info=True)
            return False

    # ── Cover ────────────────────────────────────────────────────────────────
    def _cover(self, alerts_data, analysis_data):
        risk = analysis_data.get("risk_level", "Medium")
        risk_color = {"Critical": RED, "High": ORANGE,
                      "Medium": YELLOW, "Low": GREEN}.get(risk, YELLOW)
        total = alerts_data.get("total", 0)
        hours = alerts_data.get("hours", 24)
        s = self.styles

        # Risk badge
        badge_inner = Table(
            [[Paragraph(f"⚠  RISK LEVEL: {risk.upper()}",
                        ParagraphStyle("rb", fontSize=11, textColor=WHITE,
                                       fontName="Helvetica-Bold", alignment=TA_CENTER))]],
            colWidths=[2.6 * inch],
        )
        badge_inner.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), risk_color),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        badge_wrap = Table([[badge_inner]], colWidths=[CONTENT_W])
        badge_wrap.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))

        return [
            Spacer(1, 0.3 * inch),
            badge_wrap,
            Spacer(1, 0.18 * inch),
            Paragraph("Alert Intelligence Report", s["ReportTitle"]),
            Paragraph(
                f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}  ·  "
                f"Analysis window: last {hours} hours  ·  {total} alerts",
                s["Subtitle"],
            ),
            HRFlowable(width=CONTENT_W, thickness=2, color=BLUE_L, spaceAfter=18),
        ]

    # ── KPI cards ────────────────────────────────────────────────────────────
    def _kpi_section(self, alerts_data, analysis_data):
        s = self.styles
        story = _section("Executive Summary", s)
        total = alerts_data.get("total", 1) or 1

        kpis = [
            ("Total",    str(alerts_data.get("total",    0)), BLUE_L),
            ("Critical", str(alerts_data.get("critical", 0)), RED),
            ("High",     str(alerts_data.get("high",     0)), ORANGE),
            ("Medium",   str(alerts_data.get("medium",   0)), YELLOW),
            ("Low",      str(alerts_data.get("low",      0)), GREEN),
        ]
        cells = []
        for label, val, color in kpis:
            pct = ""
            if label != "Total":
                n = int(val)
                pct = f"({round(n/total*100)}%)"
            inner = Table(
                [[Paragraph(val, ParagraphStyle("kv", fontSize=20,
                             fontName="Helvetica-Bold", textColor=color,
                             alignment=TA_CENTER))],
                 [Paragraph(label, ParagraphStyle("kl", fontSize=8,
                             fontName="Helvetica", textColor=GRAY_M,
                             alignment=TA_CENTER))],
                 [Paragraph(pct, ParagraphStyle("kp", fontSize=7,
                             fontName="Helvetica", textColor=color,
                             alignment=TA_CENTER))]],
                colWidths=[CONTENT_W / 5 - 4],
            )
            inner.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), GRAY_1),
                ("BOX",           (0, 0), (-1, -1), 0.5, BORDER),
                ("TOPPADDING",    (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LINEBELOW",     (0, 0), (-1, 0), 3, color),
            ]))
            cells.append(inner)

        kpi_row = Table([cells],
                        colWidths=[CONTENT_W / 5] * 5)
        kpi_row.setStyle(TableStyle([
            ("LEFTPADDING",  (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ]))
        story.append(kpi_row)
        story.append(Spacer(1, 0.18 * inch))

        # AI summary box
        summary = analysis_data.get("summary", "")
        if summary:
            box = Table(
                [[Paragraph(f"<b>AI Summary:</b> {summary}", s["Body"])]],
                colWidths=[CONTENT_W],
            )
            box.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
                ("BOX",           (0, 0), (-1, -1), 1, BLUE_L),
                ("TOPPADDING",    (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING",   (0, 0), (-1, -1), 12),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
            ]))
            story.append(box)
            story.append(Spacer(1, 0.12 * inch))

        return story

    # ── Charts ───────────────────────────────────────────────────────────────
    def _charts_section(self, alerts_data):
        s = self.styles
        story = _section("Alert Distribution", s)

        pie  = self._make_pie(alerts_data)
        bar  = self._make_bar(alerts_data.get("top_hosts", {}))
        trend = self._make_severity_bar(alerts_data)

        row = []
        cw  = []
        if pie:
            row.append(Image(pie, width=2.9 * inch, height=2.2 * inch))
            cw.append(3.0 * inch)
        if bar:
            row.append(Image(bar, width=3.4 * inch, height=2.2 * inch))
            cw.append(3.5 * inch)
        if row:
            t = Table([row], colWidths=cw)
            t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                   ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                   ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
            story.append(t)
            story.append(Spacer(1, 0.1 * inch))

        if trend:
            story.append(Image(trend, width=CONTENT_W, height=1.4 * inch))
            story.append(Spacer(1, 0.1 * inch))

        return story

    def _make_pie(self, data):
        try:
            vals = [data.get(k, 0) for k in ("critical", "high", "medium", "low")]
            labs = ["Critical", "High", "Medium", "Low"]
            pal  = ["#ef4444", "#f97316", "#eab308", "#22c55e"]
            pairs = [(l, v, c) for l, v, c in zip(labs, vals, pal) if v > 0]
            if not pairs:
                return None
            fig, ax = plt.subplots(figsize=(3.8, 3), facecolor="white")
            wedge_props = {"linewidth": 1.5, "edgecolor": "white"}
            ax.pie([p[1] for p in pairs],
                   labels=[p[0] for p in pairs],
                   colors=[p[2] for p in pairs],
                   autopct="%1.0f%%",
                   startangle=130,
                   wedgeprops=wedge_props,
                   textprops={"fontsize": 8})
            ax.set_title("Severity Split", fontsize=9, fontweight="bold", pad=6)
            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=130, bbox_inches="tight", facecolor="white")
            buf.seek(0); plt.close(fig)
            return buf
        except Exception as e:
            logger.error(f"Pie error: {e}"); return None

    def _make_bar(self, top_hosts):
        try:
            if not top_hosts:
                return None
            hosts  = sorted(top_hosts.items(), key=lambda x: x[1], reverse=True)[:8]
            names  = [h for h, _ in hosts]
            counts = [c for _, c in hosts]
            fig, ax = plt.subplots(figsize=(4.5, 3), facecolor="white")
            bars = ax.barh(names, counts, color="#3b82f6", edgecolor="white", height=0.55)
            for bar, cnt in zip(bars, counts):
                ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
                        str(cnt), va="center", fontsize=7.5, color="#334155")
            ax.set_xlabel("Alerts", fontsize=8)
            ax.set_title("Top Affected Hosts", fontsize=9, fontweight="bold")
            ax.invert_yaxis()
            for spine in ("top", "right"):
                ax.spines[spine].set_visible(False)
            ax.tick_params(labelsize=7.5)
            fig.tight_layout()
            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=130, bbox_inches="tight", facecolor="white")
            buf.seek(0); plt.close(fig)
            return buf
        except Exception as e:
            logger.error(f"Bar error: {e}"); return None

    def _make_severity_bar(self, alerts_data):
        """Horizontal stacked breakdown bar."""
        try:
            vals = {k: alerts_data.get(k, 0) for k in ("critical", "high", "medium", "low")}
            total = sum(vals.values())
            if total == 0:
                return None
            pal = {"critical": "#ef4444", "high": "#f97316",
                   "medium":   "#eab308", "low":  "#22c55e"}
            fig, ax = plt.subplots(figsize=(7.5, 0.8), facecolor="white")
            left = 0
            for key, color in pal.items():
                pct = vals[key] / total
                if pct > 0:
                    ax.barh(0, pct, left=left, color=color, height=0.55, edgecolor="white")
                    if pct > 0.06:
                        ax.text(left + pct / 2, 0,
                                f"{key.capitalize()}\n{vals[key]}",
                                ha="center", va="center",
                                fontsize=7.5, color="white", fontweight="bold")
                    left += pct
            ax.set_xlim(0, 1)
            ax.axis("off")
            fig.tight_layout(pad=0)
            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=130, bbox_inches="tight", facecolor="white")
            buf.seek(0); plt.close(fig)
            return buf
        except Exception as e:
            logger.error(f"Stacked bar error: {e}"); return None

    # ── Analysis / Patterns ──────────────────────────────────────────────────
    def _analysis_section(self, analysis_data):
        s = self.styles
        patterns = analysis_data.get("patterns", [])
        if not patterns:
            return []
        story = _section("Identified Patterns", s)
        for p in patterns:
            text = p.lstrip("-• ").strip()
            row = Table(
                [[Paragraph("▶", ParagraphStyle("ic", fontSize=9, textColor=BLUE_L,
                                                 fontName="Helvetica-Bold")),
                  Paragraph(text, s["Body"])]],
                colWidths=[0.22 * inch, CONTENT_W - 0.22 * inch],
            )
            row.setStyle(TableStyle([
                ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING",    (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(row)
        story.append(Spacer(1, 0.1 * inch))
        return story

    # ── Recommendations ──────────────────────────────────────────────────────
    def _recommendations_section(self, analysis_data):
        s = self.styles
        recs = analysis_data.get("recommendations", [])
        story = _section("Recommendations", s)
        if not recs:
            story.append(Paragraph("No specific recommendations at this time.", s["Body"]))
            return story
        colors_seq = [RED, ORANGE, BLUE_L]
        for i, rec in enumerate(recs, 1):
            text  = rec.lstrip("-• ").strip()
            color = colors_seq[min(i - 1, len(colors_seq) - 1)]
            num_cell = Table(
                [[Paragraph(str(i), ParagraphStyle("n", fontSize=9, textColor=WHITE,
                                                    fontName="Helvetica-Bold",
                                                    alignment=TA_CENTER))]],
                colWidths=[0.24 * inch],
            )
            num_cell.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), color),
                ("TOPPADDING",    (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            row = Table(
                [[num_cell, Paragraph(text, s["Body"])]],
                colWidths=[0.32 * inch, CONTENT_W - 0.32 * inch],
            )
            bg = GRAY_1 if i % 2 == 0 else WHITE
            row.setStyle(TableStyle([
                ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING",    (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("BACKGROUND",    (0, 0), (-1, -1), bg),
            ]))
            story.append(row)
        story.append(Spacer(1, 0.15 * inch))
        return story

    # ── Top Hosts table ──────────────────────────────────────────────────────
    def _hosts_table(self, alerts_data):
        s = self.styles
        top_hosts = alerts_data.get("top_hosts", {})
        if not top_hosts:
            return []
        story = _section("Top Affected Hosts", s)
        sorted_hosts = sorted(top_hosts.items(), key=lambda x: x[1], reverse=True)[:10]
        total_alerts = alerts_data.get("total", 1) or 1

        header = [
            Paragraph("#",      s["TH"]),
            Paragraph("Host",   s["TH"]),
            Paragraph("Alerts", s["TH"]),
            Paragraph("Share",  s["TH"]),
        ]
        rows = [header]
        for rank, (host, cnt) in enumerate(sorted_hosts, 1):
            pct = f"{round(cnt / total_alerts * 100)}%"
            rows.append([
                Paragraph(str(rank), s["TD"]),
                Paragraph(host, s["TDmono"]),
                Paragraph(str(cnt), s["TD"]),
                Paragraph(pct, s["TD"]),
            ])

        t = Table(rows, colWidths=[0.4 * inch, 4.5 * inch, 0.7 * inch, 0.8 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0), BLUE),
            ("ROWBACKGROUNDS",  (0, 1), (-1, -1), [WHITE, GRAY_1]),
            ("GRID",           (0, 0), (-1, -1), 0.4, BORDER),
            ("TOPPADDING",     (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING",  (0, 0), (-1, -1), 7),
            ("LEFTPADDING",    (0, 0), (-1, -1), 8),
            ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.2 * inch))
        return story

    # ── Full Alert Details table ─────────────────────────────────────────────
    def _alerts_table(self, problems: List[Dict[str, Any]]):
        s = self.styles
        story = _section(f"Alert Details ({len(problems)} total)", s)

        # Sort by severity (critical first)
        sev_order = {"4": 0, "5": 0, "critical": 0,
                     "3": 1, "high": 1,
                     "2": 2, "medium": 2,
                     "1": 3, "0": 3, "low": 3}
        sorted_p = sorted(problems,
                          key=lambda x: sev_order.get(str(x.get("severity", "0")).lower(), 9))

        header = [
            Paragraph("#",          s["TH"]),
            Paragraph("Severity",   s["TH"]),
            Paragraph("Host",       s["TH"]),
            Paragraph("Alert",      s["TH"]),
            Paragraph("Time",       s["TH"]),
        ]
        rows = [header]
        for i, p in enumerate(sorted_p, 1):
            sev_str = str(p.get("severity", "0"))
            sev_label = _sev_label(sev_str)
            sev_color = _sev_color(sev_str)

            host = (p.get("host") or
                    (p.get("hosts", [{}])[0].get("host", "—") if p.get("hosts") else "—"))
            name = p.get("message") or p.get("name", "—")
            ts   = p.get("timestamp") or p.get("clock", "")
            try:
                ts_fmt = datetime.fromtimestamp(int(ts)).strftime("%m/%d %H:%M")
            except Exception:
                ts_fmt = str(ts)[:16] if ts else "—"

            sev_cell = Table(
                [[Paragraph(sev_label,
                            ParagraphStyle("sc", fontSize=7.5, textColor=WHITE,
                                           fontName="Helvetica-Bold",
                                           alignment=TA_CENTER))]],
                colWidths=[0.65 * inch],
            )
            sev_cell.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), sev_color),
                ("TOPPADDING",    (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))

            bg = GRAY_1 if i % 2 == 0 else WHITE
            rows.append([
                Paragraph(str(i),  s["TD"]),
                sev_cell,
                Paragraph(host,    s["TDmono"]),
                Paragraph(name,    s["TD"]),
                Paragraph(ts_fmt,  s["TDmono"]),
            ])

        t = Table(rows,
                  colWidths=[0.3 * inch, 0.72 * inch, 1.3 * inch,
                             3.3 * inch, 0.75 * inch])
        style = [
            ("BACKGROUND",    (0, 0), (-1, 0), BLUE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GRAY_1]),
            ("GRID",          (0, 0), (-1, -1), 0.3, BORDER),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]
        t.setStyle(TableStyle(style))
        story.append(t)
        story.append(Spacer(1, 0.15 * inch))
        return story

    # ── Methodology ──────────────────────────────────────────────────────────
    def _methodology(self):
        s = self.styles
        story = _section("Methodology & Disclaimer", s)
        text = (
            "This report was generated automatically by <b>Carlos-IA</b>, an intelligent "
            "infrastructure observability platform. Alert data is sourced from Zabbix monitoring "
            "(or simulated data when Zabbix is unavailable). AI analysis is performed by a local "
            "Ollama LLM instance (Mistral) with a rule-based fallback engine. "
            "Severity classifications follow the Zabbix 5-level scale: "
            "Disaster (4–5) → Critical, High (3), Average (2) → Medium, Warning (1) → Low. "
            "Recommendations are advisory only — validate against your environment before acting. "
            "Report generated: "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
        )
        story.append(Paragraph(text, s["Small"]))
        return story
