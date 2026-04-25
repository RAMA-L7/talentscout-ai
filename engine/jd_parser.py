# engine/jd_parser.py
# Domain-agnostic JD Parser using spaCy + regex
# No LLM required — works fully offline

import re
import spacy

# Load spaCy model once
_nlp = None


def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


# ─────────────────────────────────────────────
# Section Detection
# ─────────────────────────────────────────────

SECTION_PATTERNS = {
    "role": [
        r"(?i)job\s*title\s*[:：]",
        r"(?i)role\s*title\s*[:：]",
        r"(?i)position\s*[:：]",
        r"(?i)designation\s*[:：]",
    ],
    "summary": [
        r"(?i)job\s*summary\s*[:：]",
        r"(?i)overview\s*[:：]",
        r"(?i)about\s*the\s*role\s*[:：]",
        r"(?i)description\s*[:：]",
        r"(?i)role\s*description\s*[:：]",
    ],
    "required_skills": [
        r"(?i)required\s*skills?\s*[:：]",
        r"(?i)must[\s-]*have\s*[:：]",
        r"(?i)key\s*skills?\s*[:：]",
        r"(?i)core\s*skills?\s*[:：]",
        r"(?i)technical\s*skills?\s*[:：]",
        r"(?i)qualifications?\s*[:：]",
        r"(?i)requirements?\s*[:：]",
        r"(?i)what\s*you.?ll\s*need\s*[:：]",
        r"(?i)skills?\s*(?:required|needed)\s*[:：]",
    ],
    "preferred_skills": [
        r"(?i)preferred\s*skills?\s*[:：]",
        r"(?i)nice[\s-]*to[\s-]*have\s*[:：]",
        r"(?i)good[\s-]*to[\s-]*have\s*[:：]",
        r"(?i)bonus\s*[:：]",
        r"(?i)desired\s*[:：]",
        r"(?i)additional\s*skills?\s*[:：]",
        r"(?i)plus\s*[:：]",
    ],
    "tools": [
        r"(?i)tools?\s*(?:&|and)?\s*(?:technologies|tech|stack)\s*[:：]",
        r"(?i)tech\s*stack\s*[:：]",
        r"(?i)technologies?\s*[:：]",
        r"(?i)software\s*[:：]",
        r"(?i)platforms?\s*[:：]",
    ],
    "responsibilities": [
        r"(?i)key\s*responsibilities\s*[:：]",
        r"(?i)responsibilities\s*[:：]",
        r"(?i)what\s*you.?ll\s*do\s*[:：]",
        r"(?i)duties\s*[:：]",
        r"(?i)role\s*involves?\s*[:：]",
        r"(?i)day[\s-]*to[\s-]*day\s*[:：]",
    ],
    "experience": [
        r"(?i)experience\s*(?:required|needed)?\s*[:：]",
        r"(?i)years?\s*(?:of)?\s*experience\s*[:：]",
        r"(?i)exp\s*[:：]",
    ],
    "nice_to_have": [
        r"(?i)nice[\s-]*to[\s-]*have\s*[:：]",
        r"(?i)good[\s-]*to[\s-]*have\s*[:：]",
        r"(?i)bonus\s*(?:skills?)?\s*[:：]",
    ],
}


def detect_sections(text: str) -> dict:
    """
    Split JD text into sections based on header patterns.
    Returns dict: {"role": "...", "required_skills": "...", ...}
    """
    lines = text.split("\n")
    sections = {}
    current_section = "summary"
    current_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        matched_section = None
        remainder = ""
        for section_name, patterns in SECTION_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, stripped):
                    matched_section = section_name
                    remainder = re.sub(pattern, "", stripped).strip()
                    break
            if matched_section:
                break

        if matched_section:
            if current_lines:
                sections[current_section] = "\n".join(current_lines)
            current_section = matched_section
            current_lines = [remainder] if remainder else []
        else:
            current_lines.append(stripped)

    if current_lines:
        sections[current_section] = "\n".join(current_lines)

    return sections


# ─────────────────────────────────────────────
# Extraction Helpers
# ─────────────────────────────────────────────

def extract_list_items(text: str) -> list:
    """Extract bullet points / list items from a text block."""
    items = []
    lines = text.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        cleaned = re.sub(r"^[\•\-\*\→\▪\►]\s*", "", line)
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", cleaned)
        cleaned = cleaned.strip()

        if cleaned and len(cleaned) > 2:
            items.append(cleaned)

    return items


def extract_experience_range(text: str) -> tuple:
    """Extract min/max years of experience from text."""

    # Pattern: X-Y years or X to Y years
    range_match = re.search(
        r"(\d+\.?\d*)\s*[-–—to]+\s*(\d+\.?\d*)\s*(?:years?|yrs?)",
        text, re.IGNORECASE
    )
    if range_match:
        return float(range_match.group(1)), float(range_match.group(2))

    # Pattern: X+ years
    plus_match = re.search(
        r"(\d+\.?\d*)\s*\+\s*(?:years?|yrs?)",
        text, re.IGNORECASE
    )
    if plus_match:
        min_exp = float(plus_match.group(1))
        return min_exp, min_exp + 5

    # Pattern: minimum/at least X years
    min_match = re.search(
        r"(?:minimum|at\s*least|min)\s*(\d+\.?\d*)\s*(?:years?|yrs?)",
        text, re.IGNORECASE
    )
    if min_match:
        min_exp = float(min_match.group(1))
        return min_exp, min_exp + 5

    # Pattern: plain "X years"
    plain_match = re.search(
        r"(\d+\.?\d*)\s*(?:years?|yrs?)",
        text, re.IGNORECASE
    )
    if plain_match:
        val = float(plain_match.group(1))
        return max(0, val - 2), val + 2

    return 0, 100


def extract_role_title(sections: dict, full_text: str) -> str:
    """Extract the job title / role name."""

    if "role" in sections:
        role_text = sections["role"].strip()
        for line in role_text.split("\n"):
            line = line.strip()
            if line and len(line) > 3:
                return line

    lines = full_text.strip().split("\n")
    for line in lines[:5]:
        line = line.strip()
        if re.match(r"(?i)^(job\s*description|jd|posting|vacancy)\s*$", line):
            continue
        if line and len(line) > 3 and len(line) < 100:
            if not re.match(r"^[\•\-\*]", line) and not line.endswith(":"):
                return line

    return "Not Specified"


def infer_ownership_level(text: str) -> str:
    """Infer expected ownership level from JD text — domain-agnostic."""
    text_lower = text.lower()

    high_indicators = [
        "end-to-end", "full ownership", "lead", "architect",
        "drive", "own the", "take ownership", "independently",
        "senior", "principal", "staff", "head of",
        "signoff", "full chip", "full stack", "complete lifecycle",
    ]

    medium_indicators = [
        "collaborate", "contribute", "participate", "support",
        "work with", "assist", "help", "team member",
        "block-level", "module-level", "component",
    ]

    high_count = sum(1 for kw in high_indicators if kw in text_lower)
    med_count = sum(1 for kw in medium_indicators if kw in text_lower)

    if high_count >= 3:
        return "High"
    elif high_count >= 1 or med_count >= 2:
        return "Medium"
    else:
        return "Low"


# ─────────────────────────────────────────────
# Tool Extraction (FIXED — smart approach)
# ─────────────────────────────────────────────

def extract_tools_from_skills(skill_lines: list) -> list:
    """
    Extract tool/technology names that are embedded inside skill descriptions.
    E.g., "Proficiency in tools like ICC2 / Fusion Compiler / PrimeTime"
    → ["ICC2", "Fusion Compiler", "PrimeTime"]
    """
    tools = []

    # Patterns that introduce tool names within a skill line
    tool_intro_patterns = [
        r"(?i)(?:tools?\s*(?:like|such\s*as|including)?|proficiency\s*in|experience\s*with)\s*(.+)",
        r"(?i)(?:using|via|through)\s+(.+)",
    ]

    for line in skill_lines:
        # First: remove all parenthetical content for cleaner splitting
        # But save parenthetical content separately to extract tool names
        paren_contents = re.findall(r"\(([^)]+)\)", line)
        clean_line = re.sub(r"\s*\([^)]*\)", "", line).strip()

        # Check if the line mentions tools explicitly
        for pattern in tool_intro_patterns:
            m = re.search(pattern, clean_line)
            if m:
                tool_text = m.group(1)
                # Split by / , & and or
                parts = re.split(r"\s*/\s*|\s*,\s*|\s+and\s+|\s+or\s+|\s*&\s*", tool_text)
                for part in parts:
                    part = part.strip().rstrip(".")
                    # Remove any leftover parentheses
                    part = re.sub(r"[()]", "", part).strip()
                    if part and len(part) > 1:
                        tools.append(part)

        # Extract tools from parenthetical content
        for pm in paren_contents:
            parts = re.split(r"\s*/\s*|\s*,\s*", pm)
            for part in parts:
                part = part.strip()
                # Remove any stray parentheses
                part = re.sub(r"[()]", "", part).strip()
                # Only grab items that look like tool names or abbreviations
                if part and len(part) <= 30 and re.match(r"^[A-Z]", part):
                    tools.append(part)

    return tools


def extract_inline_tools(text: str) -> list:
    """
    Extract tool names mentioned inline in text.
    Looks for patterns like capitalized multi-word names, abbreviations, etc.
    Much more conservative than the previous approach.
    """
    tools = set()

    # Pattern 1: Known tool-like patterns (word with digits, e.g., ICC2, Node.js)
    tech_pattern = re.findall(r"\b[A-Z][a-zA-Z]*\d+\b", text)
    tools.update(tech_pattern)

    # Pattern 2: Dot-separated tech names (Node.js, React.js, Vue.js)
    dot_pattern = re.findall(r"\b[A-Z][a-z]+\.(?:js|py|io|sh|NET)\b", text)
    tools.update(dot_pattern)

    # Pattern 3: ALL-CAPS abbreviations (3+ chars, likely tools/tech)
    abbr_pattern = re.findall(r"\b[A-Z]{3,}\b", text)
    # Filter out common non-tool abbreviations
    skip_abbrs = {
        "JOB", "AND", "THE", "FOR", "WITH", "FROM", "HAVE", "NOT",
        "ARE", "BUT", "ALL", "HAS", "HIS", "HER", "OUR", "WHO",
        "HOW", "MAY", "CAN", "ITS", "WILL", "MUST", "SHALL",
        "DESCRIPTION", "REQUIRED", "PREFERRED", "SKILLS", "KEY",
        "SUMMARY", "TITLE", "YEARS", "ROLE", "WORK", "ALSO",
    }
    for abbr in abbr_pattern:
        if abbr not in skip_abbrs:
            tools.add(abbr)

    return list(tools)


# ─────────────────────────────────────────────
# Skills Extraction (smart splitting)
# ─────────────────────────────────────────────

def extract_skills_from_section(text: str) -> list:
    """
    Extract individual skills from a section.
    Handles multi-skill lines and cleans prefixes.
    """
    items = extract_list_items(text)
    skills = []

    for item in items:
        # Remove common prefixes (multi-pass to handle chained prefixes)
        cleaned = item
        for _ in range(3):  # up to 3 passes
            prev = cleaned
            cleaned = re.sub(
                r"(?i)^(strong\s+)?(?:knowledge|experience|expertise|proficiency|"
                r"familiarity|exposure|hands[\s-]*on|working\s+knowledge|"
                r"understanding|ability|good|solid|deep|proven|demonstrated|"
                r"excellent)\s*(?:of|in|with|on|to)?\s*",
                "", cleaned
            ).strip()
            # Also remove "tools like", "tools such as" prefix
            cleaned = re.sub(
                r"(?i)^tools?\s*(?:like|such\s+as|including|e\.?g\.?)\s*",
                "", cleaned
            ).strip()
            if cleaned == prev:
                break

        if cleaned:
            skills.append(cleaned)

    return skills


# ─────────────────────────────────────────────
# Main Parser
# ─────────────────────────────────────────────

def parse_jd(jd_text: str) -> dict:
    """
    Parse any Job Description into structured format.
    Works across all domains — no LLM required.
    """
    # Step 1: Detect sections
    sections = detect_sections(jd_text)

    # Step 2: Extract role title
    role = extract_role_title(sections, jd_text)

    # Step 3: Extract required skills
    required_skills = []
    if "required_skills" in sections:
        required_skills = extract_skills_from_section(sections["required_skills"])

    # Step 4: Extract preferred skills
    preferred_skills = []
    for key in ["preferred_skills", "nice_to_have"]:
        if key in sections:
            preferred_skills.extend(extract_skills_from_section(sections[key]))

    # Step 5: Extract tools (layered approach)
    tools = []

    # 5a: If there's a dedicated tools section, use it
    if "tools" in sections:
        tools = extract_list_items(sections["tools"])

    # 5b: Extract tools embedded in skill lines
    all_skill_lines = required_skills + preferred_skills
    embedded_tools = extract_tools_from_skills(all_skill_lines)
    tools.extend(embedded_tools)

    # 5c: Extract inline tools from required_skills and preferred_skills sections
    for key in ["required_skills", "preferred_skills"]:
        if key in sections:
            inline = extract_inline_tools(sections[key])
            tools.extend(inline)

    # Deduplicate tools (case-insensitive)
    seen = set()
    unique_tools = []
    for t in tools:
        t_lower = t.lower().strip()
        if t_lower not in seen and len(t_lower) > 1:
            seen.add(t_lower)
            unique_tools.append(t.strip())
    tools = unique_tools

    # Step 6: Extract experience
    exp_min, exp_max = 0, 100
    if "experience" in sections:
        exp_min, exp_max = extract_experience_range(sections["experience"])
    else:
        exp_min, exp_max = extract_experience_range(jd_text)

    # Step 7: Extract responsibilities
    responsibilities = []
    if "responsibilities" in sections:
        responsibilities = extract_list_items(sections["responsibilities"])

    # Step 8: Infer ownership level
    ownership_level = infer_ownership_level(jd_text)

    # Step 9: Detect domain
    from engine.embedder import detect_domain
    all_skills = required_skills + preferred_skills
    domain = detect_domain(all_skills) if all_skills else "General"

    return {
        "role": role,
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "tools": tools,
        "experience_min": exp_min,
        "experience_max": exp_max,
        "responsibilities": responsibilities,
        "ownership_level": ownership_level,
        "domain": domain,
    }


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import json

    # Test with VLSI JD
    vlsi_jd = """
JOB DESCRIPTION

Job Title:
Senior VLSI Physical Design Engineer

Job Summary:
We are seeking a skilled VLSI Physical Design Engineer with strong expertise in backend ASIC design.

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
Familiarity with automation and scripting (Perl/Shell)
Experience with Cadence Innovus or equivalent tools

Experience Required:
4–8 years

Key Responsibilities:
Perform end-to-end physical design implementation from netlist to GDSII
Drive timing closure across all corners and modes
Develop and validate SDC timing constraints
Execute floorplanning, placement, CTS, and routing
"""

    print("=" * 60)
    print("TEST 1: VLSI JD")
    print("=" * 60)
    result = parse_jd(vlsi_jd)
    print(json.dumps(result, indent=2))

    # Test with Web Dev JD
    web_jd = """
Job Title:
Senior Full-Stack Developer

Job Summary:
Looking for an experienced full-stack developer to build modern web applications.

Required Skills:
Proficiency in React.js and TypeScript
Experience with Node.js and Express backend
Knowledge of PostgreSQL and MongoDB databases
Familiarity with REST API design and GraphQL
Experience with Git version control

Preferred Skills:
Experience with Docker and Kubernetes
Knowledge of AWS or GCP cloud platforms
Familiarity with CI/CD pipelines

Experience Required:
3-6 years

Key Responsibilities:
Design and build responsive web applications
Develop RESTful APIs and microservices
Collaborate with product and design teams
"""

    print("\n" + "=" * 60)
    print("TEST 2: Web Dev JD")
    print("=" * 60)
    result2 = parse_jd(web_jd)
    print(json.dumps(result2, indent=2))

    # Test with Data Science JD
    ds_jd = """
Position:
Machine Learning Engineer

Description:
We need an ML engineer to build and deploy production ML systems.

Requirements:
Strong Python programming skills
Experience with TensorFlow or PyTorch
Knowledge of NLP and transformer architectures
Experience with data pipelines using Spark or Airflow
Understanding of statistical modeling and A/B testing

Nice-to-Have:
Experience with MLOps tools (MLflow, Kubeflow)
Knowledge of distributed computing
Experience with LLM fine-tuning

Experience:
5+ years

Responsibilities:
Build and train ML models for production use
Design data pipelines and feature engineering workflows
Deploy models using containerized services
"""

    print("\n" + "=" * 60)
    print("TEST 3: Data Science / ML JD")
    print("=" * 60)
    result3 = parse_jd(ds_jd)
    print(json.dumps(result3, indent=2))