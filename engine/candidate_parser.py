# engine/candidate_parser.py
# Domain-agnostic candidate / resume parser
# Works with structured text input (any domain)

import re


# ─────────────────────────────────────────────
# Implicit Skill Inference
# ─────────────────────────────────────────────

# If a candidate has THESE skills → they implicitly also know THESE
IMPLICIT_SKILLS = {
    # VLSI: end-to-end implies sub-skills
    "end-to-end physical design": [
        "PnR", "Placement", "CTS", "Routing", "Floorplanning",
        "Timing Closure", "Physical Design Flow"
    ],
    "physical design flow": [
        "Floorplanning", "Placement", "CTS", "Routing"
    ],
    "pnr implementation": [
        "Placement", "CTS", "Routing"
    ],
    "timing closure": [
        "STA", "Static Timing Analysis"
    ],
    "signoff": [
        "DRC", "LVS", "Timing Signoff"
    ],
    # Web: full-stack implies both
    "full-stack": [
        "Frontend", "Backend", "API Development"
    ],
    "full stack": [
        "Frontend", "Backend", "API Development"
    ],
    "frontend development": [
        "HTML", "CSS", "JavaScript", "UI Development"
    ],
    "backend development": [
        "API Development", "Server-side", "Database"
    ],
    # ML: end-to-end implies pipeline
    "end-to-end ml": [
        "Data Preprocessing", "Model Training", "Model Deployment"
    ],
    "mlops": [
        "CI/CD", "Model Deployment", "Monitoring"
    ],
    # DevOps
    "cloud infrastructure": [
        "Deployment", "Monitoring", "Scaling"
    ],
}


def infer_implicit_skills(candidate: dict) -> list:
    """
    Infer additional skills based on what the candidate already has.
    Returns list of inferred skill strings.
    """
    all_text = " ".join(
        candidate.get("skills", []) +
        candidate.get("projects", [])
    ).lower()

    inferred = []
    for trigger, implied_skills in IMPLICIT_SKILLS.items():
        if trigger in all_text:
            inferred.extend(implied_skills)

    # Deduplicate
    seen = set()
    unique = []
    for s in inferred:
        s_lower = s.lower()
        if s_lower not in seen:
            seen.add(s_lower)
            unique.append(s)

    return unique

# High ownership keywords — works across ANY domain
HIGH_OWNERSHIP = [
    "end-to-end", "full ownership", "led", "owned", "architected",
    "designed and built", "drove", "delivered", "built from scratch",
    "independently", "single-handedly", "responsible for",
    "signoff", "full chip", "full stack", "complete lifecycle",
    "gdsii", "tape-out", "tapeout", "production deployment",
    "shipped", "launched", "from scratch", "greenfield",
    "system design", "platform", "entire",
]

# Medium ownership keywords
MEDIUM_OWNERSHIP = [
    "block-level", "block level", "module", "component",
    "contributed", "implemented", "collaborated", "participated",
    "worked on", "supported", "handled", "performed",
    "feature", "service", "endpoint", "partition",
]


def infer_ownership(text: str) -> str:
    """
    Infer ownership level from candidate's work description.
    Domain-agnostic — works for VLSI, Web Dev, ML, etc.
    """
    text_lower = text.lower()

    high_count = sum(1 for kw in HIGH_OWNERSHIP if kw in text_lower)
    med_count = sum(1 for kw in MEDIUM_OWNERSHIP if kw in text_lower)

    if high_count >= 3:
        return "end-to-end"
    elif high_count >= 1 or med_count >= 3:
        return "block"
    else:
        return "basic"


# ─────────────────────────────────────────────
# Confidence Score
# ─────────────────────────────────────────────

def compute_confidence(candidate: dict) -> float:
    """
    How complete/reliable is this candidate profile?
    Based on presence and richness of data.
    Returns 0-100.
    """
    score = 0

    # Name present
    if candidate.get("name"):
        score += 10

    # Skills present and substantial
    skills = candidate.get("skills", [])
    if len(skills) >= 5:
        score += 25
    elif len(skills) >= 3:
        score += 18
    elif len(skills) >= 1:
        score += 10

    # Tools present
    tools = candidate.get("tools", [])
    if len(tools) >= 3:
        score += 20
    elif len(tools) >= 1:
        score += 12

    # Experience present
    exp = candidate.get("experience", 0)
    if exp > 0:
        score += 15

    # Projects/work description present
    projects = candidate.get("projects", [])
    if len(projects) >= 3:
        score += 20
    elif len(projects) >= 1:
        score += 12

    # Ownership inference succeeded meaningfully
    ownership = candidate.get("ownership", "")
    if ownership == "end-to-end":
        score += 10
    elif ownership == "block":
        score += 5

    return min(score, 100)


# ─────────────────────────────────────────────
# List Cleaning
# ─────────────────────────────────────────────

def clean_list_items(lines: list, expand_parens: bool = False) -> list:
    """
    Clean and split list items from raw lines.
    If expand_parens=True, also extract parenthetical content as separate items.
    E.g., "ICC2, PrimeTime (PT Shell)" → ["ICC2", "PrimeTime", "PT Shell"]
    """
    items = []
    for line in lines:
        # Split by common delimiters (but NOT by & or "and" to preserve skill names)
        parts = re.split(r"\s*[•\-]\s*", line)
        for part in parts:
            # Further split by commas only if items look like a list
            sub_parts = [p.strip() for p in part.split(",")]
            for sp in sub_parts:
                sp = sp.strip().rstrip(".")
                if not sp or len(sp) <= 1:
                    continue

                if expand_parens and "(" in sp:
                    # Extract base name and parenthetical separately
                    # "PrimeTime (PT Shell)" → "PrimeTime" + "PT Shell"
                    base = re.sub(r"\s*\(.*?\)", "", sp).strip()
                    paren_contents = re.findall(r"\(([^)]+)\)", sp)

                    if base:
                        items.append(base)
                    for pc in paren_contents:
                        # Split parenthetical by / and ,
                        for sub in re.split(r"\s*/\s*|\s*,\s*", pc):
                            sub = sub.strip()
                            if sub and len(sub) > 1:
                                items.append(sub)
                else:
                    items.append(sp)
    return items


# ─────────────────────────────────────────────
# Section-Based Candidate Parser
# ─────────────────────────────────────────────

def parse_candidates(text: str) -> list:
    """
    Parse candidate profiles from structured text.

    Supports formats:
    - "Candidate 1:", "Candidate 2:", etc.
    - "---" separators
    - Section headers: Name:, Skills:, Tools:, Experience:, etc.

    Returns list of candidate dicts.
    """
    candidates = []

    # Split into candidate blocks
    blocks = re.split(r"(?i)(?:Candidate\s*\d+\s*:|---+)", text)

    for block in blocks:
        block = block.strip()
        if not block or len(block) < 20:
            continue

        candidate = {
            "name": "",
            "skills": [],
            "tools": [],
            "experience": 0,
            "ownership": "basic",
            "projects": [],
            "confidence": 0,
        }

        lines = [l.strip() for l in block.split("\n") if l.strip()]

        current_section = None
        skill_lines = []
        tool_lines = []
        project_lines = []

        for line in lines:
            line_lower = line.lower()

            # ── Detect section headers ──

            # Name
            if line_lower.startswith("name:"):
                candidate["name"] = line.split(":", 1)[1].strip()
                current_section = None
                continue

            # Experience
            if re.match(r"(?i)experience\s*(\(.*?\))?\s*:", line):
                exp_text = line.split(":", 1)[1].strip()
                exp_nums = re.findall(r"[\d.]+", exp_text)
                if exp_nums:
                    candidate["experience"] = float(exp_nums[0])
                current_section = None
                continue

            # Skills section
            if re.match(r"(?i)^skills?\s*[:：]", line):
                # Check for inline skills after the header
                remainder = re.sub(r"(?i)^skills?\s*[:：]\s*", "", line).strip()
                if remainder:
                    skill_lines.append(remainder)
                current_section = "skills"
                continue

            # Tools section
            if re.match(r"(?i)^tools?\s*(?:&\s*technologies?)?\s*[:：]", line):
                remainder = re.sub(r"(?i)^tools?\s*(?:&\s*technologies?)?\s*[:：]\s*", "", line).strip()
                if remainder:
                    tool_lines.append(remainder)
                current_section = "tools"
                continue

            # Projects / Key Work section
            if re.match(r"(?i)^(?:key\s*)?(?:projects?|work|achievements?|highlights?)\s*(?:/\s*\w+)?\s*[:：]", line):
                current_section = "projects"
                continue

            # Education (skip)
            if re.match(r"(?i)^education\s*[:：]", line):
                current_section = "education"
                continue

            # Certifications (skip)
            if re.match(r"(?i)^certifications?\s*[:：]", line):
                current_section = "certifications"
                continue

            # ── Collect lines under current section ──
            if current_section == "skills":
                skill_lines.append(line)
            elif current_section == "tools":
                tool_lines.append(line)
            elif current_section == "projects":
                project_lines.append(line)

        # ── Process collected lines ──
        candidate["skills"] = clean_list_items(skill_lines)
        candidate["tools"] = clean_list_items(tool_lines, expand_parens=True)
        candidate["projects"] = [
            re.sub(r"^[\•\-\*\→\▪\►]\s*", "", p).strip()
            for p in project_lines
            if p.strip() and len(p.strip()) > 5
        ]

        # Infer ownership from projects + skills text
        full_text = " ".join(project_lines + skill_lines)
        candidate["ownership"] = infer_ownership(full_text)

        # Infer implicit skills from context
        implicit = infer_implicit_skills(candidate)
        if implicit:
            candidate["inferred_skills"] = implicit
            # Add to skills pool (marked so scorer can use them)
            candidate["skills_pool"] = list(set(
                candidate["skills"] + candidate["tools"] + implicit
            ))
        else:
            candidate["inferred_skills"] = []
            candidate["skills_pool"] = list(set(
                candidate["skills"] + candidate["tools"]
            ))

        # Compute confidence
        candidate["confidence"] = compute_confidence(candidate)

        # Skip empty candidates
        if not candidate["name"]:
            continue

        candidates.append(candidate)

    return candidates


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import json

    # Test with VLSI candidates
    vlsi_data = """
Candidate 1:
Name: Prasad
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
Worked on timing-critical partitions (~1.2M instances, GHz range)

Candidate 2:
Name: Vishal S  
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
Handled designs with 1M–1.9M instances and GHz clocks
Performed floorplanning, CTS, routing, and timing optimization
"""

    print("=" * 60)
    print("TEST 1: VLSI Candidates")
    print("=" * 60)
    candidates = parse_candidates(vlsi_data)
    for c in candidates:
        print(json.dumps(c, indent=2))
        print()

    # Test with Web Dev candidates
    web_data = """
Candidate 1:
Name: Sarah Johnson
Skills:
React.js, TypeScript, Next.js
Node.js, Express, REST API development
PostgreSQL, MongoDB, Redis
Docker, AWS (EC2, S3, Lambda)
Git, CI/CD pipelines
Experience (years): 5.2
Tools:
VS Code, Postman, Jira, GitHub Actions
Key Projects / Work:
Built and launched a full-stack e-commerce platform from scratch
Led frontend architecture migration from Angular to React
Designed and deployed microservices on AWS ECS
Implemented CI/CD pipelines reducing deployment time by 60%

Candidate 2:
Name: Raj Patel
Skills:
JavaScript, React.js basics
HTML, CSS, Bootstrap
Basic Node.js
MySQL queries
Experience (years): 1.5
Tools:
VS Code, Git
Key Projects / Work:
Contributed to frontend bug fixes on team project
Built a personal portfolio website
Participated in code reviews
"""

    print("=" * 60)
    print("TEST 2: Web Dev Candidates")
    print("=" * 60)
    candidates2 = parse_candidates(web_data)
    for c in candidates2:
        print(json.dumps(c, indent=2))
        print()