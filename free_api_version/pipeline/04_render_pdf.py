"""
pipeline/04_render_pdf.py
Converts output/manuscript.md → output/Building_LLMs_from_Scratch.pdf
Uses reportlab for a polished, book-quality PDF.
No LaTeX or pandoc dependency needed.
"""

import os
import re
import yaml
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    HRFlowable, KeepTogether, Table, TableStyle
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Color palette ────────────────────────────────────────────────────────────
DARK_BG   = HexColor("#1a1a2e")
ACCENT    = HexColor("#e94560")
LIGHT_BG  = HexColor("#f5f5f5")
DARK_TEXT = HexColor("#1a1a2e")
MID_GRAY  = HexColor("#555555")
CODE_BG   = HexColor("#f0f0f0")
RULE_CLR  = HexColor("#e94560")

PAGE_W, PAGE_H = A4
MARGIN = 2.5 * cm

def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)

# ── Styles ───────────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["title"] = ParagraphStyle(
        "BookTitle",
        fontName="Helvetica-Bold",
        fontSize=32,
        leading=40,
        textColor=white,
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    styles["subtitle"] = ParagraphStyle(
        "BookSubtitle",
        fontName="Helvetica",
        fontSize=16,
        leading=22,
        textColor=HexColor("#cccccc"),
        alignment=TA_CENTER,
        spaceAfter=8,
    )
    styles["author"] = ParagraphStyle(
        "Author",
        fontName="Helvetica-Oblique",
        fontSize=13,
        leading=18,
        textColor=HexColor("#aaaaaa"),
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    styles["toc_heading"] = ParagraphStyle(
        "TOCHeading",
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=26,
        textColor=DARK_TEXT,
        spaceBefore=20,
        spaceAfter=14,
    )
    styles["toc_entry"] = ParagraphStyle(
        "TOCEntry",
        fontName="Helvetica",
        fontSize=11,
        leading=18,
        textColor=DARK_TEXT,
        leftIndent=10,
        spaceAfter=4,
    )
    styles["toc_entry_chapter"] = ParagraphStyle(
        "TOCEntryChapter",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=18,
        textColor=DARK_TEXT,
        leftIndent=10,
        spaceAfter=4,
    )
    styles["chapter_heading"] = ParagraphStyle(
        "ChapterHeading",
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=30,
        textColor=DARK_TEXT,
        spaceBefore=0,
        spaceAfter=18,
    )
    styles["chapter_number"] = ParagraphStyle(
        "ChapterNumber",
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=ACCENT,
        spaceBefore=0,
        spaceAfter=4,
    )
    styles["section_heading"] = ParagraphStyle(
        "SectionHeading",
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=20,
        textColor=DARK_TEXT,
        spaceBefore=18,
        spaceAfter=8,
    )
    styles["body"] = ParagraphStyle(
        "BodyText",
        fontName="Helvetica",
        fontSize=11,
        leading=17,
        textColor=DARK_TEXT,
        alignment=TA_JUSTIFY,
        spaceAfter=10,
    )
    styles["bold_body"] = ParagraphStyle(
        "BoldBody",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=17,
        textColor=DARK_TEXT,
        spaceAfter=6,
    )
    styles["code"] = ParagraphStyle(
        "Code",
        fontName="Courier",
        fontSize=9,
        leading=13,
        textColor=HexColor("#222222"),
        backColor=CODE_BG,
        leftIndent=12,
        rightIndent=12,
        spaceBefore=6,
        spaceAfter=6,
    )
    styles["foreword_heading"] = ParagraphStyle(
        "ForewordHeading",
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=26,
        textColor=DARK_TEXT,
        spaceBefore=0,
        spaceAfter=14,
    )
    return styles

# ── Page templates ───────────────────────────────────────────────────────────
class BookDocTemplate(SimpleDocTemplate):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        self.page_number = 0

    def handle_pageEnd(self):
        self.page_number += 1
        super().handle_pageEnd()

def _header_footer(canvas, doc):
    canvas.saveState()
    page_num = doc.page
    w, h = A4

    # Skip header/footer on cover (page 1)
    if page_num > 1:
        # Header line
        canvas.setStrokeColor(RULE_CLR)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, h - 1.5*cm, w - MARGIN, h - 1.5*cm)

        # Header text
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MID_GRAY)
        canvas.drawString(MARGIN, h - 1.3*cm, "Building LLMs from Scratch")
        canvas.drawRightString(w - MARGIN, h - 1.3*cm, "")

        # Footer line
        canvas.line(MARGIN, 1.5*cm, w - MARGIN, 1.5*cm)

        # Page number
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(MID_GRAY)
        canvas.drawCentredString(w / 2, 1.0*cm, str(page_num - 1))  # -1 for cover

    canvas.restoreState()

# ── Markdown → ReportLab parser ──────────────────────────────────────────────
def md_to_para(text: str, style) -> Paragraph:
    """Convert inline markdown to reportlab XML tags."""
    # First comprehensively escape native XML characters safely
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    # Bold+italic
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', text)
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<font name="Courier" size="9">\1</font>', text)
    # Escape XML but preserve our tags
    # (reportlab handles &amp; etc. natively in Paragraph)
    return Paragraph(text, style)

def parse_markdown(md_text: str, styles: dict) -> list:
    """Parse full markdown manuscript into reportlab flowables."""
    story = []
    lines = md_text.split("\n")
    i = 0
    in_code_block = False
    code_lines = []

    while i < len(lines):
        line = lines[i]

        # Code blocks
        if line.strip().startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lines = []
            else:
                in_code_block = False
                code_text = "\n".join(code_lines)
                # Escape XML chars
                code_text = code_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(code_text.replace("\n", "<br/>"), styles["code"]))
                story.append(Spacer(1, 6))
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # H1: title page (special)
        if line.startswith("# "):
            text = line[2:].strip()
            story.append(PageBreak())
            # Colored cover block
            story.append(Spacer(1, 3*cm))
            story.append(md_to_para(text, styles["title"]))
            i += 1
            continue

        # H2: chapter or section heading
        if line.startswith("## "):
            text = line[3:].strip()
            story.append(PageBreak())
            story.append(Spacer(1, 1*cm))
            # Detect "Chapter N:" pattern
            ch_match = re.match(r'^Chapter (\d+):\s*(.+)$', text)
            if ch_match:
                story.append(Paragraph(f"Chapter {ch_match.group(1)}", styles["chapter_number"]))
                story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=12))
                story.append(Paragraph(ch_match.group(2), styles["chapter_heading"]))
            elif text in ("Foreword", "Glossary", "Table of Contents"):
                story.append(Paragraph(text, styles["foreword_heading"]))
                story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceAfter=12))
            else:
                story.append(Paragraph(text, styles["chapter_heading"]))
            story.append(Spacer(1, 0.3*cm))
            i += 1
            continue

        # H3: sub-section
        if line.startswith("### "):
            text = line[4:].strip()
            story.append(md_to_para(text, styles["section_heading"]))
            i += 1
            continue

        # HR divider
        if line.strip() in ("---", "***", "___"):
            story.append(Spacer(1, 8))
            story.append(HRFlowable(width="80%", thickness=0.5, color=MID_GRAY,
                                    hAlign="CENTER", spaceAfter=8))
            i += 1
            continue

        # Blank line
        if not line.strip():
            i += 1
            continue

        # TOC entries
        if line.startswith("- "):
            text = line[2:].strip()
            if text.startswith("Chapter"):
                story.append(md_to_para(text, styles["toc_entry_chapter"]))
            else:
                story.append(md_to_para(text, styles["toc_entry"]))
            i += 1
            continue

        # Regular paragraph: accumulate consecutive lines
        para_lines = []
        while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "-", "```", "---")):
            para_lines.append(lines[i])
            i += 1
        if para_lines:
            text = " ".join(para_lines)
            story.append(md_to_para(text, styles["body"]))
        continue

    return story

# ── Cover page ───────────────────────────────────────────────────────────────
def build_cover(cfg, styles) -> list:
    book = cfg["book"]
    story = []

    def draw_cover(canvas, doc):
        w, h = A4
        # Dark background
        canvas.setFillColor(DARK_BG)
        canvas.rect(0, 0, w, h, fill=1, stroke=0)
        # Accent bar
        canvas.setFillColor(ACCENT)
        canvas.rect(0, h * 0.38, w, 4, fill=1, stroke=0)
        # Subtle grid lines for aesthetic
        canvas.setStrokeColor(HexColor("#2a2a4e"))
        canvas.setLineWidth(0.3)
        for x in range(0, int(w), 40):
            canvas.line(x, 0, x, h)
        for y in range(0, int(h), 40):
            canvas.line(0, y, w, y)

    # We'll just build the text; background is drawn via onPage
    # Use Table to center everything on the page
    story.append(Spacer(1, 6 * cm))
    story.append(md_to_para(book["title"].upper(), styles["title"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(md_to_para(book["subtitle"], styles["subtitle"]))
    story.append(Spacer(1, 1.5 * cm))
    story.append(md_to_para(book["author"], styles["author"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(md_to_para(f"Version {book['version']}", styles["author"]))
    story.append(PageBreak())
    return story, draw_cover

# ── Main ─────────────────────────────────────────────────────────────────────
def run():
    cfg = load_config()
    manuscript_path = cfg["paths"]["manuscript_md"]
    output_pdf = cfg["paths"]["output_pdf"]
    os.makedirs(cfg["paths"]["output_dir"], exist_ok=True)

    print(f"Reading manuscript: {manuscript_path}")
    with open(manuscript_path, encoding="utf-8") as f:
        md_text = f.read()

    styles = make_styles()

    # Build cover
    cover_story, draw_cover_fn = build_cover(cfg, styles)

    # Parse main content (skip first title since we handle cover manually)
    # Remove the leading "# Title" block from md
    lines = md_text.split("\n")
    start_idx = 0
    for j, l in enumerate(lines):
        if l.startswith("# "):
            start_idx = j + 1
            break
    # Skip subtitle/author/version lines
    while start_idx < len(lines) and not lines[start_idx].startswith("##"):
        start_idx += 1

    content_md = "\n".join(lines[start_idx:])
    content_story = parse_markdown(content_md, styles)

    full_story = cover_story + content_story

    print(f"Rendering PDF → {output_pdf}")
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm,
        title=cfg["book"]["title"],
        author=cfg["book"]["author"],
        subject=cfg["book"]["subtitle"],
    )

    def on_page(canvas, doc):
        if doc.page == 1:
            draw_cover_fn(canvas, doc)
        _header_footer(canvas, doc)

    doc.build(full_story, onFirstPage=on_page, onLaterPages=on_page)
    size_mb = os.path.getsize(output_pdf) / 1024 / 1024
    print(f"✓ PDF saved → {output_pdf} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    run()
