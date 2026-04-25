# engine/scorer.py
# Domain-agnostic scoring engine using semantic matching
# No hardcoded skills, no domain-specific logic

from engine.embedder import (
    compute_match_ratio,
    skill_gap_analysis,
    semantic_similarity,
)


# ─────────────────────────────────────────────
# Match Score (Technical Fit) — out of 100
# ─────────────────────────────────────────────
# Breakdown:
#   Required Skills  → 40 pts
#   Tools            → 20 pts
#   Experience       → 20 pts
#   Preferred Skills → 10 pts
#   Ownership        → 10 pts

def score_required_skills(candidate: dict, jd: dict) -> tuple:
    """
    Score required skills match (0-40).
    Returns (score, gap_analysis_dict).
    Pools candidate skills + tools for matching, with stricter threshold.
    """
    cand_skills = candidate.get("skills", [])
    cand_tools = candidate.get("tools", [])
    jd_skills = jd.get("required_skills", [])

    if not jd_skills:
        return 40.0, {"matched": [], "gaps": [], "match_ratio": 1.0}

    # Pool skills + tools but deduplicate
    cand_pool = list(set(cand_skills + cand_tools))

    # Use stricter threshold for required skills
    gap = skill_gap_analysis(cand_pool, jd_skills, threshold=0.50)
    ratio = gap["match_ratio"]

    # Scoring curve with proper spread
    if ratio >= 0.90:
        score = 40
    elif ratio >= 0.75:
        score = 32 + (ratio - 0.75) * 53  # 32-40
    elif ratio >= 0.55:
        score = 22 + (ratio - 0.55) * 50  # 22-32
    elif ratio >= 0.35:
        score = 12 + (ratio - 0.35) * 50  # 12-22
    else:
        score = ratio * 34  # 0-12

    return round(score, 1), gap


def score_tools(candidate: dict, jd: dict) -> float:
    """Score tool match (0-20). Uses skills_pool."""
    cand_pool = candidate.get("skills_pool", candidate.get("tools", []))
    jd_tools = jd.get("tools", [])

    if not jd_tools:
        return 12.0

    ratio = compute_match_ratio(cand_pool, jd_tools, threshold=0.45)

    if ratio >= 0.80:
        return 20.0
    elif ratio >= 0.60:
        return 14 + (ratio - 0.60) * 30
    elif ratio >= 0.35:
        return 7 + (ratio - 0.35) * 28
    else:
        return ratio * 20


def score_experience(candidate: dict, jd: dict) -> float:
    """Score experience fit (0-20). Uses soft boundaries for near-matches."""
    exp = candidate.get("experience", 0)
    min_exp = jd.get("experience_min", 0)
    max_exp = jd.get("experience_max", 100)

    if min_exp <= exp <= max_exp:
        # Perfect fit
        return 20.0
    elif exp > max_exp:
        # Over-qualified: mild penalty (senior candidates are valuable)
        overshoot = exp - max_exp
        if overshoot <= 1:
            return 19.0  # Barely over — almost no penalty
        elif overshoot <= 3:
            return 17.0
        else:
            penalty = min(overshoot * 0.8, 5)
            return 20.0 - penalty
    else:
        # Under-qualified: soft boundary
        shortfall = min_exp - exp
        if shortfall <= 0.5:
            return 18.0  # 3.5 vs 4.0 → nearly full credit
        elif shortfall <= 1.0:
            return 15.0  # 3.0 vs 4.0 → partial penalty
        elif shortfall <= 2.0:
            return 10.0
        else:
            # Big gap
            if min_exp == 0:
                return 12.0
            ratio = exp / min_exp
            return max(ratio * 12, 3.0)


def score_preferred_skills(candidate: dict, jd: dict) -> float:
    """Score preferred/nice-to-have skills (0-10). Uses skills_pool."""
    cand_pool = candidate.get("skills_pool", candidate.get("skills", []))
    pref_skills = jd.get("preferred_skills", [])

    if not pref_skills:
        return 5.0

    ratio = compute_match_ratio(cand_pool, pref_skills, threshold=0.45)
    return round(ratio * 10, 1)


def score_ownership(candidate: dict, jd: dict) -> float:
    """Score ownership level alignment (0-10)."""
    cand_ownership = candidate.get("ownership", "basic")
    jd_ownership = jd.get("ownership_level", "Medium").lower()

    ownership_scores = {
        "end-to-end": {"high": 10, "medium": 9, "low": 8},
        "block":      {"high": 7,  "medium": 8, "low": 9},
        "basic":      {"high": 3,  "medium": 5, "low": 7},
    }

    return float(ownership_scores.get(cand_ownership, {}).get(jd_ownership, 5))


def compute_match_score(candidate: dict, jd: dict) -> tuple:
    """
    Compute total Match Score (0-100).
    Returns (total_score, breakdown_dict, gap_analysis).
    """
    skill_score, gap = score_required_skills(candidate, jd)
    tool_score = score_tools(candidate, jd)
    exp_score = score_experience(candidate, jd)
    pref_score = score_preferred_skills(candidate, jd)
    own_score = score_ownership(candidate, jd)

    total = skill_score + tool_score + exp_score + pref_score + own_score

    # Cap at 100
    total = min(total, 100.0)

    breakdown = {
        "required_skills": round(skill_score, 1),
        "tools": round(tool_score, 1),
        "experience": round(exp_score, 1),
        "preferred_skills": round(pref_score, 1),
        "ownership": round(own_score, 1),
    }

    return round(total, 1), breakdown, gap


# ─────────────────────────────────────────────
# Interest Score (Behavioral Fit) — out of 100
# ─────────────────────────────────────────────
# Breakdown:
#   Role Alignment    → 40 pts
#   Seniority Fit     → 20 pts
#   Growth Potential   → 20 pts
#   Selectiveness     → 20 pts

def compute_interest_score(candidate: dict, jd: dict, match_score: float) -> tuple:
    """
    Estimate candidate's likely interest in the role.
    Uses match score, experience alignment, and ownership level.
    Returns (total_score, breakdown_dict).
    """
    exp = candidate.get("experience", 0)
    min_exp = jd.get("experience_min", 0)
    max_exp = jd.get("experience_max", 100)
    cand_ownership = candidate.get("ownership", "basic")

    # ── Role Alignment (0-40) ──
    # Higher match = more likely interested (role fits their profile)
    if match_score >= 85:
        role_alignment = 35
    elif match_score >= 70:
        role_alignment = 28
    elif match_score >= 55:
        role_alignment = 22
    elif match_score >= 40:
        role_alignment = 15
    else:
        role_alignment = 8

    # Bonus if experience is in sweet spot
    if min_exp <= exp <= max_exp:
        role_alignment = min(role_alignment + 3, 40)

    # ── Seniority Fit (0-20) ──
    if min_exp <= exp <= max_exp:
        seniority = 18
    elif exp > max_exp:
        # Over-qualified might be less interested
        overshoot = exp - max_exp
        if overshoot <= 2:
            seniority = 15
        elif overshoot <= 5:
            seniority = 10
        else:
            seniority = 6
    else:
        # Under-qualified might be very eager
        seniority = 14

    # ── Growth Potential (0-20) ──
    # Junior/mid candidates see more growth potential
    if exp <= 3:
        growth = 16  # Early career — high growth motivation
    elif exp <= 6:
        growth = 13
    elif exp <= 10:
        growth = 10
    else:
        growth = 7  # Very senior — growth less of a draw

    # Higher ownership expectation = more growth opportunity
    jd_ownership = jd.get("ownership_level", "Medium").lower()
    if jd_ownership == "high" and cand_ownership in ("block", "basic"):
        growth = min(growth + 3, 20)  # Step-up opportunity

    # ── Selectiveness (0-20) ──
    # More experienced candidates are pickier
    if exp >= 10:
        selectiveness = 8   # Very selective
    elif exp >= 7:
        selectiveness = 12
    elif exp >= 4:
        selectiveness = 16
    else:
        selectiveness = 18  # Less selective, more open

    total = role_alignment + seniority + growth + selectiveness
    total = min(total, 100.0)

    breakdown = {
        "role_alignment": round(role_alignment, 1),
        "seniority_fit": round(seniority, 1),
        "growth_potential": round(growth, 1),
        "selectiveness": round(selectiveness, 1),
    }

    return round(total, 1), breakdown


# ─────────────────────────────────────────────
# Final Score
# ─────────────────────────────────────────────

def compute_final_score(match_score: float, interest_score: float) -> float:
    """Final Score = (0.7 × Match) + (0.3 × Interest)"""
    return round((0.7 * match_score) + (0.3 * interest_score), 1)


# ─────────────────────────────────────────────
# Main Scoring Function
# ─────────────────────────────────────────────

def score_candidate(candidate: dict, jd: dict) -> dict:
    """
    Score a single candidate against a JD.
    Returns candidate dict enriched with all scores and analysis.
    """
    # Match Score
    match_score, match_breakdown, gap = compute_match_score(candidate, jd)

    # Interest Score (depends on match score)
    interest_score, interest_breakdown = compute_interest_score(
        candidate, jd, match_score
    )

    # Final Score
    final_score = compute_final_score(match_score, interest_score)

    # Enrich candidate dict
    candidate["match_score"] = match_score
    candidate["interest_score"] = interest_score
    candidate["final_score"] = final_score
    candidate["match_breakdown"] = match_breakdown
    candidate["interest_breakdown"] = interest_breakdown
    candidate["skill_gap"] = gap

    return candidate


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import json

    # Simulated parsed JD (Web Dev)
    jd = {
        "role": "Senior Full-Stack Developer",
        "required_skills": [
            "React.js", "TypeScript", "Node.js", "Express",
            "PostgreSQL", "MongoDB", "REST API", "Git"
        ],
        "preferred_skills": [
            "Docker", "Kubernetes", "AWS", "CI/CD"
        ],
        "tools": ["VS Code", "Jira", "GitHub Actions", "Postman"],
        "experience_min": 3,
        "experience_max": 6,
        "ownership_level": "Medium",
        "domain": "Web Development",
    }

    # Strong candidate
    candidate1 = {
        "name": "Sarah Johnson",
        "skills": [
            "React.js", "TypeScript", "Next.js", "Node.js",
            "Express", "REST API", "PostgreSQL", "MongoDB",
            "Redis", "Docker", "AWS", "Git", "CI/CD"
        ],
        "tools": ["VS Code", "Postman", "Jira", "GitHub Actions"],
        "experience": 5.2,
        "ownership": "end-to-end",
        "projects": [
            "Built full-stack e-commerce platform from scratch",
            "Led frontend architecture migration",
        ],
        "confidence": 100,
    }

    # Weak candidate
    candidate2 = {
        "name": "Raj Patel",
        "skills": [
            "JavaScript", "React.js", "HTML", "CSS",
            "Bootstrap", "Node.js", "MySQL"
        ],
        "tools": ["VS Code", "Git"],
        "experience": 1.5,
        "ownership": "basic",
        "projects": [
            "Frontend bug fixes",
            "Personal portfolio website",
        ],
        "confidence": 82,
    }

    print("=" * 60)
    print("SCORING: Web Dev JD")
    print("=" * 60)

    for cand in [candidate1, candidate2]:
        scored = score_candidate(cand, jd)
        print(f"\n{'─' * 50}")
        print(f"  {scored['name']}")
        print(f"  Match:    {scored['match_score']}/100")
        print(f"    Skills:    {scored['match_breakdown']['required_skills']}/40")
        print(f"    Tools:     {scored['match_breakdown']['tools']}/20")
        print(f"    Exp:       {scored['match_breakdown']['experience']}/20")
        print(f"    Preferred: {scored['match_breakdown']['preferred_skills']}/10")
        print(f"    Ownership: {scored['match_breakdown']['ownership']}/10")
        print(f"  Interest: {scored['interest_score']}/100")
        print(f"    Role:      {scored['interest_breakdown']['role_alignment']}/40")
        print(f"    Seniority: {scored['interest_breakdown']['seniority_fit']}/20")
        print(f"    Growth:    {scored['interest_breakdown']['growth_potential']}/20")
        print(f"    Select:    {scored['interest_breakdown']['selectiveness']}/20")
        print(f"  Final:    {scored['final_score']}/100")
        print(f"\n  Skill Gaps:")
        for g in scored["skill_gap"]["gaps"]:
            print(f"    ❌ {g['jd_skill']} (closest: {g['closest']}, {g['score']:.3f})")
        for m in scored["skill_gap"]["matched"]:
            print(f"    ✅ {m['jd_skill']} ← {m['candidate_skill']} ({m['score']:.3f})")