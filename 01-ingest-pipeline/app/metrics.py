from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime

from app import gst_rules


def _parse_dt(value: str) -> date | None:
    if not value or len(value) < 10:
        return None
    try:
        return datetime.strptime(value[:19], "%Y-%m-%d %H:%M:%S").date()
    except ValueError:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()


def compute_metrics(
    *,
    merchant: dict,
    orders: list[dict],
    as_of: date | None = None,
    previous_pct: float | None = None,
) -> dict:
    as_of = as_of or date.today()
    fy0 = gst_rules.fy_start(as_of)
    profile = gst_rules.profile(merchant["state_code"], merchant["business_type"])  # type: ignore[arg-type]

    monthly: dict[str, float] = defaultdict(float)
    paytm_total = 0.0
    for o in orders:
        raw = o.get("order_completed_time") or o.get("orderCompletedTime") or ""
        d = _parse_dt(str(raw))
        if d is None or d < fy0 or d > as_of:
            continue
        amt = float(o.get("amount") or 0)
        paytm_total += amt
        monthly[d.strftime("%Y-%m")] += amt

    other = float(merchant.get("other_income_inr") or 0)
    aggregate = paytm_total + other
    limit = profile.registration_limit_inr
    pct = round(100.0 * aggregate / limit, 2) if limit else 0.0
    elapsed = max((as_of - fy0).days, 1)
    eta = gst_rules.months_to_limit(aggregate, limit, elapsed)
    new_cp = gst_rules.checkpoint_hit(pct, previous_pct)
    crossed = [c for c in gst_rules.CHECKPOINTS if pct >= c * 100]

    return {
        "merchant_id": merchant["merchant_id"],
        "name": merchant["name"],
        "mid": merchant["mid"],
        "state_code": profile.state_code,
        "business_type": profile.business_type,
        "phone": merchant.get("phone"),
        "email": merchant.get("email"),
        "language": merchant.get("language") or "en",
        "is_special_category": profile.is_special_category,
        "fy_label": gst_rules.fy_label(as_of),
        "as_of": as_of.isoformat(),
        "paytm_turnover": round(paytm_total, 2),
        "other_income": round(other, 2),
        "aggregate_turnover": round(aggregate, 2),
        "threshold": limit,
        "pct": pct,
        "monthly": {k: round(v, 2) for k, v in sorted(monthly.items())},
        "months_to_threshold": eta,
        "checkpoints_already_crossed": crossed,
        "new_checkpoint": new_cp,
        "composition_eligible": aggregate < profile.composition_limit_inr,
        "composition_limit": profile.composition_limit_inr,
        "composition_rate_hint": profile.composition_rate_hint,
        "gst_portal": gst_rules.GST_PORTAL,
        "data_caveat": (
            "Turnover for GST registration is PAN-India aggregate across all sales channels. "
            "This estimate uses Paytm settlement/order data only, plus any other income you entered."
        ),
        "source": "paytm_passbook",
        "advisor_url": None,
    }
