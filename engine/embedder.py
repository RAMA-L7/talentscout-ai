# engine/embedder.py
# Semantic Engine — Foundation for domain-agnostic matching
# Hybrid approach: semantic embeddings + token overlap + compound matching

import re
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# ─────────────────────────────────────────────
# Singleton Model Loader
# ─────────────────────────────────────────────
_model = None


def get_model():
    global _model
    if _model is None:
        print("⏳ Loading semantic model (first time only)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ Model loaded.")
    return _model


# ─────────────────────────────────────────────
# Abbreviation / Alias Map
# ─────────────────────────────────────────────

ALIAS_MAP = {
    # VLSI — tools & concepts
    "sta": "static timing analysis",
    "pnr": "placement and routing",
    "cts": "clock tree synthesis",
    "drc": "design rule check",
    "lvs": "layout versus schematic",
    "eco": "engineering change order",
    "gdsii": "gdsii tapeout layout",
    "icc2": "icc2 synopsys physical design",
    "icc": "icc synopsys physical design",
    "primetime": "primetime timing analysis",
    "pt shell": "primetime timing analysis shell",
    "pt": "primetime timing analysis",
    "fc shell": "fusion compiler synopsys physical design shell",
    "fc": "fusion compiler synopsys physical design",
    "fm shell": "formality verification equivalence checking shell",
    "fusion compiler": "fusion compiler synopsys physical design",
    "innovus": "innovus cadence physical design",
    "calibre": "calibre siemens signoff drc lvs",
    "icv": "icv synopsys signoff verification",
    "dc": "design compiler synopsys synthesis",
    "genus": "genus cadence synthesis tool",
    "conformal": "conformal cadence equivalence checking lec",
    "lec": "logic equivalence checking conformal verification",
    "dmsa": "distributed multi scenario timing analysis",
    "mcmm": "multi corner multi mode timing analysis",
    "mscts": "multi source clock tree synthesis",
    "sdc": "sdc synopsys design constraints timing",
    # Web / Software
    "react": "react javascript frontend ui framework",
    "react.js": "react javascript frontend ui framework",
    "node.js": "nodejs backend javascript server runtime",
    "node": "nodejs backend javascript server runtime",
    "express": "express nodejs backend web framework",
    "express.js": "express nodejs backend web framework",
    "html": "html web markup frontend",
    "css": "css web styling frontend design",
    "js": "javascript programming language",
    "javascript": "javascript programming language web",
    "typescript": "typescript typed javascript programming",
    "angular": "angular frontend javascript framework",
    "vue": "vue frontend javascript framework",
    "vue.js": "vue frontend javascript framework",
    "django": "django python web backend framework",
    "flask": "flask python web backend framework",
    "fastapi": "fastapi python web api backend framework",
    "rest api": "rest api web service backend endpoint",
    "graphql": "graphql api query language",
    "mongodb": "mongodb nosql document database",
    "postgresql": "postgresql relational sql database",
    "postgres": "postgresql relational sql database",
    "mysql": "mysql relational sql database",
    "redis": "redis in-memory cache database",
    "nextjs": "nextjs react fullstack framework",
    "next.js": "nextjs react fullstack framework",
    # DevOps / Cloud
    "docker": "docker containerization deployment devops",
    "kubernetes": "kubernetes container orchestration deployment",
    "k8s": "kubernetes container orchestration deployment",
    "aws": "aws amazon web services cloud platform",
    "gcp": "gcp google cloud platform",
    "azure": "azure microsoft cloud platform",
    "terraform": "terraform infrastructure as code provisioning",
    "jenkins": "jenkins cicd build automation pipeline",
    "ci/cd": "cicd continuous integration deployment pipeline",
    "ansible": "ansible configuration management automation",
    "nginx": "nginx web server reverse proxy",
    # Data / ML
    "tensorflow": "tensorflow deep learning ml framework",
    "pytorch": "pytorch deep learning ml framework",
    "pandas": "pandas python data analysis library",
    "numpy": "numpy python numerical computing",
    "scikit-learn": "scikit learn machine learning python",
    "sklearn": "scikit learn machine learning python",
    "nlp": "natural language processing text ai",
    "llm": "large language model ai",
    "sql": "sql structured query language database",
    "spark": "apache spark distributed data processing",
    "hadoop": "hadoop distributed data processing big data",
    "tableau": "tableau data visualization analytics",
    "power bi": "power bi microsoft data visualization",
    # Mobile
    "flutter": "flutter cross platform mobile app dart",
    "react native": "react native cross platform mobile javascript",
    "swift": "swift apple ios macos programming",
    "kotlin": "kotlin android mobile programming jvm",
    # General
    "python": "python programming language",
    "java": "java programming language enterprise",
    "c++": "c++ programming language systems",
    "c#": "csharp programming language dotnet microsoft",
    "go": "go golang programming language backend",
    "golang": "go golang programming language backend",
    "rust": "rust programming language systems safety",
    "git": "git version control source code",
    "agile": "agile software development methodology",
    "scrum": "scrum agile project management",
    "tcl": "tcl scripting language eda automation",
    "perl": "perl scripting language text processing",
    "shell": "shell bash scripting linux automation",
}

# ─────────────────────────────────────────────
# Tool Equivalence Groups
# ─────────────────────────────────────────────
# Items in the same group are considered equivalent (score = 1.0)

EQUIVALENCE_GROUPS = [
    {"fc shell", "fusion compiler", "fc"},
    {"pt shell", "primetime", "pt"},
    {"icc", "icc2"},
    {"calibre", "icv"},  # Both are signoff tools
    {"conformal", "lec"},
    {"dc", "genus"},  # Both are synthesis tools
    {"react", "react.js"},
    {"node", "node.js"},
    {"express", "express.js"},
    {"vue", "vue.js"},
    {"next.js", "nextjs"},
    {"postgres", "postgresql"},
    {"k8s", "kubernetes"},
    {"sklearn", "scikit-learn"},
    {"golang", "go"},
]


def are_equivalent(text1: str, text2: str) -> bool:
    """Check if two items are in the same equivalence group."""
    t1 = text1.strip().lower()
    t2 = text2.strip().lower()

    if t1 == t2:
        return True

    for group in EQUIVALENCE_GROUPS:
        if t1 in group and t2 in group:
            return True

    return False


# ─────────────────────────────────────────────
# Compound Skill Handling
# ─────────────────────────────────────────────

def split_compound_skill(skill: str) -> list:
    """
    Break a compound skill into sub-components.
    "PnR (Placement, CTS, Routing)" → ["PnR", "Placement", "CTS", "Routing"]
    "DRC, LVS, IR Drop, and EM analysis" → ["DRC", "LVS", "IR Drop", "EM analysis"]
    "ICC2 / Fusion Compiler / PrimeTime" → ["ICC2", "Fusion Compiler", "PrimeTime"]
    """
    components = []

    # Extract base name (before parentheses)
    base = re.sub(r"\s*\(.*?\)", "", skill).strip()
    if base:
        components.append(base)

    # Extract parenthetical content
    paren_matches = re.findall(r"\(([^)]+)\)", skill)
    for pm in paren_matches:
        parts = re.split(r"\s*[,/]\s*|\s+and\s+|\s*&\s*", pm)
        components.extend([p.strip() for p in parts if p.strip()])

    # If no parentheses, try splitting the whole thing by , / & and
    if not paren_matches and any(d in skill for d in [",", "/", " & ", " and "]):
        parts = re.split(r"\s*[,/]\s*|\s+and\s+|\s*&\s*", skill)
        components = [p.strip() for p in parts if p.strip()]

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for c in components:
        c_lower = c.lower()
        if c_lower not in seen and len(c) > 1:
            seen.add(c_lower)
            unique.append(c)

    return unique if unique else [skill]


def compound_match_score(jd_skill: str, candidate_items: list, threshold: float) -> tuple:
    """
    Match a potentially compound JD skill against candidate items.
    If the JD skill has sub-components, check if candidate covers ALL of them.

    Returns (score, best_match_text)
    """
    sub_skills = split_compound_skill(jd_skill)

    if len(sub_skills) <= 1:
        # Simple skill — use normal matching
        return None, None  # Signal to use standard matching

    # Check how many sub-components the candidate covers
    matched_subs = 0
    match_details = []

    for sub in sub_skills:
        best_score = 0.0
        best_item = ""

        for cand_item in candidate_items:
            # Check equivalence first
            if are_equivalent(sub, cand_item):
                score = 1.0
            else:
                score = _raw_hybrid_similarity(sub, cand_item)

            if score > best_score:
                best_score = score
                best_item = cand_item

        if best_score >= threshold:
            matched_subs += 1
            match_details.append(f"{sub}")

    if not sub_skills:
        return None, None

    ratio = matched_subs / len(sub_skills)

    # If candidate covers most sub-components, give high score
    if ratio >= 0.75:
        return max(0.75, ratio), f"{', '.join(match_details)} ({matched_subs}/{len(sub_skills)} sub-skills)"
    elif ratio >= 0.50:
        return ratio * 0.9, f"{', '.join(match_details)} ({matched_subs}/{len(sub_skills)} sub-skills)"
    else:
        return ratio * 0.7, f"partial: {', '.join(match_details)}" if match_details else None


# ─────────────────────────────────────────────
# Core Similarity Functions
# ─────────────────────────────────────────────

def expand_text(text: str) -> str:
    """Expand abbreviations to canonical form."""
    lookup = text.strip().lower()
    if lookup in ALIAS_MAP:
        return ALIAS_MAP[lookup]
    return lookup


def tokenize(text: str) -> set:
    """Break text into lowercase tokens for overlap matching."""
    text = expand_text(text)
    tokens = set(re.findall(r'[a-z0-9#+.]+', text.lower()))
    tokens = {t for t in tokens if len(t) > 1 or t in {'c', 'r'}}
    return tokens


def token_similarity(text1: str, text2: str) -> float:
    """Jaccard-like overlap on expanded tokens."""
    t1 = tokenize(text1)
    t2 = tokenize(text2)
    if not t1 or not t2:
        return 0.0
    intersection = t1 & t2
    union = t1 | t2
    if not union:
        return 0.0
    return len(intersection) / len(union)


def get_embeddings(texts: list) -> np.ndarray:
    """Convert list of texts to embedding vectors."""
    model = get_model()
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=False)


def embedding_similarity(text1: str, text2: str) -> float:
    """Pure semantic similarity via embeddings."""
    e1 = expand_text(text1)
    e2 = expand_text(text2)
    embeddings = get_embeddings([e1, e2])
    score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return float(max(0.0, score))


def _raw_hybrid_similarity(text1: str, text2: str) -> float:
    """Internal hybrid similarity without equivalence check."""
    tok_score = token_similarity(text1, text2)
    sem_score = embedding_similarity(text1, text2)
    return max(tok_score, sem_score)


def hybrid_similarity(text1: str, text2: str) -> float:
    """
    Combined score: equivalence > token_overlap > semantic_similarity
    """
    # Check equivalence first (instant 1.0)
    if are_equivalent(text1, text2):
        return 1.0

    return _raw_hybrid_similarity(text1, text2)


def semantic_similarity(text1: str, text2: str) -> float:
    """Public API — uses hybrid matching."""
    return hybrid_similarity(text1, text2)


def batch_similarity(queries: list, targets: list) -> np.ndarray:
    """
    Compute hybrid similarity matrix between two lists.
    Returns (len(queries), len(targets)) matrix.
    """
    if not queries or not targets:
        return np.array([])

    # Token matrix (fast)
    tok_matrix = np.zeros((len(queries), len(targets)))
    for i, q in enumerate(queries):
        for j, t in enumerate(targets):
            # Check equivalence first
            if are_equivalent(q, t):
                tok_matrix[i][j] = 1.0
            else:
                tok_matrix[i][j] = token_similarity(q, t)

    # Semantic matrix (batch embedding)
    q_expanded = [expand_text(q) for q in queries]
    t_expanded = [expand_text(t) for t in targets]
    q_emb = get_embeddings(q_expanded)
    t_emb = get_embeddings(t_expanded)
    sem_matrix = cosine_similarity(q_emb, t_emb)

    return np.maximum(tok_matrix, sem_matrix)


# ─────────────────────────────────────────────
# Core Matching Functions (with compound support)
# ─────────────────────────────────────────────

def best_match_scores(candidate_items: list, jd_items: list, threshold: float = 0.45) -> dict:
    """
    For each JD item, find the best matching candidate item.
    Supports compound skills: "PnR (Placement, CTS, Routing)"
    Uses greedy assignment to prevent double-counting.
    """
    if not candidate_items or not jd_items:
        return {}

    results = {}
    used_candidates = set()

    # Phase 1: Handle compound skills first
    compound_results = {}
    simple_jd_items = []

    for jd_item in jd_items:
        comp_score, comp_match = compound_match_score(jd_item, candidate_items, threshold)
        if comp_score is not None and comp_score >= threshold:
            compound_results[jd_item] = {
                "best_match": comp_match,
                "score": round(comp_score, 3),
                "matched": True
            }
        else:
            simple_jd_items.append(jd_item)

    # Phase 2: Handle simple skills with greedy assignment
    if simple_jd_items:
        sim_matrix = batch_similarity(simple_jd_items, candidate_items)

        # Sort by best available score (strongest matches first)
        jd_scored = []
        for i, jd_item in enumerate(simple_jd_items):
            best_score = float(np.max(sim_matrix[i]))
            jd_scored.append((i, jd_item, best_score))
        jd_scored.sort(key=lambda x: x[2], reverse=True)

        for i, jd_item, _ in jd_scored:
            row = sim_matrix[i].copy()

            # Mask used candidates
            for used_idx in used_candidates:
                row[used_idx] = -1

            best_idx = int(np.argmax(row))
            best_score = float(row[best_idx])

            if best_score >= threshold:
                used_candidates.add(best_idx)

            results[jd_item] = {
                "best_match": candidate_items[best_idx],
                "score": round(best_score, 3),
                "matched": best_score >= threshold
            }

    # Merge compound + simple results (preserving original JD order)
    final = {}
    for jd_item in jd_items:
        if jd_item in compound_results:
            final[jd_item] = compound_results[jd_item]
        elif jd_item in results:
            final[jd_item] = results[jd_item]

    return final


def compute_match_ratio(candidate_items: list, jd_items: list, threshold: float = 0.45) -> float:
    """What fraction of JD items are matched by the candidate?"""
    if not jd_items:
        return 0.0
    matches = best_match_scores(candidate_items, jd_items, threshold)
    matched_count = sum(1 for v in matches.values() if v["matched"])
    return matched_count / len(jd_items)


def skill_gap_analysis(candidate_items: list, jd_items: list, threshold: float = 0.45) -> dict:
    """
    Identify what the candidate is missing from the JD.
    Returns matched items, gaps, and match ratio.
    """
    matches = best_match_scores(candidate_items, jd_items, threshold)

    matched = []
    gaps = []

    for jd_item, info in matches.items():
        if info["matched"]:
            matched.append({
                "jd_skill": jd_item,
                "candidate_skill": info["best_match"],
                "score": info["score"]
            })
        else:
            gaps.append({
                "jd_skill": jd_item,
                "closest": info["best_match"],
                "score": info["score"]
            })

    return {
        "matched": matched,
        "gaps": gaps,
        "match_ratio": len(matched) / max(len(jd_items), 1)
    }


def detect_domain(skills: list) -> str:
    """Auto-detect domain from a list of skills."""
    domain_signatures = {
        "VLSI / Chip Design": [
            "physical design", "timing closure", "STA", "GDSII",
            "placement and routing", "synthesis", "DRC", "LVS"
        ],
        "Web Development": [
            "React", "Node.js", "HTML", "CSS", "JavaScript",
            "REST API", "frontend", "backend"
        ],
        "Data Science / ML": [
            "machine learning", "deep learning", "pandas", "TensorFlow",
            "PyTorch", "NLP", "data analysis", "statistics"
        ],
        "DevOps / Cloud": [
            "Docker", "Kubernetes", "AWS", "CI/CD", "Terraform",
            "Jenkins", "cloud infrastructure", "monitoring"
        ],
        "Mobile Development": [
            "Android", "iOS", "Flutter", "React Native",
            "Swift", "Kotlin", "mobile app"
        ],
        "Cybersecurity": [
            "penetration testing", "network security", "encryption",
            "vulnerability assessment", "SIEM", "firewall"
        ],
        "Embedded Systems": [
            "RTOS", "firmware", "microcontroller", "embedded C",
            "ARM", "IoT", "device drivers"
        ],
        "Healthcare / Clinical": [
            "patient care", "clinical trials", "EMR", "HIPAA",
            "medical devices", "diagnostics"
        ],
        "Finance / Fintech": [
            "risk analysis", "trading", "compliance", "blockchain",
            "payment systems", "quantitative analysis"
        ],
        "General Software Engineering": [
            "software development", "agile", "system design",
            "microservices", "testing", "debugging"
        ]
    }

    if not skills:
        return "General"

    best_domain = "General"
    best_score = 0.0

    for domain, signatures in domain_signatures.items():
        total = 0.0
        for sig in signatures:
            scores = [hybrid_similarity(skill, sig) for skill in skills]
            total += max(scores) if scores else 0.0
        avg = total / len(signatures)

        if avg > best_score:
            best_score = avg
            best_domain = domain

    return best_domain


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🔍 Testing Hybrid Semantic Engine...\n")

    # Test 1: Equivalence
    print("--- Equivalence Tests ---")
    pairs = [
        ("FC Shell", "Fusion Compiler"),
        ("PT Shell", "PrimeTime"),
        ("ICC", "ICC2"),
        ("React", "React.js"),
    ]
    for a, b in pairs:
        score = hybrid_similarity(a, b)
        eq = are_equivalent(a, b)
        print(f"  {a:20s} ↔ {b:20s} | equiv={eq}  score={score:.3f}")

    # Test 2: Compound skill matching
    print("\n--- Compound Skill Tests ---")
    cand = ["Placement", "CTS", "Routing", "Floorplanning", "STA"]
    jd_skill = "PnR (Placement, CTS, Routing)"
    score, match = compound_match_score(jd_skill, cand, threshold=0.45)
    print(f"  JD: {jd_skill}")
    print(f"  Candidate has: {cand}")
    print(f"  Score: {score:.3f} | Match: {match}")

    cand2 = ["DRC/LVS/EM/Crosstalk Analysis", "IR Drop"]
    jd_skill2 = "DRC, LVS, IR Drop, and EM analysis"
    score2, match2 = compound_match_score(jd_skill2, cand2, threshold=0.45)
    print(f"\n  JD: {jd_skill2}")
    print(f"  Candidate has: {cand2}")
    print(f"  Score: {score2:.3f} | Match: {match2}")

    # Test 3: Full skill gap with compounds
    print("\n--- Full Skill Gap (VLSI) ---")
    gap = skill_gap_analysis(
        candidate_items=[
            "Physical Design (Netlist → GDSII)",
            "Static Timing Analysis (STA) & Timing Closure",
            "Floorplanning", "Placement", "CTS", "Routing",
            "DRC/LVS/EM/Crosstalk Analysis",
            "SDC Constraints Development",
            "TCL Scripting", "DMSA",
            "ICC2", "PrimeTime", "FC Shell", "Calibre",
        ],
        jd_items=[
            "Physical Design Flow (Floorplan to GDSII)",
            "Static Timing Analysis (STA) & Timing Closure",
            "PnR (Placement, CTS, Routing)",
            "ICC2 / Fusion Compiler / PrimeTime",
            "DRC, LVS, IR Drop, and EM analysis",
            "SDC constraints development",
            "TCL scripting",
        ],
        threshold=0.45
    )
    for m in gap["matched"]:
        print(f"  ✅ {m['jd_skill']:45s} ← {m['candidate_skill']} ({m['score']:.3f})")
    for g in gap["gaps"]:
        print(f"  ❌ {g['jd_skill']:45s}   closest: {g['closest']} ({g['score']:.3f})")
    print(f"  Match Ratio: {gap['match_ratio']:.2f}")