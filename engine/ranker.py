# engine/ranker.py
# Ranking engine — sorts candidates and assigns hiring verdicts


def assign_verdict(final_score: float) -> str:
    """Hiring decision based on final score."""
    if final_score >= 85:
        return "Strong Hire"
    elif final_score >= 72:
        return "Hire"
    elif final_score >= 58:
        return "Consider"
    elif final_score >= 45:
        return "Needs Evaluation"
    else:
        return "Not Recommended"


def assign_tier(rank: int, total: int) -> str:
    """Assign tier label based on rank position."""
    if total <= 1:
        return "Only Candidate"
    if rank == 1:
        return "Top Tier"
    if rank == total:
        return "Lower Tier"

    # Middle candidates
    if total <= 3:
        return "Mid Tier"

    pct = rank / total
    if pct <= 0.33:
        return "Top Tier"
    elif pct <= 0.66:
        return "Mid Tier"
    else:
        return "Lower Tier"


def rank_candidates(candidates: list) -> list:
    """
    Rank candidates by:
      1. Final Score (primary)
      2. Match Score (tie-breaker)
      3. Experience (secondary tie-breaker)

    Enriches each candidate with: verdict, rank, tier.
    """
    # Sort by final score, then match score, then experience
    ranked = sorted(
        candidates,
        key=lambda x: (
            x.get("final_score", 0),
            x.get("match_score", 0),
            x.get("experience", 0),
        ),
        reverse=True,
    )

    total = len(ranked)

    for i, c in enumerate(ranked):
        c["rank"] = i + 1
        c["verdict"] = assign_verdict(c.get("final_score", 0))
        c["tier"] = assign_tier(i + 1, total)

    return ranked


# ─────────────────────────────────────────────
# Candidate Comparison
# ─────────────────────────────────────────────

def compare_top_two(ranked: list) -> dict:
    """
    Generate head-to-head comparison between #1 and #2.
    Returns comparison dict with advantages/disadvantages.
    """
    if len(ranked) < 2:
        return {}

    first = ranked[0]
    second = ranked[1]

    comparison = {
        "candidate_1": first["name"],
        "candidate_2": second["name"],
        "score_diff": round(first["final_score"] - second["final_score"], 1),
        "advantages_1": [],
        "advantages_2": [],
    }

    # Compare each breakdown dimension
    b1 = first.get("match_breakdown", {})
    b2 = second.get("match_breakdown", {})

    dimensions = {
        "required_skills": ("Required Skills", 40),
        "tools": ("Tools", 20),
        "experience": ("Experience", 20),
        "preferred_skills": ("Preferred Skills", 10),
        "ownership": ("Ownership", 10),
    }

    for key, (label, max_score) in dimensions.items():
        s1 = b1.get(key, 0)
        s2 = b2.get(key, 0)

        if s1 > s2 + 1:  # Meaningful difference
            comparison["advantages_1"].append(
                f"{label}: {s1}/{max_score} vs {s2}/{max_score}"
            )
        elif s2 > s1 + 1:
            comparison["advantages_2"].append(
                f"{label}: {s2}/{max_score} vs {s1}/{max_score}"
            )

    # Compare interest breakdown
    i1 = first.get("interest_breakdown", {})
    i2 = second.get("interest_breakdown", {})

    interest_dims = {
        "role_alignment": ("Role Alignment", 40),
        "seniority_fit": ("Seniority Fit", 20),
        "growth_potential": ("Growth Potential", 20),
        "selectiveness": ("Openness", 20),
    }

    for key, (label, max_score) in interest_dims.items():
        s1 = i1.get(key, 0)
        s2 = i2.get(key, 0)

        if s1 > s2 + 2:
            comparison["advantages_1"].append(
                f"{label}: {s1}/{max_score} vs {s2}/{max_score}"
            )
        elif s2 > s1 + 2:
            comparison["advantages_2"].append(
                f"{label}: {s2}/{max_score} vs {s1}/{max_score}"
            )

    # Experience comparison
    e1 = first.get("experience", 0)
    e2 = second.get("experience", 0)
    if abs(e1 - e2) >= 1:
        more_exp = first["name"] if e1 > e2 else second["name"]
        comparison["experience_note"] = (
            f"{more_exp} has more experience ({max(e1, e2)} vs {min(e1, e2)} years)"
        )

    # Ownership comparison
    o1 = first.get("ownership", "basic")
    o2 = second.get("ownership", "basic")
    if o1 != o2:
        comparison["ownership_note"] = (
            f"{first['name']}: {o1} ownership | {second['name']}: {o2} ownership"
        )

    return comparison


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import json

    candidates = [
        {
            "name": "Sarah Johnson",
            "match_score": 99.0,
            "interest_score": 90,
            "final_score": 96.3,
            "experience": 5.2,
            "ownership": "end-to-end",
            "match_breakdown": {
                "required_skills": 40, "tools": 20,
                "experience": 20, "preferred_skills": 10, "ownership": 9
            },
            "interest_breakdown": {
                "role_alignment": 40, "seniority_fit": 18,
                "growth_potential": 16, "selectiveness": 16
            },
        },
        {
            "name": "Raj Patel",
            "match_score": 65.0,
            "interest_score": 80,
            "final_score": 69.5,
            "experience": 1.5,
            "ownership": "basic",
            "match_breakdown": {
                "required_skills": 36, "tools": 14,
                "experience": 10, "preferred_skills": 0, "ownership": 5
            },
            "interest_breakdown": {
                "role_alignment": 30, "seniority_fit": 14,
                "growth_potential": 18, "selectiveness": 18
            },
        },
    ]

    ranked = rank_candidates(candidates)

    print("=" * 50)
    print("RANKED CANDIDATES")
    print("=" * 50)
    for c in ranked:
        print(f"  #{c['rank']} {c['name']:20s} | {c['final_score']:5.1f} | {c['verdict']:18s} | {c['tier']}")

    print("\n" + "=" * 50)
    print("HEAD-TO-HEAD COMPARISON")
    print("=" * 50)
    comp = compare_top_two(ranked)
    print(json.dumps(comp, indent=2))