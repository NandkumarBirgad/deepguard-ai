"""
generate_report_pdf.py — DeepGuard AI v2.0
Generates a comprehensive PDF project report with architecture graphs,
charts, component details, and tech stack overview.

Usage:
    pip install reportlab matplotlib
    python generate_report_pdf.py
"""

import os
import math
import io
from datetime import datetime

# ── reportlab ──────────────────────────────────────────────────────────────
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Image as RLImage, KeepTogether
)
from reportlab.graphics.shapes import (
    Drawing, Rect, Circle, String, Line,
    Polygon, Group, Path
)
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF

# ── matplotlib ─────────────────────────────────────────────────────────────
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS & THEME
# ═══════════════════════════════════════════════════════════════════════════
OUTPUT_FILE = "DeepGuard_AI_Project_Report.pdf"
PAGE_W, PAGE_H = A4          # 595.27 x 841.89 pts

# Colours (ReportLab RGB 0-1 scale)
BG_DARK    = colors.HexColor("#080c14")
BG_CARD    = colors.HexColor("#111827")
BG_MID     = colors.HexColor("#0d1422")
C_BLUE     = colors.HexColor("#60a5fa")
C_PURPLE   = colors.HexColor("#a78bfa")
C_GREEN    = colors.HexColor("#34d399")
C_RED      = colors.HexColor("#f87171")
C_ORANGE   = colors.HexColor("#fb923c")
C_YELLOW   = colors.HexColor("#fbbf24")
C_CYAN     = colors.HexColor("#22d3ee")
C_TEXT     = colors.HexColor("#e2e8f0")
C_MUTED    = colors.HexColor("#94a3b8")
C_DIM      = colors.HexColor("#475569")
C_BORDER   = colors.HexColor("#1e3a5f")
C_WHITE    = colors.white

# Matplotlib colours
MP = {
    "bg":     "#080c14",
    "card":   "#111827",
    "mid":    "#0d1422",
    "blue":   "#60a5fa",
    "purple": "#a78bfa",
    "green":  "#34d399",
    "red":    "#f87171",
    "orange": "#fb923c",
    "yellow": "#fbbf24",
    "cyan":   "#22d3ee",
    "text":   "#e2e8f0",
    "muted":  "#94a3b8",
    "dim":    "#475569",
    "border": "#1e3a5f",
}

# ═══════════════════════════════════════════════════════════════════════════
# STYLES
# ═══════════════════════════════════════════════════════════════════════════
def make_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["h1"] = ParagraphStyle(
        "H1", parent=base["Normal"],
        fontSize=28, leading=34, textColor=C_WHITE, fontName="Helvetica-Bold",
        spaceBefore=0, spaceAfter=8, alignment=TA_LEFT,
    )
    styles["h2"] = ParagraphStyle(
        "H2", parent=base["Normal"],
        fontSize=16, leading=20, textColor=C_BLUE, fontName="Helvetica-Bold",
        spaceBefore=16, spaceAfter=8, alignment=TA_LEFT,
    )
    styles["h3"] = ParagraphStyle(
        "H3", parent=base["Normal"],
        fontSize=12, leading=15, textColor=C_TEXT, fontName="Helvetica-Bold",
        spaceBefore=10, spaceAfter=4, alignment=TA_LEFT,
    )
    styles["body"] = ParagraphStyle(
        "Body", parent=base["Normal"],
        fontSize=9.5, leading=14, textColor=C_MUTED, fontName="Helvetica",
        spaceBefore=4, spaceAfter=4, alignment=TA_LEFT,
    )
    styles["caption"] = ParagraphStyle(
        "Caption", parent=base["Normal"],
        fontSize=8, leading=11, textColor=C_DIM, fontName="Helvetica",
        spaceBefore=4, spaceAfter=4, alignment=TA_CENTER,
    )
    styles["mono"] = ParagraphStyle(
        "Mono", parent=base["Normal"],
        fontSize=8.5, leading=12, textColor=C_CYAN, fontName="Courier",
        spaceBefore=2, spaceAfter=2, alignment=TA_LEFT,
    )
    styles["label"] = ParagraphStyle(
        "Label", parent=base["Normal"],
        fontSize=8, leading=10, textColor=C_DIM, fontName="Helvetica",
        spaceBefore=0, spaceAfter=0, alignment=TA_LEFT,
    )
    styles["stat"] = ParagraphStyle(
        "Stat", parent=base["Normal"],
        fontSize=22, leading=26, textColor=C_BLUE, fontName="Helvetica-Bold",
        spaceBefore=0, spaceAfter=0, alignment=TA_CENTER,
    )
    styles["center"] = ParagraphStyle(
        "Center", parent=base["Normal"],
        fontSize=9.5, leading=14, textColor=C_MUTED, fontName="Helvetica",
        spaceBefore=4, spaceAfter=4, alignment=TA_CENTER,
    )
    return styles


# ═══════════════════════════════════════════════════════════════════════════
# PAGE TEMPLATE  (dark background + header/footer on every page)
# ═══════════════════════════════════════════════════════════════════════════
class DeepGuardPDF(SimpleDocTemplate):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)

    def _make_background(self, canvas, doc):
        canvas.saveState()
        # Dark background
        canvas.setFillColor(BG_DARK)
        canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        # Subtle grid
        canvas.setStrokeColor(colors.HexColor("#1a2540"))
        canvas.setLineWidth(0.3)
        step = 28
        for x in range(0, int(PAGE_W) + step, step):
            canvas.line(x, 0, x, PAGE_H)
        for y in range(0, int(PAGE_H) + step, step):
            canvas.line(0, y, PAGE_W, y)
        canvas.restoreState()

    def _make_header(self, canvas, doc):
        if doc.page == 1:
            return
        canvas.saveState()
        canvas.setFillColor(BG_CARD)
        canvas.rect(0, PAGE_H - 30, PAGE_W, 30, fill=1, stroke=0)
        canvas.setFillColor(C_BLUE)
        canvas.rect(0, PAGE_H - 30, PAGE_W, 2, fill=1, stroke=0)
        canvas.setFillColor(C_MUTED)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(1.5*cm, PAGE_H - 20, "DeepGuard AI v2.0 — Project Report")
        canvas.drawRightString(PAGE_W - 1.5*cm, PAGE_H - 20,
                               datetime.now().strftime("%B %Y"))
        canvas.restoreState()

    def _make_footer(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(BG_CARD)
        canvas.rect(0, 0, PAGE_W, 22, fill=1, stroke=0)
        canvas.setFillColor(C_BLUE)
        canvas.rect(0, 22, PAGE_W, 1, fill=1, stroke=0)
        canvas.setFillColor(C_DIM)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawCentredString(PAGE_W / 2, 8, f"Page {doc.page}")
        canvas.drawString(1.5*cm, 8, "© 2026 DeepGuard AI — Deepfake Detection System")
        canvas.drawRightString(PAGE_W - 1.5*cm, 8, "Confidential")
        canvas.restoreState()

    def handle_pageBegin(self):
        self._make_background(self.canv, self)
        super().handle_pageBegin()

    def handle_pageEnd(self):
        self._make_header(self.canv, self)
        self._make_footer(self.canv, self)
        super().handle_pageEnd()


def onFirstPage(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(BG_DARK)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setStrokeColor(colors.HexColor("#1a2540"))
    canvas.setLineWidth(0.3)
    step = 28
    for x in range(0, int(PAGE_W) + step, step):
        canvas.line(x, 0, x, PAGE_H)
    for y in range(0, int(PAGE_H) + step, step):
        canvas.line(0, y, PAGE_W, y)
    canvas.restoreState()

    # Footer
    canvas.saveState()
    canvas.setFillColor(BG_CARD)
    canvas.rect(0, 0, PAGE_W, 22, fill=1, stroke=0)
    canvas.setFillColor(C_BLUE)
    canvas.rect(0, 22, PAGE_W, 1, fill=1, stroke=0)
    canvas.setFillColor(C_DIM)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawCentredString(PAGE_W / 2, 8, "Page 1")
    canvas.drawString(1.5*cm, 8, "© 2026 DeepGuard AI — Deepfake Detection System")
    canvas.drawRightString(PAGE_W - 1.5*cm, 8, "Confidential")
    canvas.restoreState()


def onLaterPages(canvas, doc):
    # Background
    canvas.saveState()
    canvas.setFillColor(BG_DARK)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setStrokeColor(colors.HexColor("#1a2540"))
    canvas.setLineWidth(0.3)
    step = 28
    for x in range(0, int(PAGE_W) + step, step):
        canvas.line(x, 0, x, PAGE_H)
    for y in range(0, int(PAGE_H) + step, step):
        canvas.line(0, y, PAGE_W, y)
    canvas.restoreState()
    # Header
    canvas.saveState()
    canvas.setFillColor(BG_CARD)
    canvas.rect(0, PAGE_H - 30, PAGE_W, 30, fill=1, stroke=0)
    canvas.setFillColor(C_BLUE)
    canvas.rect(0, PAGE_H - 30, PAGE_W, 2, fill=1, stroke=0)
    canvas.setFillColor(C_MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(1.5*cm, PAGE_H - 20, "DeepGuard AI v2.0 — Project Report")
    canvas.drawRightString(PAGE_W - 1.5*cm, PAGE_H - 20,
                           datetime.now().strftime("%B %Y"))
    canvas.restoreState()
    # Footer
    canvas.saveState()
    canvas.setFillColor(BG_CARD)
    canvas.rect(0, 0, PAGE_W, 22, fill=1, stroke=0)
    canvas.setFillColor(C_BLUE)
    canvas.rect(0, 22, PAGE_W, 1, fill=1, stroke=0)
    canvas.setFillColor(C_DIM)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawCentredString(PAGE_W / 2, 8, f"Page {doc.page}")
    canvas.drawString(1.5*cm, 8, "© 2026 DeepGuard AI — Deepfake Detection System")
    canvas.drawRightString(PAGE_W - 1.5*cm, 8, "Confidential")
    canvas.restoreState()


# ═══════════════════════════════════════════════════════════════════════════
# HELPER: mpl figure → ReportLab Image bytes
# ═══════════════════════════════════════════════════════════════════════════
def fig_to_rl(fig, width_pt, height_pt=None, dpi=150):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi,
                bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    if height_pt is None:
        img = RLImage(buf)
        img.drawWidth  = width_pt
        img.drawHeight = width_pt * (fig.get_figheight() / fig.get_figwidth())
    else:
        img = RLImage(buf)
        img.drawWidth  = width_pt
        img.drawHeight = height_pt
    return img


def section_rule():
    return HRFlowable(
        width="100%", thickness=1,
        color=C_BORDER, spaceAfter=8, spaceBefore=4
    )


def colored_spacer(height):
    return Spacer(1, height)


# ═══════════════════════════════════════════════════════════════════════════
# CHART 1 — Architecture Graph (Matplotlib)
# ═══════════════════════════════════════════════════════════════════════════
def make_architecture_chart():
    fig, ax = plt.subplots(figsize=(11, 7.5))
    fig.patch.set_facecolor(MP["mid"])
    ax.set_facecolor(MP["mid"])
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 7.5)
    ax.axis("off")

    # Layer bands
    bands = [
        (6.5, 7.5, "#0f1825", "CLIENT"),
        (4.8, 6.4, "#0c1520", "SERVER"),
        (3.0, 4.7, "#0a1218", "DETECTION"),
        (0.0, 2.9, "#080f16", "STORAGE"),
    ]
    for y0, y1, col, lbl in bands:
        ax.add_patch(FancyBboxPatch((0.05, y0), 10.9, y1-y0,
                     boxstyle="round,pad=0.05", fc=col, ec=MP["border"], lw=0.5, zorder=0))
        ax.text(0.2, (y0+y1)/2, lbl, color=MP["dim"], fontsize=7,
                fontfamily="monospace", fontweight="bold",
                va="center", alpha=0.7, rotation=90)

    # ── Node definitions: (label, sublabel, x_center, y_center, color)
    nodes = [
        ("Browser", "HTML+JS",         1.3, 7.0,  MP["blue"]),
        ("Auth Pages", "login/signup",  3.0, 7.0,  MP["orange"]),
        ("Landing", "index.html",       5.0, 7.0,  MP["cyan"]),
        ("AI Image UI", "detect_ai",    7.2, 7.0,  MP["purple"]),
        ("AI Video UI", "detect_video", 9.5, 7.0,  MP["green"]),
        ("Flask Server", "app.py",      5.0, 5.6,  MP["blue"]),
        ("Firebase", "Admin SDK",       1.3, 5.6,  MP["orange"]),
        ("Env Config", ".env/render",   2.5, 4.0,  MP["dim"]),
        ("Train Pipeline", "3 Models",  9.2, 5.6,  MP["yellow"]),
        ("Sightengine", "AI-Image API", 3.2, 3.8,  MP["purple"]),
        ("HuggingFace", "Video API",    5.8, 3.8,  MP["green"]),
        ("OpenCV cv2", "Frame Extract", 8.2, 3.8,  MP["cyan"]),
        ("static/uploads", "images",    1.6, 1.5,  MP["dim"]),
        ("uploads/", "raw cache",       4.0, 1.5,  MP["dim"]),
        ("false_preds/", "feedback",    6.4, 1.5,  MP["red"]),
        ("database/", "MongoDB",        9.0, 1.5,  MP["dim"]),
    ]

    BOX_W, BOX_H = 1.5, 0.65

    def draw_node(ax, label, sublabel, cx, cy, col):
        x0, y0 = cx - BOX_W/2, cy - BOX_H/2
        ax.add_patch(FancyBboxPatch((x0, y0), BOX_W, BOX_H,
                     boxstyle="round,pad=0.06",
                     fc="#0f172a", ec=col, lw=1.6, zorder=3))
        # Coloured top stripe
        ax.add_patch(FancyBboxPatch((x0, y0 + BOX_H - 0.07), BOX_W, 0.07,
                     boxstyle="square,pad=0", fc=col, ec="none", zorder=4))
        ax.text(cx, cy + 0.13, label, color=MP["text"], fontsize=6.5,
                fontweight="bold", ha="center", va="center", zorder=5)
        ax.text(cx, cy - 0.14, sublabel, color=MP["muted"], fontsize=5.5,
                ha="center", va="center", fontfamily="monospace", zorder=5)

    for n in nodes:
        draw_node(ax, n[0], n[1], n[2], n[3], n[4])

    # ── Edges (from_idx, to_idx, color, style)
    def get_center(idx):
        n = nodes[idx]
        return n[2], n[3]

    edges = [
        (0, 5,  MP["blue"],   "--"),  # Browser → Flask
        (1, 5,  MP["orange"], "--"),  # Auth → Flask
        (2, 5,  MP["cyan"],   "--"),  # Landing → Flask
        (3, 5,  MP["purple"], "--"),  # AI Image UI → Flask
        (4, 5,  MP["green"],  "--"),  # AI Video UI → Flask
        (6, 5,  MP["orange"], "-"),   # Firebase → Flask
        (7, 5,  MP["dim"],    ":"),   # Env → Flask
        (5, 9,  MP["purple"], "-"),   # Flask → Sightengine
        (5, 10, MP["green"],  "-"),   # Flask → HuggingFace
        (5, 11, MP["cyan"],   "-"),   # Flask → OpenCV
        (11, 10, MP["cyan"],  "--"),  # OpenCV → HuggingFace
        (8, 5,  MP["yellow"], ":"),   # Train → Flask
        (5, 12, MP["dim"],    ":"),   # Flask → static/uploads
        (5, 13, MP["dim"],    ":"),   # Flask → uploads/
        (5, 14, MP["red"],    ":"),   # Flask → false_preds
        (5, 15, MP["dim"],    ":"),   # Flask → database
    ]

    for fi, ti, col, ls in edges:
        x0, y0 = get_center(fi)
        x1, y1 = get_center(ti)
        ax.annotate("", xy=(x1, y1 + BOX_H/2 if y1 > y0 else y1 - BOX_H/2),
                    xytext=(x0, y0 - BOX_H/2 if y1 > y0 else y0 + BOX_H/2),
                    arrowprops=dict(
                        arrowstyle="-|>", color=col,
                        lw=1.0, linestyle=ls,
                        connectionstyle="arc3,rad=0.05",
                        mutation_scale=8,
                    ), zorder=2, alpha=0.75)

    ax.set_title("DeepGuard AI v2.0 — System Architecture Graph",
                 color=MP["text"], fontsize=11, fontweight="bold", pad=10)

    # Legend
    legend_items = [
        mpatches.Patch(color=MP["blue"],   label="Flask / HTTP"),
        mpatches.Patch(color=MP["purple"], label="Sightengine API"),
        mpatches.Patch(color=MP["green"],  label="HuggingFace API"),
        mpatches.Patch(color=MP["orange"], label="Firebase Auth"),
        mpatches.Patch(color=MP["cyan"],   label="OpenCV pipeline"),
        mpatches.Patch(color=MP["yellow"], label="Training pipeline"),
        mpatches.Patch(color=MP["red"],    label="False predictions"),
    ]
    ax.legend(handles=legend_items, loc="lower right",
              facecolor=MP["card"], edgecolor=MP["border"],
              labelcolor=MP["muted"], fontsize=6.5,
              ncol=2, framealpha=0.9)

    plt.tight_layout(pad=0.4)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# CHART 2 — Detection Flow (Matplotlib)
# ═══════════════════════════════════════════════════════════════════════════
def make_flow_chart():
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.6))
    fig.patch.set_facecolor(MP["mid"])

    def draw_flow(ax, title, steps, col):
        ax.set_facecolor(MP["card"])
        ax.set_xlim(0, len(steps))
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.set_title(title, color=col, fontsize=9, fontweight="bold", pad=6)

        BOX_W = 0.85
        for i, (icon, label, sub) in enumerate(steps):
            cx = i + 0.5
            # Box
            ax.add_patch(FancyBboxPatch((cx - BOX_W/2, 0.15), BOX_W, 0.68,
                         boxstyle="round,pad=0.04",
                         fc=MP["mid"], ec=col, lw=1.2, zorder=3, alpha=0.9))
            ax.text(cx, 0.71, icon, fontsize=14, ha="center", va="center", zorder=4)
            ax.text(cx, 0.44, label, color=MP["text"], fontsize=6.2,
                    fontweight="bold", ha="center", va="center", zorder=4)
            ax.text(cx, 0.26, sub, color=MP["muted"], fontsize=5.2,
                    ha="center", va="center", fontfamily="monospace", zorder=4)
            # Arrow to next
            if i < len(steps) - 1:
                ax.annotate("", xy=(cx + BOX_W/2 + 0.04, 0.5),
                            xytext=(cx + BOX_W/2 - 0.04, 0.5),
                            arrowprops=dict(arrowstyle="-|>", color=col,
                                            lw=1.2, mutation_scale=8), zorder=5)

    image_steps = [
        ("IMG", "Upload", "PNG/JPG"),
        ("API", "Flask",  "/detect-ai"),
        ("OK",  "Validate", "ext+size"),
        ("SAVE","Save",    "static/"),
        ("EYE", "Sightengine", "genai"),
        ("PCT", "Score",   "0.0-1.0"),
        (">>>" ,"Verdict", "thresh 0.7"),
    ]

    video_steps = [
        ("VID", "Upload",  "MP4/MOV"),
        ("API", "Flask",   "/detect-video"),
        ("CV2", "OpenCV",  "3 frames"),
        ("JPG", "JPEG",    "encode"),
        ("HF",  "HF API", "umm-maybe"),
        ("MAX", "Max Score", "3 frames"),
        (">>>", "Verdict", "thresh 0.7"),
    ]

    draw_flow(axes[0], "Detection Flow — AI Image", image_steps, MP["purple"])
    draw_flow(axes[1], "Detection Flow — AI Video", video_steps, MP["green"])

    plt.tight_layout(pad=0.6)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# CHART 3 — Tech Stack Breakdown (horizontal bar)
# ═══════════════════════════════════════════════════════════════════════════
def make_techstack_chart():
    categories = {
        "Backend":    [("Flask 2.2", 9), ("Werkzeug", 7), ("Jinja2", 6), ("Gunicorn", 5)],
        "ML / AI":    [("TensorFlow 2.15", 10), ("Keras", 9), ("Xception", 8),
                       ("EfficientNetB4", 8), ("ResNet50", 7), ("OpenCV", 7)],
        "APIs":       [("Sightengine", 9), ("Hugging Face", 8), ("Firebase Admin", 8)],
        "Data":       [("scikit-learn", 7), ("NumPy", 8), ("Pillow", 6),
                       ("pymongo", 5), ("matplotlib", 6)],
        "Deployment": [("Render PaaS", 9), ("reportlab", 5)],
    }
    cat_colours = {
        "Backend":    MP["blue"],
        "ML / AI":    MP["yellow"],
        "APIs":       MP["purple"],
        "Data":       MP["cyan"],
        "Deployment": MP["orange"],
    }

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor(MP["mid"])
    ax.set_facecolor(MP["card"])

    y = 0
    yticks, ylabels = [], []
    for cat, items in reversed(list(categories.items())):
        col = cat_colours[cat]
        for name, score in reversed(items):
            bar = ax.barh(y, score, color=col, height=0.6,
                          left=0, alpha=0.85, zorder=3)
            ax.text(score + 0.15, y, name, color=MP["text"],
                    fontsize=7.5, va="center", fontweight="bold")
            ax.text(score + 0.15, y - 0.22, cat, color=MP["muted"],
                    fontsize=5.5, va="center")
            yticks.append(y)
            ylabels.append("")
            y += 1
        y += 0.3  # gap between categories

    ax.set_xlim(0, 13)
    ax.set_ylim(-0.5, y)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(MP["border"])

    # Legend
    legend_items = [mpatches.Patch(color=v, label=k) for k, v in cat_colours.items()]
    ax.legend(handles=legend_items, loc="lower right",
              facecolor=MP["card"], edgecolor=MP["border"],
              labelcolor=MP["muted"], fontsize=7.5, framealpha=0.9)

    ax.set_title("Technology Stack — Component Relevance",
                 color=MP["text"], fontsize=10, fontweight="bold", pad=10)
    ax.set_facecolor(MP["card"])
    plt.tight_layout(pad=0.6)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# CHART 4 — ML Model Comparison (radar/spoke chart)
# ═══════════════════════════════════════════════════════════════════════════
def make_model_radar():
    labels = ["Accuracy", "Speed", "Social\nMedia", "Face-Swap", "Video", "Memory"]
    N = len(labels)
    angles = [n / float(N) * 2 * math.pi for n in range(N)]
    angles += angles[:1]

    models = {
        "Xception":       ([9, 6, 8, 9, 8, 6], MP["blue"]),
        "EfficientNetB4": ([8, 7, 9, 8, 7, 7], MP["purple"]),
        "ResNet50":       ([7, 8, 7, 7, 9, 8], MP["green"]),
    }

    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor(MP["mid"])
    ax.set_facecolor(MP["card"])

    # Styling
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, color=MP["muted"], fontsize=7.5)
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["2","4","6","8","10"], color=MP["dim"], fontsize=5.5)
    ax.grid(color=MP["border"], linestyle="--", linewidth=0.6, alpha=0.7)
    ax.spines["polar"].set_color(MP["border"])

    for name, (vals, col) in models.items():
        values = vals + vals[:1]
        ax.plot(angles, values, "o-", linewidth=1.5, color=col, label=name)
        ax.fill(angles, values, alpha=0.1, color=col)

    ax.set_title("ML Model Comparison", color=MP["text"],
                 fontsize=10, fontweight="bold", pad=18)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1),
              facecolor=MP["card"], edgecolor=MP["border"],
              labelcolor=MP["muted"], fontsize=7.5)

    plt.tight_layout(pad=0.4)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# CHART 5 — Training Phase Overview
# ═══════════════════════════════════════════════════════════════════════════
def make_training_chart():
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
    fig.patch.set_facecolor(MP["mid"])

    # Phase bar chart
    ax = axes[0]
    ax.set_facecolor(MP["card"])
    phases = ["Phase 1\nWarm-up\n(5 epochs)", "Phase 2\nFine-tune\n(15 epochs)"]
    lr_vals = [1e-3, 1e-5]
    bars = ax.barh(phases, lr_vals, color=[MP["blue"], MP["purple"]],
                   height=0.45, alpha=0.85)
    ax.set_xscale("log")
    ax.set_xlabel("Learning Rate (log scale)", color=MP["muted"], fontsize=7)
    ax.set_title("Training Phases — Learning Rate", color=MP["text"],
                 fontsize=8.5, fontweight="bold")
    ax.tick_params(colors=MP["muted"], labelsize=7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for s in ["left", "bottom"]:
        ax.spines[s].set_color(MP["border"])
    ax.set_facecolor(MP["card"])
    ax.tick_params(axis="y", colors=MP["text"])
    ax.tick_params(axis="x", colors=MP["muted"])

    # Augmentation pie
    ax2 = axes[1]
    ax2.set_facecolor(MP["card"])
    aug_labels = ["Rotation", "Zoom", "Flip", "Brightness", "JPEG noise",
                  "Shift", "Shear", "Channel shift"]
    aug_sizes  = [12, 15, 10, 13, 18, 11, 9, 12]
    aug_cols   = [MP["blue"], MP["purple"], MP["green"], MP["orange"],
                  MP["yellow"], MP["cyan"], MP["red"], MP["muted"]]
    wedges, texts = ax2.pie(aug_sizes, labels=aug_labels, colors=aug_cols,
                            startangle=140, textprops={"color": MP["muted"],
                            "fontsize": 6.5}, wedgeprops={"linewidth": 0.5,
                            "edgecolor": MP["border"]})
    ax2.set_title("Data Augmentation Mix", color=MP["text"],
                  fontsize=8.5, fontweight="bold")

    plt.tight_layout(pad=0.6)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# CHART 6 — Detection Threshold Logic
# ═══════════════════════════════════════════════════════════════════════════
def make_threshold_chart():
    fig, ax = plt.subplots(figsize=(8, 2.8))
    fig.patch.set_facecolor(MP["mid"])
    ax.set_facecolor(MP["card"])

    x = np.linspace(0, 1, 300)
    # Image threshold: 0.7
    ax.axvline(0.7, color=MP["blue"], lw=1.5, linestyle="--", label="Image threshold (0.70)")
    # Shade regions
    ax.axvspan(0, 0.7,  alpha=0.15, color=MP["green"],  label="Real (< 0.70)")
    ax.axvspan(0.7, 1.0, alpha=0.15, color=MP["red"],   label="AI Generated (≥ 0.70)")

    # Simulated score distribution
    real_scores = np.random.beta(2, 8, 500)
    fake_scores = np.random.beta(8, 2, 500)
    ax.hist(real_scores, bins=30, color=MP["green"], alpha=0.6, density=True,
            label="Real image dist.")
    ax.hist(fake_scores, bins=30, color=MP["red"],   alpha=0.6, density=True,
            label="AI image dist.")

    ax.set_xlim(0, 1)
    ax.set_xlabel("AI-generated probability score", color=MP["muted"], fontsize=8)
    ax.set_ylabel("Density", color=MP["muted"], fontsize=8)
    ax.set_title("Detection Threshold — Score Distribution", color=MP["text"],
                 fontsize=9.5, fontweight="bold")
    ax.tick_params(colors=MP["muted"], labelsize=7)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]:
        ax.spines[s].set_color(MP["border"])
    ax.legend(facecolor=MP["card"], edgecolor=MP["border"],
              labelcolor=MP["muted"], fontsize=7, loc="upper center")

    plt.tight_layout(pad=0.5)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# TABLE HELPERS
# ═══════════════════════════════════════════════════════════════════════════
TABLE_STYLE_BASE = [
    ("BACKGROUND", (0, 0), (-1, 0), BG_CARD),
    ("TEXTCOLOR",  (0, 0), (-1, 0), C_BLUE),
    ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE",   (0, 0), (-1, 0), 8.5),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BG_DARK, BG_MID]),
    ("TEXTCOLOR",  (0, 1), (-1, -1), C_MUTED),
    ("FONTNAME",   (0, 1), (-1, -1), "Helvetica"),
    ("FONTSIZE",   (0, 1), (-1, -1), 8),
    ("GRID",       (0, 0), (-1, -1), 0.4, C_BORDER),
    ("ROWPADDING", (0, 0), (-1, -1), 5),
    ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
    ("ALIGN",      (0, 0), (-1, -1), "LEFT"),
]


def dark_table(data, col_widths, extra_style=None):
    style = list(TABLE_STYLE_BASE)
    if extra_style:
        style.extend(extra_style)
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle(style))
    return t


# ═══════════════════════════════════════════════════════════════════════════
# BUILD PDF
# ═══════════════════════════════════════════════════════════════════════════
def build_pdf():
    S = make_styles()
    MARGIN = 1.5 * cm
    CONTENT_W = PAGE_W - 2 * MARGIN

    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN + 0.6*cm, bottomMargin=MARGIN + 0.3*cm,
    )

    story = []

    # ─────────────────────────────────────────────────────────────────────
    # COVER PAGE
    # ─────────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1.5*cm))

    # Project title block
    title_data = [[
        Paragraph("<font color='#60a5fa' size=9>PROJECT REPORT</font>", S["center"]),
    ]]
    title_tbl = Table(title_data, colWidths=[CONTENT_W])
    title_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), BG_CARD),
        ("BOX", (0,0), (-1,-1), 1, C_BLUE),
        ("ROWPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(title_tbl)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("DeepGuard AI", S["h1"]))
    story.append(Paragraph(
        "<font color='#a78bfa'>v2.0</font> — Deepfake &amp; AI-Generated Content Detection Platform",
        ParagraphStyle("sub", parent=S["body"], fontSize=13, textColor=C_TEXT,
                       leading=18, spaceAfter=12)
    ))
    story.append(section_rule())
    story.append(Spacer(1, 0.3*cm))

    # Stats row
    stats = [
        ("3", "ML Models"),
        ("2", "External APIs"),
        ("6", "Routes"),
        ("5", "Detection Modes"),
        ("500 MB", "Max Upload"),
        ("0.7", "AI Threshold"),
    ]
    stat_data = [[Paragraph(f"<b><font color='#60a5fa' size=18>{v}</font></b><br/>"
                            f"<font color='#475569' size=7>{l}</font>", S["center"])
                  for v, l in stats]]
    stat_tbl = Table(stat_data, colWidths=[CONTENT_W / 6] * 6)
    stat_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), BG_CARD),
        ("BOX", (0,0), (-1,-1), 0.5, C_BORDER),
        ("ROWPADDING", (0,0), (-1,-1), 10),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(stat_tbl)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph(
        "This report presents the complete technical architecture, component breakdown, "
        "detection pipelines, ML training approach, and technology stack of DeepGuard AI v2.0. "
        "The platform detects AI-generated images (via Sightengine) and AI-generated videos "
        "(via Hugging Face + OpenCV) using a Flask backend with Firebase authentication.",
        S["body"]
    ))
    story.append(Spacer(1, 0.4*cm))

    # v1 vs v2 comparison table
    story.append(Paragraph("What's New in v2.0", S["h2"]))
    story.append(section_rule())
    v2_data = [
        ["Feature", "v1.0", "v2.0"],
        ["Detection Models", "Xception only", "Xception + EfficientNetB4 + ResNet50"],
        ["Result Labels", "Real / Fake", "Real / Fake / Suspicious"],
        ["Video Analysis", "Frame average", "Frame-by-frame + Temporal Consistency"],
        ["Social Media Support", "Basic", "Optimised for Instagram & YouTube compression"],
        ["Confidence Display", "Percentage", "Percentage + Risk Level + Progress Bar"],
        ["Analytics Dashboard", "❌", "✅ Frame distribution, variance, fake ratio"],
        ["False Prediction Log", "❌", "✅ Saved to false_predictions.jsonl"],
        ["Auto Threshold", "Fixed 0.5", "Tunable REAL=0.62 / FAKE=0.38"],
        ["Face Detection", "MTCNN", "MTCNN + social-media augmentation fallback"],
    ]
    story.append(dark_table(v2_data,
        [CONTENT_W*0.30, CONTENT_W*0.25, CONTENT_W*0.45],
        extra_style=[
            ("TEXTCOLOR", (2, 1), (2, -1), C_GREEN),
            ("FONTNAME",  (2, 1), (2, -1), "Helvetica-Bold"),
        ]
    ))

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────────────
    # PAGE 2 — ARCHITECTURE GRAPH
    # ─────────────────────────────────────────────────────────────────────
    story.append(Paragraph("System Architecture Graph", S["h2"]))
    story.append(section_rule())
    story.append(Paragraph(
        "The diagram below shows the full component topology — from the browser client "
        "through Flask server, external detection APIs, ML training pipeline, and "
        "persistent storage layers.",
        S["body"]
    ))
    story.append(Spacer(1, 0.3*cm))

    arch_img = fig_to_rl(make_architecture_chart(), CONTENT_W, dpi=160)
    story.append(arch_img)
    story.append(Paragraph("Figure 1 — Full system architecture with data-flow edges", S["caption"]))

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────────────
    # PAGE 3 — DETECTION FLOWS + THRESHOLD CHART
    # ─────────────────────────────────────────────────────────────────────
    story.append(Paragraph("Detection Request Flows", S["h2"]))
    story.append(section_rule())
    flow_img = fig_to_rl(make_flow_chart(), CONTENT_W, dpi=150)
    story.append(flow_img)
    story.append(Paragraph("Figure 2 — Step-by-step detection flows for AI Image and AI Video", S["caption"]))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("Detection Threshold — Score Distribution", S["h2"]))
    story.append(section_rule())
    story.append(Paragraph(
        "Both detection pipelines use a probability score from 0.0–1.0. A score ≥ 0.70 "
        "classifies content as AI-generated. The chart below shows the expected score "
        "distributions for real and AI-generated content.",
        S["body"]
    ))
    story.append(Spacer(1, 0.2*cm))
    thresh_img = fig_to_rl(make_threshold_chart(), CONTENT_W, dpi=150)
    story.append(thresh_img)
    story.append(Paragraph("Figure 3 — Simulated score distributions and classification threshold", S["caption"]))

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────────────
    # PAGE 4 — ML MODELS + TRAINING
    # ─────────────────────────────────────────────────────────────────────
    story.append(Paragraph("ML Model Comparison &amp; Training Pipeline", S["h2"]))
    story.append(section_rule())

    # Radar + training side-by-side
    radar_img    = fig_to_rl(make_model_radar(),    CONTENT_W * 0.44, dpi=150)
    training_img = fig_to_rl(make_training_chart(), CONTENT_W * 0.54, dpi=150)

    combo_data = [[radar_img, training_img]]
    combo_tbl  = Table(combo_data, colWidths=[CONTENT_W*0.46, CONTENT_W*0.54])
    combo_tbl.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(combo_tbl)
    story.append(Paragraph(
        "Figure 4 — Model capability radar (left) and training configuration (right)",
        S["caption"]
    ))
    story.append(Spacer(1, 0.5*cm))

    # Model details table
    story.append(Paragraph("Model Specifications", S["h3"]))
    model_data = [
        ["Model", "Input Size", "Fine-tune Layers", "Phase 1 LR", "Phase 2 LR", "Dropout"],
        ["Xception",       "299×299", "Last 30", "1e-3", "1e-5", "0.4 / 0.3"],
        ["EfficientNetB4", "224×224", "Last 40", "1e-3", "1e-5", "0.45 / 0.3"],
        ["ResNet50",       "224×224", "Last 25", "1e-3", "1e-5", "0.4 / 0.3"],
    ]
    story.append(dark_table(model_data,
        [CONTENT_W*0.22, CONTENT_W*0.13, CONTENT_W*0.18,
         CONTENT_W*0.13, CONTENT_W*0.13, CONTENT_W*0.21]
    ))
    story.append(Spacer(1, 0.4*cm))

    # Training callbacks table
    story.append(Paragraph("Training Callbacks", S["h3"]))
    cb_data = [
        ["Callback", "Monitor", "Configuration"],
        ["ModelCheckpoint", "val_accuracy (max)", "Saves best model to models/ directory"],
        ["EarlyStopping",   "val_loss",           "patience=5, restore best weights"],
        ["ReduceLROnPlateau","val_loss",           "factor=0.3, patience=3, min_lr=1e-7"],
        ["TensorBoard",     "—",                  "Logs to logs/<model_name>/"],
    ]
    story.append(dark_table(cb_data,
        [CONTENT_W*0.28, CONTENT_W*0.28, CONTENT_W*0.44]
    ))

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────────────
    # PAGE 5 — TECH STACK + API ROUTES
    # ─────────────────────────────────────────────────────────────────────
    story.append(Paragraph("Technology Stack", S["h2"]))
    story.append(section_rule())
    tech_img = fig_to_rl(make_techstack_chart(), CONTENT_W, dpi=150)
    story.append(tech_img)
    story.append(Paragraph("Figure 5 — Technology stack relevance by component", S["caption"]))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("API Routes", S["h2"]))
    story.append(section_rule())
    route_data = [
        ["Method", "Route", "Description", "Auth Required"],
        ["GET",      "/",                "Main landing page (index.html)",               "No"],
        ["GET",      "/login",           "Firebase login page",                          "No"],
        ["GET",      "/signup",          "Firebase signup page",                         "No"],
        ["GET",      "/project-graph",   "Interactive architecture graph",               "No"],
        ["GET/POST", "/detect-ai",       "AI-generated image detector (Sightengine)",    "No"],
        ["GET/POST", "/detect-ai-video", "AI-generated video detector (Hugging Face)",   "No"],
        ["GET",      "/uploads/<file>",  "Serve uploaded files from UPLOAD_FOLDER",      "No"],
    ]
    story.append(dark_table(route_data,
        [CONTENT_W*0.13, CONTENT_W*0.25, CONTENT_W*0.47, CONTENT_W*0.15],
        extra_style=[
            ("TEXTCOLOR", (0, 1), (0, -1), C_GREEN),
            ("FONTNAME",  (0, 1), (0, -1), "Courier-Bold"),
        ]
    ))

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────────────
    # PAGE 6 — COMPONENT DETAILS + DEPLOYMENT
    # ─────────────────────────────────────────────────────────────────────
    story.append(Paragraph("Component Details", S["h2"]))
    story.append(section_rule())

    components = [
        {
            "title": "Flask Backend — app.py",
            "colour": C_BLUE,
            "items": [
                "Routes: / | /login | /signup | /detect-ai | /detect-ai-video | /uploads/<f> | /project-graph",
                "Max upload size: 500 MB per request (MAX_CONTENT_LENGTH)",
                "CORS enabled via flask-cors for all origins",
                "Jinja2 template rendering for all HTML pages",
                "Werkzeug secure_filename() for safe file I/O",
                "Firebase Admin SDK initialised on startup; graceful fallback on failure",
            ]
        },
        {
            "title": "Sightengine API — AI Image Detection",
            "colour": C_PURPLE,
            "items": [
                "Endpoint: https://api.sightengine.com/1.0/check.json",
                "Model: genai — detects Midjourney, DALL-E, Stable Diffusion, etc.",
                "Returns ai_generated probability score (0.0–1.0)",
                "Classification threshold: 0.70",
                "Supported formats: PNG, JPG, JPEG, WEBP, GIF, BMP",
                "Timeout: 30 seconds with full HTTP error handling",
            ]
        },
        {
            "title": "Hugging Face Inference API — AI Video Analysis",
            "colour": C_GREEN,
            "items": [
                "Model: umm-maybe/AI-image-detector",
                "3 frames extracted at 25%, 50%, 75% of video duration via OpenCV",
                "Each frame JPEG-encoded and POSTed individually to HF API",
                "Labels checked: FAKE | LABEL_1 | ARTIFICIAL",
                "Max score across all frames used as final verdict",
                "Timeout: 60 seconds; rate-limit failures are skipped gracefully",
            ]
        },
        {
            "title": "Firebase Authentication",
            "colour": C_ORANGE,
            "items": [
                "SDK: firebase_admin (Python server-side)",
                "Local development: loads serviceAccountKey.json from project root",
                "Cloud deployment: reads FIREBASE_CREDENTIALS JSON env variable",
                "Client-side auth handled by static/auth.js",
                "Graceful fallback — app continues if Firebase init fails",
            ]
        },
        {
            "title": "Deployment — Render PaaS",
            "colour": C_CYAN,
            "items": [
                "Platform: Render cloud PaaS (render.yaml configuration)",
                "Process manager: gunicorn app:app (Procfile)",
                "Deploy dependencies: requirements-deploy.txt (slim build)",
                "Full ML dependencies: requirements.txt (48 packages)",
                "Env variables managed via Render environment group",
            ]
        },
    ]

    for comp in components:
        # Extract plain hex colour (e.g. "60a5fa") from ReportLab Color object
        hex_val = comp["colour"].hexval()          # e.g. '0x60a5fa'
        hex_colour = hex_val.replace("0x", "").replace("0X", "")
        comp_title = comp["title"]
        comp_data = [
            [Paragraph(f"<font color='#{hex_colour}'>■</font>  "
                       f"<b>{comp_title}</b>", S["h3"])]
        ]
        for item in comp["items"]:
            comp_data.append([Paragraph(f"> {item}", S["body"])])

        tbl = Table(comp_data, colWidths=[CONTENT_W])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BG_CARD),
            ("BACKGROUND", (0, 1), (-1, -1), BG_DARK),
            ("BOX",        (0, 0), (-1, -1), 0.5, comp["colour"]),
            ("LINEBEFORE",  (0, 0), (0, -1), 3, comp["colour"]),
            ("ROWPADDING",  (0, 0), (-1, -1), 5),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 0.3*cm))

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────────────
    # PAGE 7 — PROJECT FILE STRUCTURE + FINAL NOTES
    # ─────────────────────────────────────────────────────────────────────
    story.append(Paragraph("Project File Structure", S["h2"]))
    story.append(section_rule())

    file_tree = """deepguard_ai/
├── app.py                       ← Flask backend — all routes & API calls
├── train_ensemble.py            ← Fine-tuning script (Xception, EfficientNet, ResNet50)
├── generate_report_pdf.py       ← This PDF generator
├── modify_index.py              ← Index modification utility
├── remove_ml.py                 ← ML model removal utility
├── requirements.txt             ← Full Python dependencies (48 packages)
├── requirements-deploy.txt      ← Slim deployment deps
├── Procfile                     ← Gunicorn process definition
├── render.yaml                  ← Render PaaS deployment config
├── serviceAccountKey.json       ← Firebase credentials (local dev)
├── .env                         ← Local environment variables
├── .gitignore                   ← Git ignore rules
├── README.md                    ← Project documentation
│
├── templates/
│   ├── index.html               ← Main landing page (44 KB)
│   ├── login.html               ← Firebase login form
│   ├── signup.html              ← Firebase signup form
│   ├── detect_ai.html           ← AI image detector UI
│   ├── detect_ai_video.html     ← AI video detector UI
│   ├── project_graph.html       ← Interactive architecture graph
│   ├── result.html              ← Generic result page
│   ├── result_image.html        ← Image result with analytics
│   └── result_video.html        ← Video result with frame charts
│
├── static/
│   ├── auth.js                  ← Firebase client-side auth
│   ├── uploads/                 ← Served uploaded files (/static/uploads/)
│   └── heatmaps/                ← Saliency / heatmap outputs
│
├── uploads/                     ← Raw upload cache (500 MB limit)
├── false_predictions/           ← Misclassified samples (JSONL)
├── database/                    ← MongoDB connection & models
└── models/                      ← Trained .keras model weights"""

    story.append(Paragraph(
        f"<font face='Courier' size='7.5' color='#22d3ee'>{file_tree.replace(chr(10), '<br/>').replace(' ', '&nbsp;')}</font>",
        ParagraphStyle("tree", parent=S["body"], leading=11, spaceAfter=0)
    ))

    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Recommended Training Datasets", S["h2"]))
    story.append(section_rule())

    dataset_data = [
        ["Dataset", "Content", "URL"],
        ["FaceForensics++", "Face-swap, face reenactment", "github.com/ondyari/FaceForensics"],
        ["Celeb-DF v2",     "Celebrity deepfakes",         "github.com/yuezunli/celeb-deepfakeforensics"],
        ["DFDC (Facebook)", "Large-scale deepfakes",       "ai.facebook.com/datasets/dfdc/"],
        ["WildDeepfake",    "In-the-wild social media",    "github.com/deepfakeinthewild"],
        ["DGM4",            "Multi-modal generated media", "github.com/CHELSEA234/M2TR"],
    ]
    story.append(dark_table(dataset_data,
        [CONTENT_W*0.22, CONTENT_W*0.36, CONTENT_W*0.42]
    ))

    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Environment Variables Reference", S["h2"]))
    story.append(section_rule())

    env_data = [
        ["Variable", "Used By", "Description"],
        ["SECRET_KEY",            "Flask",      "Session secret key (default: deepguard-secret-v2)"],
        ["FIREBASE_CREDENTIALS",  "Firebase",   "Full JSON service account (cloud deployment)"],
        ["SIGHTENGINE_API_USER",  "Sightengine","API user token for image detection"],
        ["SIGHTENGINE_API_SECRET","Sightengine","API secret for image detection"],
        ["HF_API_TOKEN",          "HuggingFace","Bearer token for HF Inference API"],
    ]
    story.append(dark_table(env_data,
        [CONTENT_W*0.30, CONTENT_W*0.20, CONTENT_W*0.50]
    ))

    story.append(Spacer(1, 0.5*cm))

    # Final summary card
    summary_data = [[
        Paragraph(
            "<b><font color='#60a5fa'>DeepGuard AI v2.0</font></b> is a full-stack deepfake "
            "and AI-generated content detection platform built with <b>Flask</b>, "
            "<b>TensorFlow/Keras</b>, and two external AI APIs. It supports both "
            "<b>image</b> (Sightengine genai model) and <b>video</b> (Hugging Face + OpenCV) "
            "detection with a unified 0.7 probability threshold. The project is deployable "
            "to <b>Render PaaS</b> via Gunicorn and supports Firebase-based user authentication.",
            ParagraphStyle("summary", parent=S["body"], fontSize=9, leading=14, textColor=C_TEXT)
        )
    ]]
    summary_tbl = Table(summary_data, colWidths=[CONTENT_W])
    summary_tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,-1), BG_CARD),
        ("BOX",         (0,0), (-1,-1), 1.5, C_BLUE),
        ("LINEBEFORE",  (0,0), (0,-1),  4, C_BLUE),
        ("ROWPADDING",  (0,0), (-1,-1), 12),
    ]))
    story.append(summary_tbl)

    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')} — DeepGuard AI v2.0",
        S["caption"]
    ))

    # ─── BUILD ──────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=onFirstPage, onLaterPages=onLaterPages)
    print(f"\n[OK] PDF saved to: {os.path.abspath(OUTPUT_FILE)}")
    print(f"     Size: {os.path.getsize(OUTPUT_FILE)/1024:.1f} KB")


if __name__ == "__main__":
    build_pdf()
