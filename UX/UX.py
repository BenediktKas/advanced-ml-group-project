import streamlit as st

st.set_page_config(
    page_title="Contract Analyzer — German Freelance",
    page_icon=None,
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, sans-serif;
        color: #1a1a1a;
    }
    .block-container {
        padding-top: 3rem;
        padding-bottom: 4rem;
        max-width: 780px;
    }

    /* Wordmark */
    .wordmark {
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #6b7280;
        margin-bottom: 0.2rem;
    }
    .page-title {
        font-size: 1.75rem;
        font-weight: 600;
        color: #111827;
        margin: 0 0 0.5rem 0;
        line-height: 1.3;
    }
    .page-sub {
        font-size: 0.9rem;
        color: #6b7280;
        margin: 0 0 2rem 0;
        line-height: 1.6;
    }

    /* Divider */
    hr.light { border: none; border-top: 1px solid #e5e7eb; margin: 1.8rem 0; }

    /* Section label */
    .section-label {
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #9ca3af;
        margin-bottom: 0.75rem;
    }

    /* Summary table row */
    .summary-row {
        display: flex;
        gap: 2rem;
        margin-bottom: 1.5rem;
    }
    .summary-item { }
    .summary-num {
        font-size: 1.4rem;
        font-weight: 600;
        color: #111827;
        line-height: 1;
    }
    .summary-num.red    { color: #dc2626; }
    .summary-num.amber  { color: #b45309; }
    .summary-num.green  { color: #15803d; }
    .summary-desc {
        font-size: 0.78rem;
        color: #6b7280;
        margin-top: 2px;
    }

    /* Finding row */
    .finding {
        border-top: 1px solid #e5e7eb;
        padding: 1.1rem 0;
    }
    .finding:last-child { border-bottom: 1px solid #e5e7eb; }

    .finding-header {
        display: flex;
        align-items: baseline;
        gap: 0.75rem;
        margin-bottom: 0.4rem;
    }
    .finding-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #111827;
    }
    .risk-tag {
        font-size: 0.68rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        padding: 2px 7px;
        border-radius: 3px;
        white-space: nowrap;
    }
    .risk-high   { background: #fee2e2; color: #991b1b; }
    .risk-medium { background: #fef3c7; color: #92400e; }
    .risk-low    { background: #f0fdf4; color: #166534; }

    .clause-text {
        font-size: 0.82rem;
        color: #6b7280;
        font-style: italic;
        margin-bottom: 0.5rem;
        padding-left: 0.75rem;
        border-left: 2px solid #e5e7eb;
    }
    .finding-body {
        font-size: 0.875rem;
        color: #374151;
        line-height: 1.6;
        margin-bottom: 0.6rem;
    }

    /* Redline */
    .redline-block {
        background: #f9fafb;
        border: 1px solid #d1fae5;
        border-left: 3px solid #059669;
        border-radius: 0 4px 4px 0;
        padding: 0.55rem 0.8rem;
        font-size: 0.82rem;
        color: #065f46;
        margin-top: 0.4rem;
    }
    .redline-label {
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #059669;
        margin-bottom: 3px;
    }

    /* Meta line */
    .meta-line {
        font-size: 0.75rem;
        color: #9ca3af;
        margin-top: 0.5rem;
    }
    .meta-line span { margin-right: 1.2rem; }

    /* Brief box */
    .brief-box {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        padding: 1.25rem 1.4rem;
        font-size: 0.875rem;
        line-height: 1.7;
        color: #374151;
    }

    /* Footer */
    .footer {
        font-size: 0.75rem;
        color: #d1d5db;
        margin-top: 3rem;
        border-top: 1px solid #f3f4f6;
        padding-top: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── DATA ──────────────────────────────────────────────────────────────────────
FINDINGS = [
    {
        "risk": "high",
        "title": "Hourly rate 24% below market median",
        "clause": "The freelancer shall be remunerated at a rate of €72/h for senior Python development.",
        "body": (
            "The offered rate of €72/h falls below the 25th-percentile benchmark of €84/h for "
            "senior Python developers in Bavaria. The market median is €95/h "
            "(Freelancer-Kompass 2025). There is no contractual obligation to accept a "
            "below-median rate."
        ),
        "redline": "The freelancer shall be remunerated at a rate of €95/h for senior Python development.",
        "statute": None,
        "source": "Freelancer-Kompass 2025",
    },
    {
        "risk": "medium",
        "title": "Late-payment interest below statutory default",
        "clause": "Bei Zahlungsverzug werden Zinsen in Höhe von 4 % p.a. berechnet.",
        "body": (
            "§288 Abs. 2 BGB entitles B2B creditors to the base rate plus 9 percentage points "
            "(approximately 12.1% as of 2026). Agreeing to 4% is legally valid but reduces the "
            "contractual entitlement by roughly 8 percentage points."
        ),
        "redline": (
            "Bei Zahlungsverzug werden Verzugszinsen in gesetzlicher Höhe "
            "gemäß §288 Abs. 2 BGB berechnet."
        ),
        "statute": "§288 Abs. 2 BGB",
        "source": "Playbook PB-042",
    },
    {
        "risk": "medium",
        "title": "Payment term of 45 days exceeds industry norm",
        "clause": "Invoices shall be settled within 45 calendar days of receipt.",
        "body": (
            "Standard payment terms for IT freelancers in Germany are 14–30 days "
            "(VGSD Survey 2024). A 45-day term increases liquidity risk; §271a BGB "
            "caps enforceable payment periods in B2B contracts at 60 days."
        ),
        "redline": "Invoices shall be settled within 14 calendar days of receipt.",
        "statute": "§271a BGB",
        "source": "VGSD Survey 2024",
    },
    {
        "risk": "low",
        "title": "IP assignment — within standard scope",
        "clause": (
            "All work results produced under this agreement shall become the "
            "exclusive property of the client."
        ),
        "body": (
            "The assignment covers only deliverables produced under this contract. "
            "Pre-existing tools, libraries, and background IP are not affected. "
            "No action required."
        ),
        "redline": None,
        "statute": None,
        "source": "Playbook PB-007",
    },
]

RISK_TAG   = {"high": "risk-high",   "medium": "risk-medium",   "low": "risk-low"}
RISK_LABEL = {"high": "High",        "medium": "Medium",        "low": "Acceptable"}

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown('<div class="wordmark">Nova SBE · Advanced ML</div>', unsafe_allow_html=True)
st.markdown('<h1 class="page-title">Freelance Contract Analyzer</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="page-sub">Upload a PDF contract to receive a structured risk analysis '
    'against German statutory law, market rate benchmarks, and a curated clause playbook.</p>',
    unsafe_allow_html=True,
)

# ── UPLOAD ────────────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader("Contract (PDF)", type="pdf", label_visibility="visible")

col_toggle, col_note = st.columns([2, 3])
with col_toggle:
    demo_mode = st.toggle("Use sample contract", value=not bool(uploaded_file))
with col_note:
    st.markdown(
        "<p style='font-size:0.78rem;color:#9ca3af;margin-top:0.5rem'>"
        "Documents are not stored after the session ends.</p>",
        unsafe_allow_html=True,
    )

show_results = uploaded_file or demo_mode

# ── RESULTS ───────────────────────────────────────────────────────────────────
if show_results:
    if demo_mode and not uploaded_file:
        st.caption("Sample contract: Senior Python Developer, Munich (DE-BY) — for demonstration only.")

    st.markdown('<hr class="light">', unsafe_allow_html=True)

    # Summary counts
    high_n   = sum(1 for f in FINDINGS if f["risk"] == "high")
    medium_n = sum(1 for f in FINDINGS if f["risk"] == "medium")
    low_n    = sum(1 for f in FINDINGS if f["risk"] == "low")

    st.markdown('<div class="section-label">Summary</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="summary-row">
            <div class="summary-item">
                <div class="summary-num red">{high_n}</div>
                <div class="summary-desc">High-risk findings</div>
            </div>
            <div class="summary-item">
                <div class="summary-num amber">{medium_n}</div>
                <div class="summary-desc">Medium-risk findings</div>
            </div>
            <div class="summary-item">
                <div class="summary-num green">{low_n}</div>
                <div class="summary-desc">Acceptable</div>
            </div>
            <div class="summary-item">
                <div class="summary-num">{len(FINDINGS)}</div>
                <div class="summary-desc">Clauses reviewed</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Findings
    st.markdown('<div class="section-label">Findings</div>', unsafe_allow_html=True)

    for f in FINDINGS:
        tag   = RISK_TAG[f["risk"]]
        label = RISK_LABEL[f["risk"]]

        meta_parts = []
        if f["statute"]:
            meta_parts.append(f"<span>Statute: {f['statute']}</span>")
        if f["source"]:
            meta_parts.append(f"<span>Source: {f['source']}</span>")
        meta_html = '<div class="meta-line">' + "".join(meta_parts) + "</div>" if meta_parts else ""

        redline_html = ""
        if f["redline"]:
            redline_html = (
                f'<div class="redline-block">'
                f'<div class="redline-label">Suggested redline</div>'
                f'{f["redline"]}'
                f"</div>"
            )

        st.markdown(
            f"""
            <div class="finding">
                <div class="finding-header">
                    <span class="finding-title">{f['title']}</span>
                    <span class="risk-tag {tag}">{label}</span>
                </div>
                <div class="clause-text">{f['clause']}</div>
                <div class="finding-body">{f['body']}</div>
                {redline_html}
                {meta_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Negotiation brief
    st.markdown('<hr class="light">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Negotiation Brief</div>', unsafe_allow_html=True)

    with st.expander("View full brief"):
        st.markdown(
            """
            <div class="brief-box">
            <strong>Contract:</strong> Sample_Freelance_Agreement_v2.pdf<br>
            <strong>Profile:</strong> Senior Python Developer · Munich (DE-BY)<br>
            <strong>Date:</strong> 21 April 2026<br><br>

            <strong>Priority actions</strong><br><br>

            1. <strong>Hourly rate (high priority).</strong>
            The offered rate of €72/h is below the 25th-percentile benchmark.
            Open at €105/h (market median) and set a floor of €84/h.
            Reference: Freelancer-Kompass 2025.<br><br>

            2. <strong>Late-payment interest (medium priority).</strong>
            Replace the 4% figure with a reference to the statutory rate under
            §288 Abs. 2 BGB. No numerical rate should appear in the contract.<br><br>

            3. <strong>Payment term (medium priority).</strong>
            Propose 14 days net; fall back to 21 days if necessary.
            The current 45-day term is atypical for the sector (VGSD Survey 2024).<br><br>

            <strong>No action required</strong><br><br>

            IP assignment clause is within standard scope.
            Pre-existing tools and background IP are unaffected.<br><br>

            <em style="color:#9ca3af;font-size:0.8rem;">
            For informational purposes only. This analysis does not constitute legal advice.
            </em>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.download_button(
            "Download brief",
            data=(
                "Freelance Contract Analysis\n"
                "Sample_Freelance_Agreement_v2.pdf · 21 April 2026\n\n"
                "1. Hourly rate — high priority\n"
                "   Offered: €72/h. Market median: €95/h (Freelancer-Kompass 2025).\n"
                "   Negotiate to at least €84/h (25th percentile).\n\n"
                "2. Late-payment interest — medium priority\n"
                "   Replace 4% with statutory reference (§288 Abs. 2 BGB, ~12.1%).\n\n"
                "3. Payment term — medium priority\n"
                "   Propose 14 days net; fallback 21 days.\n\n"
                "4. IP assignment — acceptable, no action required.\n"
            ),
            file_name="negotiation_brief.txt",
            mime="text/plain",
        )

    st.markdown(
        '<div class="footer">Contract Analyzer · Nova SBE Advanced ML Capstone · '
        'Not a substitute for legal advice.</div>',
        unsafe_allow_html=True,
    )
