# engine/resume_parser.py
# PDF Resume Parser — extracts structured candidate data from resume PDFs
# Handles real-world resume formats: bullet points, tables, inline mentions

import re
import fitz  # PyMuPDF


# ─────────────────────────────────────────────
# PDF Text Extraction
# ─────────────────────────────────────────────

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract all text from a PDF file (bytes)."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text("text") + "\n"
        doc.close()
        return text.strip()
    except Exception as e:
        print(f"⚠️ PDF extraction error: {e}")
        return ""


# ─────────────────────────────────────────────
# Resume Section Detection
# ─────────────────────────────────────────────

RESUME_SECTIONS = {
    "summary": [
        r"(?i)(?:professional\s+)?(?:experience\s+)?summary\s*[:：]?\s*$",
        r"(?i)objective\s*[:：]?\s*$",
        r"(?i)about\s+me\s*[:：]?\s*$",
        r"(?i)profile\s*[:：]?\s*$",
        r"(?i)career\s+objective\s*[:：]?\s*$",
        r"(?i)summary\s+of\s+expertise\s*[:：]?\s*$",
        r"(?i)experience\s+summary\s*[:：]?\s*$",
    ],
    "skills": [
        r"(?i)(?:technical\s+)?skills?\s*[:：]?\s*$",
        r"(?i)core\s+competenc(?:ies|y)\s*[:：]?\s*$",
        r"(?i)technologies?\s*[:：]?\s*$",
        r"(?i)tech(?:nical)?\s+(?:skills?|stack|expertise)\s*[:：]?\s*$",
        r"(?i)areas?\s+of\s+expertise\s*[:：]?\s*$",
        r"(?i)key\s+skills?\s*[:：]?\s*$",
    ],
    "experience": [
        r"(?i)(?:work\s+)?experience\s*[:：]?\s*$",
        r"(?i)professional\s+experience\s*[:：]?\s*$",
        r"(?i)employment\s+history\s*[:：]?\s*$",
        r"(?i)work\s+history\s*[:：]?\s*$",
    ],
    "projects": [
        r"(?i)projects?\s*[:：]?\s*$",
        r"(?i)key\s+projects?\s*[:：]?\s*$",
        r"(?i)project\s+details?\s*[:：]?\s*$",
        r"(?i)notable\s+projects?\s*[:：]?\s*$",
    ],
    "education": [
        r"(?i)education\s*[:：]?\s*$",
        r"(?i)academic\s*[:：]?\s*$",
        r"(?i)qualifications?\s*[:：]?\s*$",
    ],
    "certifications": [
        r"(?i)certifications?\s*[:：]?\s*$",
        r"(?i)licenses?\s*(?:&|and)?\s*certifications?\s*[:：]?\s*$",
    ],
    "tools_section": [
        r"(?i)tools?\s*(?:&|and)?\s*(?:technologies|tech)?\s*[:：]?\s*$",
        r"(?i)software\s*[:：]?\s*$",
    ],
}


def detect_resume_sections(text: str) -> dict:
    """Split resume text into sections."""
    lines = text.split("\n")
    sections = {}
    current_section = "header"
    current_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        matched_section = None
        for section_name, patterns in RESUME_SECTIONS.items():
            for pattern in patterns:
                if re.match(pattern, stripped):
                    matched_section = section_name
                    break
            if matched_section:
                break

        if matched_section:
            if current_lines:
                sections[current_section] = "\n".join(current_lines)
            current_section = matched_section
            current_lines = []
        else:
            current_lines.append(stripped)

    if current_lines:
        sections[current_section] = "\n".join(current_lines)

    return sections


# ─────────────────────────────────────────────
# Name Extraction
# ─────────────────────────────────────────────

def extract_name(sections: dict, full_text: str) -> str:
    """Extract candidate name — typically the first prominent line."""
    header = sections.get("header", "")
    lines = header.split("\n")

    for line in lines[:5]:
        line = line.strip()
        if not line or len(line) < 3:
            continue

        # Skip emails, phones, URLs, addresses
        if re.search(r"@|http|www\.|\.com|\.org|\.net", line, re.IGNORECASE):
            continue
        if re.search(r"\+?\d[\d\s\-]{7,}", line):
            continue
        if re.search(r"\d{5,}", line):
            continue
        # Skip company names / headers
        if re.match(r"(?i)^(resume|curriculum|cv|page\s)", line):
            continue

        words = line.split()
        if 1 <= len(words) <= 5:
            alpha_ratio = sum(1 for w in words if w[0].isalpha()) / len(words)
            if alpha_ratio >= 0.8:
                name = re.sub(r"[,|•·].*$", "", line).strip()
                name = re.sub(r"(?i)^(mr\.?|ms\.?|mrs\.?|dr\.?)\s+", "", name).strip()
                if name and len(name) >= 3:
                    return name

    return "Unknown Candidate"


def extract_email(text: str) -> str:
    match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else ""


def extract_phone(text: str) -> str:
    match = re.search(r"[\+]?[\d][\d\s\-\(\)]{7,15}", text)
    return match.group(0).strip() if match else ""


# ─────────────────────────────────────────────
# Experience Extraction
# ─────────────────────────────────────────────

def extract_years_experience(sections: dict, full_text: str) -> float:
    """Extract total years of experience from multiple patterns."""

    patterns = [
        r"(\d+\.?\d*)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:total\s+)?(?:experience|exp)",
        r"(?:experience|exp)\s*(?:of)?\s*(\d+\.?\d*)\+?\s*(?:years?|yrs?)",
        r"(?:over|more\s+than|around|approximately|about|~|having\s+around)\s*(\d+\.?\d*)\s*(?:years?|yrs?)",
        r"(\d+\.?\d*)\s*(?:years?|yrs?)\s*(?:of)?\s*(?:total\s+)?(?:experience|exp)",
        r"having\s+(?:around\s+)?(\d+\.?\d*)\s*(?:years?|yrs?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            return float(match.group(1))

    # Strategy 2: Calculate from date ranges
    exp_text = sections.get("experience", "") + sections.get("projects", "")
    if exp_text:
        years = re.findall(r"(20\d{2}|19\d{2})", exp_text)
        if len(years) >= 2:
            years_int = [int(y) for y in years]
            span = max(years_int) - min(years_int)
            if 0 < span <= 40:
                return float(span)

    return 0


# ─────────────────────────────────────────────
# DEEP Skills & Tools Extraction
# ─────────────────────────────────────────────

# Known VLSI / EDA skills and tools
KNOWN_SKILLS_DB = {
    # VLSI skills
    "physical design", "sta", "static timing analysis", "timing closure",
    "pnr", "placement", "cts", "routing", "floorplanning", "floorplan",
    "clock tree synthesis", "eco", "drc", "lvs", "ir drop", "em analysis",
    "emir", "signoff", "timing signoff", "sdc", "sdc constraints",
    "power planning", "congestion", "crosstalk", "multi-voltage",
    "low power", "multi-corner", "multi-mode", "mcmm", "dmsa",
    "synthesis", "lec", "logical equivalence", "gdsii", "netlist",
    "rc extraction", "timing analysis", "setup", "hold",
    "clock gating", "retiming", "buffer insertion", "gate sizing",
    # Web / Software
    "react", "react.js", "node.js", "javascript", "typescript",
    "html", "css", "python", "java", "rest api", "graphql",
    "mongodb", "postgresql", "mysql", "redis", "docker",
    "kubernetes", "aws", "gcp", "azure", "ci/cd", "git",
    "microservices", "frontend", "backend", "full stack",
    # ML / Data
    "machine learning", "deep learning", "tensorflow", "pytorch",
    "nlp", "data analysis", "pandas", "numpy", "sql",
    # General
    "tcl", "tcl scripting", "perl", "shell", "python scripting",
    "verilog", "vhdl", "systemverilog", "automation",
    "scripting", "debugging", "agile",
}

KNOWN_TOOLS_DB = {
    # VLSI / EDA
    "icc2", "icc", "fusion compiler", "primetime", "pt", "pt-si", "ptc",
    "dc", "dct", "design compiler", "genus", "innovus",
    "calibre", "icv", "conformal", "starrc", "tweaker",
    "tempus", "quantus", "aprisa", "fc shell", "fm shell",
    "pt shell", "ptpx",
    # Web / Software
    "vs code", "postman", "jira", "github", "github actions",
    "jenkins", "terraform", "ansible", "nginx",
    # ML / Data
    "jupyter", "spark", "airflow", "mlflow", "tableau",
    # General
    "git", "linux", "unix", "windows",
}


def deep_extract_skills(sections: dict, full_text: str) -> list:
    """
    Extract skills from ALL sections of the resume — not just "Skills:".
    Scans summary, experience, projects, and skills sections.
    Uses both pattern matching and known skill database.
    """
    skills = set()
    full_lower = full_text.lower()

    # ── 1. Extract from explicit skills section ──
    if "skills" in sections:
        text = sections["skills"]
        lines = text.split("\n")
        for line in lines:
            # Handle "Domain: Physical Design" or "Domain Physical Design" format
            domain_match = re.match(r"(?i)domain\s*[:：]?\s*(.+)", line)
            if domain_match:
                skills.add(domain_match.group(1).strip())
                continue

            # Handle "Tools: X, Y, Z" format (inline)
            tools_match = re.match(r"(?i)tools?\s*[:：]\s*(.+)", line)
            if tools_match:
                continue  # Tools extracted separately

            # Handle "Language: Verilog" format
            lang_match = re.match(r"(?i)(?:languages?|scripting)\s*[:：]\s*(.+)", line)
            if lang_match:
                parts = re.split(r"\s*[,/&]\s*|\s+and\s+", lang_match.group(1))
                for p in parts:
                    p = p.strip().rstrip(".")
                    if p and len(p) > 1:
                        skills.add(p)
                continue

            # General skill items
            parts = re.split(r"\s*[•\-\*|,]\s*", line)
            for part in parts:
                part = part.strip().rstrip(".")
                if part and len(part) > 1 and len(part) < 80:
                    if not re.match(r"(?i)^(and|or|etc|the|with|for|in)$", part):
                        skills.add(part)

    # ── 2. Extract from summary section ──
    for key in ["summary", "header"]:
        if key in sections:
            text = sections[key]
            lines = text.split("\n")
            for line in lines:
                line = line.strip()
                # Remove bullet markers
                cleaned = re.sub(r"^[\•\-\*●▪►]\s*", "", line).strip()
                if not cleaned or len(cleaned) < 10:
                    continue

                # Extract skills mentioned in context
                # "5+ years experience in STA domain" → STA
                # "Good knowledge in TCL scripting" → TCL scripting
                # "experience in Placement, CTS, Routing" → Placement, CTS, Routing
                skill_patterns = [
                    r"(?i)(?:experience|expertise|knowledge|exposure|proficient|worked)\s+(?:in|on|with)\s+(.+?)(?:\.|$)",
                    r"(?i)(?:involved in|responsible for)\s+(.+?)(?:\.|$)",
                    r"(?i)(?:good|strong|solid|deep)\s+(?:knowledge|experience|exposure)\s+(?:in|on|of|with)\s+(.+?)(?:\.|$)",
                ]
                for pattern in skill_patterns:
                    matches = re.findall(pattern, cleaned)
                    for match in matches:
                        # Split by comma to get individual items
                        parts = re.split(r"\s*,\s*|\s+and\s+", match)
                        for part in parts:
                            part = part.strip().rstrip(".")
                            if part and len(part) > 2 and len(part) < 60:
                                skills.add(part)

    # ── 3. Scan against known skills database ──
    for known_skill in KNOWN_SKILLS_DB:
        if known_skill in full_lower:
            skills.add(known_skill.title() if len(known_skill) > 3 else known_skill.upper())

    # ── 4. Extract from project descriptions ──
    if "projects" in sections:
        text = sections["projects"]
        for known_skill in KNOWN_SKILLS_DB:
            if known_skill in text.lower():
                skills.add(known_skill.title() if len(known_skill) > 3 else known_skill.upper())

    # Clean up
    cleaned_skills = []
    seen = set()
    for s in skills:
        s = s.strip()
        s_lower = s.lower()
        # Skip very generic items
        if s_lower in {"etc", "and", "the", "for", "with", "as", "well", "also"}:
            continue
        if len(s) < 2 or len(s) > 80:
            continue
        if s_lower not in seen:
            seen.add(s_lower)
            cleaned_skills.append(s)

    return cleaned_skills


def deep_extract_tools(sections: dict, full_text: str) -> list:
    """
    Extract tools from ALL sections — skills section, project details, inline mentions.
    """
    tools = set()
    full_lower = full_text.lower()

    # ── 1. From skills section — "Tools: X, Y, Z" lines ──
    for key in ["skills", "tools_section"]:
        if key in sections:
            text = sections[key]
            lines = text.split("\n")
            for line in lines:
                # Match "Tools: X, Y, Z" or "EDA Tools: X, Y, Z"
                tools_match = re.match(
                    r"(?i)(?:eda\s+)?tools?\s*[:：]\s*(.+)", line
                )
                if tools_match:
                    parts = re.split(
                        r"\s*[,/]\s*|\s+and\s+|\s*&\s*",
                        tools_match.group(1)
                    )
                    for p in parts:
                        p = p.strip().rstrip(".")
                        # Clean "calibre(DRC & LVS)" → "Calibre"
                        p = re.sub(r"\s*\(.*?\)", "", p).strip()
                        if p and len(p) > 1:
                            tools.add(p)

    # ── 2. From project sections — "Tools: X, Y" or "PNR tool Used: X" ──
    if "projects" in sections:
        text = sections["projects"]
        lines = text.split("\n")
        for line in lines:
            tool_match = re.match(
                r"(?i)(?:tools?\s*(?:used)?|pnr\s+tools?\s*(?:used)?)\s*[:：]\s*(.+)",
                line
            )
            if tool_match:
                parts = re.split(
                    r"\s*[,/]\s*|\s+and\s+|\s*&\s*",
                    tool_match.group(1)
                )
                for p in parts:
                    p = p.strip().rstrip(".")
                    p = re.sub(r"\s*\(.*?\)", "", p).strip()
                    if p and len(p) > 1:
                        tools.add(p)

    # ── 3. Scan against known tools database ──
    for known_tool in KNOWN_TOOLS_DB:
        # Use word boundary matching for short tools
        if len(known_tool) <= 3:
            if re.search(r"\b" + re.escape(known_tool) + r"\b", full_lower):
                tools.add(known_tool.upper())
        else:
            if known_tool in full_lower:
                tools.add(known_tool.title())

    # Deduplicate
    seen = set()
    unique = []
    for t in tools:
        t = t.strip()
        t_lower = t.lower()
        if t_lower not in seen and len(t) > 1:
            seen.add(t_lower)
            unique.append(t)

    return unique


def extract_projects_from_resume(sections: dict) -> list:
    """Extract project descriptions."""
    projects = []

    for key in ["projects", "experience"]:
        if key in sections:
            text = sections[key]
            lines = text.split("\n")
            for line in lines:
                line = line.strip()
                cleaned = re.sub(r"^[\•\-\*\→\▪\►●]\s*", "", line).strip()
                if cleaned and len(cleaned) > 20:
                    projects.append(cleaned)

    return projects[:15]


# ─────────────────────────────────────────────
# Main Resume Parser
# ─────────────────────────────────────────────

def parse_resume_pdf(pdf_bytes: bytes, filename: str = "") -> dict:
    """
    Parse a single PDF resume into structured candidate data.
    Uses deep extraction to find skills across ALL sections.
    """
    from engine.candidate_parser import infer_ownership, infer_implicit_skills, compute_confidence

    text = extract_text_from_pdf(pdf_bytes)

    if not text:
        return {
            "name": filename.replace(".pdf", "") if filename else "Unknown",
            "skills": [],
            "tools": [],
            "experience": 0,
            "ownership": "basic",
            "projects": [],
            "inferred_skills": [],
            "skills_pool": [],
            "confidence": 0,
            "source": filename,
            "_parse_error": "Could not extract text from PDF",
        }

    sections = detect_resume_sections(text)

    # Extract fields using deep extraction
    name = extract_name(sections, text)
    skills = deep_extract_skills(sections, text)
    tools = deep_extract_tools(sections, text)
    experience = extract_years_experience(sections, text)
    projects = extract_projects_from_resume(sections)

    candidate = {
        "name": name,
        "skills": skills,
        "tools": tools,
        "experience": experience,
        "ownership": "basic",
        "projects": projects,
        "source": filename,
    }

    # Infer ownership
    full_text = " ".join(skills + projects)
    candidate["ownership"] = infer_ownership(full_text)

    # Infer implicit skills
    implicit = infer_implicit_skills(candidate)
    candidate["inferred_skills"] = implicit
    candidate["skills_pool"] = list(set(skills + tools + implicit))

    # Compute confidence
    candidate["confidence"] = compute_confidence(candidate)

    return candidate


def parse_multiple_pdfs(pdf_files: list) -> list:
    """
    Parse multiple PDF resumes.
    pdf_files: list of (filename, bytes) tuples
    Returns list of candidate dicts.
    """
    candidates = []
    for filename, pdf_bytes in pdf_files:
        candidate = parse_resume_pdf(pdf_bytes, filename)
        if candidate.get("name") and candidate.get("name") != "Unknown Candidate":
            candidates.append(candidate)
        elif candidate.get("skills"):
            candidate["name"] = filename.replace(".pdf", "").replace("_", " ").title()
            candidates.append(candidate)

    return candidates


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import json

    sample_resume = """
Vikram Kumar.

Professional Experience Summary:
● 5.2 years of total Experience in STA domain in VLSI industry
● Professional experience of 5+ years involved in Sub-system and block level Timing Closure,
RC Extraction, ECO's Generations etc.
● Good knowledge in TCL scripting
● Good exposure in DC, DCT, FC, PT-SI, PTC, Tweaker, DMSA and ICC2
● Having good experience in STA flow in Placement, CTS, Timing Closure, RC Extraction, ECO's.
● Provided regular feedback of Internal, Interface setup/hold timing analysis, timing DRC,
noise violations and constraints updates to the PD, RTL/DFT owners as needed.
● Experience on tech nodes is 3nm, 5nm, 7nm

Technical Skills:
Domain: Synthesis and STA
Tools: DC, DCT, StarRC, PT-SI, PTC, TWEAKER and DMSA
Language: Verilog

Project Details:
Project 7: Kanap_s (Camera module) - 
● Worked on STA for 3 HM's and TOP level.
● Complete responsible for timing closure, for 3 hm's and TOP level sta.
● Responsible for cleanup of all the check_timing, check_timing_constraints issues.
● Timing fixes on critical setup and hold paths.
● Rolling Tweaker for timing fixes in this Eco stage.
Tools: StarRC, PT-SI and TWEAKER
Technology: 3nm
"""

    sections = detect_resume_sections(sample_resume)
    print("=" * 50)
    print("SECTIONS DETECTED:")
    for s, content in sections.items():
        print(f"\n[{s}] ({len(content)} chars)")
        print(content[:150])

    print("\n" + "=" * 50)
    print("DEEP EXTRACTION:")
    print("=" * 50)
    print(f"\nName: {extract_name(sections, sample_resume)}")
    print(f"Experience: {extract_years_experience(sections, sample_resume)} years")

    skills = deep_extract_skills(sections, sample_resume)
    print(f"\nSkills ({len(skills)}):")
    for s in skills:
        print(f"  • {s}")

    tools = deep_extract_tools(sections, sample_resume)
    print(f"\nTools ({len(tools)}):")
    for t in tools:
        print(f"  • {t}")