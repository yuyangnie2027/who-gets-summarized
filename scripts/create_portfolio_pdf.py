#!/usr/bin/env python3
"""Build the submission PDF for "Who Gets Summarized?" by Yuyang Nie."""

from __future__ import annotations

import subprocess
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, NameObject
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT.parent / "pdf" / "Who Gets Summarized Portfolio Yuyang Nie.pdf"
TMP = ROOT / "tmp" / "pdf"
TMP_PDF = TMP / "portfolio-source.pdf"
SOURCE_PDF = ROOT / "tmp" / "source" / "cm20240131-translate-e.pdf"
SOURCE_IMAGE = TMP / "legco-page-49.png"

PAGE_W, PAGE_H = landscape(A4)
M = 44

PAPER = HexColor("#F5F7F9")
PAPER_DEEP = HexColor("#E8EDF2")
WHITE = HexColor("#FFFFFF")
INK = HexColor("#172231")
MUTED = HexColor("#5E6977")
RULE = HexColor("#98A4B1")
BLUE = HexColor("#2B527C")
BLUE_SOFT = HexColor("#DBE6F0")
ACCENT = HexColor("#8F4554")
ACCENT_SOFT = HexColor("#EADDE1")

# One type family throughout. Avenir Next adds a quieter editorial character
# while retaining the clarity needed for data-heavy pages.
AVENIR_PATH = Path("/System/Library/Fonts/Avenir Next.ttc")
if AVENIR_PATH.exists():
    pdfmetrics.registerFont(TTFont("AvenirNext-Regular", str(AVENIR_PATH), subfontIndex=7))
    pdfmetrics.registerFont(TTFont("AvenirNext-DemiBold", str(AVENIR_PATH), subfontIndex=2))
    FONT = "AvenirNext-Regular"
    FONT_B = "AvenirNext-DemiBold"
else:
    FONT = "Helvetica"
    FONT_B = "Helvetica-Bold"

PUBLIC_URL = "https://yuyangnie2027.github.io/who-gets-summarized/"
PUBLIC_DISPLAY = "yuyangnie2027.github.io/\nwho-gets-summarized/"
REPO_URL = "https://github.com/yuyangnie2027/who-gets-summarized"
REPO_DISPLAY = "github.com/yuyangnie2027/\nwho-gets-summarized"
SOURCE_URL = "https://www.legco.gov.hk/yr2024/english/counmtg/hansard/cm20240131-translate-e.pdf#nameddest=orq05"
API_URL = "https://www.legco.gov.hk/en/open-legco/open-data/hansard-database.html"
CHECKSUM = "2aa29c311ce071cc196fcf8046345bcfbd93515f541af38af15fea53301a6f0d"

TOPICS = [
    ("STR", "Strategy"), ("INF", "Infrastructure"), ("LAB", "Work and talent"),
    ("REG", "Law and regulation"), ("APP", "Public applications"),
    ("SME", "SME adoption"), ("DAT", "Data governance"),
    ("SAF", "Safety and deepfakes"),
]

TURNS = [
    dict(id="T01", speaker="Duncan Chiu", role="Member", page="49-50", words=293, topics=["STR", "INF", "LAB", "REG", "SME"], summary="Requests an overall AI strategy, a review timetable and support for smaller firms."),
    dict(id="T02", speaker="Secretary for I&T", role="Government", page="50-52", words=773, topics=["STR", "INF", "LAB", "REG", "APP", "SME", "DAT"], summary="Sets out existing plans, safeguards, infrastructure, talent schemes and subsidies."),
    dict(id="T03", speaker="Duncan Chiu", role="Member", page="52-53", words=282, topics=["LAB", "APP", "STR"], summary="Asks departments to audit tasks that AI may change and plan staff redeployment."),
    dict(id="T04", speaker="Secretary for I&T", role="Government", page="53-54", words=265, topics=["LAB", "APP", "INF"], summary="Cites manpower projections and AI-supported public-service initiatives."),
    dict(id="T05", speaker="Doreen Kong", role="Member", page="54", words=131, topics=["REG", "SAF"], summary="Requests legal parameters and a legislative timetable."),
    dict(id="T06", speaker="Secretary for I&T", role="Government", page="54-55", words=289, topics=["REG", "SAF", "STR"], summary="Argues that statute may lag technology and cites current legal frameworks."),
    dict(id="T07", speaker="Shang Hailong", role="Member", page="55", words=269, topics=["APP", "STR", "INF"], summary="Asks when government-created AI application scenarios will be implemented."),
    dict(id="T08", speaker="Secretary for I&T", role="Government", page="55-56", words=312, topics=["APP", "INF", "STR"], summary="Describes ecosystem groundwork and speech-recognition work for 1823."),
    dict(id="T09", speaker="Sunny Tan", role="Member", page="56-57", words=94, topics=["SME", "LAB", "APP"], summary="Asks how SMEs and traditional industries can join AI transformation."),
    dict(id="T10", speaker="Secretary for I&T", role="Government", page="57", words=181, topics=["SME", "APP", "LAB"], summary="Points to voucher and matching-fund schemes for digital adoption."),
    dict(id="T11", speaker="Chan Chun-ying", role="Member", page="57-58", words=67, topics=["DAT", "INF"], summary="Asks whether a city-wide data park could support AI development."),
    dict(id="T12", speaker="Secretary for I&T", role="Government", page="57-58", words=196, topics=["DAT", "INF", "STR", "REG"], summary="Discusses computing, data, talent, data flows and institutional coordination."),
    dict(id="T13", speaker="Nixie Lam", role="Member", page="58", words=118, topics=["SAF", "REG"], summary="Asks for a timetable for AI legislation, especially on deepfakes."),
    dict(id="T14", speaker="Secretary for I&T", role="Government", page="58-59", words=193, topics=["SAF", "REG", "STR"], summary="Calls for regulatory balance but gives no legislative timetable."),
]

SELECTED = {"T01", "T02", "T07", "T09", "T11", "T13"}
STABILITY = {
    "T01": 1.0, "T02": 1.0, "T07": 1.0, "T09": 1.0, "T13": 1.0,
    "T11": 0.605, "T05": 0.395, "T03": 0.0, "T04": 0.0, "T06": 0.0,
    "T08": 0.0, "T10": 0.0, "T12": 0.0, "T14": 0.0,
}


def wrap(text: str, width: float, font: str, size: float) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        line = words[0]
        for word in words[1:]:
            candidate = f"{line} {word}"
            if stringWidth(candidate, font, size) <= width:
                line = candidate
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def text_block(c, text: str, x: float, y: float, w: float, size: float = 11.5,
               leading: float | None = None, font: str = FONT, color=INK,
               max_lines: int | None = None) -> float:
    leading = leading or size * 1.35
    lines = wrap(text, w, font, size)
    if max_lines is not None:
        lines = lines[:max_lines]
    c.setFillColor(color)
    c.setFont(font, size)
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def label(c, text: str, x: float, y: float, color=BLUE, size: float = 8.5):
    c.setFillColor(color)
    c.setFont(FONT_B, size)
    c.drawString(x, y, text.upper())


def page_base(c, page: int, section: str):
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setStrokeColor(RULE)
    c.setLineWidth(0.7)
    c.line(M, PAGE_H - 31, PAGE_W - M, PAGE_H - 31)
    c.line(M, 28, PAGE_W - M, 28)
    c.setFillColor(MUTED)
    c.setFont(FONT_B, 7.8)
    c.drawString(M, PAGE_H - 22, f"WHO GETS SUMMARIZED? / {section.upper()}")
    c.drawRightString(PAGE_W - M, PAGE_H - 22, "YUYANG NIE / 2026")
    c.setFont(FONT, 7.5)
    c.drawString(M, 17, "HKBU AI AND DIGITAL MEDIA PORTFOLIO")
    c.drawRightString(PAGE_W - M, 17, f"{page:02d}")


def heading(c, eyebrow: str, title: str, subtitle: str | None = None, y: float = PAGE_H - 72):
    label(c, eyebrow, M, y)
    y -= 31
    y = text_block(c, title, M, y, PAGE_W - 2 * M, 27, 30, FONT_B, INK)
    if subtitle:
        y -= 6
        y = text_block(c, subtitle, M, y, PAGE_W - 2 * M, 11.5, 15, FONT, MUTED)
    return y


def card(c, x: float, y: float, w: float, h: float, fill=WHITE, stroke=RULE):
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(0.8)
    c.rect(x, y, w, h, fill=1, stroke=1)


def metric(c, x: float, y: float, w: float, value: str, name: str, accent=BLUE):
    card(c, x, y, w, 72, WHITE, RULE)
    c.setFillColor(accent)
    c.rect(x, y, 5, 72, fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont(FONT_B, 24)
    c.drawString(x + 16, y + 34, value)
    c.setFillColor(MUTED)
    c.setFont(FONT_B, 8.5)
    c.drawString(x + 16, y + 16, name.upper())


def draw_qr(c, url: str, x: float, y: float, size: float):
    qr = QrCodeWidget(url)
    x0, y0, x1, y1 = qr.getBounds()
    scale = size / (x1 - x0)
    c.setFillColor(WHITE)
    c.rect(x, y, size, size, fill=1, stroke=0)
    for shape in qr.draw().contents:
        if getattr(shape, "fillColor", None) is None:
            continue
        c.setFillColor(shape.fillColor)
        c.rect(
            x + (shape.x - x0) * scale,
            y + (shape.y - y0) * scale,
            shape.width * scale,
            shape.height * scale,
            fill=1,
            stroke=0,
        )


def ensure_source_image() -> Path | None:
    if SOURCE_IMAGE.exists():
        return SOURCE_IMAGE
    if not SOURCE_PDF.exists():
        return None
    TMP.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "pdftoppm", "-f", "49", "-l", "49", "-singlefile", "-png", "-r", "150",
        str(SOURCE_PDF), str(SOURCE_IMAGE.with_suffix("")),
    ], check=True)
    return SOURCE_IMAGE


def cover(c):
    page_base(c, 1, "Overview")
    label(c, "Interactive research prototype", M, PAGE_H - 62, ACCENT, 9)
    c.setFillColor(INK)
    c.setFont(FONT_B, 41)
    c.drawString(M, PAGE_H - 117, "WHO GETS")
    c.drawString(M, PAGE_H - 160, "SUMMARIZED?")
    text_block(c, "An interactive audit of how a 3,463-word public record becomes a six-turn policy brief.", M, PAGE_H - 196, 455, 15, 20, FONT, INK)
    card(c, M, 191, 455, 103, WHITE, BLUE)
    label(c, "What it is", M + 18, 270)
    text_block(c, "A browser-based editorial instrument. It lets a reviewer change selection priorities, compare alternative summaries and inspect every omission before publication.", M + 18, 247, 418, 12, 16, FONT, INK)
    gap = 10
    mw = (455 - gap * 3) / 4
    for i, (value, name) in enumerate([("3,463", "source words"), ("14", "turns"), ("6", "retained"), ("8/8", "topics")]):
        metric(c, M + i * (mw + gap), 91, mw, value, name, BLUE if i != 2 else ACCENT)
    qx = 566
    card(c, qx, 91, PAGE_W - M - qx, 371, WHITE, RULE)
    label(c, "Project mechanism", qx + 24, 432, ACCENT, 9)
    stages = [
        ("01", "VERIFIED INPUT", "Official record / 3,463 words / 14 turns"),
        ("02", "EDITORIAL CONTROL", "Three presets / eight topic priorities"),
        ("03", "AUDITABLE OUTPUT", "Coverage / omissions / sensitivity"),
    ]
    yy = 365
    for number, title, detail in stages:
        c.setFillColor(PAPER_DEEP); c.rect(qx + 24, yy - 34, 184, 58, fill=1, stroke=0)
        c.setFillColor(ACCENT if number == "02" else BLUE); c.setFont(FONT_B, 20); c.drawString(qx + 35, yy, number)
        c.setFillColor(INK); c.setFont(FONT_B, 9); c.drawString(qx + 79, yy + 3, title)
        text_block(c, detail, qx + 79, yy - 15, 118, 8.5, 11, FONT, MUTED)
        yy -= 76
    draw_qr(c, PUBLIC_URL, qx + 24, 103, 68)
    label(c, "Open public demo", qx + 104, 158, BLUE, 7.5)
    text_block(c, PUBLIC_DISPLAY, qx + 104, 139, 104, 7.2, 8.6, FONT_B, INK)
    c.linkURL(PUBLIC_URL, (qx + 20, 99, PAGE_W - M - 10, 174), relative=0)
    c.setFillColor(ACCENT)
    c.rect(qx, 91, 7, 371, fill=1, stroke=0)


def one_screen(c):
    page_base(c, 2, "Project in one screen")
    heading(c, "The whole project", "One record. Three selection rules. Every omission visible.", "A transparent ranking engine selects and audits documented turns from one official record.")
    col_w = 222
    xs = [M, M + 250, M + 500]
    for x, t in zip(xs, ["1 / INPUT", "2 / PROCESS", "3 / OUTPUT"]):
        card(c, x, 105, col_w, 315, WHITE, RULE)
        label(c, t, x + 18, 392, BLUE if t != "2 / PROCESS" else ACCENT)
    text_block(c, "Official Legislative Council record", xs[0] + 18, 355, 185, 16, 20, FONT_B)
    text_block(c, "31 January 2024\nPrinted pages 49-59\n7 speakers / 14 turns\n3,463 English words", xs[0] + 18, 291, 185, 11.5, 20, FONT)
    c.setFillColor(BLUE_SOFT); c.rect(xs[0] + 18, 131, 186, 92, fill=1, stroke=0)
    c.setFillColor(BLUE); c.rect(xs[0] + 18, 131, 119, 92, fill=1, stroke=0)
    c.setFillColor(WHITE); c.setFont(FONT_B, 18); c.drawString(xs[0] + 34, 171, "63.8%")
    c.setFont(FONT_B, 8); c.drawString(xs[0] + 34, 154, "GOVERNMENT WORD SHARE")
    sy = 349
    for code, title in [("A", "Verify source"), ("B", "Segment turns"), ("C", "Rank with MMR"), ("D", "Audit result")]:
        c.setFillColor(ACCENT); c.circle(xs[1] + 35, sy + 4, 13, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont(FONT_B, 9); c.drawCentredString(xs[1] + 35, sy + 1, code)
        c.setFillColor(INK); c.setFont(FONT_B, 11); c.drawString(xs[1] + 58, sy, title)
        if sy > 180:
            c.setStrokeColor(RULE); c.line(xs[1] + 35, sy - 12, xs[1] + 35, sy - 47)
        sy -= 63
    text_block(c, "TF-IDF similarity + speaker novelty + topic coverage + redundancy penalty", xs[1] + 18, 136, 185, 10.5, 14, FONT, MUTED)
    text_block(c, "A traceable six-turn brief", xs[2] + 18, 355, 185, 16, 20, FONT_B)
    for i, tid in enumerate(["T01", "T02", "T07", "T09", "T11", "T13"]):
        yy = 318 - i * 34
        c.setFillColor(BLUE_SOFT if i < 2 else WHITE); c.setStrokeColor(RULE); c.rect(xs[2] + 18, yy, 186, 25, fill=1, stroke=1)
        c.setFillColor(BLUE if i < 2 else INK); c.setFont(FONT_B, 9.5)
        turn = next(t for t in TURNS if t["id"] == tid)
        c.drawString(xs[2] + 27, yy + 8, f"{tid}  {turn['speaker']}")
    text_block(c, "Coverage: 6/7 speakers, 8/8 topics\nRepresentation gap: 0.016", xs[2] + 18, 137, 185, 10.5, 16, FONT_B, ACCENT)


def use_case(c):
    page_base(c, 3, "Purpose and audience")
    heading(c, "What problem does it solve?", "A reviewer needs to see the editorial choice before a summary becomes the record.", "The prototype makes every retained and omitted turn visible when a long, attributable public document is compressed.")

    cards = [
        ("EDITOR", "Compare several defensible briefs before publication.", "See whether a concise version over-rewards one institution or repeats the same claim."),
        ("RESEARCHER", "Trace each retained statement back to the official pages.", "Inspect source identity, turn boundaries, topic labels and the full omission ledger."),
        ("CIVIC-MEDIA TEAM", "Explain selection choices to readers and collaborators.", "Use coverage, divergence and stability as review prompts rather than invisible scores."),
    ]
    x = M
    for role, need, action in cards:
        card(c, x, 232, 230, 188, WHITE, RULE)
        label(c, role, x + 17, 394, ACCENT)
        text_block(c, need, x + 17, 360, 196, 14, 18, FONT_B, INK)
        text_block(c, action, x + 17, 292, 196, 10.8, 15, FONT, MUTED)
        x += 247

    label(c, "Review workflow", M, 194, BLUE)
    stages = [
        ("01", "Load the verified record"),
        ("02", "Set an editorial objective"),
        ("03", "Compare selection and omissions"),
        ("04", "Publish with an audit trail"),
    ]
    x = M
    for i, (number, title) in enumerate(stages):
        c.setFillColor(BLUE if i < 3 else ACCENT)
        c.circle(x + 14, 148, 14, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont(FONT_B, 8); c.drawCentredString(x + 14, 145, number)
        text_block(c, title, x + 36, 154, 126, 10.5, 14, FONT_B, INK)
        if i < 3:
            c.setStrokeColor(RULE); c.setLineWidth(1); c.line(x + 165, 148, x + 181, 148)
        x += 184
    card(c, M, 62, PAGE_W - 2 * M, 56, PAPER_DEEP, RULE)
    label(c, "Design position", M + 16, 95, ACCENT)
    text_block(c, "Editorial judgement becomes visible, comparable and reversible through explicit controls and source-linked results.", M + 135, 96, PAGE_W - 2 * M - 151, 11.5, 15, FONT_B, INK)


def primary_source(c):
    page_base(c, 4, "Primary source")
    heading(c, "Real data", "The work begins with a verifiable public record.", "The visual below reproduces the official English record, with its page location and checksum preserved.")
    image_path = ensure_source_image()
    ix, iy, iw, ih = M, 69, 286, 404
    if image_path:
        c.drawImage(ImageReader(str(image_path)), ix, iy, iw, ih, preserveAspectRatio=True, anchor="c", mask="auto")
        c.setStrokeColor(ACCENT); c.setLineWidth(2); c.rect(ix + 24, iy + 207, 218, 94, fill=0, stroke=1)
        label(c, "Question starts here", ix + 30, iy + 310, ACCENT, 8)
    else:
        card(c, ix, iy, iw, ih, WHITE, RULE)
        text_block(c, "Run npm run fetch:source to download and verify the official source PDF.", ix + 25, iy + 230, iw - 50, 14, 19, FONT_B)
    rx = 366
    card(c, rx, 271, PAGE_W - M - rx, 202, WHITE, BLUE)
    label(c, "Source dossier", rx + 22, 445)
    text_block(c, "Official Record of Proceedings", rx + 22, 416, 392, 19, 23, FONT_B)
    text_block(c, "Oral question: “Developing artificial intelligence”\nMeeting: 31 January 2024\nPrinted pages: 49-59\nRundown ID: 1291567 / Hansard ID: 6481\nRetrieved and verified: 3 November 2026", rx + 22, 379, 392, 11.5, 21, FONT)
    card(c, rx, 69, PAGE_W - M - rx, 181, PAPER_DEEP, RULE)
    label(c, "Integrity record", rx + 22, 224, ACCENT)
    text_block(c, "The source script resolves the LegCo OData identity, downloads the PDF and checks its SHA-256 hash before analysis.", rx + 22, 196, 390, 11.5, 16, FONT)
    label(c, "SHA-256", rx + 22, 135, BLUE)
    text_block(c, CHECKSUM, rx + 22, 113, 390, 9, 12, FONT, MUTED)
    c.setFont(FONT_B, 9); c.setFillColor(BLUE); c.drawString(rx + 22, 84, "OFFICIAL RECORD")
    c.linkURL(SOURCE_URL, (rx + 18, 69, rx + 165, 104), relative=0)
    c.drawString(rx + 190, 84, "OPEN-DATA DOCUMENTATION")
    c.linkURL(API_URL, (rx + 185, 69, PAGE_W - M, 104), relative=0)


def record_structure(c):
    page_base(c, 5, "Record structure")
    heading(c, "Before any summarization, the record is already uneven.", "Answers are expected to be longer than questions. The point is to document that baseline before compression changes it again.")

    label(c, "Word share by institutional role", M, 414, BLUE)
    c.setFillColor(ACCENT_SOFT)
    c.rect(M, 351, PAGE_W - 2 * M, 46, fill=1, stroke=0)
    c.setFillColor(ACCENT)
    c.rect(M, 351, (PAGE_W - 2 * M) * 0.362, 46, fill=1, stroke=0)
    c.setFillColor(BLUE)
    c.rect(M + (PAGE_W - 2 * M) * 0.362, 351, (PAGE_W - 2 * M) * 0.638, 46, fill=1, stroke=0)
    c.setFillColor(WHITE); c.setFont(FONT_B, 10)
    c.drawString(M + 15, 369, "MEMBERS’ QUESTIONS 36.2%")
    c.drawRightString(PAGE_W - M - 15, 369, "GOVERNMENT RESPONSES 63.8%")

    speakers = [
        ("Secretary for I&T", 2209, BLUE), ("Duncan Chiu", 575, ACCENT),
        ("Shang Hailong", 269, ACCENT), ("Doreen Kong", 131, ACCENT),
        ("Nixie Lam", 118, ACCENT), ("Sunny Tan", 94, ACCENT),
        ("Chan Chun-ying", 67, ACCENT),
    ]
    label(c, "Words by speaker", M, 315, BLUE)
    y = 283
    max_words = max(v for _, v, _ in speakers)
    for name, value, color in speakers:
        c.setFillColor(INK); c.setFont(FONT_B, 9.5); c.drawString(M, y + 2, name)
        c.setFillColor(PAPER_DEEP); c.rect(M + 145, y, 420, 14, fill=1, stroke=0)
        c.setFillColor(color); c.rect(M + 145, y, 420 * value / max_words, 14, fill=1, stroke=0)
        c.setFillColor(INK); c.setFont(FONT_B, 9); c.drawRightString(M + 597, y + 2, f"{value:,}")
        y -= 29

    card(c, 657, 122, PAGE_W - M - 657, 179, WHITE, RULE)
    label(c, "Why record this?", 675, 275, ACCENT)
    text_block(c, "A summary can look balanced while reproducing or amplifying the source’s institutional imbalance. The audit therefore reports role share beside topic and speaker coverage.", 675, 245, PAGE_W - M - 693, 11, 15, FONT, INK)
    metric(c, 657, 53, 135, "63.8%", "baseline government share", BLUE)


def corpus_map(c):
    page_base(c, 6, "Corpus map")
    heading(c, "14 documented turns", "The dataset keeps source order, role, length and page anchor.", "Blue rows are retained. Burgundy marks member questions; navy marks government responses.")
    x0, y0 = M, 415
    c.setFont(FONT_B, 8.5); c.setFillColor(MUTED)
    for x, txt in [(x0, "TURN"), (x0 + 45, "SPEAKER"), (x0 + 190, "WORDS"), (x0 + 310, "TOPICS"), (PAGE_W - 93, "PAGE")]: c.drawString(x, y0, txt)
    y = y0 - 22; max_words = max(t["words"] for t in TURNS)
    for t in TURNS:
        selected = t["id"] in SELECTED
        if selected:
            c.setFillColor(BLUE_SOFT); c.rect(x0 - 8, y - 6, PAGE_W - 2 * M + 16, 25, fill=1, stroke=0)
        c.setFillColor(BLUE if t["role"] == "Government" else ACCENT); c.rect(x0, y, 5, 13, fill=1, stroke=0)
        c.setFillColor(INK); c.setFont(FONT_B, 9); c.drawString(x0 + 13, y + 2, t["id"])
        c.setFont(FONT_B if selected else FONT, 9.5); c.drawString(x0 + 45, y + 2, t["speaker"])
        c.setFillColor(PAPER_DEEP); c.rect(x0 + 190, y, 95, 12, fill=1, stroke=0)
        c.setFillColor(BLUE if t["role"] == "Government" else ACCENT); c.rect(x0 + 190, y, 95 * t["words"] / max_words, 12, fill=1, stroke=0)
        c.setFillColor(INK); c.setFont(FONT_B, 8); c.drawRightString(x0 + 302, y + 2, str(t["words"]))
        tx = x0 + 320
        for topic in t["topics"]:
            c.setFillColor(WHITE); c.setStrokeColor(RULE); c.rect(tx, y - 1, 25, 15, fill=1, stroke=1)
            c.setFillColor(MUTED); c.setFont(FONT_B, 7.2); c.drawCentredString(tx + 12.5, y + 3, topic); tx += 29
        c.setFillColor(MUTED); c.setFont(FONT, 8.5); c.drawRightString(PAGE_W - M, y + 2, t["page"])
        y -= 26
    label(c, "Reading the map", M, 42, ACCENT)
    text_block(c, "The longest turn is T02 at 773 words. The balanced brief retains six turns while preserving all eight annotated topics.", M + 110, 42, PAGE_W - 2 * M - 110, 10.5, 13, FONT, MUTED)


def risks(c):
    page_base(c, 7, "Research question")
    heading(c, "Why this matters", "A fluent summary can still distribute attention badly.", "The project treats compression as both a language task and an editorial allocation problem.")
    xs = [M, M + 250, M + 500]
    cards = [
        ("01", "Institutional dominance", "The source already gives government responses 63.8% of all words. A short brief can silently amplify that baseline.", "63.8%", "government word share"),
        ("02", "Question-answer collapse", "Selecting only answers removes the questions that explain why law, work, SMEs, data and deepfakes entered the record.", "6", "supplementary questions"),
        ("03", "Parameter fragility", "A turn may appear essential only because one weight is narrowly tuned. Stability should be reported beside relevance.", "200", "seeded perturbations"),
    ]
    for x, (n, title, body, value, caption) in zip(xs, cards):
        card(c, x, 95, 220, 332, WHITE, RULE)
        c.setFillColor(ACCENT); c.setFont(FONT_B, 30); c.drawString(x + 18, 378, n)
        text_block(c, title, x + 18, 337, 184, 16, 20, FONT_B)
        text_block(c, body, x + 18, 279, 184, 11.5, 16, FONT)
        c.setStrokeColor(RULE); c.line(x + 18, 165, x + 202, 165)
        c.setFillColor(BLUE); c.setFont(FONT_B, 34); c.drawString(x + 18, 120, value)
        c.setFillColor(MUTED); c.setFont(FONT_B, 8.5); c.drawString(x + 18, 103, caption.upper())


def method(c):
    page_base(c, 8, "Method")
    heading(c, "Deterministic selection", "The ranking rule is inspectable, reproducible and diversity-aware.", "Documented turns are ranked with explicit weights, coverage rewards and a TF-IDF redundancy penalty.")
    x = M
    for n, title, body in [("1", "Relevance", "Score topic fit and source specificity."), ("2", "Coverage", "Reward new topics, speakers and roles."), ("3", "Redundancy", "Penalise TF-IDF cosine similarity."), ("4", "Audit", "Report divergence, omissions and stability.")]:
        card(c, x, 303, 168, 120, WHITE, RULE)
        c.setFillColor(ACCENT); c.setFont(FONT_B, 22); c.drawString(x + 15, 388, n)
        c.setFillColor(INK); c.setFont(FONT_B, 13); c.drawString(x + 45, 389, title)
        text_block(c, body, x + 15, 354, 138, 10.5, 14, FONT, MUTED); x += 183
    card(c, M, 183, PAGE_W - 2 * M, 92, INK, INK)
    label(c, "Selection utility", M + 18, 249, BLUE_SOFT)
    c.setFillColor(WHITE); c.setFont(FONT_B, 17); c.drawString(M + 18, 215, "utility = relevance + topic coverage + speaker novelty - redundancy")
    c.setFont(FONT, 10); c.setFillColor(BLUE_SOFT); c.drawString(M + 18, 197, "Candidates are chosen one at a time; the penalty changes after each selection.")
    card(c, M, 69, 455, 92, WHITE, RULE); label(c, "Implemented code", M + 16, 139, ACCENT)
    text_block(c, "const utility = relevance * R + topicCoverage * C + speakerDiversity * S - redundancyPenalty * maxSimilarity;", M + 16, 116, 425, 10.5, 14, FONT_B, INK)
    card(c, 520, 69, PAGE_W - M - 520, 92, PAPER_DEEP, RULE); label(c, "Audit metric", 536, 139, BLUE)
    text_block(c, "Jensen-Shannon divergence compares the full record and selected topic distributions on a bounded symmetric scale.", 536, 116, PAGE_W - M - 552, 10.5, 14, FONT, INK)


def metric_explainer(c):
    page_base(c, 9, "Audit logic")
    heading(c, "A fair summary needs more than one score.", "The interface combines three different questions so a reviewer can see where a concise brief succeeds and where it remains uncertain.")

    panels = [
        ("01", "Relevance", "Does the selected turn match the stated editorial objective?", "TF-IDF topic fit", BLUE),
        ("02", "Representation", "Does the selected topic mix still resemble the complete record?", "Jensen-Shannon divergence", ACCENT),
        ("03", "Stability", "Would a small change in topic weights alter the selected turns?", "200 seeded perturbations", MUTED),
    ]
    x = M
    for number, title, question, measure, color in panels:
        card(c, x, 243, 230, 181, WHITE, color)
        c.setFillColor(color); c.setFont(FONT_B, 26); c.drawString(x + 16, 382, number)
        c.setFillColor(INK); c.setFont(FONT_B, 16); c.drawString(x + 16, 350, title)
        text_block(c, question, x + 16, 317, 198, 11, 15, FONT, INK)
        c.setStrokeColor(RULE); c.line(x + 16, 277, x + 214, 277)
        label(c, measure, x + 16, 258, color, 7.8)
        x += 247

    card(c, M, 86, 460, 129, INK, INK)
    label(c, "Representation gap", M + 18, 189, BLUE_SOFT)
    c.setFillColor(WHITE); c.setFont(FONT_B, 23); c.drawString(M + 18, 153, "JSD(P || Q) = 1/2 KL(P || M) + 1/2 KL(Q || M)")
    text_block(c, "P is the full-record topic distribution; Q is the selected-brief distribution; M is their midpoint. Lower values indicate closer topic distributions and are read beside coverage metrics.", M + 18, 124, 424, 9.8, 13, FONT, BLUE_SOFT)

    card(c, 523, 86, PAGE_W - M - 523, 129, PAPER_DEEP, RULE)
    label(c, "How to read the dashboard", 541, 189, ACCENT)
    text_block(c, "Coverage prevents silent disappearance. Divergence shows distributional movement. Stability reveals dependence on narrow settings. A human reviewer must interpret all three together.", 541, 158, PAGE_W - M - 559, 11, 15, FONT_B, INK)


def interface(c):
    page_base(c, 10, "Interactive interface")
    heading(c, "Working interface", "The research method becomes an interactive audit.", "Choose a preset or adjust eight topic priorities, then inspect the selected brief and omission ledger.")
    sx, sy, sw, sh = M, 77, PAGE_W - 2 * M, 347
    card(c, sx, sy, sw, sh, WHITE, INK)
    c.setFillColor(INK); c.rect(sx, sy + sh - 32, sw, 32, fill=1, stroke=0)
    c.setFillColor(WHITE); c.setFont(FONT_B, 9); c.drawString(sx + 14, sy + sh - 21, "WHO GETS SUMMARIZED? / LIVE AUDIT")
    cx, cy, cw = sx + 16, sy + 18, 190
    c.setFillColor(PAPER_DEEP); c.rect(cx, cy, cw, sh - 66, fill=1, stroke=0)
    label(c, "1 / Choose an objective", cx + 12, sy + sh - 58, ACCENT)
    for i, name in enumerate(["Balanced public record", "Policy and safeguards", "Implementation and access"]):
        yy = sy + sh - 91 - i * 41
        c.setFillColor(BLUE if i == 0 else WHITE); c.setStrokeColor(RULE); c.rect(cx + 10, yy, cw - 20, 31, fill=1, stroke=1)
        c.setFillColor(WHITE if i == 0 else INK); c.setFont(FONT_B, 8); c.drawString(cx + 18, yy + 11, name)
    label(c, "2 / Adjust priorities", cx + 12, sy + sh - 224, ACCENT)
    for i, (code, _) in enumerate(TOPICS[:5]):
        yy = sy + sh - 251 - i * 23
        c.setFillColor(MUTED); c.setFont(FONT_B, 7.5); c.drawString(cx + 12, yy, code)
        c.setFillColor(RULE); c.rect(cx + 42, yy + 1, 105, 5, fill=1, stroke=0)
        c.setFillColor(BLUE); c.rect(cx + 42, yy + 1, 48 + i * 9, 5, fill=1, stroke=0)
    ox = sx + 226
    label(c, "3 / Inspect the result", ox, sy + sh - 58, BLUE)
    c.setFillColor(INK); c.setFont(FONT_B, 16); c.drawString(ox, sy + sh - 87, "Balanced public record")
    for i, (value, name) in enumerate([("6/14", "turns"), ("6/7", "speakers"), ("8/8", "topics"), ("0.016", "gap")]):
        mx = ox + i * 104
        c.setFillColor(BLUE if i < 3 else ACCENT); c.setFont(FONT_B, 15); c.drawString(mx, sy + sh - 122, value)
        c.setFillColor(MUTED); c.setFont(FONT_B, 7); c.drawString(mx, sy + sh - 137, name.upper())
    for i, tid in enumerate(["T01", "T02", "T07", "T09", "T11", "T13"]):
        yy = sy + sh - 175 - i * 30; t = next(item for item in TURNS if item["id"] == tid)
        c.setFillColor(BLUE_SOFT if i % 2 == 0 else PAPER_DEEP); c.rect(ox, yy, sw - 242, 22, fill=1, stroke=0)
        c.setFillColor(INK); c.setFont(FONT_B, 8.2); c.drawString(ox + 9, yy + 7, f"{tid}  {t['speaker']}  /  p. {t['page']}")


def balanced_result(c):
    page_base(c, 11, "Balanced result")
    heading(c, "Selected brief", "Six turns retain all eight annotated topics.", "Every displayed sentence is an author-reviewed paraphrase with its speaker, role and source-page anchor.")
    positions = [(M, 301), (M + 376, 301), (M, 178), (M + 376, 178), (M, 55), (M + 376, 55)]
    for t, (x, y) in zip([t for t in TURNS if t["id"] in SELECTED], positions):
        card(c, x, y, 354, 106, WHITE, BLUE)
        c.setFillColor(BLUE); c.rect(x, y, 7, 106, fill=1, stroke=0)
        c.setFillColor(INK); c.setFont(FONT_B, 10.5); c.drawString(x + 18, y + 81, f"{t['id']}  {t['speaker']}")
        c.setFillColor(MUTED); c.setFont(FONT_B, 8); c.drawRightString(x + 336, y + 81, f"P. {t['page']}")
        text_block(c, t["summary"], x + 18, y + 59, 316, 10.2, 13.5, FONT, INK, 3)
        c.setFillColor(ACCENT); c.setFont(FONT_B, 7); c.drawString(x + 18, y + 12, "AUTHOR’S PARAPHRASE / SOURCE LINKED")


def omission_ledger(c):
    page_base(c, 12, "Omission ledger")
    heading(c, "Omission becomes inspectable data.", "Every turn remains visible with its status, page anchor and short source-linked description.")
    x0, y = M, 400
    c.setFillColor(MUTED); c.setFont(FONT_B, 8)
    for x, txt in [(x0, "STATUS"), (x0 + 65, "TURN / SPEAKER"), (x0 + 236, "SOURCE-LINKED DESCRIPTION"), (PAGE_W - 88, "PAGE")]:
        c.drawString(x, y, txt)
    y -= 22
    for t in TURNS:
        selected = t["id"] in SELECTED
        c.setFillColor(BLUE_SOFT if selected else WHITE)
        c.setStrokeColor(RULE)
        c.rect(x0, y - 4, PAGE_W - 2 * M, 23, fill=1, stroke=1)
        c.setFillColor(BLUE if selected else MUTED)
        c.rect(x0, y - 4, 6, 23, fill=1, stroke=0)
        c.setFont(FONT_B, 7.8)
        c.drawString(x0 + 14, y + 3, "RETAINED" if selected else "OMITTED")
        c.setFillColor(INK); c.setFont(FONT_B, 8.8)
        c.drawString(x0 + 65, y + 3, f"{t['id']}  {t['speaker']}")
        summary = t["summary"]
        if stringWidth(summary, FONT, 8.2) > 430:
            while stringWidth(summary + "...", FONT, 8.2) > 430 and len(summary) > 10:
                summary = summary[:-1]
            summary = summary.rstrip() + "..."
        c.setFillColor(MUTED); c.setFont(FONT, 8.2); c.drawString(x0 + 236, y + 3, summary)
        c.setFillColor(INK); c.setFont(FONT_B, 8); c.drawRightString(PAGE_W - M - 10, y + 3, t["page"])
        y -= 24
    label(c, "Balanced result", M, 38, ACCENT)
    text_block(c, "6 retained / 8 omitted. The ledger keeps the complete source structure available for review.", M + 110, 38, PAGE_W - 2 * M - 110, 10.3, 13, FONT, MUTED)


def representation(c):
    page_base(c, 13, "Representation audit")
    heading(c, "Does the short brief still resemble the full record?", "The topic mix is compared before and after compression; lower divergence indicates a closer distribution.")
    full = [16.3, 17.8, 13.3, 19.2, 12.0, 8.2, 6.0, 7.2]
    brief = [16.4, 17.4, 13.2, 19.0, 12.1, 8.4, 6.6, 6.9]
    x_label, x_bar, y = M, 160, 397
    c.setFont(FONT_B, 8); c.setFillColor(MUTED); c.drawString(x_bar, y + 28, "FULL RECORD"); c.drawString(x_bar + 246, y + 28, "SELECTED BRIEF")
    for (code, name), a, b in zip(TOPICS, full, brief):
        c.setFillColor(INK); c.setFont(FONT_B, 9); c.drawString(x_label, y + 2, code)
        c.setFont(FONT, 9); c.setFillColor(MUTED); c.drawString(x_label + 31, y + 2, name)
        c.setFillColor(PAPER_DEEP); c.rect(x_bar, y, 210, 12, fill=1, stroke=0); c.rect(x_bar + 246, y, 210, 12, fill=1, stroke=0)
        c.setFillColor(MUTED); c.rect(x_bar, y, 210 * a / 22, 12, fill=1, stroke=0)
        c.setFillColor(BLUE); c.rect(x_bar + 246, y, 210 * b / 22, 12, fill=1, stroke=0)
        c.setFillColor(INK); c.setFont(FONT_B, 8); c.drawRightString(x_bar + 235, y + 2, f"{a:.1f}%"); c.drawRightString(x_bar + 481, y + 2, f"{b:.1f}%")
        y -= 36
    metrics = [("6/7", "speakers retained"), ("8/8", "topics retained"), ("46.6%", "source words retained"), ("0.016", "representation gap")]
    mw = (PAGE_W - 2 * M - 30) / 4
    for i, (value, name) in enumerate(metrics): metric(c, M + i * (mw + 10), 55, mw, value, name, ACCENT if i == 3 else BLUE)


def sensitivity(c):
    page_base(c, 14, "Sensitivity")
    heading(c, "A result should reveal how fragile it is.", "Two hundred seeded runs perturb every topic weight within plus or minus 18% and rerun the selector.")
    x0, y, bar_x, bar_w = M, 405, 230, 430
    visible = [t for t in sorted(TURNS, key=lambda item: (-STABILITY[item["id"]], int(item["id"][1:]))) if STABILITY[t["id"]] > 0]
    for t in visible:
        freq = STABILITY[t["id"]]
        c.setFillColor(INK); c.setFont(FONT_B, 8.5); c.drawString(x0, y + 2, t["id"])
        c.setFont(FONT, 8.5); c.drawString(x0 + 32, y + 2, t["speaker"])
        c.setFillColor(PAPER_DEEP); c.rect(bar_x, y, bar_w, 12, fill=1, stroke=0)
        c.setFillColor(BLUE if freq >= 0.6 else ACCENT); c.rect(bar_x, y, bar_w * freq, 12, fill=1, stroke=0)
        c.setFillColor(INK); c.setFont(FONT_B, 8.5); c.drawRightString(PAGE_W - M, y + 2, f"{freq * 100:.1f}%")
        y -= 29
    c.setFillColor(INK); c.setFont(FONT_B, 8.5); c.drawString(x0, y + 2, "0% GROUP")
    c.setFont(FONT, 8.5); c.drawString(x0 + 66, y + 2, "7 turns")
    c.setFillColor(PAPER_DEEP); c.rect(bar_x, y, bar_w, 12, fill=1, stroke=0)
    c.setFillColor(INK); c.setFont(FONT_B, 8.5); c.drawRightString(PAGE_W - M, y + 2, "0.0%")
    card(c, 515, 66, PAGE_W - M - 515, 102, WHITE, RULE); label(c, "Interpretation", 532, 143, ACCENT)
    text_block(c, "Five turns survive every trial. T11 and T05 compete for the sixth position, exposing the brief’s unstable editorial choice.", 532, 119, PAGE_W - M - 550, 10.5, 14, FONT, INK)
    metric(c, M, 66, 190, "88.7%", "mean selection overlap", BLUE); metric(c, M + 202, 66, 190, "200", "deterministic trials", BLUE)


def alternatives(c):
    page_base(c, 15, "Alternative briefs")
    heading(c, "Each short brief reflects an editorial position.", "Three presets make different editorial commitments while keeping the selection rule and omissions inspectable.")
    x = M
    for title, ids, speakers, topics, gap, color in [
        ("Balanced public record", "T01  T02  T07  T09  T11  T13", "6/7", "8/8", "0.016", BLUE),
        ("Policy and safeguards", "T01  T02  T05  T07  T13", "5/7", "8/8", "0.008", ACCENT),
        ("Implementation and access", "T01  T02  T07  T09  T13", "5/7", "8/8", "0.013", MUTED),
    ]:
        card(c, x, 224, 230, 196, WHITE, color); c.setFillColor(color); c.rect(x, 410, 230, 10, fill=1, stroke=0)
        text_block(c, title, x + 16, 383, 198, 14, 18, FONT_B)
        c.setFillColor(MUTED); c.setFont(FONT_B, 8.5); c.drawString(x + 16, 326, ids)
        for i, (value, name) in enumerate([(speakers, "speakers"), (topics, "topics"), (gap, "gap")]):
            mx = x + 16 + i * 70; c.setFillColor(color); c.setFont(FONT_B, 17); c.drawString(mx, 271, value)
            c.setFillColor(MUTED); c.setFont(FONT_B, 7.5); c.drawString(mx, 251, name.upper())
        x += 247
    card(c, M, 65, PAGE_W - 2 * M, 131, PAPER_DEEP, RULE); label(c, "Pareto view", M + 18, 171, BLUE)
    text_block(c, "A candidate stays on the frontier only when no other brief is simultaneously better in relevance, topic fidelity and speaker coverage.", M + 18, 148, 325, 10.5, 14, FONT)
    px, py, pw, ph = 470, 84, 300, 86
    c.setStrokeColor(RULE); c.line(px, py, px, py + ph); c.line(px, py, px + pw, py)
    c.setFillColor(MUTED); c.setFont(FONT_B, 7.5); c.drawString(px, py - 13, "LOWER FIDELITY"); c.drawRightString(px + pw, py - 13, "HIGHER FIDELITY")
    for dx, dy, name, color in [(78, 51, "Balanced", BLUE), (208, 68, "Policy", ACCENT), (163, 34, "Access", MUTED)]:
        c.setFillColor(color); c.circle(px + dx, py + dy, 6, fill=1, stroke=0); c.setFont(FONT_B, 8); c.drawString(px + dx + 9, py + dy - 2, name)


def engineering(c):
    page_base(c, 16, "Code and reflection")
    heading(c, "The mechanism is part of the evidence.", "The repository contains the sourced corpus, deterministic engine, public interface, PDF generator and validation suite.")
    card(c, M, 221, 347, 208, INK, INK); label(c, "Repository map", M + 18, 403, BLUE_SOFT)
    repo = "dist/src/\n  data.js     source record + 14 turns\n  engine.js   TF-IDF, MMR, JSD, stability\n  app.js      interaction + audit rendering\n\nscripts/\n  fetch-source.mjs\n  create_portfolio_pdf.py\n\ndocs/METHODOLOGY.md"
    text_block(c, repo, M + 18, 378, 310, 10, 15, FONT, WHITE)
    card(c, 412, 221, PAGE_W - M - 412, 208, WHITE, RULE); label(c, "Verified engineering", 432, 403, ACCENT)
    y = 372
    for item in ["12 reproducibility checks pass", "Official source checksum verified", "Seeded 200-run stability analysis", "Deterministic browser-based selector", "TF-IDF, JSD and Pareto diagnostics", "Page-level provenance on every turn"]:
        c.setFillColor(BLUE); c.circle(438, y + 3, 3, fill=1, stroke=0)
        c.setFillColor(INK); c.setFont(FONT_B, 10.5); c.drawString(451, y, item); y -= 27
    card(c, M, 68, 520, 127, PAPER_DEEP, RULE); label(c, "Reflection", M + 18, 169, ACCENT)
    text_block(c, "“I designed the project as a small editorial instrument that makes the distribution of attention reviewable before a summary becomes the record.”", M + 18, 145, 484, 12.5, 17, FONT_B, INK)
    qx = 590
    card(c, qx, 68, PAGE_W - M - qx, 127, WHITE, RULE)
    label(c, "Public project", qx + 16, 169, BLUE)
    label(c, "Live demo", qx + 16, 145, ACCENT, 7.3)
    text_block(c, PUBLIC_DISPLAY, qx + 16, 130, PAGE_W - M - qx - 32, 7.4, 8.8, FONT_B, INK)
    label(c, "Source code", qx + 16, 102, ACCENT, 7.3)
    text_block(c, REPO_DISPLAY, qx + 16, 87, PAGE_W - M - qx - 32, 7.1, 8.4, FONT, MUTED)
    c.linkURL(PUBLIC_URL, (qx + 12, 112, PAGE_W - M - 8, 154), relative=0)
    c.linkURL(REPO_URL, (qx + 12, 71, PAGE_W - M - 8, 108), relative=0)


def build():
    TMP.mkdir(parents=True, exist_ok=True); OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(TMP_PDF), pagesize=(PAGE_W, PAGE_H), pageCompression=1, initialFontName=FONT, initialFontSize=10)
    c.setTitle("Who Gets Summarized? - Portfolio by Yuyang Nie"); c.setAuthor("Yuyang Nie"); c.setCreator("Yuyang Nie")
    for page in [
        cover, one_screen, use_case, primary_source, record_structure, corpus_map,
        risks, method, metric_explainer, interface, balanced_result,
        omission_ledger, representation, sensitivity, alternatives, engineering,
    ]:
        page(c); c.showPage()
    c.save()
    reader = PdfReader(str(TMP_PDF)); writer = PdfWriter(); writer.clone_document_from_reader(reader)
    # ReportLab's QR renderer inserts empty Times-Roman text states. Remove those
    # no-op states so the final PDF contains one visible type family only.
    for page in writer.pages:
        font_dict = page["/Resources"].get("/Font")
        fonts = font_dict.get_object() if font_dict else {}
        times_keys = {
            str(key)
            for key, value in fonts.items()
            if "Times-Roman" in str(value.get_object().get("/BaseFont", ""))
        }
        stream = ContentStream(page.get_contents(), writer)
        stream.operations = [
            (operands, operator)
            for operands, operator in stream.operations
            if not (operator == b"Tf" and str(operands[0]) in times_keys)
        ]
        page.replace_contents(stream)
        for key in times_keys:
            fonts.pop(NameObject(key), None)
    writer.add_metadata({"/Title": "Who Gets Summarized? - Portfolio by Yuyang Nie", "/Author": "Yuyang Nie", "/Creator": "Yuyang Nie", "/Producer": "Yuyang Nie", "/Subject": "Provenance-first editorial audit of a real public record", "/Keywords": "editorial audit, provenance, public record, MMR, Jensen-Shannon divergence"})
    with OUTPUT.open("wb") as f: writer.write(f)
    print(OUTPUT)


if __name__ == "__main__":
    build()
