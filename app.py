# app.py
# TalentScout AI — Streamlit Interface
# Domain-agnostic AI recruitment decision system

import streamlit as st
from engine.jd_parser import parse_jd
from engine.candidate_parser import parse_candidates
from engine.resume_parser import parse_multiple_pdfs
from engine.scorer import score_candidate
from engine.ranker import rank_candidates
from engine.validator import validate_jd, validate_candidates
from engine.reporter import generate_report

# ─────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="TalentScout AI",
    page_icon="🚀",
    layout="wide",
)

# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
st.title("🚀 TalentScout AI")
st.caption("Domain-agnostic AI-powered recruitment decision system — works with any JD, any domain, any experience level.")

st.markdown("---")

# ─────────────────────────────────────────────
# Sample Data
# ─────────────────────────────────────────────

SAMPLE_JD = """Job Title:
Senior VLSI Physical Design Engineer

Job Summary:
We are seeking a skilled VLSI Physical Design Engineer with strong expertise in backend ASIC design, focusing on timing closure and signoff.

Required Skills:
Strong knowledge of Physical Design Flow (Floorplan to GDSII)
Expertise in Static Timing Analysis (STA) & Timing Closure
Hands-on experience with PnR (Placement, CTS, Routing)
Proficiency in tools like ICC2 / Fusion Compiler / PrimeTime
Knowledge of DRC, LVS, IR Drop, and EM analysis
Experience with SDC constraints development
Working knowledge of TCL scripting

Preferred Skills:
Experience with multi-corner multi-mode (MCMM/DMSA) analysis
Knowledge of multi-voltage and low-power design techniques
Exposure to Calibre / ICV signoff tools

Experience Required:
4–8 years

Key Responsibilities:
Perform end-to-end physical design implementation from netlist to GDSII
Drive timing closure across all corners and modes
"""

SAMPLE_CANDIDATES = """Candidate 1:
Name: V. Prasad
Skills:
Physical Design (Netlist → GDSII)
Static Timing Analysis (STA) & Timing Closure
Floorplanning, Placement, CTS, Routing
ECO Implementation (Setup/Hold fixes)
DRC/LVS/EM/Crosstalk Analysis
SDC Constraints Development
TCL Scripting, DMSA
Experience (years): 6.8
Tools:
ICC2, PrimeTime (PT Shell), FC Shell, FM Shell
Calibre, Conformal (LEC/ECO)
Key Projects / Work:
Led multiple block-level designs across 5nm, 7nm, 28nm
Owned end-to-end PD flow including timing closure and signoff

Candidate 2:
Name: Vishal S. Pujari
Skills:
Physical Design (PnR Implementation)
Timing Analysis & Closure
Congestion Analysis & Optimization
ECO Fixes (Setup/Hold/DRV)
Floorplanning & Macro Placement
Basic TCL Scripting
Experience (years): 3.9
Tools:
Fusion Compiler, ICC2, PrimeTime, Genus
Key Projects / Work:
Worked on block-level PnR implementation across 5nm, 7nm, 14nm
Performed floorplanning, CTS, routing, and timing optimization

Candidate 3:
Name: Praveen Kumar
Skills:
End-to-End Physical Design (Synthesis → GDSII)
STA & Multi-mode/Multi-corner Timing Closure (DMSA)
Power Planning & Multi-voltage Design
IR Drop & EM Analysis
Congestion Optimization & Floorplan Exploration
ECO Implementation (Functional + Timing)
TCL, Shell, Perl Scripting
Experience (years): 7.8
Tools:
DC, ICC, ICC2, Fusion Compiler, PrimeTime
Cadence Innovus
Calibre, ICV
Key Projects / Work:
Delivered multiple multi-million gate designs across 5nm–40nm
Owned partition/block-level implementation and signoff
Implemented clock mesh/MSCTS for latency and skew optimization
Developed automation scripts for congestion and density fixes
"""

# ─────────────────────────────────────────────
# Input Section
# ─────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Job Description")
    jd_mode = st.radio(
        "JD Input Mode",
        ["Paste Text", "Upload PDF"],
        horizontal=True,
        key="jd_mode"
    )

    if jd_mode == "Paste Text":
        use_sample_jd = st.checkbox("Use sample JD", value=False)
        jd_input = st.text_area(
            "Paste your Job Description here",
            value=SAMPLE_JD if use_sample_jd else "",
            height=300,
            placeholder="Paste any Job Description — VLSI, Web Dev, Data Science, Finance, Healthcare..."
        )
        jd_pdf = None
    else:
        jd_pdf = st.file_uploader(
            "Upload JD as PDF",
            type=["pdf"],
            key="jd_pdf"
        )
        jd_input = None
        use_sample_jd = False

with col2:
    st.subheader("👥 Candidate Profiles")
    cand_mode = st.radio(
        "Candidate Input Mode",
        ["Paste Text", "Upload Resumes (PDF)"],
        horizontal=True,
        key="cand_mode"
    )

    if cand_mode == "Paste Text":
        use_sample_cand = st.checkbox("Use sample candidates", value=False)
        candidate_input = st.text_area(
            "Paste candidate profiles here",
            value=SAMPLE_CANDIDATES if use_sample_cand else "",
            height=300,
            placeholder="Candidate 1:\nName: ...\nSkills:\n...\nExperience (years): ...\nTools:\n..."
        )
        resume_pdfs = None
    else:
        resume_pdfs = st.file_uploader(
            "Upload resume PDFs (multiple allowed)",
            type=["pdf"],
            accept_multiple_files=True,
            key="resume_pdfs"
        )
        candidate_input = None
        use_sample_cand = False

        if resume_pdfs:
            st.success(f"📄 {len(resume_pdfs)} resume(s) uploaded")
            for f in resume_pdfs:
                st.caption(f"  • {f.name}")

st.markdown("---")

# ─────────────────────────────────────────────
# Run Analysis
# ─────────────────────────────────────────────
if st.button("🔍 Run Analysis", type="primary", use_container_width=True):

    # ─── Parse JD ───
    with st.spinner("Parsing Job Description..."):
        try:
            if jd_mode == "Upload PDF" and jd_pdf:
                from engine.resume_parser import extract_text_from_pdf
                jd_text = extract_text_from_pdf(jd_pdf.read())
                if not jd_text.strip():
                    st.error("Could not extract text from JD PDF. Please try pasting the text instead.")
                    st.stop()
            elif jd_mode == "Paste Text" and jd_input and jd_input.strip():
                jd_text = jd_input
            else:
                st.error("Please provide a Job Description.")
                st.stop()

            jd = parse_jd(jd_text)
            jd = validate_jd(jd)
        except ValueError as e:
            st.error(f"JD parsing error: {e}")
            st.stop()

    # ─── Parse Candidates ───
    with st.spinner("Parsing Candidate Profiles..."):
        try:
            if cand_mode == "Upload Resumes (PDF)" and resume_pdfs:
                pdf_files = [(f.name, f.read()) for f in resume_pdfs]
                candidates = parse_multiple_pdfs(pdf_files)

                if not candidates:
                    st.error("Could not extract candidate data from uploaded PDFs. Please check the files.")
                    st.stop()

                st.info(f"📄 Successfully parsed {len(candidates)} candidate(s) from PDFs")

            elif cand_mode == "Paste Text" and candidate_input and candidate_input.strip():
                candidates = parse_candidates(candidate_input)
            else:
                st.error("Please provide at least one candidate profile.")
                st.stop()

            candidates = validate_candidates(candidates)
        except ValueError as e:
            st.error(f"Candidate parsing error: {e}")
            st.stop()

    # ─── Debug: Parsed JD ───
    with st.expander("🔧 Parsed JD (Debug)", expanded=False):
        st.json(jd)

    # ─── Debug: Parsed Candidates ───
    with st.expander("🔧 Parsed Candidates (Debug)", expanded=False):
        for c in candidates:
            # Clean up for display (remove large fields)
            display = {k: v for k, v in c.items() if k != "skills_pool"}
            st.json(display)

    # ─── Score ───
    with st.spinner("Scoring candidates (semantic matching)..."):
        scored = [score_candidate(c, jd) for c in candidates]

    # ─── Rank ───
    ranked = rank_candidates(scored)

    # ─── Quick Summary Cards ───
    st.markdown("---")
    st.subheader("⚡ Quick Summary")

    cols = st.columns(min(len(ranked), 4))
    for i, c in enumerate(ranked[:4]):
        with cols[i]:
            verdict = c.get("verdict", "N/A")
            emoji = {
                "Strong Hire": "🟢",
                "Hire": "🔵",
                "Consider": "🟡",
                "Needs Evaluation": "🟠",
                "Not Recommended": "🔴",
            }.get(verdict, "⚪")

            st.metric(
                label=f"#{c['rank']} {c['name']}",
                value=f"{c['final_score']}/100",
                delta=verdict,
            )
            st.caption(
                f"Match: {c['match_score']} | "
                f"Interest: {c['interest_score']} | "
                f"{emoji} {verdict}"
            )

            # Show source if from PDF
            if c.get("source"):
                st.caption(f"📄 Source: {c['source']}")

    # ─── Full Report ───
    st.markdown("---")
    with st.spinner("Generating report..."):
        report = generate_report(jd, ranked)

    st.markdown(report)

    # ─── Download Report ───
    st.markdown("---")
    st.download_button(
        label="📥 Download Report as Markdown",
        data=report,
        file_name="talentscout_report.md",
        mime="text/markdown",
        use_container_width=True,
    )