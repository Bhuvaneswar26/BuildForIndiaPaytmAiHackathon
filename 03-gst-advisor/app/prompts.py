from pathlib import Path
import re

from app.rag import Chunk

SYSTEM = """You are GST Pulse, a calm explainer for small Indian merchants (kirana, tailors, tea stalls).
You do not file GST. You explain registration, composition, and what Paytm GST Pulse is estimating.
Never impersonate a GST officer or send a fake notice.
Always mention: turnover for the threshold is PAN-India aggregate, and this app only sees Paytm data plus what the merchant typed.
Use the retrieved knowledge. If unsure, say so and point to the GST portal.
Keep answers short. Match the user's language when possible.
Shared numbers: goods ₹40L / services ₹20L in most states; special-category ₹20L / ₹10L; composition goods ₹1.5Cr / services ₹50L.
"""


def clean_text(text: str) -> str:
    text = re.sub(r"```(?:\w+)?\s*([\s\S]*?)```", r"\1", text)
    text = re.sub(r"!\[([^]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*+]\s+", "• ", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"(`{1,3}|\*{1,3}|_{1,3})", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extractive_answer(question: str, hits: list[tuple[float, Chunk]]) -> str:
    query_terms = set(re.findall(r"[a-zA-Z0-9₹%]+", question.lower()))
    document_query = bool(query_terms & {"document", "documents", "proof", "paperwork", "upload", "uploads"})
    if document_query:
        query_terms.update({"document", "documents", "proof", "photo", "bank", "pan", "deed", "certificate"})
    candidates: list[tuple[float, str]] = []
    for chunk_score, chunk in hits:
        text = re.sub(r"^#{1,6}\s*", "", chunk.text, flags=re.MULTILINE)
        if document_query:
            for label in re.findall(r"\*\*([^*]+)\*\*", text):
                if re.search(r"deed|certificate|photo|receipt|khata|electricity|rent|lease|consent|bank|pan|aadhaar", label, re.IGNORECASE):
                    candidates.append((chunk_score + 20.0, label.strip()))
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", text):
            is_bullet = sentence.lstrip().startswith(("- ", "* ", "+ ", "• "))
            sentence = sentence.strip(" -*•\t")
            terms = set(re.findall(r"[a-zA-Z0-9₹%]+", sentence.lower()))
            overlap = len(query_terms & terms)
            boilerplate = (
                "description:", "compatibility:", "license:", "version:", "published:",
                "this skill helps", "establish the legal foundation"
            )
            if (overlap or (document_query and is_bullet)) and len(sentence) >= (10 if is_bullet else 35) and not sentence.lower().startswith(boilerplate):
                document_detail = re.search(
                    r"deed|certificate|photo|receipt|khata|electricity|rent|lease|consent|bank|pan|aadhaar|jpg|pdf|mb|kb",
                    sentence,
                    re.IGNORECASE,
                )
                if document_query and document_detail:
                    overlap += 8
                bullet_bonus = 8.0 if document_query and is_bullet else 0.0
                candidates.append((chunk_score + overlap * 1.5 + bullet_bonus, sentence))
    candidates.sort(key=lambda item: item[0], reverse=True)
    selected: list[str] = []
    for _, sentence in candidates:
        if sentence not in selected:
            selected.append(sentence)
        if len(selected) == 5:
            break
    joined = "\n\n".join(selected) or "No directly matching explanation was found in the knowledge base."
    return clean_text(
        "Here is what GST Pulse can tell you from its knowledge base "
        "(not a government notice, and not tax filing):\n\n"
        f"{joined}\n\n"
        "If this does not match your state or business type, ask again with those details. "
        "Registration itself is on https://reg.gst.gov.in/registration/"
    )


def skill_text() -> str:
    skill = Path(__file__).resolve().parent.parent / "skills" / "gst-explainer-consistency" / "SKILL.md"
    if skill.exists():
        return skill.read_text(encoding="utf-8")
    return ""
