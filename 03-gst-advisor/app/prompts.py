from pathlib import Path
import re

from app.rag import Chunk

SYSTEM = """You are GST Pulse, a calm explainer for small Indian merchants (kirana, tailors, tea stalls).
You do not file GST. You explain registration, composition, documents, timelines, and what Paytm GST Pulse is estimating.
Never impersonate a GST officer or send a fake notice.

Write a DETAILED, practical answer a merchant can actually use. Short summaries are not enough.

Rules:
- Use ONLY the retrieved GST notes. Do not invent rates, deadlines, document names, or steps.
- If several notes are relevant, combine them into one coherent explanation. Skip table-of-contents, version history, and unrelated sections.
- Preserve numbers, conditions, file formats, size limits, and caveats exactly as written.
- Structure the reply with short headings and bullets so it is easy to scan.
- Never output tables, markdown pipes, HTML, images, diagrams, flowcharts, or ASCII boxes. The chat UI cannot show them. Turn any table-like facts into plain bullet lines such as "Goods, most states: Rs 40 lakh".
- Always mention: turnover for the threshold is PAN-India aggregate, and this app only sees Paytm data plus what the merchant typed.
- End with what the merchant should do next, and point to the GST portal when registration is involved.
- If the notes do not answer the question, say so clearly and still share the closest related facts from the notes.
- Match the user's language when possible.

Shared numbers (use these unless a retrieved note is more specific): goods ₹40L / services ₹20L in most states; special-category ₹20L / ₹10L; composition goods ₹1.5Cr / services ₹50L.
"""

ANSWER_INSTRUCTIONS = """Answer the question in detail using the retrieved GST notes below.

Required shape:
1) Direct answer in 2–4 sentences.
2) The relevant numbers, eligibility, and conditions.
3) Practical steps, documents, or timelines if they appear in the notes (do not collapse a procedure into one line).
4) Caveats and what to do next.

Write enough that a first-time merchant understands the topic without opening another page.
Do not use outside knowledge. Do not invent facts.
Output plain text only: headings and bullets are fine. Do not use tables, images, HTML, or diagrams.
"""


_BOX = re.compile(r"[┌┐└┘├┤┬┴┼─│═║╔╗╚╝╠╣╦╩╬▀▄█░▒▓]")
_IMG_HTML = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_TABLE_HTML = re.compile(r"<table\b[\s\S]*?</table>", re.IGNORECASE)
_MD_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
_HTML_TAG = re.compile(r"</?(?:table|thead|tbody|tr|th|td|img|figure|svg|canvas)[^>]*>", re.IGNORECASE)


def _cells(line: str) -> list[str]:
    raw = line.strip().strip("|")
    return [c.strip() for c in raw.split("|")]


def _is_table_divider(line: str) -> bool:
    cells = _cells(line)
    if not cells:
        return False
    return all(re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) or c == "" for c in cells)


def _is_table_row(line: str) -> bool:
    s = line.strip()
    return s.startswith("|") and s.count("|") >= 2


def _tables_to_bullets(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        if _is_table_row(lines[i]):
            rows: list[list[str]] = []
            while i < len(lines) and (_is_table_row(lines[i]) or not lines[i].strip()):
                if lines[i].strip() and not _is_table_divider(lines[i]):
                    rows.append(_cells(lines[i]))
                i += 1
            if not rows:
                continue
            headers = rows[0]
            body = rows[1:] if len(rows) > 1 else []
            if not body:
                out.append("• " + "; ".join(c for c in headers if c))
                continue
            for row in body:
                bits = []
                for idx, value in enumerate(row):
                    if not value:
                        continue
                    label = headers[idx] if idx < len(headers) else ""
                    bits.append(f"{label}: {value}" if label else value)
                if bits:
                    out.append("• " + "; ".join(bits))
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def _drop_ascii_art(text: str) -> str:
    kept: list[str] = []
    for line in text.splitlines():
        if _BOX.search(line) and len(_BOX.findall(line)) >= 2:
            continue
        if re.fullmatch(r"[\s\-_=*#/\\<>]{6,}", line.strip()):
            continue
        kept.append(line)
    return "\n".join(kept)


def flatten_for_display(text: str) -> str:
    """Knowledge and model output must be readable in a plain chat bubble."""
    text = _TABLE_HTML.sub("", text)
    text = _IMG_HTML.sub("", text)
    text = _MD_IMAGE.sub("", text)
    text = re.sub(r"```(?:mermaid|svg|html|xml)[\s\S]*?```", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```(?:\w+)?\s*([\s\S]*?)```", r"\1", text)
    text = _tables_to_bullets(text)
    text = _drop_ascii_art(text)
    text = _HTML_TAG.sub("", text)
    return text


def clean_text(text: str) -> str:
    text = flatten_for_display(text)
    text = re.sub(r"!\[([^]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*+]\s+", "• ", text, flags=re.MULTILINE)
    text = re.sub(r"(`{1,3}|\*{1,3}|_{1,3})", "", text)
    text = re.sub(r"\|", " ", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


_SKIP_EXTRACT_HEADINGS = {
    "table of contents",
    "quick navigation",
    "version history",
    "version history & updates",
    "related guides",
    "notes for professionals & advisors",
    "document storage & record management",
}


def extractive_answer(question: str, hits: list[tuple[float, Chunk]]) -> str:
    """Stitch full relevant knowledge sections, not a handful of sentences."""
    parts: list[str] = []
    used = 0
    max_chars = 9000
    seen_text: set[str] = set()
    for _, chunk in hits:
        title = (chunk.title or "").strip()
        if title.lower() in _SKIP_EXTRACT_HEADINGS:
            continue
        body = clean_text(chunk.text)
        if len(body) < 60 or body in seen_text:
            continue
        seen_text.add(body)
        heading = title or chunk.source
        block = f"{heading}\n{body}"
        if parts and used + len(block) > max_chars:
            break
        parts.append(block)
        used += len(block)
        if used >= max_chars:
            break
    joined = "\n\n".join(parts) or "No directly matching explanation was found in the knowledge base."
    return (
        "Here is a detailed explanation from GST Pulse's knowledge base "
        "(not a government notice, and not tax filing):\n\n"
        f"{joined}\n\n"
        "Turnover for the registration line is PAN-India aggregate. GST Pulse only sees Paytm "
        "plus any other income you typed. If this does not match your state or business type, "
        "ask again with those details. Registration itself is on https://reg.gst.gov.in/registration/"
    )


def skill_text() -> str:
    skill = Path(__file__).resolve().parent.parent / "skills" / "gst-explainer-consistency" / "SKILL.md"
    if skill.exists():
        return skill.read_text(encoding="utf-8")
    return ""
