"""
generate_pdf.py
Generates data/quarterly_analytics_report.pdf using only the standard library
+ fpdf2 (pure-Python, no system dependencies).

Run:  pip install fpdf2
      python generate_pdf.py
"""

from fpdf import FPDF
import os

OUTPUT = os.path.join(os.path.dirname(__file__), "quarterly_analytics_report.pdf")


class ReportPDF(FPDF):
    BRAND_BLUE  = (30,  80,  160)
    BRAND_DARK  = (20,  20,   40)
    BRAND_GRAY  = (100, 100, 120)
    LIGHT_GRAY  = (240, 242, 248)
    WHITE       = (255, 255, 255)
    GREEN       = (34,  139,  34)
    RED         = (200,  40,  40)

    def header(self):
        self.set_fill_color(*self.BRAND_BLUE)
        self.rect(0, 0, 210, 14, "F")
        self.set_text_color(*self.WHITE)
        self.set_font("Helvetica", "B", 10)
        self.set_y(3)
        self.cell(0, 8, "SAGA  |  Conversational Analytics Agent", align="L")
        self.set_y(3)
        self.cell(0, 8, "CONFIDENTIAL", align="R")
        self.set_text_color(*self.BRAND_DARK)
        self.ln(16)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*self.BRAND_GRAY)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")


def title_page(pdf: ReportPDF):
    pdf.add_page()
    pdf.set_fill_color(*ReportPDF.BRAND_BLUE)
    pdf.rect(0, 55, 210, 80, "F")

    pdf.set_y(65)
    pdf.set_text_color(*ReportPDF.WHITE)
    pdf.set_font("Helvetica", "B", 28)
    pdf.cell(0, 14, "Quarterly Business Review", align="C", ln=True)
    pdf.set_font("Helvetica", "", 16)
    pdf.cell(0, 10, "Q1 2025 — Revenue & Customer Analytics", align="C", ln=True)
    pdf.set_font("Helvetica", "I", 11)
    pdf.cell(0, 8, "Prepared by: SAGA Analytics Platform", align="C", ln=True)
    pdf.cell(0, 8, "Report Date: June 2025", align="C", ln=True)

    pdf.set_y(155)
    pdf.set_text_color(*ReportPDF.BRAND_DARK)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_fill_color(*ReportPDF.LIGHT_GRAY)
    pdf.rect(20, 155, 170, 28, "F")
    pdf.set_xy(25, 158)
    pdf.multi_cell(160, 6,
        "This report is generated automatically by the SAGA Conversational Analytics Agent "
        "and contains forward-looking statements.  Internal use only.",
        align="L")


def section_title(pdf: ReportPDF, text: str):
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*ReportPDF.BRAND_BLUE)
    pdf.ln(4)
    pdf.cell(0, 8, text, ln=True)
    pdf.set_draw_color(*ReportPDF.BRAND_BLUE)
    pdf.set_line_width(0.5)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 170, pdf.get_y())
    pdf.ln(3)
    pdf.set_text_color(*ReportPDF.BRAND_DARK)


def kpi_block(pdf: ReportPDF, kpis: list):
    """Render a row of KPI cards."""
    card_w  = 40
    card_h  = 24
    gap     = 5
    start_x = 15
    x = start_x

    for label, value, change, up in kpis:
        pdf.set_fill_color(*ReportPDF.LIGHT_GRAY)
        pdf.rect(x, pdf.get_y(), card_w, card_h, "F")
        pdf.set_xy(x + 2, pdf.get_y() + 2)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*ReportPDF.BRAND_GRAY)
        pdf.cell(card_w - 4, 5, label, ln=True)

        pdf.set_x(x + 2)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*ReportPDF.BRAND_DARK)
        pdf.cell(card_w - 4, 7, value, ln=True)

        pdf.set_x(x + 2)
        pdf.set_font("Helvetica", "", 7)
        color = ReportPDF.GREEN if up else ReportPDF.RED
        arrow = "▲" if up else "▼"
        pdf.set_text_color(*color)
        pdf.cell(card_w - 4, 5, f"{arrow} {change} vs last quarter", ln=True)

        x += card_w + gap

    pdf.ln(card_h + 4)
    pdf.set_text_color(*ReportPDF.BRAND_DARK)


def table(pdf: ReportPDF, headers: list, rows: list, col_widths: list):
    # Header row
    pdf.set_fill_color(*ReportPDF.BRAND_BLUE)
    pdf.set_text_color(*ReportPDF.WHITE)
    pdf.set_font("Helvetica", "B", 9)
    for h, w in zip(headers, col_widths):
        pdf.cell(w, 7, h, border=0, fill=True, align="C")
    pdf.ln()

    # Data rows
    pdf.set_font("Helvetica", "", 8.5)
    for i, row in enumerate(rows):
        fill = (i % 2 == 0)
        pdf.set_fill_color(*ReportPDF.LIGHT_GRAY if fill else ReportPDF.WHITE)
        pdf.set_text_color(*ReportPDF.BRAND_DARK)
        for cell, w in zip(row, col_widths):
            pdf.cell(w, 6, str(cell), border=0, fill=fill, align="C")
        pdf.ln()
    pdf.ln(3)


def body_text(pdf: ReportPDF, text: str):
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(*ReportPDF.BRAND_DARK)
    pdf.multi_cell(0, 5.5, text)
    pdf.ln(2)


def build_report(pdf: ReportPDF):
    # ── Page 2 – Executive Summary ──────────────────────────────────────────
    pdf.add_page()
    section_title(pdf, "1.  Executive Summary")
    body_text(pdf,
        "Q1 2025 was a strong quarter for the SAGA platform.  Monthly Recurring Revenue (MRR) "
        "grew 18 % quarter-over-quarter, driven primarily by Enterprise plan upgrades and strong "
        "net new business in the Asia Pacific region.  Customer churn improved significantly, "
        "dropping from 3.2 % in Q4 2024 to 2.1 % in Q1 2025 — the lowest in company history.\n\n"
        "Key highlights:\n"
        "  • 4 new Enterprise logos signed, adding $7,996 / month in MRR\n"
        "  • Pro plan remains the most popular tier with 48 % of active accounts\n"
        "  • Net Promoter Score (NPS) rose 7 points to 64\n"
        "  • Support ticket volume down 22 % thanks to in-app SAGA AI assistant adoption"
    )

    section_title(pdf, "2.  Key Performance Indicators")
    kpi_block(pdf, [
        ("Total MRR",        "$87,450",  "+18 %", True),
        ("Active Customers",  "16",       "+3",    True),
        ("Churn Rate",        "2.1 %",    "-1.1 pp", True),
        ("Avg. Revenue / Customer", "$5,466", "+14 %", True),
    ])

    # ── Page 3 – Revenue Breakdown ──────────────────────────────────────────
    pdf.add_page()
    section_title(pdf, "3.  Revenue by Plan")
    table(pdf,
          ["Plan", "Accounts", "MRR (USD)", "% of Total", "QoQ Δ"],
          [
              ["Enterprise", "5", "$9,995",  "11.4 %", "+25 %"],
              ["Pro",        "8", "$3,992",  "4.6 %",  "+14 %"],
              ["Starter",    "7", "$693",    "0.8 %",  "+5 %"],
              ["(Churned)",  "5", "—",       "—",      "—"],
              ["TOTAL",      "20", "$14,680", "100 %",  "+18 %"],
          ],
          [38, 30, 38, 32, 32])

    section_title(pdf, "4.  Revenue by Region")
    table(pdf,
          ["Region", "Customers", "MRR (USD)", "Churn", "NPS"],
          [
              ["North America",  "9",  "$8,991",  "2.3 %", "66"],
              ["Europe",         "5",  "$2,993",  "1.8 %", "61"],
              ["Asia Pacific",   "3",  "$2,097",  "0.0 %", "70"],
              ["Latin America",  "2",  "$198",    "0.0 %", "58"],
          ],
          [48, 28, 38, 28, 28])

    # ── Page 4 – Churn & Retention ──────────────────────────────────────────
    pdf.add_page()
    section_title(pdf, "5.  Churn Analysis")
    body_text(pdf,
        "Five customers churned during Q1 2025.  Exit surveys and CRM notes indicate "
        "the following primary churn reasons:\n\n"
        "  1. Budget cuts / cost reduction  — 2 customers (40 %)\n"
        "  2. Switched to a competitor      — 1 customer  (20 %)\n"
        "  3. Business closure              — 1 customer  (20 %)\n"
        "  4. Lack of Enterprise features   — 1 customer  (20 %)\n\n"
        "Churned accounts were predominantly on the Starter plan ($99/mo), resulting "
        "in a relatively low MRR impact of $495 / month.\n\n"
        "Retention initiatives launched in Q1:\n"
        "  • 90-day onboarding health check cadence for new Pro/Enterprise accounts\n"
        "  • In-app usage nudges for accounts using < 30 % of their query quota\n"
        "  • Dedicated customer success manager assigned to all Enterprise accounts"
    )

    section_title(pdf, "6.  Churned Customer Detail")
    table(pdf,
          ["Customer", "Plan", "MRR Lost", "Tenure (mo)", "Churn Reason"],
          [
              ["Summit Analytics", "Pro",     "$499", "6",  "Budget cuts"],
              ["Redwood Retail",   "Starter",  "$99",  "4",  "Competitor"],
              ["Orbit Logistics",  "Pro",     "$499",  "5",  "Budget cuts"],
              ["Maplesoft Inc",    "Starter",  "$99",  "3",  "Business closed"],
              ["(Confidential)",   "Enterprise","$1,999", "8", "Missing features"],
          ],
          [48, 24, 26, 28, 44])

    # ── Page 5 – Outlook & Recommendations ─────────────────────────────────
    pdf.add_page()
    section_title(pdf, "7.  Q2 2025 Outlook")
    body_text(pdf,
        "Pipeline entering Q2 is the strongest on record.  The sales team has 12 qualified "
        "opportunities in late-stage evaluation, with a combined potential MRR of $15,000+.  "
        "Enterprise deal velocity has improved following the launch of the dedicated "
        "Enterprise onboarding track in March.\n\n"
        "Targets for Q2 2025:\n"
        "  • MRR target: $102,000  (+17 % QoQ)\n"
        "  • Net new logos: 5\n"
        "  • Churn rate: ≤ 1.8 %\n"
        "  • NPS target: 68"
    )

    section_title(pdf, "8.  Strategic Recommendations")
    body_text(pdf,
        "Based on Q1 data and customer feedback, the following initiatives are recommended "
        "for prioritisation in Q2:\n\n"
        "  A) Launch a mid-tier 'Growth' plan at $249/mo to reduce the pricing gap between "
        "     Starter and Pro and capture mid-market customers who feel Starter is too limited "
        "     but are not ready for the full Pro commitment.\n\n"
        "  B) Introduce annual billing for the Starter plan with a 15 % discount to improve "
        "     cash flow predictability and reduce monthly churn exposure.\n\n"
        "  C) Invest in the SAGA AI in-app assistant — usage data shows that accounts "
        "     engaging with the assistant > 10 times / week have a 0 % churn rate.  Driving "
        "     this engagement should be the top retention lever.\n\n"
        "  D) Expand Asia Pacific go-to-market: APAC customers have 0 % churn and the "
        "     highest NPS (70), yet represent only 15 % of revenue.  A regional partnership "
        "     program could unlock significant growth."
    )

    section_title(pdf, "9.  Appendix — Data Sources")
    body_text(pdf,
        "All figures in this report are sourced from:\n"
        "  • SAGA platform billing database (analytics.db)\n"
        "  • CRM export — June 2025\n"
        "  • NPS survey — 62 respondents, Q1 2025\n"
        "  • Exit survey — 5 churned accounts, Q1 2025\n\n"
        "For questions, contact the Analytics team at analytics@saga-platform.io"
    )


def main():
    pdf = ReportPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(left=15, top=15, right=15)

    title_page(pdf)
    build_report(pdf)

    pdf.output(OUTPUT)
    print(f"✅  PDF written to: {OUTPUT}")


if __name__ == "__main__":
    main()
