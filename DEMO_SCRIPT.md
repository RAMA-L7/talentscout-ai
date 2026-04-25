# 🎬 TalentScout AI — Demo Video Script

**Total Duration:** 3–5 minutes
**Tool:** OBS Studio / Loom / Screen recorder of your choice

---

## Scene 1: Intro (15 sec)

**Show:** App title screen with empty inputs

**Say/Caption:**
> "TalentScout AI — an offline, domain-agnostic AI recruiter that works with any JD, any domain, any experience level. No API keys needed."

---

## Scene 2: PDF Resume Upload (45 sec)

**Actions:**
1. Paste the VLSI JD in the left panel (already typed or use sample checkbox)
2. Switch candidate mode to **"Upload Resumes (PDF)"**
3. Drag & drop 4 PDF resumes
4. Show the "4 resume(s) uploaded" confirmation
5. Click **"Run Analysis"**

**Say/Caption:**
> "We paste a VLSI Physical Design JD and upload 4 real candidate resumes as PDFs. One click — the system handles everything."

---

## Scene 3: Auto Parsing Results (30 sec)

**Actions:**
1. Expand **"Parsed JD (Debug)"** — show extracted skills, tools, experience range, domain
2. Expand **"Parsed Candidates (Debug)"** — show one candidate's extracted skills, tools, inferred skills
3. Collapse both

**Say/Caption:**
> "The system auto-detected VLSI domain, extracted 7 required skills, 3 preferred skills, 14 tools from the JD — and deep-extracted skills from every section of each resume including summaries and project descriptions."

---

## Scene 4: Quick Summary + Ranking (30 sec)

**Actions:**
1. Scroll to **Quick Summary** cards — show all 4 candidates with scores
2. Scroll to **Final Ranking** table

**Say/Caption:**
> "Rama Krishna scores 95.8 — Strong Hire. Vikram 82.8 — Hire. Ashok 77.1 — Hire. Meghana 71.2 — Consider. Clear separation with meaningful verdicts."

---

## Scene 5: Deep Explainability (60 sec)

**Actions:**
1. Scroll to **#1 Rama Krishna** evaluation
2. Show the **score breakdown table** (skills 40/40, tools 20/20, etc.)
3. Show **Skill Analysis** — highlight the ✅ compound matching:
   - "PnR (Placement, CTS, Routing) ← 4/4 sub-skills"
   - "ICC2 / Fusion Compiler / PrimeTime ← 3/3 sub-skills"
4. Scroll to **simulated conversation** — show the eager junior tone
5. Scroll to **explanation** — show match + interest reasoning

**Say/Caption:**
> "Every score is fully transparent. Compound skills like PnR are decomposed — Placement, CTS, Routing matched individually. Tool equivalence means FC Shell matches Fusion Compiler automatically. The simulated conversation adapts to seniority — Rama Krishna gets an eager junior tone because he has 2.8 years."

---

## Scene 6: Skill Gaps + Actions (30 sec)

**Actions:**
1. Scroll to **#2 Vikram Kumar** — show the ❌ gaps:
   - "DRC, LVS, IR Drop — closest: DCT (0.26)"
   - "SDC constraints — closest: DMSA (0.35)"
2. Scroll to **Recommended Actions** section
3. Highlight: "Interview Vikram — probe depth in DRC/LVS and SDC during interview"

**Say/Caption:**
> "The system shows exactly what each candidate is missing and recommends specific interview focus areas. This is actionable intelligence, not just a score."

---

## Scene 7: Head-to-Head + Agent Reasoning (20 sec)

**Actions:**
1. Show **Head-to-Head: #1 vs #2** comparison
2. Show **Agent Reasoning Steps** — 8-step transparent trace

**Say/Caption:**
> "Head-to-head comparison shows Rama Krishna leads in required skills (40 vs 30.2) while Vikram has more experience (5.2 vs 2.8 years). The agent reasoning trace shows exactly how the system reached its conclusion — parse, detect, score, rank, decide."

---

## Scene 8: Domain Switch (45 sec)

**Actions:**
1. Clear the JD
2. Paste a **Web Development JD** (Senior Full-Stack Developer)
3. Switch to **Paste Text** mode for candidates
4. Paste 2 web dev candidates (one strong, one weak)
5. Click **Run Analysis**
6. Show results — different domain, different skills, same system

**Say/Caption:**
> "Now watch — same system, completely different domain. We switch from VLSI to Web Development. React, Node.js, PostgreSQL — the semantic engine understands all of it. No reconfiguration needed. That's what domain-agnostic means."

---

## Scene 9: Download + Closing (15 sec)

**Actions:**
1. Click **"Download Report as Markdown"**
2. Show the downloaded file

**Say/Caption:**
> "One-click report export. TalentScout AI — an offline AI recruiter that automates the first 70% of hiring decisions. Built with Python, Streamlit, and sentence-transformers. No API keys. Fully explainable. Any domain."

---

## 📋 Checklist Before Recording

- [ ] App running: `streamlit run app.py`
- [ ] Sample VLSI JD ready
- [ ] 4 PDF resumes ready for upload
- [ ] Web Dev JD + 2 text candidates ready for domain switch
- [ ] Browser zoomed to ~90% for readability
- [ ] Screen recorder set to 1080p
- [ ] Close unnecessary tabs/notifications

## 🎥 Recording Tips

- **Don't rush** — let each screen render fully before moving
- **Pause 2 seconds** on important results (ranking table, skill gaps)
- **Use mouse cursor** to highlight key numbers as you explain
- **Record in one take** if possible — cuts feel less natural for demos
- **Background music** — optional, keep it subtle and royalty-free