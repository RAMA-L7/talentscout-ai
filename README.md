# 🚀 TalentScout AI

**Domain-agnostic AI-powered recruitment decision system**

TalentScout AI is an intelligent hiring assistant that reads any job description, evaluates candidates, simulates recruiter-candidate engagement, and delivers explainable hiring decisions — all running **fully offline** with no API keys required.

> **Not a scoring tool. An AI Recruiter.**

---

## 🎯 What It Does

```
Job Description → Parse → Score → Rank → Explain → Decide
```

Given a JD and candidate profiles (text or PDF resumes), TalentScout AI:

1. **Understands the job** — extracts skills, tools, experience, ownership expectations
2. **Evaluates candidates** — semantic skill matching, not keyword matching
3. **Predicts interest** — simulates whether a candidate would accept the role
4. **Ranks and decides** — Strong Hire / Hire / Consider / Not Recommended
5. **Explains everything** — skill gaps, score breakdowns, head-to-head comparisons
6. **Recommends actions** — specific next steps for each candidate

---

## 🧠 Why It's Different

| Traditional ATS | TalentScout AI |
|---|---|
| Keyword matching | Semantic understanding |
| "React" ≠ "frontend" | "React" ≈ "frontend" ✅ |
| Single domain | Any domain, any JD |
| Black box scores | Full explainability |
| Needs API keys | Fully offline |
| Just filters | Reasons like a recruiter |

**Core innovation:** Hybrid semantic matching (sentence-transformers + token overlap + compound skill decomposition + tool equivalence) replaces rigid keyword matching, making the system work across VLSI, Web Dev, Data Science, DevOps, Healthcare, Finance — any domain.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                   Streamlit UI                   │
│         (Dual Mode: Text Paste / PDF Upload)     │
└──────────────────────┬──────────────────────────┘
                       │
          ┌────────────▼────────────┐
          │      JD Parser          │  ← spaCy NLP + regex
          │   (jd_parser.py)        │     section detection
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │   Candidate Parser      │  ← structured text parser
          │ (candidate_parser.py)   │     OR
          │   Resume Parser         │  ← PDF deep extraction
          │  (resume_parser.py)     │     (PyMuPDF + pattern matching)
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │    Semantic Engine       │  ← sentence-transformers
          │    (embedder.py)         │     all-MiniLM-L6-v2 (offline)
          │                          │     hybrid similarity
          │  • Token matching        │     compound skill decomposition
          │  • Embedding similarity  │     tool equivalence groups
          │  • Alias expansion       │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │    Scoring Engine        │  ← weighted multi-factor scoring
          │    (scorer.py)           │
          │                          │
          │  Match Score (100):      │
          │   Skills    40           │
          │   Tools     20           │
          │   Experience 20          │
          │   Preferred  10          │
          │   Ownership  10          │
          │                          │
          │  Interest Score (100):   │
          │   Role Alignment  40     │
          │   Seniority Fit   20     │
          │   Growth          20     │
          │   Selectiveness   20     │
          │                          │
          │  Final = 0.7×Match       │
          │        + 0.3×Interest    │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │    Ranking Engine        │  ← sort + verdict + tier
          │    (ranker.py)           │     head-to-head comparison
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │    Report Generator      │  ← dynamic conversations
          │    (reporter.py)         │     explanations, actions
          │                          │     agent reasoning trace
          └──────────────────────────┘
```

---

## 📊 Scoring Logic (Deep Dive)

### Match Score — Technical Fit (0–100)

| Component | Weight | How It Works |
|---|---|---|
| Required Skills | 40 pts | Semantic match ratio against JD skills. Compound skills (e.g., "PnR: Placement, CTS, Routing") are decomposed and matched individually. |
| Tools | 20 pts | Matched via equivalence groups (FC Shell = Fusion Compiler) + semantic similarity. Candidate skills are pooled with tools. |
| Experience | 20 pts | Soft boundary matching. 3.9 yrs vs 4.0 yr minimum = 18/20, not 0. Overqualified candidates get mild penalty. |
| Preferred Skills | 10 pts | Semantic match against nice-to-have skills. |
| Ownership | 10 pts | Inferred from action verbs: "led", "owned", "built from scratch" = end-to-end. "Contributed", "worked on" = block-level. |

### Interest Score — Behavioral Fit (0–100)

| Component | Weight | How It Works |
|---|---|---|
| Role Alignment | 40 pts | Higher match score → more likely interested. Bonus for experience sweet spot. |
| Seniority Fit | 20 pts | Overqualified candidates may be less interested. Underqualified may be eager. |
| Growth Potential | 20 pts | Junior candidates see more growth opportunity. Step-up roles get bonus. |
| Selectiveness | 20 pts | Senior candidates are pickier. Junior candidates are more open. |

### Final Score

```
Final = (0.7 × Match Score) + (0.3 × Interest Score)
```

### Verdict Thresholds

| Score | Verdict |
|---|---|
| 85+ | Strong Hire |
| 72–84 | Hire |
| 58–71 | Consider |
| 45–57 | Needs Evaluation |
| < 45 | Not Recommended |

---

## 🔍 Semantic Matching — How It Works

TalentScout doesn't just compare strings. It **understands meaning** through three layers:

### Layer 1: Alias Expansion
```
"STA" → "static timing analysis"
"FC Shell" → "fusion compiler synopsys physical design shell"
"React.js" → "react javascript frontend ui framework"
```

### Layer 2: Token Overlap (Jaccard)
After expansion, tokens are compared. "STA" and "Static Timing Analysis" share all tokens → score = 1.0.

### Layer 3: Embedding Similarity
Using `all-MiniLM-L6-v2` (384-dim vectors), conceptual relationships are captured:
- "React.js" ↔ "frontend development" → 0.41
- "Docker" ↔ "containerization" → 0.60

### Layer 4: Compound Decomposition
```
JD: "PnR (Placement, CTS, Routing)"
→ Split into: ["PnR", "Placement", "CTS", "Routing"]
→ Check each against candidate skills
→ 4/4 matched = 1.0
```

### Layer 5: Tool Equivalence
```
FC Shell = Fusion Compiler
PT Shell = PrimeTime
ICC = ICC2
PostgreSQL = Postgres
Kubernetes = k8s
```

**Final score = max(token_score, embedding_score, equivalence_score)**

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- ~2 GB disk space (for PyTorch + sentence-transformers model)

### Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/talentscout-ai.git
cd talentscout-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Run
streamlit run app.py
```

On first run, the semantic model (`all-MiniLM-L6-v2`, ~80MB) downloads automatically.

### Requirements

```
streamlit
sentence-transformers
spacy
scikit-learn
numpy
pandas
PyMuPDF
```

---

## 💻 Usage

### Mode 1: PDF Resume Upload
1. Paste or upload a Job Description
2. Upload candidate resumes as PDF files (multiple supported)
3. Click **Run Analysis**
4. View ranked results with full explainability

### Mode 2: Structured Text
1. Paste a Job Description
2. Paste candidate profiles in structured format:
```
Candidate 1:
Name: John Smith
Skills:
React.js, TypeScript, Node.js
PostgreSQL, MongoDB
Experience (years): 5.2
Tools:
VS Code, Docker, AWS
Key Projects / Work:
Built full-stack e-commerce platform
Led frontend architecture migration
```
3. Click **Run Analysis**

### Output Includes
- **Quick Summary Cards** — at-a-glance scores and verdicts
- **Detailed Score Breakdown** — per-component scoring table
- **Skill Gap Analysis** — ✅ matched / ❌ missing for every requirement
- **Simulated Conversations** — seniority-aware recruiter-candidate dialogue
- **Match & Interest Explanations** — why each score was given
- **Head-to-Head Comparison** — #1 vs #2 advantages
- **Recruiter Actions** — specific next steps per candidate
- **Agent Reasoning Steps** — transparent 8-step decision trace
- **Downloadable Report** — one-click markdown export

---

## 📁 Project Structure

```
talentscout/
├── app.py                     # Streamlit UI (dual-mode input)
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── engine/
│   ├── __init__.py
│   ├── embedder.py            # Semantic engine (foundation)
│   │                           #   - hybrid similarity
│   │                           #   - alias expansion
│   │                           #   - compound decomposition
│   │                           #   - tool equivalence
│   │                           #   - domain detection
│   ├── jd_parser.py           # JD parser (spaCy NLP + regex)
│   ├── candidate_parser.py    # Structured text candidate parser
│   ├── resume_parser.py       # PDF resume deep extractor
│   ├── scorer.py              # Weighted scoring engine
│   ├── ranker.py              # Ranking + verdicts + comparison
│   ├── reporter.py            # Dynamic report generator
│   └── validator.py           # Input validation
└── data/
    ├── JD.txt                 # Sample job description
    └── candidates_data.txt    # Sample candidate profiles
```

---

## 🧪 Testing Individual Components

```bash
# Test semantic engine
python -m engine.embedder

# Test JD parser (3 domain tests)
python -m engine.jd_parser

# Test candidate parser
python -m engine.candidate_parser

# Test scorer
python -m engine.scorer

# Test ranker
python -m engine.ranker

# Test resume parser
python -m engine.resume_parser
```

---

## 🌐 Domains Tested

| Domain | Status |
|---|---|
| VLSI / Chip Design | ✅ Tested with real resumes |
| Web Development | ✅ Tested with sample data |
| Data Science / ML | ✅ Tested with sample data |
| DevOps / Cloud | ✅ Domain detection verified |
| Mobile Development | ✅ Domain detection verified |
| Cybersecurity | ✅ Domain detection verified |
| Embedded Systems | ✅ Domain detection verified |
| Healthcare | ✅ Domain detection verified |
| Finance / Fintech | ✅ Domain detection verified |

---

## 🔑 Key Design Decisions

1. **No API keys** — Entire system runs offline using `all-MiniLM-L6-v2` sentence-transformer model. No OpenAI, no Gemini, no cloud dependency.

2. **Hybrid matching over pure embeddings** — Short technical terms like "STA" or "PnR" embed poorly. Token overlap after alias expansion solves this.

3. **Compound skill decomposition** — JD requirements like "PnR (Placement, CTS, Routing)" are split and each sub-skill is matched independently.

4. **Greedy assignment** — Each candidate skill can only match one JD requirement, preventing inflation where one strong skill matches everything.

5. **Implicit skill inference** — "End-to-end Physical Design" implies knowledge of PnR, Placement, CTS, Routing without needing explicit mention.

6. **Deep PDF extraction** — Skills are extracted from ALL resume sections (summary, projects, skills), not just clean "Skills:" headers.

7. **Soft experience boundaries** — 3.9 years vs 4.0 year minimum is a near-miss, not a rejection. Real hiring works this way.

---

## 📝 License

MIT License

---

## 🤝 Contributing

Pull requests welcome. For major changes, please open an issue first.

---

*Built with Python, Streamlit, sentence-transformers, spaCy, and scikit-learn.*