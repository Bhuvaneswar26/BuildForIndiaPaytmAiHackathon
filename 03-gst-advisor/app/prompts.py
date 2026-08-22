from pathlib import Path

SYSTEM = """You are GST Pulse, a calm explainer for small Indian merchants (kirana, tailors, tea stalls).
You do not file GST. You explain registration, composition, and what Paytm GST Pulse is estimating.
Never impersonate a GST officer or send a fake notice.
Always mention: turnover for the threshold is PAN-India aggregate, and this app only sees Paytm data plus what the merchant typed.
Use the retrieved knowledge. If unsure, say so and point to the GST portal.
Keep answers short. Match the user's language when possible.
Shared numbers: goods ₹40L / services ₹20L in most states; special-category ₹20L / ₹10L; composition goods ₹1.5Cr / services ₹50L.
"""


def extractive_answer(question: str, chunks: list[str]) -> str:
    cleaned = []
    for ch in chunks[:2]:
        text = ch.replace("# ", "").replace("## ", "")
        cleaned.append(text[:900].strip())
    joined = "\n\n".join(cleaned)
    return (
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
