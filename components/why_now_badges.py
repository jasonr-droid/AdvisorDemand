# components/why_now_badges.py
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any

import pandas as pd
import streamlit as st

from lib.feature_flags import on
from lib.analytics import track

def _to_df(maybe) -> pd.DataFrame:
    """Normalize list/None/DataFrame into a DataFrame."""
    if isinstance(maybe, pd.DataFrame):
        return maybe
    if maybe is None:
        return pd.DataFrame()
    try:
        return pd.DataFrame(maybe)
    except Exception:
        return pd.DataFrame()

def _hid(*parts) -> str:
    return hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()[:12]

@st.cache_data(show_spinner=False, ttl=300)
def build_why_now_signals(_data_service, county_fips: str, days: int = 90) -> pd.DataFrame:
    """Fuse Licenses, RFPs, Awards → unified 'Why-Now' signals frame."""
    cutoff = datetime.now() - timedelta(days=days)

    lic_df   = _to_df(_data_service.get_license_data(county_fips, refresh=False))
    rfp_df   = _to_df(_data_service.get_rfp_data(county_fips, refresh=False))
    award_df = _to_df(_data_service.get_awards_data(county_fips, refresh=False))

    signals: List[Dict[str, Any]] = []

    # Licenses → "New License"
    if not lic_df.empty:
        lic_df["issued_date"] = pd.to_datetime(lic_df.get("issued_date"), errors="coerce")
        lic_recent = lic_df[lic_df["issued_date"] >= cutoff]
        for _, r in lic_recent.iterrows():
            signals.append({
                "id": _hid("lic", r.get("license_id"), r.get("issued_date")),
                "entity": r.get("jurisdiction") or "Business (license)",
                "naics": r.get("naics"),
                "badge": "New License",
                "signal_type": "new_license",
                "occurred_at": r.get("issued_date"),
                "source": "Licenses",
                "url": r.get("source_url"),
                "extra": r.get("status"),
            })

    # RFPs → "RFP"
    if not rfp_df.empty:
        rfp_df["posted_date"] = pd.to_datetime(rfp_df.get("posted_date"), errors="coerce")
        rfp_recent = rfp_df[rfp_df["posted_date"] >= cutoff]
        for _, r in rfp_recent.iterrows():
            signals.append({
                "id": _hid("rfp", r.get("notice_id")),
                "entity": r.get("title") or "Procurement",
                "naics": r.get("naics"),
                "badge": "RFP",
                "signal_type": "rfp",
                "occurred_at": r.get("posted_date"),
                "source": "SAM.gov",
                "url": r.get("url") or r.get("source_url"),
                "extra": None,
            })

    # Awards → "Award"
    if not award_df.empty:
        award_df["action_date"] = pd.to_datetime(award_df.get("action_date"), errors="coerce")
        award_recent = award_df[award_df["action_date"] >= cutoff]
        for _, r in award_recent.iterrows():
            signals.append({
                "id": _hid("awd", r.get("award_id")),
                "entity": r.get("agency") or "Award",
                "naics": r.get("naics"),
                "badge": "Award",
                "signal_type": "award",
                "occurred_at": r.get("action_date"),
                "source": "USAspending",
                "url": r.get("url") or r.get("source_url"),
                "extra": r.get("amount"),
            })

    df = pd.DataFrame(signals)
    if df.empty:
        return df

    df = df.sort_values(by="occurred_at", ascending=False).reset_index(drop=True)
    return df

def render_why_now_badges(data_service, county_fips: str, default_days: int = 90, limit: int = 50):
    """Streamlit UI to display Why-Now badges (flag-gated)."""
    if not on("FEATURE_COMPANY_INTENT_LIST", "true"):
        st.info("🔒 Why-Now panel is disabled (FEATURE_COMPANY_INTENT_LIST=false).")
        return

    with st.container(border=True):
        st.subheader("Why-Now: Companies with Recent Signals")
        col_a, col_b = st.columns([1, 3])
        days = col_a.slider("Lookback (days)", min_value=7, max_value=365, value=default_days, step=7)
        col_b.caption("Signals come from Licenses, SAM.gov (RFPs), and USAspending (Awards).")

        df = build_why_now_signals(data_service, county_fips, days)
        track("company_signals_ui_viewed", {"county_fips": county_fips, "days": days, "count": int(df.shape[0])})

        if df.empty:
            st.warning("No recent signals found for the selected window.")
            return

        # Display top N signals nicely
        for _, row in df.head(limit).iterrows():
            badge = row["badge"]
            when  = row["occurred_at"]
            label = row["entity"]
            src   = row["source"]
            url   = row.get("url")
            naics = row.get("naics")

            # simple, readable line item
            left, right = st.columns([0.8, 0.2])
            with left:
                st.markdown(
                    f"**{badge}** · {label}  \n"
                    f"_{when.date() if pd.notnull(when) else '—'}_ • {src}"
                    + (f" • NAICS {naics}" if naics else ""),
                )
                if url:
                    st.markdown(f"[Open link]({url})")

            with right:
                # Let user mark it as a target — logs an analytics event
                if st.button("Mark target", key=f"t_{row['id']}"):
                    track("target_marked", {
                        "id": row["id"], "badge": badge, "source": src,
                        "county_fips": county_fips, "occurred_at": str(when)
                    })
                    st.toast("Marked as target ✓")

        st.caption(f"Showing {min(limit, df.shape[0])} of {df.shape[0]} recent signals.")
