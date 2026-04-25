# TalentScout AI — Approach, Architecture & Trade-offs

## The Problem
Recruiters spend hours manually screening resumes against job descriptions. Existing ATS tools rely on rigid keyword matching — "React" won't match "frontend development", and "STA" won't match "Static Timing Analysis." We need an AI agent that truly understands skills, not just strings.

## My Approach
Build a **fully offline, domain-agnostic** recruitment agent that uses semantic understanding instead of keyword matching. The system should work with any JD — VLSI, Web Dev, Data Science, Healthcare — without reconfiguration.

**Key insight:** Pure embedding models perform poorly on short technical terms (3-letter abbreviations, tool names). The solution is a **hybrid matching engine** that combines three strategies: alias expansion → token overlap → semantic embeddings → take the best score.

## Architecture

```
JD (text/PDF) ──→ JD Parser (spaCy + regex) ──→ Structured JD
                                                      │
Candidates (text/PDF) ──→ Candidate Parser ────→ Structured Profiles
                          (deep extraction)            │
                                                       ▼
                                              ┌─────────────────┐
                                              │ Semantic Engine  │
                                              │  (embedder.py)  │
                                              │                 │
                                              │ Layer 1: Alias  │
                                              │ Layer 2: Token  │
                                              │ Layer 3: Embed  │
                                              │ Layer 4: Compound│
                                              │ Layer 5: Equiv  │
                                              └────────┬────────┘
                                                       │
                                              ┌────────▼────────┐
                                              │  Scoring Engine  │
                                              │  Match (0-100)   │
                                              │  Interest (0-100)│
                                              │  Final = 0.7M+0.3I│
                                              └────────┬────────┘
                                                       │
                                              ┌────────▼────────┐
                                              │   Report Output  │
                                              │  • Rankings      │
                                              │  • Skill gaps    │
                                              │  • Conversations │
                                              │  • Actions       │
                                              │  • Reasoning     │
                                              └─────────────────┘
```

## Scoring Logic

**Match Score (Technical Fit):** Required Skills (40) + Tools (20) + Experience (20) + Preferred Skills (10) + Ownership (10)

**Interest Score (Behavioral Fit):** Role Alignment (40) + Seniority Fit (20) + Growth Potential (20) + Selectiveness (20)

**Final Score** = 0.7 × Match + 0.3 × Interest

## What Makes This Work

1. **Hybrid Matching:** "STA" → expanded to "static timing analysis" → token overlap with JD = 1.0. Pure embeddings gave 0.10 for the same pair.

2. **Compound Decomposition:** JD says "PnR (Placement, CTS, Routing)" — the system splits this into sub-skills and checks each individually. A candidate with Placement + CTS + Routing gets full credit.

3. **Tool Equivalence:** FC Shell = Fusion Compiler. PT Shell = PrimeTime. ICC = ICC2. Defined as equivalence groups, scored as 1.0 automatically.

4. **Implicit Skill Inference:** "End-to-end Physical Design" implies PnR, Placement, CTS, Routing — added to candidate's skill pool without explicit mention.

5. **Deep PDF Extraction:** Real resumes don't have clean "Skills:" sections. The parser scans summaries, project descriptions, and inline mentions against a known skills database.

## Trade-offs & Decisions

| Decision | Why | Trade-off |
|---|---|---|
| **Offline-only (no LLM API)** | Zero cost, no rate limits, works anywhere | Less flexible than GPT-4 for edge cases |
| **sentence-transformers over full LLM** | 80MB model vs 7B+ parameters, runs on any laptop | Lower semantic range, compensated by hybrid approach |
| **Hybrid matching over pure embeddings** | Short terms ("STA", "PnR") embed poorly | Requires maintaining an alias map — but it's extensible |
| **Greedy assignment in matching** | Prevents one strong candidate skill from inflating multiple JD matches | May occasionally miss a valid secondary match |
| **Soft experience boundaries** | 3.9 yrs vs 4.0 yr minimum is a near-miss, not a rejection | Slightly less precise boundary enforcement |
| **Simulated interest (not real)** | Can't actually talk to candidates | Behavioral model based on seniority + match alignment — directionally useful |
| **Rule-based JD parser over LLM** | Deterministic, fast, no API dependency | Won't handle very unusual JD formats |

## Tech Stack
- **Python 3.10** — core language
- **Streamlit** — UI framework
- **sentence-transformers** (all-MiniLM-L6-v2) — semantic embeddings, fully offline
- **spaCy** (en_core_web_sm) — NLP for JD parsing
- **scikit-learn** — cosine similarity computation
- **PyMuPDF** — PDF text extraction for resume upload
- **NumPy/Pandas** — data handling

All free, no API keys, no trial tiers consumed.

## What I'd Improve With More Time
- LLM-powered JD parsing for unusual formats
- Real candidate database with vector search (FAISS/Chroma)
- Multi-language resume support
- Interview question generation from skill gaps
- Feedback loop to calibrate scoring thresholds per domain 
