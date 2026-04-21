import streamlit as st

st.set_page_config(
    page_title="FreelanceGuard · Contract Analyzer",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Global */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 960px; }

    /* Hero */
    .hero { text-align: center; padding: 2.5rem 1rem 1.5rem; }
    .hero h1 { font-size: 2.6rem; font-weight: 800; margin-bottom: 0.3rem; }
    .hero p  { font-size: 1.1rem; color: #6b7280; margin-top: 0; }
    .brand  { color: #2563eb; }

    /* Upload card */
    .upload-card {
        border: 2px dashed #93c5fd;
        border-radius: 14px;
        background: #eff6ff;
        padding: 2rem 1.5rem;
        text-align: center;
        margin-bottom: 1.5rem;
    }

    /* Score ring */
    .score-ring {
        display: inline-block;
        width: 100px; height: 100px;
        border-radius: 50%;
        line-height: 100px;
        font-size: 2rem;
        font-weight: 800;
        color: white;
        margin-bottom: 0.4rem;
    }
    .score-red    { background: #ef4444; }
    .score-yellow { background: #f59e0b; }
    .score-green  { background: #22c55e; }

    /* Flag cards */
    .flag-card {
        border-left: 5px solid #e5e7eb;
        background: #f9fafb;
        border-radius: 0 10px 10px 0;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
    }
    .flag-high   { border-left-color: #ef4444; background: #fef2f2; }
    .flag-medium { border-left-color: #f59e0b; background: #fffbeb; }
    .flag-low    { border-left-color: #22c55e; background: #f0fdf4; }

    .flag-title { font-weight: 700; font-size: 1rem; margin-bottom: 0.25rem; }
    .flag-body  { font-size: 0.9rem; color: #374151; }
    .flag-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 99px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-bottom: 0.4rem;
    }
    .badge-high   { background: #fee2e2; color: #b91c1c; }
    .badge-medium { background: #fef3c7; color: #92400e; }
    .badge-low    { background: #dcfce7; color: #166534; }

    /* Redline box */
    .redline {
        background: #f0fdf4;
        border: 1px solid #86efac;
        border-radius: 8px;
        padding: 0.6rem 0.9rem;
        font-size: 0.85rem;
        color: #166534;
        margin-top: 0.5rem;
    }
    .redline-label { font-weight: 700; margin-bottom: 2px; }

    /* Stat cards */
    .stat-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.1rem 1rem;
        text-align: center;
    }
    .stat-num  { font-size: 2rem; font-weight: 800; }
    .stat-label{ font-size: 0.8rem; color: #6b7280; margin-top: 2px; }

    /* Section headers */
    .section-header {
        font-size: 1.15rem;
        font-weight: 700;
        color: #111827;
        border-bottom: 2px solid #e5e7eb;
        padding-bottom: 0.4rem;
        margin: 1.6rem 0 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── MOCK DATA ─────────────────────────────────────────────────────────────────
MOCK_FLAGS = [
    {
        "risk": "high",
        "title": "Hourly Rate 24 % Below Market Median",
        "clause": "The freelancer shall be remunerated at a rate of €72/h for senior Python development.",
        "explanation": (
            "The offered rate of €72/h is 24 % below the market median of €95/h for senior Python "
            "developers in Bavaria (source: Freelancer-Kompass 2025). The 25th percentile is €84/h, "
            "meaning this rate is below even the lower quartile."
        ),
        "redline": "The freelancer shall be remunerated at a rate of €95/h for senior Python development.",
        "statute": None,
        "source": "Freelancer-Kompass 2025, row 312",
    },
    {
        "risk": "medium",
        "title": "Late-Payment Interest Below Statutory Default",
        "clause": "Bei Zahlungsverzug werden Zinsen in Höhe von 4 % p.a. berechnet.",
        "explanation": (
            "§288 Abs. 2 BGB sets the statutory late-payment interest rate for B2B transactions at "
            "base rate + 9 pp (≈ 12.1 % in 2026). Accepting 4 % forfeits your legal entitlement."
        ),
        "redline": "Bei Zahlungsverzug werden Verzugszinsen in gesetzlicher Höhe gemäß §288 Abs. 2 BGB berechnet.",
        "statute": "§288 Abs. 2 BGB",
        "source": "Playbook entry PB-042",
    },
    {
        "risk": "medium",
        "title": "Payment Term 45 Days — Above Industry Norm",
        "clause": "Invoices shall be settled within 45 calendar days of receipt.",
        "explanation": (
            "Market-standard net payment for IT freelancers in Germany is 14–30 days (VGSD Survey 2024). "
            "45 days increases your cash-flow risk with no legal obligation to accept it."
        ),
        "redline": "Invoices shall be settled within 14 calendar days of receipt.",
        "statute": None,
        "source": "payment_term_norms table, row 88",
    },
    {
        "risk": "low",
        "title": "IP Assignment — Standard Scope",
        "clause": "All work results produced under this agreement shall become the exclusive property of the client.",
        "explanation": (
            "The IP assignment is limited to deliverables produced under this contract and does not "
            "include pre-existing tools or background IP. No further action required."
        ),
        "redline": None,
        "statute": None,
        "source": "Playbook entry PB-007",
    },
]

RISK_BADGE = {"high": "badge-high", "medium": "badge-medium", "low": "badge-low"}
FLAG_CLASS  = {"high": "flag-high",  "medium": "flag-medium",  "low": "flag-low"}
RISK_LABEL  = {"high": "High Risk",  "medium": "Medium Risk",  "low": "Low Risk ✓"}
RISK_EMOJI  = {"high": "🔴", "medium": "🟡", "low": "🟢"}

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="hero">
        <h1>⚖️ <span class="brand">FreelanceGuard</span></h1>
        <p>AI-powered contract analysis for German freelancers — powered by a curated legal playbook,<br>
        market benchmarks, and §-exact statutory references.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── UPLOAD ────────────────────────────────────────────────────────────────────
st.markdown('<div class="upload-card">', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "Drop your freelance contract here (PDF)",
    type="pdf",
    label_visibility="visible",
)
st.markdown(
    "<p style='color:#6b7280;font-size:0.85rem;margin-top:0.5rem'>"
    "Your document is processed locally and never stored permanently.</p>",
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

# ── DEMO TOGGLE ───────────────────────────────────────────────────────────────
demo_mode = st.toggle("Run with sample contract (demo)", value=not bool(uploaded_file))
show_results = uploaded_file or demo_mode

# ── RESULTS ───────────────────────────────────────────────────────────────────
if show_results:
    if demo_mode and not uploaded_file:
        st.info("**Demo mode** — showing analysis for a sample Python-developer contract (Munich, senior).")

    st.markdown("---")

    # ── Summary row ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Analysis Summary</div>', unsafe_allow_html=True)

    high_count   = sum(1 for f in MOCK_FLAGS if f["risk"] == "high")
    medium_count = sum(1 for f in MOCK_FLAGS if f["risk"] == "medium")
    low_count    = sum(1 for f in MOCK_FLAGS if f["risk"] == "low")
    overall      = "high" if high_count else ("medium" if medium_count else "low")
    score_class  = {"high": "score-red", "medium": "score-yellow", "low": "score-green"}[overall]
    score_label  = {"high": "HIGH", "medium": "MED", "low": "LOW"}[overall]

    col_ring, col_s1, col_s2, col_s3, col_s4 = st.columns([1.4, 1, 1, 1, 1])

    with col_ring:
        st.markdown(
            f'<div style="text-align:center">'
            f'<div class="score-ring {score_class}">{score_label}</div>'
            f'<div style="font-size:0.8rem;color:#6b7280">Overall Risk</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_s1:
        st.markdown(
            f'<div class="stat-card"><div class="stat-num" style="color:#ef4444">{high_count}</div>'
            f'<div class="stat-label">High-risk flags</div></div>',
            unsafe_allow_html=True,
        )
    with col_s2:
        st.markdown(
            f'<div class="stat-card"><div class="stat-num" style="color:#f59e0b">{medium_count}</div>'
            f'<div class="stat-label">Medium-risk flags</div></div>',
            unsafe_allow_html=True,
        )
    with col_s3:
        st.markdown(
            f'<div class="stat-card"><div class="stat-num" style="color:#22c55e">{low_count}</div>'
            f'<div class="stat-label">Low / no issue</div></div>',
            unsafe_allow_html=True,
        )
    with col_s4:
        st.markdown(
            f'<div class="stat-card"><div class="stat-num" style="color:#2563eb">{len(MOCK_FLAGS)}</div>'
            f'<div class="stat-label">Clauses reviewed</div></div>',
            unsafe_allow_html=True,
        )

    # ── Flag list ─────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Flagged Clauses</div>', unsafe_allow_html=True)

    for flag in MOCK_FLAGS:
        risk      = flag["risk"]
        fc        = FLAG_CLASS[risk]
        badge_cls = RISK_BADGE[risk]
        label     = RISK_LABEL[risk]
        emoji     = RISK_EMOJI[risk]

        st.markdown(
            f"""
            <div class="flag-card {fc}">
                <span class="flag-badge {badge_cls}">{emoji} {label}</span>
                <div class="flag-title">{flag['title']}</div>
                <div class="flag-body" style="color:#6b7280;font-size:0.82rem;margin-bottom:0.5rem">
                    <em>Contract text:</em> "{flag['clause']}"
                </div>
                <div class="flag-body">{flag['explanation']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_left, col_right = st.columns([3, 2])
        with col_left:
            if flag["redline"]:
                st.markdown(
                    f'<div class="redline">'
                    f'<div class="redline-label">✏️ Suggested redline</div>'
                    f'{flag["redline"]}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        with col_right:
            meta = []
            if flag["statute"]:
                meta.append(f"📜 **Statute:** {flag['statute']}")
            if flag["source"]:
                meta.append(f"🗄️ **Source:** {flag['source']}")
            if meta:
                st.markdown("  \n".join(meta))

        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

    # ── Negotiation brief ─────────────────────────────────────────────────────
    st.markdown('<div class="section-header">One-Page Negotiation Brief</div>', unsafe_allow_html=True)

    with st.expander("View full brief", expanded=False):
        st.markdown(
            """
**Contract:** Sample_Freelance_Agreement_v2.pdf
**Analyzed:** 2026-04-21
**Profile:** Senior Python Developer · Munich (DE-BY)

---

### Priority Actions

1. **[HIGH] Push back on the hourly rate.** At €72/h you are 24 % below market. Open negotiation at €105/h
   (median) and accept no less than €84/h (25th percentile). Cite Freelancer-Kompass 2025.

2. **[MEDIUM] Replace the late-payment clause.** Delete the 4 % figure; insert the statutory reference
   ("gesetzlicher Zinssatz gemäß §288 Abs. 2 BGB"). This preserves your full legal entitlement (~12.1 %).

3. **[MEDIUM] Shorten payment terms from 45 to 14 days.** Standard for IT freelancers per VGSD 2024.
   Counter-offer: 14 days; fallback: 21 days.

### No Action Required

- **IP assignment** is standard in scope — limited to deliverables only.

---
*Generated by FreelanceGuard · for informational purposes only, not legal advice.*
            """
        )
        st.download_button(
            "⬇️  Download brief as text",
            data="FreelanceGuard Negotiation Brief\n\n[Full brief content here]",
            file_name="negotiation_brief.txt",
            mime="text/plain",
        )

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        "<p style='text-align:center;font-size:0.78rem;color:#9ca3af'>"
        "FreelanceGuard · Nova SBE Advanced ML Capstone · "
        "For informational purposes only — not a substitute for legal advice."
        "</p>",
        unsafe_allow_html=True,
    )
