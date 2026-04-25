# 📋 Sample Inputs & Outputs — TalentScout AI

## Sample Input 1: VLSI Domain

### Job Description (Input)
```
Job Title: Senior VLSI Physical Design Engineer

Job Summary:
We are seeking a skilled VLSI Physical Design Engineer with strong expertise
in backend ASIC design, focusing on timing closure and signoff.

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

Experience Required: 4–8 years
```

### Candidates (Input — structured text)
```
Candidate 1:
Name: Prasad
Skills:
Physical Design (Netlist → GDSII), STA & Timing Closure
Floorplanning, Placement, CTS, Routing
DRC/LVS/EM/Crosstalk Analysis, SDC Constraints, TCL Scripting, DMSA
Experience (years): 6.8
Tools: ICC2, PrimeTime, FC Shell, Calibre, Conformal

Candidate 2:
Name: Vishal S.
Skills:
Physical Design (PnR Implementation), Timing Analysis & Closure
Congestion Analysis, ECO Fixes, Floorplanning, Basic TCL Scripting
Experience (years): 3.9
Tools: Fusion Compiler, ICC2, PrimeTime, Genus

Candidate 3:
Name: Praveen
Skills:
End-to-End Physical Design (Synthesis → GDSII)
STA & Multi-mode/Multi-corner Timing Closure (DMSA)
Power Planning & Multi-voltage Design, IR Drop & EM Analysis
TCL, Shell, Perl Scripting
Experience (years): 7.8
Tools: DC, ICC, ICC2, Fusion Compiler, PrimeTime, Cadence Innovus, Calibre, ICV
```

### Output (Ranking)

| Rank | Candidate | Match Score | Interest Score | Final Score | Verdict |
|------|-----------|-------------|----------------|-------------|---------|
| #1 | Prasad | 86.3 | 82 | 85.0 | Strong Hire |
| #2 | Praveen | 79.4 | 71 | 76.9 | Hire |
| #3 | Vishal S. | 54.3 | 63 | 56.9 | Needs Evaluation |

### Output (Skill Gap — Vishal S.)
```
✅ TCL scripting ← Basic TCL Scripting (0.97)
✅ Static Timing Analysis (STA) & Timing Closure ← Timing Analysis & Closure (0.80)
✅ PnR (Placement, CTS, Routing) ← Physical Design (PnR Implementation) (0.60)
✅ ICC2 / Fusion Compiler / PrimeTime ← Fusion Compiler (0.55)
❌ Physical Design Flow (Floorplan to GDSII) — closest: Floorplanning (0.47)
❌ SDC constraints development — closest: ICC2 (0.27)
❌ DRC, LVS, IR Drop, and EM analysis — closest: ECO Fixes (0.29)
```

### Output (Recommended Actions)
```
📌 Interview Prasad for senior/lead roles requiring STA, Timing Closure
   and end-to-end ownership
📌 Interview Praveen — probe depth in PnR and SDC during interview
📌 Hold Vishal S. — significant gaps; consider for junior pipeline
```

---

## Sample Input 2: Web Development Domain

### Job Description (Input)
```
Job Title: Senior Full-Stack Developer

Required Skills:
Proficiency in React.js and TypeScript
Experience with Node.js and Express backend
Knowledge of PostgreSQL and MongoDB databases
Familiarity with REST API design and GraphQL
Experience with Git version control

Preferred Skills:
Docker and Kubernetes, AWS or GCP, CI/CD pipelines

Experience Required: 3-6 years
```

### Candidates (Input)
```
Candidate 1:
Name: Sarah Johnson
Skills: React.js, TypeScript, Next.js, Node.js, Express, REST API,
PostgreSQL, MongoDB, Redis, Docker, AWS, Git, CI/CD
Experience (years): 5.2
Tools: VS Code, Postman, Jira, GitHub Actions

Candidate 2:
Name: Raj Patel
Skills: JavaScript, React.js, HTML, CSS, Bootstrap, Node.js, MySQL
Experience (years): 1.5
Tools: VS Code, Git
```

### Output (Ranking)

| Rank | Candidate | Match Score | Interest Score | Final Score | Verdict |
|------|-----------|-------------|----------------|-------------|---------|
| #1 | Sarah Johnson | 99.0 | 90 | 96.3 | Strong Hire |
| #2 | Raj Patel | 65.0 | 80 | 69.5 | Consider |

### Output (Simulated Conversation — Sarah Johnson)
```
Recruiter:
Hi Sarah, we have an opening for a Senior Full-Stack Developer
that seems to align with your background.

Sarah Johnson:
That sounds like a great fit. My experience in React.js, TypeScript,
Node.js aligns well with what you're describing. I'd be happy to
discuss further and learn about the growth path in this role.
```

---

## Sample Input 3: PDF Resume Upload

### Input
- JD: Same VLSI JD as above
- Candidates: 4 PDF resumes uploaded (Vikram Kumar, Meghana R, Rama Krishna Ketha, Veernapu Ashok)

### Output (Ranking)

| Rank | Candidate | Match Score | Interest Score | Final Score | Verdict | Source |
|------|-----------|-------------|----------------|-------------|---------|--------|
| #1 | Rama Krishna Ketha | 97.0 | 93 | 95.8 | Strong Hire | Syn_LEC_Rama_Krishna_2.8yrs.pdf |
| #2 | Vikram Kumar | 83.5 | 81 | 82.8 | Hire | STA_Vikram_5+Yrs.pdf |
| #3 | Veernapu Ashok | 75.4 | 81 | 77.1 | Hire | PNR_Ashok_4.6yrs.pdf |
| #4 | Meghana R | 68.7 | 77 | 71.2 | Consider | PD_Meghana_R_3.5_yrs.pdf |

### Output (Agent Reasoning Steps)
```
1. Parsed JD → extracted 7 required skills, 3 preferred skills, 14 tools
2. Detected Domain → VLSI / Chip Design
3. Parsed 4 candidates → extracted skills, tools, experience, ownership level
4. Semantic matching → hybrid similarity (token + embedding) with compound skill support
5. Scored candidates → weighted model: Skills (40) + Tools (20) + Experience (20) + Preferred (10) + Ownership (10)
6. Simulated interest → behavioral scoring based on role alignment, seniority, growth potential
7. Ranked & decided → Final = (0.7 × Match) + (0.3 × Interest) → verdicts assigned
8. Implicit skill inference → inferred additional skills from candidate context
```